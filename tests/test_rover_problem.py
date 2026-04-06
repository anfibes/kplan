import pytest

from domains.rover.actions import RoverAction
from domains.rover.problem import RoverProblem
from domains.rover.state import RoverState


def build_problem(
    *,
    width: int = 5,
    height: int = 5,
    initial: RoverState = RoverState(0, 0),
    goal: RoverState = RoverState(4, 4),
    blocked_cells: frozenset[tuple[int, int]] = frozenset(),
) -> RoverProblem:
    return RoverProblem(
        width=width,
        height=height,
        initial=initial,
        goal=goal,
        blocked_cells=blocked_cells,
    )


def test_initial_state_is_returned_correctly() -> None:
    problem = build_problem(initial=RoverState(1, 2))

    assert problem.initial_state() == RoverState(1, 2)


def test_is_goal_returns_true_only_for_goal_state() -> None:
    problem = build_problem(goal=RoverState(3, 3))

    assert problem.is_goal(RoverState(3, 3)) is True
    assert problem.is_goal(RoverState(2, 3)) is False


def test_all_four_actions_are_available() -> None:
    problem = build_problem()
    state = RoverState(2, 2)

    actions = problem.get_actions(state)

    assert actions == {
        RoverAction.MOVE_NORTH,
        RoverAction.MOVE_SOUTH,
        RoverAction.MOVE_EAST,
        RoverAction.MOVE_WEST,
    }


def test_move_north_from_central_cell_returns_expected_successors() -> None:
    problem = build_problem()
    state = RoverState(2, 2)

    successors = problem.get_successors(state, RoverAction.MOVE_NORTH)

    assert successors == {
        RoverState(2, 3),  # intended move
        RoverState(1, 2),  # lateral slip left
        RoverState(3, 2),  # lateral slip right
        RoverState(2, 2),  # failure / no movement
    }


def test_move_west_from_left_border_stays_in_place_for_invalid_transition() -> None:
    problem = build_problem()
    state = RoverState(0, 2)

    successors = problem.get_successors(state, RoverAction.MOVE_WEST)

    assert successors == {
        RoverState(0, 2),  # west is invalid -> stay
        RoverState(0, 3),  # slip north
        RoverState(0, 1),  # slip south
    }


def test_blocked_cells_are_normalized_to_current_state() -> None:
    problem = build_problem(
        blocked_cells=frozenset({(2, 3), (1, 2)})
    )
    state = RoverState(2, 2)

    successors = problem.get_successors(state, RoverAction.MOVE_NORTH)

    assert successors == {
        RoverState(2, 2),  # north blocked -> stay
        RoverState(3, 2),  # right slip valid
    }


def test_problem_rejects_initial_state_outside_grid() -> None:
    with pytest.raises(ValueError, match="Initial state is outside the grid."):
        build_problem(initial=RoverState(-1, 0))


def test_problem_rejects_goal_state_outside_grid() -> None:
    with pytest.raises(ValueError, match="Goal state is outside the grid."):
        build_problem(goal=RoverState(10, 10))


def test_problem_rejects_blocked_initial_state() -> None:
    with pytest.raises(ValueError, match="Initial state cannot be blocked."):
        build_problem(
            initial=RoverState(1, 1),
            blocked_cells=frozenset({(1, 1)}),
        )


def test_problem_rejects_blocked_goal_state() -> None:
    with pytest.raises(ValueError, match="Goal state cannot be blocked."):
        build_problem(
            goal=RoverState(4, 4),
            blocked_cells=frozenset({(4, 4)}),
        )


def test_problem_rejects_blocked_cells_outside_grid() -> None:
    with pytest.raises(ValueError, match=r"Blocked cell \(9, 9\) is outside the grid."):
        build_problem(
            blocked_cells=frozenset({(9, 9)}),
        )