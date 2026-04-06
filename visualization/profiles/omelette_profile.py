from __future__ import annotations

from core.planning_result import PlanningResult
from core.problem import Problem
from domains.omelette.actions import OmeletteAction
from domains.omelette.problem import OmeletteProblem
from domains.omelette.state import OmeletteState
from visualization.profile import SortKey, VisualizationProfile


class OmeletteVisualizationProfile(
    VisualizationProfile[OmeletteState, OmeletteAction]
):
    def graph_title(
        self,
        problem: Problem[OmeletteState, OmeletteAction],
        result: PlanningResult[OmeletteState, OmeletteAction],
        mode: str,
        requested_k: int | None,
    ) -> str | None:
        if not isinstance(problem, OmeletteProblem):
            return None

        initial_k = result.k_values.get(problem.initial_state(), -1)

        parts = [
            "kPlan — Omelette Domain",
            f"total_eggs={problem.total_eggs}",
            f"goal_good_eggs={problem.goal_good_eggs}",
        ]

        if requested_k is not None:
            parts.append(f"requested_k={requested_k}")

        parts.extend(
            [
                f"mode={mode}",
                f"initial_k={initial_k}",
            ]
        )

        return " | ".join(parts)

    def graph_explanation(
        self,
        problem: Problem[OmeletteState, OmeletteAction],
    ) -> str | None:
        return "k(s) = maximum number of future adverse outcomes still tolerable from state s"

    def graph_state_format(
        self,
        problem: Problem[OmeletteState, OmeletteAction],
    ) -> str | None:
        return "state = eggs_in_pan quality discarded_eggs | F=clean, T=contaminated"

    def state_repr(self, state: OmeletteState) -> str:
        return str(state)

    def state_sort_key(self, state: OmeletteState) -> SortKey:
        used_eggs = state.eggs_in_pan + state.discarded_eggs
        bad_flag = 1 if state.has_bad_egg_in_pan else 0

        return (
            used_eggs,
            bad_flag,
            -state.eggs_in_pan,
            state.discarded_eggs,
        )

    def is_bad_outcome(self, state: OmeletteState) -> bool:
        return state.has_bad_egg_in_pan

    def cluster_key(self, state: OmeletteState) -> int:
        return state.eggs_in_pan + state.discarded_eggs

    def cluster_label(self, key: str | int) -> str:
        return f"used eggs = {key}"