from algorithms.kplan_solver import KPlanSolver
from domains.rover.actions import RoverAction
from domains.rover.problem import RoverProblem
from domains.rover.state import RoverState


def build_problem() -> RoverProblem:
    return RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
    )


def test_goal_state_has_requested_k_value() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    result = solver.solve(problem, k=2)

    assert result.k_values[RoverState(1, 1)] == 2


def test_initial_state_has_at_least_zero_kplan_when_goal_is_reachable() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    result = solver.solve(problem, k=0)

    assert result.k_values[RoverState(0, 0)] >= 0


def test_policy_returns_some_action_for_promoted_non_goal_state() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    result = solver.solve(problem, k=0)

    action = result.policy.get_action(RoverState(0, 0))

    assert action is not None


def test_policy_returns_none_for_goal_state() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    result = solver.solve(problem, k=1)

    assert result.policy.get_action(RoverState(1, 1)) is None


def test_states_returns_all_explored_states_as_frozenset() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=1)

    states = solver.states()

    assert isinstance(states, frozenset)
    assert states == frozenset(
        {
            RoverState(0, 0),
            RoverState(0, 1),
            RoverState(1, 0),
            RoverState(1, 1),
        }
    )


def test_goal_states_returns_goal_states_as_frozenset() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=1)

    goal_states = solver.goal_states()

    assert isinstance(goal_states, frozenset)
    assert goal_states == frozenset({RoverState(1, 1)})


def test_actions_for_returns_available_actions_for_known_state() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=0)

    actions = solver.actions_for(RoverState(0, 0))

    assert isinstance(actions, frozenset)
    assert actions == frozenset(
        {
            RoverAction.MOVE_NORTH,
            RoverAction.MOVE_SOUTH,
            RoverAction.MOVE_EAST,
            RoverAction.MOVE_WEST,
        }
    )


def test_actions_for_returns_empty_frozenset_for_unknown_state() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=0)

    actions = solver.actions_for(RoverState(99, 99))

    assert isinstance(actions, frozenset)
    assert actions == frozenset()


def test_successors_of_returns_successors_for_known_state_action() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=0)

    successors = solver.successors_of(RoverState(0, 0), RoverAction.MOVE_EAST)

    assert isinstance(successors, frozenset)
    assert successors
    assert all(isinstance(state, RoverState) for state in successors)


def test_successors_of_returns_empty_frozenset_for_unknown_transition() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=0)

    successors = solver.successors_of(RoverState(99, 99), RoverAction.MOVE_EAST)

    assert isinstance(successors, frozenset)
    assert successors == frozenset()


def test_predecessors_of_returns_predecessor_state_action_pairs() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=0)

    predecessors = solver.predecessors_of(RoverState(1, 1))

    assert isinstance(predecessors, frozenset)
    assert predecessors
    assert all(isinstance(item, tuple) for item in predecessors)
    assert all(len(item) == 2 for item in predecessors)


def test_predecessors_of_returns_empty_frozenset_for_unknown_state() -> None:
    problem = build_problem()
    solver = KPlanSolver[RoverState, RoverAction]()

    solver.solve(problem, k=0)

    predecessors = solver.predecessors_of(RoverState(99, 99))

    assert isinstance(predecessors, frozenset)
    assert predecessors == frozenset()