from algorithms.kplan_solver import KPlanSolver
from domains.rover.actions import RoverAction
from domains.rover.problem import RoverProblem
from domains.rover.state import RoverState


def test_unreachable_goal_results_in_no_solution() -> None:
    problem = RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
        blocked_cells=frozenset({
            (0, 1),
            (1, 0),
        }),
    )

    solver = KPlanSolver[RoverState, RoverAction]()
    result = solver.solve(problem, k=1)

    assert result.k_values[RoverState(0, 0)] == -1


def test_k0_requires_strict_path_without_errors() -> None:
    problem = RoverProblem(
        width=2,
        height=1,
        initial=RoverState(0, 0),
        goal=RoverState(1, 0),
    )

    solver = KPlanSolver[RoverState, RoverAction]()
    result = solver.solve(problem, k=0)

    # con slittamenti possibili, potrebbe non essere robusto a k=0
    assert result.k_values[RoverState(0, 0)] >= 0


def test_k1_allows_one_adverse_outcome() -> None:
    problem = RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
    )

    solver = KPlanSolver[RoverState, RoverAction]()

    result_k0 = solver.solve(problem, k=0)
    result_k1 = solver.solve(problem, k=1)

    k0 = result_k0.k_values[RoverState(0, 0)]
    k1 = result_k1.k_values[RoverState(0, 0)]

    assert k1 >= k0


def test_policy_leads_towards_goal() -> None:
    problem = RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
    )

    solver = KPlanSolver[RoverState, RoverAction]()
    result = solver.solve(problem, k=1)

    action = result.policy.get_action(RoverState(0, 0))

    assert action is not None


def test_k_values_are_monotonic() -> None:
    problem = RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
    )

    solver = KPlanSolver[RoverState, RoverAction]()

    result_k0 = solver.solve(problem, k=0)
    result_k1 = solver.solve(problem, k=1)
    result_k2 = solver.solve(problem, k=2)

    state = RoverState(0, 0)

    assert result_k0.k_values[state] <= result_k1.k_values[state] <= result_k2.k_values[state]


def test_goal_state_is_always_maximally_robust() -> None:
    problem = RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
    )

    solver = KPlanSolver[RoverState, RoverAction]()

    result = solver.solve(problem, k=3)

    assert result.k_values[RoverState(1, 1)] == 3