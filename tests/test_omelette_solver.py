from algorithms.kplan_solver import KPlanSolver
from domains.omelette.actions import OmeletteAction
from domains.omelette.problem import OmeletteProblem
from domains.omelette.state import OmeletteState


def build_problem(
    total_eggs: int = 4,
    goal_good_eggs: int = 2,
) -> OmeletteProblem:
    return OmeletteProblem(
        total_eggs=total_eggs,
        goal_good_eggs=goal_good_eggs,
    )


def test_goal_state_has_requested_k_value() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=2)

    assert result.k_values[OmeletteState(2, False, 0)] == 2


def test_initial_state_has_kplan_1_with_four_eggs_and_goal_two() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=3)

    assert result.k_values[problem.initial_state()] == 1


def test_initial_state_does_not_reach_kplan_2_with_four_eggs_and_goal_two() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=3)

    assert result.k_values[problem.initial_state()] < 2


def test_initial_state_has_kplan_0_with_two_eggs_and_goal_two() -> None:
    problem = build_problem(total_eggs=2, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=1)

    assert result.k_values[problem.initial_state()] == 0


def test_state_with_too_many_discarded_eggs_can_remain_without_plan() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=2)

    assert result.k_values[OmeletteState(0, False, 3)] == -1


def test_policy_chooses_break_egg_in_initial_state() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=2)

    assert result.policy.get_action(problem.initial_state()) == OmeletteAction.BREAK_EGG


def test_policy_chooses_empty_pan_in_contaminated_state_when_recovery_is_possible() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=1)

    assert result.policy.get_action(OmeletteState(1, True, 0)) == OmeletteAction.EMPTY_PAN


def test_clean_state_with_one_good_egg_has_a_policy_action() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=2)

    assert result.policy.get_action(OmeletteState(1, False, 0)) is not None


def test_hopeless_state_has_no_policy_action() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)
    solver = KPlanSolver[OmeletteState, OmeletteAction]()

    result = solver.solve(problem, k=2)

    assert result.k_values[OmeletteState(0, False, 3)] == -1
    assert result.policy.get_action(OmeletteState(0, False, 3)) is None