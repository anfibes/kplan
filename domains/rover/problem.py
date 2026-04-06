from dataclasses import dataclass, field
from typing import FrozenSet

from core.problem import Problem
from core.state import State
from domains.rover.actions import RoverAction
from domains.rover.state import RoverState


@dataclass(frozen=True)
class RoverProblem(Problem[RoverState, RoverAction]):
    width: int
    height: int
    initial: RoverState
    goal: RoverState
    blocked_cells: FrozenSet[tuple[int, int]] = field(
        default_factory=lambda: frozenset()
    )

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Grid width and height must be greater than zero.")

        if not self._is_within_bounds(self.initial):
            raise ValueError("Initial state is outside the grid.")

        if not self._is_within_bounds(self.goal):
            raise ValueError("Goal state is outside the grid.")

        if self._is_blocked(self.initial):
            raise ValueError("Initial state cannot be blocked.")

        if self._is_blocked(self.goal):
            raise ValueError("Goal state cannot be blocked.")

        for x, y in self.blocked_cells:
            if not self._is_within_bounds_xy(x, y):
                raise ValueError(f"Blocked cell ({x}, {y}) is outside the grid.")

    def initial_state(self) -> RoverState:
        return self.initial

    def get_actions(self, state: RoverState) -> set[RoverAction]:
        self._validate_state_type(state)

        return {
            RoverAction.MOVE_NORTH,
            RoverAction.MOVE_SOUTH,
            RoverAction.MOVE_EAST,
            RoverAction.MOVE_WEST,
        }

    def get_successors(self, state: RoverState, action: RoverAction) -> set[RoverState]:
        self._validate_state_type(state)

        candidate_positions = self._candidate_positions(state, action)

        successors = {
            self._normalize_position(state, x, y)
            for x, y in candidate_positions
        }

        return successors

    def is_goal(self, state: RoverState) -> bool:
        self._validate_state_type(state)
        return state == self.goal

    def _candidate_positions(
        self,
        state: RoverState,
        action: RoverAction,
    ) -> list[tuple[int, int]]:
        x = state.x
        y = state.y

        if action == RoverAction.MOVE_NORTH:
            return [
                (x, y + 1),
                (x - 1, y),
                (x + 1, y),
                (x, y),
            ]

        if action == RoverAction.MOVE_SOUTH:
            return [
                (x, y - 1),
                (x - 1, y),
                (x + 1, y),
                (x, y),
            ]

        if action == RoverAction.MOVE_EAST:
            return [
                (x + 1, y),
                (x, y + 1),
                (x, y - 1),
                (x, y),
            ]

        if action == RoverAction.MOVE_WEST:
            return [
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
                (x, y),
            ]

        raise ValueError(f"Unsupported action: {action}")

    def _normalize_position(
        self,
        current_state: RoverState,
        x: int,
        y: int,
    ) -> RoverState:
        if not self._is_within_bounds_xy(x, y):
            return current_state

        candidate = RoverState(x=x, y=y)

        if self._is_blocked(candidate):
            return current_state

        return candidate

    def _is_within_bounds(self, state: RoverState) -> bool:
        return self._is_within_bounds_xy(state.x, state.y)

    def _is_within_bounds_xy(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_blocked(self, state: RoverState) -> bool:
        return (state.x, state.y) in self.blocked_cells

    def _validate_state_type(self, state: State) -> None:
        if not isinstance(state, RoverState):
            raise TypeError(
                f"RoverProblem expects RoverState, got {type(state).__name__}."
            )