from collections import deque
from dataclasses import dataclass
from typing import Generic, Mapping, TypeVar

from core.planner import Planner
from core.planning_result import PlanningResult
from core.policy import Policy
from core.problem import Problem
from core.state import State

StateT = TypeVar("StateT", bound=State)
ActionT = TypeVar("ActionT")


@dataclass(frozen=True)
class ExplicitPolicy(Generic[StateT, ActionT], Policy[StateT, ActionT]):
    _actions_by_state: Mapping[StateT, ActionT]

    def get_action(self, state: StateT) -> ActionT | None:
        return self._actions_by_state.get(state)


class KPlanSolver(Generic[StateT, ActionT], Planner[StateT, ActionT]):
    """
    Generic k-plan solver.

    Current capabilities:
    - explores the reachable state space
    - stores actions, successors and predecessors
    - computes k-values through backward propagation
    - builds an explicit state -> action policy

    Semantics:
    - kPlan = 0  -> there exists a path/policy to the goal with zero tolerated
                    adverse outcomes
    - kPlan = i  -> there exists a policy that tolerates up to i adverse outcomes
    """

    def __init__(self) -> None:
        self._reset()

    def solve(
        self,
        problem: Problem[StateT, ActionT],
        k: int,
    ) -> PlanningResult[StateT, ActionT]:
        if k < 0:
            raise ValueError("k must be greater than or equal to zero.")

        self._reset()
        self._explore(problem)
        self._compute_k_values(k)

        policy = ExplicitPolicy[StateT, ActionT](dict(self._policy_actions))

        return PlanningResult(
            policy=policy,
            k_values=dict(self._k_values),
        )

    def _reset(self) -> None:
        self._states: set[StateT] = set()
        self._goal_states: set[StateT] = set()
        self._actions_by_state: dict[StateT, set[ActionT]] = {}
        self._successors_by_state_action: dict[tuple[StateT, ActionT], set[StateT]] = {}
        self._predecessors_by_state: dict[StateT, set[tuple[StateT, ActionT]]] = {}

        self._k_values: dict[StateT, int] = {}
        self._policy_actions: dict[StateT, ActionT] = {}

    def _explore(self, problem: Problem[StateT, ActionT]) -> None:
        initial_state = problem.initial_state()
        queue: deque[StateT] = deque([initial_state])

        while queue:
            current_state = queue.popleft()

            if current_state in self._states:
                continue

            self._states.add(current_state)
            self._predecessors_by_state.setdefault(current_state, set())

            if problem.is_goal(current_state):
                self._goal_states.add(current_state)

            actions = set(problem.get_actions(current_state))
            self._actions_by_state[current_state] = actions

            for action in actions:
                successors = set(problem.get_successors(current_state, action))
                self._successors_by_state_action[(current_state, action)] = successors

                for successor in successors:
                    self._predecessors_by_state.setdefault(successor, set()).add(
                        (current_state, action)
                    )

                    if successor not in self._states:
                        queue.append(successor)

    def _compute_k_values(self, max_k: int) -> None:
        self._k_values = {state: -1 for state in self._states}
        self._policy_actions = {}

        for level in range(max_k + 1):
            queue: deque[StateT] = deque()

            for goal_state in self._goal_states:
                if self._k_values[goal_state] < level:
                    self._k_values[goal_state] = level
                queue.append(goal_state)

            while queue:
                current_state = queue.popleft()

                predecessors = self._predecessors_by_state.get(current_state, set())

                for predecessor_state, action in predecessors:
                    if self._k_values[predecessor_state] >= level:
                        continue

                    if self._can_promote_state(predecessor_state, action, level):
                        self._k_values[predecessor_state] = level
                        self._policy_actions[predecessor_state] = action
                        queue.append(predecessor_state)

    def _can_promote_state(
        self,
        state: StateT,
        action: ActionT,
        level: int,
    ) -> bool:
        successors = self._successors_by_state_action.get((state, action), set())

        if not successors:
            return False

        minimum_required_level = level - 1

        for successor in successors:
            if self._k_values.get(successor, -1) < minimum_required_level:
                return False

        return True

    def states(self) -> frozenset[StateT]:
        return frozenset(self._states)

    def goal_states(self) -> frozenset[StateT]:
        return frozenset(self._goal_states)

    def actions_for(self, state: StateT) -> frozenset[ActionT]:
        return frozenset(self._actions_by_state.get(state, set()))

    def successors_of(self, state: StateT, action: ActionT) -> frozenset[StateT]:
        return frozenset(self._successors_by_state_action.get((state, action), set()))

    def predecessors_of(self, state: StateT) -> frozenset[tuple[StateT, ActionT]]:
        return frozenset(self._predecessors_by_state.get(state, set()))