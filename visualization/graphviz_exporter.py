from __future__ import annotations

from typing import Generic, Literal, TypeVar

from algorithms.kplan_solver import KPlanSolver
from core.planning_result import PlanningResult
from core.problem import Problem
from core.state import State
from visualization.profile import VisualizationProfile

StateT = TypeVar("StateT", bound=State)
ActionT = TypeVar("ActionT")

GraphMode = Literal["full_graph", "policy_only"]


class GraphvizExporter(Generic[StateT, ActionT]):
    def __init__(
        self,
        mode: GraphMode = "full_graph",
        simplify_action_labels: bool = True,
        highlight_bad_outcomes: bool = True,
        title: str | None = None,
        show_legend: bool = False,
        requested_k: int | None = None,
        profile: VisualizationProfile[StateT, ActionT] | None = None,
    ) -> None:
        if mode not in {"full_graph", "policy_only"}:
            raise ValueError("mode must be 'full_graph' or 'policy_only'.")

        self._mode = mode
        self._simplify_action_labels = simplify_action_labels
        self._highlight_bad_outcomes = highlight_bad_outcomes
        self._title = title
        self._show_legend = show_legend
        self._requested_k = requested_k
        self._profile = profile or VisualizationProfile()

    def export(
        self,
        problem: Problem[StateT, ActionT],
        solver: KPlanSolver[StateT, ActionT],
        result: PlanningResult[StateT, ActionT],
    ) -> str:
        if self._mode == "policy_only":
            visible_states = self._policy_reachable_states(problem, solver, result)
        else:
            visible_states = set(solver.states())

        states = self._sorted_states(frozenset(visible_states))
        node_ids = {state: f"s{index}" for index, state in enumerate(states)}

        initial_state = problem.initial_state()
        initial_k = result.k_values.get(initial_state, -1)

        lines: list[str] = [
            "digraph kplan {",
            "    rankdir=LR;",
            '    graph [pad="0.3", nodesep="0.4", ranksep="0.7", splines=true];',
            '    node [shape=circle, fontname="Helvetica", fontsize="11", margin="0.08"];',
            '    edge [fontname="Helvetica", fontsize="10"];',
        ]

        lines.extend(
            self._graph_header_lines(
                problem=problem,
                result=result,
                initial_k=initial_k,
            )
        )

        if self._show_legend:
            lines.extend(self._legend_lines())

        lines.extend(self._cluster_lines(states, node_ids))

        for state in states:
            node_id = node_ids[state]
            k_value = result.k_values.get(state, -1)
            is_initial = state == initial_state
            is_goal = problem.is_goal(state)
            is_dead_end = k_value == -1

            label = self._format_state_label(
                solver=solver,
                state=state,
                k_value=k_value,
                is_goal=is_goal,
            )

            attributes = self._node_attributes(
                label=label,
                is_initial=is_initial,
                is_goal=is_goal,
                is_dead_end=is_dead_end,
            )

            lines.append(f"    {node_id} [{self._format_attributes(attributes)}];")

        for state in states:
            source_id = node_ids[state]
            policy_action = result.policy.get_action(state)
            actions = self._actions_to_render(solver, state, policy_action)

            for action in actions:
                successors = self._sorted_states(solver.successors_of(state, action))

                for successor in successors:
                    if successor not in visible_states:
                        continue

                    target_id = node_ids[successor]
                    attributes = self._edge_attributes(
                        action=action,
                        is_policy_action=(policy_action == action),
                        successor=successor,
                    )

                    lines.append(
                        f"    {source_id} -> {target_id} "
                        f"[{self._format_attributes(attributes)}];"
                    )

        lines.append("}")
        return "\n".join(lines)

    def export_to_file(
        self,
        problem: Problem[StateT, ActionT],
        solver: KPlanSolver[StateT, ActionT],
        result: PlanningResult[StateT, ActionT],
        output_path: str,
    ) -> None:
        dot = self.export(problem, solver, result)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(dot)

    def _graph_header_lines(
        self,
        problem: Problem[StateT, ActionT],
        result: PlanningResult[StateT, ActionT],
        initial_k: int,
    ) -> list[str]:
        title = self._title or self._profile.graph_title(
            problem=problem,
            result=result,
            mode=self._mode,
            requested_k=self._requested_k,
        )

        explanation = self._profile.graph_explanation(problem)
        state_format = self._profile.graph_state_format(problem)

        parts: list[str] = []

        if title:
            parts.append(title)

        if explanation:
            parts.append(explanation)

        if state_format:
            parts.append(state_format)

        if not parts:
            return []

        graph_label = "".join(f"{part}\\l" for part in parts)

        return [
            '    labelloc="t";',
            '    labeljust="l";',
            '    margin="0.2";',
            '    fontname="Helvetica";',
            f'    label="{graph_label}";',
        ]

    def _legend_lines(self) -> list[str]:
        return []

    def _actions_to_render(
        self,
        solver: KPlanSolver[StateT, ActionT],
        state: StateT,
        policy_action: ActionT | None,
    ) -> list[ActionT]:
        if self._mode == "policy_only":
            if policy_action is None:
                return []
            return [policy_action]

        return self._sorted_actions(solver.actions_for(state))

    def _policy_reachable_states(
        self,
        problem: Problem[StateT, ActionT],
        solver: KPlanSolver[StateT, ActionT],
        result: PlanningResult[StateT, ActionT],
    ) -> set[StateT]:
        initial_state = problem.initial_state()
        visited: set[StateT] = set()
        to_visit: list[StateT] = [initial_state]

        while to_visit:
            state = to_visit.pop()

            if state in visited:
                continue

            visited.add(state)

            policy_action = result.policy.get_action(state)
            if policy_action is None:
                continue

            for successor in solver.successors_of(state, policy_action):
                if successor not in visited:
                    to_visit.append(successor)

        return visited

    def _cluster_lines(
        self,
        states: list[StateT],
        node_ids: dict[StateT, str],
    ) -> list[str]:
        groups: dict[str | int, list[StateT]] = {}

        for state in states:
            key = self._profile.cluster_key(state)
            if key is None:
                continue

            groups.setdefault(key, []).append(state)

        lines: list[str] = []

        for key in sorted(groups, key=str):
            ranked_states = sorted(groups[key], key=self._profile.state_sort_key)
            node_list = "; ".join(node_ids[state] for state in ranked_states)
            cluster_name = str(key).replace(" ", "_").replace("-", "_")

            lines.append(f"    subgraph cluster_{cluster_name} {{")
            lines.append(f'        label="{self._profile.cluster_label(key)}";')
            lines.append('        color="gray85";')
            lines.append('        style="rounded";')
            lines.append(f"        {node_list};")
            lines.append("    }")

        return lines

    def _sorted_states(self, states: frozenset[StateT]) -> list[StateT]:
        return sorted(states, key=self._profile.state_sort_key)

    def _sorted_actions(self, actions: frozenset[ActionT]) -> list[ActionT]:
        return sorted(
            actions,
            key=lambda action: self._profile.action_label(
                action,
                simplify=self._simplify_action_labels,
            ),
        )

    def _format_state_label(
        self,
        solver: KPlanSolver[StateT, ActionT],
        state: StateT,
        k_value: int,
        is_goal: bool,
    ) -> str:
        state_repr = self._profile.state_repr(state)
        goal_distance = solver.goal_distance_of(state)
        distance_label = "∞" if goal_distance is None else str(goal_distance)

        if is_goal:
            return f"{state_repr}\\nGOAL\\nk=∞\\nd={distance_label}"

        return f"{state_repr}\\nk={k_value}\\nd={distance_label}"

    def _node_attributes(
        self,
        label: str,
        is_initial: bool,
        is_goal: bool,
        is_dead_end: bool,
    ) -> dict[str, str]:
        attributes: dict[str, str] = {
            "label": label,
            "shape": "circle",
        }

        if is_initial:
            attributes["penwidth"] = "2"

        if is_goal:
            attributes["peripheries"] = "2"
            attributes["color"] = "green"

        if is_dead_end:
            attributes["color"] = "red"

        return attributes

    def _edge_attributes(
        self,
        action: ActionT,
        is_policy_action: bool,
        successor: StateT,
    ) -> dict[str, str]:
        attributes: dict[str, str] = {
            "label": self._profile.action_label(
                action,
                simplify=self._simplify_action_labels,
            ),
        }

        if is_policy_action:
            attributes["color"] = "blue"
            attributes["penwidth"] = "2"

        if self._highlight_bad_outcomes and self._profile.is_bad_outcome(successor):
            attributes["color"] = "red"
            attributes["penwidth"] = "2"

        return attributes

    def _format_attributes(self, attributes: dict[str, str]) -> str:
        parts: list[str] = []

        for key, value in attributes.items():
            escaped_value = value.replace('"', '\\"')
            parts.append(f'{key}="{escaped_value}"')

        return ", ".join(parts)