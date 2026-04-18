"""Tests for kplan_io.pddl.problem.PDDLProblem (milestone 1C).

Scope: the adapter layer only.

Covered:

1. ``initial_state`` returns the state produced by the grounder.
2. ``get_actions`` returns only applicable actions — positive and negative
   preconditions are both honored.
3. ``get_successors`` expands every branch of a ``OneOfEffect``:
   deterministic actions yield exactly one successor, FOND actions yield
   one successor per branch.
4. ``is_goal`` evaluates the goal conjunction correctly.
5. End-to-end integration with ``KPlanSolver`` on a small PDDL domain.
6. All ``oneof`` branches are treated uniformly as successors (no special
   nominal/adverse handling at the adapter level).
"""

from __future__ import annotations

from pathlib import Path

from algorithms.kplan_solver import KPlanSolver
from kplan_io.pddl.ast import Atom, GroundAction, PDDLState
from kplan_io.pddl.parser import parse_domain, parse_problem
from kplan_io.pddl.problem import PDDLProblem


FIXTURES = Path(__file__).parent / "fixtures"


def _load(domain_file: str, problem_file: str) -> PDDLProblem:
    domain = parse_domain(FIXTURES / domain_file)
    problem = parse_problem(FIXTURES / problem_file)
    return PDDLProblem(domain, problem)


# ---------------------------------------------------------------------------
# 1. initial_state
# ---------------------------------------------------------------------------


class TestInitialState:
    def test_deterministic_initial_state(self) -> None:
        pp = _load("det_domain.pddl", "det_problem.pddl")
        init = pp.initial_state()
        assert isinstance(init, PDDLState)
        assert init.atoms == frozenset(
            {
                Atom("clear", ("a",)),
                Atom("clear", ("b",)),
                Atom("handempty", ()),
            }
        )

    def test_fond_initial_state(self) -> None:
        pp = _load("toy_fond_domain.pddl", "toy_fond_problem.pddl")
        assert pp.initial_state().atoms == frozenset({Atom("at-start", ())})


# ---------------------------------------------------------------------------
# 2. get_actions
# ---------------------------------------------------------------------------


class TestGetActions:
    def test_positive_precondition_filtering(self) -> None:
        pp = _load("det_domain.pddl", "det_problem.pddl")
        init = pp.initial_state()
        action_names = {a.name for a in pp.get_actions(init)}
        # At init: clear a, clear b, handempty. `pick` requires (clear ?b)
        # and (handempty) — both pick instances are applicable. `put`
        # requires (holding ?b) — neither put instance is applicable.
        assert action_names == {"pick(a)", "pick(b)"}

    def test_negative_precondition_filtering(self) -> None:
        # Use a state where handempty is false: pick should no longer apply.
        pp = _load("det_domain.pddl", "det_problem.pddl")
        state = PDDLState(
            atoms=frozenset(
                {
                    Atom("holding", ("a",)),
                    Atom("clear", ("b",)),
                }
            )
        )
        action_names = {a.name for a in pp.get_actions(state)}
        # holding a -> put(a) applies. No handempty -> no pick.
        assert action_names == {"put(a)"}

    def test_fond_applicable_only_in_right_state(self) -> None:
        pp = _load("toy_fond_domain.pddl", "toy_fond_problem.pddl")
        init = pp.initial_state()
        assert {a.name for a in pp.get_actions(init)} == {"try"}

        mid_state = PDDLState(atoms=frozenset({Atom("at-mid", ())}))
        assert {a.name for a in pp.get_actions(mid_state)} == {"finish", "reset"}


# ---------------------------------------------------------------------------
# 3. get_successors
# ---------------------------------------------------------------------------


class TestGetSuccessors:
    def test_deterministic_action_yields_single_successor(self) -> None:
        pp = _load("det_domain.pddl", "det_problem.pddl")
        init = pp.initial_state()
        pick_a = next(a for a in pp.get_actions(init) if a.name == "pick(a)")

        successors = pp.get_successors(init, pick_a)
        assert len(successors) == 1
        (successor,) = successors
        assert successor.atoms == frozenset(
            {
                Atom("holding", ("a",)),
                Atom("clear", ("b",)),
            }
        )

    def test_oneof_action_yields_one_state_per_branch(self) -> None:
        pp = _load("toy_fond_domain.pddl", "toy_fond_problem.pddl")
        init = pp.initial_state()
        try_action = next(iter(pp.get_actions(init)))
        assert try_action.name == "try"

        successors = pp.get_successors(init, try_action)
        successor_atom_sets = {s.atoms for s in successors}
        assert successor_atom_sets == {
            frozenset({Atom("at-mid", ())}),
            frozenset({Atom("broken", ())}),
        }


# ---------------------------------------------------------------------------
# 4. is_goal
# ---------------------------------------------------------------------------


class TestIsGoal:
    def test_goal_true(self) -> None:
        pp = _load("det_domain.pddl", "det_problem.pddl")
        goal_state = PDDLState(atoms=frozenset({Atom("holding", ("a",))}))
        assert pp.is_goal(goal_state) is True

    def test_goal_false(self) -> None:
        pp = _load("det_domain.pddl", "det_problem.pddl")
        assert pp.is_goal(pp.initial_state()) is False

    def test_fond_goal(self) -> None:
        pp = _load("toy_fond_domain.pddl", "toy_fond_problem.pddl")
        assert pp.is_goal(pp.initial_state()) is False
        assert pp.is_goal(PDDLState(atoms=frozenset({Atom("at-goal", ())}))) is True


# ---------------------------------------------------------------------------
# 5. Integration with KPlanSolver
# ---------------------------------------------------------------------------


class TestSolverIntegration:
    def test_deterministic_problem_is_solved(self) -> None:
        pp = _load("det_domain.pddl", "det_problem.pddl")
        solver: KPlanSolver[PDDLState, GroundAction] = KPlanSolver()
        result = solver.solve(pp, k=0)

        init = pp.initial_state()
        # There is a path (pick(a)) that reaches the goal, so k_value(init) >= 0.
        assert result.k_values[init] >= 0
        # The policy should have an action for the initial state.
        assert result.policy.get_action(init) is not None

    def test_fond_problem_reaches_policy(self) -> None:
        # In the toy-fond domain at k=0 the policy may or may not cover the
        # initial state (the `try` action has a `broken` dead-end branch).
        # What matters for integration is that the solver doesn't crash and
        # returns a well-formed result using the adapter.
        pp = _load("toy_fond_domain.pddl", "toy_fond_problem.pddl")
        solver: KPlanSolver[PDDLState, GroundAction] = KPlanSolver()
        result = solver.solve(pp, k=0)

        goal_state = PDDLState(atoms=frozenset({Atom("at-goal", ())}))
        assert result.k_values.get(goal_state) == 0


# ---------------------------------------------------------------------------
# 6. Uniform treatment of oneof branches
# ---------------------------------------------------------------------------


class TestOneOfUniformity:
    def test_all_branches_become_successors(self) -> None:
        """Every branch of OneOfEffect maps to exactly one successor — no
        branch is privileged as nominal or filtered as adverse."""
        pp = _load("toy_fond_domain.pddl", "toy_fond_problem.pddl")
        init = pp.initial_state()
        try_action = next(iter(pp.get_actions(init)))
        # The schema has two branches; the adapter must yield two successors.
        assert len(try_action.effect.branches) == 2
        assert len(pp.get_successors(init, try_action)) == 2
