from algorithms.kplan_solver import KPlanSolver
from domains.omelette.actions import OmeletteAction
from domains.omelette.problem import OmeletteProblem
from domains.omelette.state import OmeletteState
from visualization.graphviz_exporter import GraphvizExporter
from core.planning_result import PlanningResult


def build_problem() -> OmeletteProblem:
    return OmeletteProblem(
        total_eggs=4,
        goal_good_eggs=2,
    )


def build_result() -> tuple[
    OmeletteProblem,
    KPlanSolver[OmeletteState, OmeletteAction],
    PlanningResult[OmeletteState, OmeletteAction],
]:
    problem = build_problem()
    solver = KPlanSolver[OmeletteState, OmeletteAction]()
    result = solver.solve(problem, k=2)
    return problem, solver, result


def test_policy_only_renders_only_policy_reachable_states() -> None:
    problem, solver, result = build_result()

    exporter = GraphvizExporter[OmeletteState, OmeletteAction](
        mode="policy_only",
        simplify_action_labels=True,
        highlight_bad_outcomes=True,
    )

    dot = exporter.export(problem, solver, result)

    # stati che devono comparire nel sottografo della policy
    assert 'label="0 F 0\\nk=1"' in dot
    assert 'label="1 F 0\\nk=1"' in dot
    assert 'label="1 T 0\\nk=0"' in dot
    assert 'label="0 F 1\\nk=0"' in dot
    assert 'label="1 T 1\\nk=0"' in dot
    assert 'label="2 F 0\\nGOAL\\nk=∞"' in dot
    assert 'label="2 F 1\\nGOAL\\nk=∞"' in dot
    assert 'label="2 F 2\\nGOAL\\nk=∞"' in dot

    # stati non raggiungibili seguendo la policy a partire dall'iniziale
    assert 'label="3 F 0\\nGOAL\\nk=∞"' not in dot
    assert 'label="3 F 1\\nGOAL\\nk=∞"' not in dot
    assert 'label="4 F 0\\nGOAL\\nk=∞"' not in dot
    assert 'label="0 F 4\\nk=-1"' not in dot


def test_full_graph_includes_states_hidden_by_policy_only() -> None:
    problem, solver, result = build_result()

    exporter = GraphvizExporter[OmeletteState, OmeletteAction](
        mode="full_graph",
        simplify_action_labels=True,
        highlight_bad_outcomes=True,
    )

    dot = exporter.export(problem, solver, result)

    assert 'label="3 F 0\\nGOAL\\nk=∞"' in dot
    assert 'label="3 F 1\\nGOAL\\nk=∞"' in dot
    assert 'label="4 F 0\\nGOAL\\nk=∞"' in dot
    assert 'label="0 F 4\\nk=-1"' in dot


def test_policy_only_uses_simplified_action_labels() -> None:
    problem, solver, result = build_result()

    exporter = GraphvizExporter[OmeletteState, OmeletteAction](
        mode="policy_only",
        simplify_action_labels=True,
        highlight_bad_outcomes=True,
    )

    dot = exporter.export(problem, solver, result)

    assert 'label="break_egg"' in dot
    assert 'label="empty_pan"' in dot
    assert "BREAK_EGG" not in dot
    assert "EMPTY_PAN" not in dot


def test_goals_are_rendered_with_infinite_k_label() -> None:
    problem, solver, result = build_result()

    exporter = GraphvizExporter[OmeletteState, OmeletteAction](
        mode="policy_only",
        simplify_action_labels=True,
        highlight_bad_outcomes=True,
    )

    dot = exporter.export(problem, solver, result)

    assert "\\nGOAL\\nk=∞" in dot

def test_show_goal_distance_adds_distance_to_labels_when_enabled() -> None:
    problem, solver, result = build_result()

    exporter = GraphvizExporter[OmeletteState, OmeletteAction](
        mode="policy_only",
        simplify_action_labels=True,
        highlight_bad_outcomes=True,
        show_goal_distance=True,
    )

    dot = exporter.export(problem, solver, result)

    assert 'label="0 F 0\\nk=1\\nd=2"' in dot
    assert 'label="1 F 0\\nk=1\\nd=1"' in dot
    assert 'label="2 F 0\\nGOAL\\nk=∞\\nd=0"' in dot