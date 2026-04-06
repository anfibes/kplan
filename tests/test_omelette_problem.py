import pytest

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


def test_initial_state_is_empty_clean_and_with_no_discarded_eggs() -> None:
    problem = build_problem()

    assert problem.initial_state() == OmeletteState(
        eggs_in_pan=0,
        has_bad_egg_in_pan=False,
        discarded_eggs=0,
    )


def test_goal_state_is_recognized_when_enough_good_eggs_are_in_pan() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    assert problem.is_goal(
        OmeletteState(
            eggs_in_pan=2,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        )
    )


def test_state_with_bad_egg_in_pan_is_not_goal() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    assert not problem.is_goal(
        OmeletteState(
            eggs_in_pan=2,
            has_bad_egg_in_pan=True,
            discarded_eggs=0,
        )
    )


def test_state_with_too_few_good_eggs_is_not_goal() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    assert not problem.is_goal(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        )
    )


def test_get_actions_allows_break_egg_when_eggs_are_available() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    actions = problem.get_actions(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=False,
            discarded_eggs=1,
        )
    )

    assert OmeletteAction.BREAK_EGG in actions


def test_get_actions_allows_empty_pan_when_pan_is_not_empty() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    actions = problem.get_actions(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        )
    )

    assert OmeletteAction.EMPTY_PAN in actions


def test_get_actions_allows_both_actions_when_pan_has_eggs_and_more_eggs_are_available() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    actions = problem.get_actions(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=True,
            discarded_eggs=1,
        )
    )

    assert actions == {
        OmeletteAction.BREAK_EGG,
        OmeletteAction.EMPTY_PAN,
    }


def test_get_actions_allows_only_break_egg_when_pan_is_empty_and_eggs_are_available() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    actions = problem.get_actions(
        OmeletteState(
            eggs_in_pan=0,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        )
    )

    assert actions == {OmeletteAction.BREAK_EGG}


def test_get_actions_allows_only_empty_pan_when_no_eggs_are_available_but_pan_is_not_empty() -> None:
    problem = build_problem(total_eggs=2, goal_good_eggs=2)

    actions = problem.get_actions(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=True,
            discarded_eggs=1,
        )
    )

    assert actions == {OmeletteAction.EMPTY_PAN}


def test_get_actions_returns_empty_set_when_no_eggs_are_available_and_pan_is_empty() -> None:
    problem = build_problem(total_eggs=2, goal_good_eggs=2)

    actions = problem.get_actions(
        OmeletteState(
            eggs_in_pan=0,
            has_bad_egg_in_pan=False,
            discarded_eggs=2,
        )
    )

    assert actions == set()


def test_break_egg_from_clean_state_produces_good_and_bad_successors() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    successors = problem.get_successors(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        ),
        OmeletteAction.BREAK_EGG,
    )

    assert successors == {
        OmeletteState(
            eggs_in_pan=2,
            has_bad_egg_in_pan=False,
            discarded_eggs=0,
        ),
        OmeletteState(
            eggs_in_pan=2,
            has_bad_egg_in_pan=True,
            discarded_eggs=0,
        ),
    }


def test_break_egg_from_already_contaminated_state_keeps_state_contaminated() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    successors = problem.get_successors(
        OmeletteState(
            eggs_in_pan=1,
            has_bad_egg_in_pan=True,
            discarded_eggs=0,
        ),
        OmeletteAction.BREAK_EGG,
    )

    assert successors == {
        OmeletteState(
            eggs_in_pan=2,
            has_bad_egg_in_pan=True,
            discarded_eggs=0,
        )
    }


def test_empty_pan_discards_all_eggs_and_cleans_the_pan() -> None:
    problem = build_problem(total_eggs=4, goal_good_eggs=2)

    successors = problem.get_successors(
        OmeletteState(
            eggs_in_pan=2,
            has_bad_egg_in_pan=True,
            discarded_eggs=1,
        ),
        OmeletteAction.EMPTY_PAN,
    )

    assert successors == {
        OmeletteState(
            eggs_in_pan=0,
            has_bad_egg_in_pan=False,
            discarded_eggs=3,
        )
    }


def test_problem_rejects_non_positive_total_eggs() -> None:
    with pytest.raises(ValueError, match="total_eggs must be greater than zero."):
        build_problem(total_eggs=0, goal_good_eggs=1)


def test_problem_rejects_non_positive_goal_good_eggs() -> None:
    with pytest.raises(ValueError, match="goal_good_eggs must be greater than zero."):
        build_problem(total_eggs=2, goal_good_eggs=0)


def test_problem_rejects_goal_good_eggs_greater_than_total_eggs() -> None:
    with pytest.raises(
        ValueError,
        match="goal_good_eggs cannot be greater than total_eggs.",
    ):
        build_problem(total_eggs=2, goal_good_eggs=3)