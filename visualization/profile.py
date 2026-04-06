from __future__ import annotations

from typing import Generic, TypeVar

from core.planning_result import PlanningResult
from core.problem import Problem
from core.state import State

StateT = TypeVar("StateT", bound=State)
ActionT = TypeVar("ActionT")
SortKey = str | tuple[int, ...]


class VisualizationProfile(Generic[StateT, ActionT]):
    def graph_title(
        self,
        problem: Problem[StateT, ActionT],
        result: PlanningResult[StateT, ActionT],
        mode: str,
        requested_k: int | None,
    ) -> str | None:
        return None

    def graph_explanation(
        self,
        problem: Problem[StateT, ActionT],
    ) -> str | None:
        return None

    def graph_state_format(
        self,
        problem: Problem[StateT, ActionT],
    ) -> str | None:
        return None

    def state_repr(self, state: StateT) -> str:
        return str(state)

    def state_sort_key(self, state: StateT) -> SortKey:
        return str(state)

    def action_label(self, action: ActionT, simplify: bool = True) -> str:
        if simplify and hasattr(action, "name"):
            action_name = getattr(action, "name")
            if isinstance(action_name, str):
                return action_name.lower()

        return str(action)

    def is_bad_outcome(self, state: StateT) -> bool:
        return False

    def cluster_key(self, state: StateT) -> str | int | None:
        return None

    def cluster_label(self, key: str | int) -> str:
        return str(key)