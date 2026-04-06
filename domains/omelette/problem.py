from dataclasses import dataclass

from core.problem import Problem
from domains.omelette.actions import OmeletteAction
from domains.omelette.state import OmeletteState


@dataclass(frozen=True)
class OmeletteProblem(Problem[OmeletteState, OmeletteAction]):
    total_eggs: int
    goal_good_eggs: int

    def __post_init__(self) -> None:
        if self.total_eggs <= 0:
            raise ValueError("total_eggs must be greater than zero.")

        if self.goal_good_eggs <= 0:
            raise ValueError("goal_good_eggs must be greater than zero.")

        if self.goal_good_eggs > self.total_eggs:
            raise ValueError("goal_good_eggs cannot be greater than total_eggs.")

    def initial_state(self) -> OmeletteState:
        return OmeletteState(
            eggs_in_pan=0,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        )

    def is_goal(self, state: OmeletteState) -> bool:
        return (
            state.eggs_in_pan >= self.goal_good_eggs
            and not state.has_bad_egg_in_pan
        )

    def get_actions(self, state: OmeletteState) -> set[OmeletteAction]:
        actions: set[OmeletteAction] = set()

        if self._has_eggs_available(state):
            actions.add(OmeletteAction.BREAK_EGG)

        if state.eggs_in_pan > 0:
            actions.add(OmeletteAction.EMPTY_PAN)

        return actions

    def get_successors(
        self,
        state: OmeletteState,
        action: OmeletteAction,
    ) -> set[OmeletteState]:
        if action == OmeletteAction.BREAK_EGG:
            return self._break_egg_successors(state)

        if action == OmeletteAction.EMPTY_PAN:
            return {self._empty_pan_successor(state)}

        raise ValueError(f"Unsupported action: {action}")

    def _has_eggs_available(self, state: OmeletteState) -> bool:
        used_eggs = state.eggs_in_pan + state.discarded_eggs
        return used_eggs < self.total_eggs

    def _break_egg_successors(self, state: OmeletteState) -> set[OmeletteState]:
        if not self._has_eggs_available(state):
            return set()

        good_successor = OmeletteState(
            eggs_in_pan=state.eggs_in_pan + 1,
            has_bad_egg_in_pan=state.has_bad_egg_in_pan,
            discarded_eggs=state.discarded_eggs,
        )

        bad_successor = OmeletteState(
            eggs_in_pan=state.eggs_in_pan + 1,
            has_bad_egg_in_pan=True,
            discarded_eggs=state.discarded_eggs,
        )

        return {good_successor, bad_successor}

    def _empty_pan_successor(self, state: OmeletteState) -> OmeletteState:
        return OmeletteState(
            eggs_in_pan=0,
            has_bad_egg_in_pan=False,
            discarded_eggs=state.discarded_eggs + state.eggs_in_pan,
        )