"""Tests for kplan_io.pddl.grounder.

Milestone 1B scope: grounding only. No PDDLProblem adapter, no CLI.

The tests validate:

1. Deterministic grounding produces the expected number of actions with
   stable naming and ordering.
2. Grounded actions contain no variables in preconditions or effects.
3. Type hierarchy (single inheritance) is respected during grounding.
4. Zero-parameter schemas produce exactly one grounded action.
5. Schemas with no compatible objects produce zero grounded actions.
6. Invalid initial states are rejected with GroundingError.
7. Type-incompatible init atoms are rejected with GroundingError.
8. oneof branches are fully grounded.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kplan_io.pddl.ast import Atom, PDDLState
from kplan_io.pddl.errors import GroundingError
from kplan_io.pddl.grounder import ground
from kplan_io.pddl.parser import parse_domain, parse_problem


FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _contains_variables(action_name: str, atoms: frozenset[Atom]) -> list[str]:
    """Return any variable-like terms found in a set of atoms."""
    return [
        arg
        for atom in atoms
        for arg in atom.args
        if arg.startswith("?")
    ]


# ---------------------------------------------------------------------------
# 1. Deterministic grounding smoke test
# ---------------------------------------------------------------------------


class TestDeterministicGrounding:
    """Ground the det-toy domain (pick/put × {a, b})."""

    def setup_method(self) -> None:
        domain = parse_domain(FIXTURES / "det_domain.pddl")
        problem = parse_problem(FIXTURES / "det_problem.pddl")
        self.result = ground(domain, problem)

    def test_ground_action_count(self) -> None:
        # pick(a), pick(b), put(a), put(b)
        assert len(self.result.actions) == 4

    def test_ground_action_names(self) -> None:
        names = [a.name for a in self.result.actions]
        assert names == ["pick(a)", "pick(b)", "put(a)", "put(b)"]

    def test_schema_names_preserved(self) -> None:
        schemas = {a.schema_name for a in self.result.actions}
        assert schemas == {"pick", "put"}

    def test_args_are_ground_objects(self) -> None:
        for action in self.result.actions:
            for arg in action.args:
                assert not arg.startswith("?"), f"variable in args of {action.name}"

    def test_preconditions_contain_no_variables(self) -> None:
        for action in self.result.actions:
            for lit in action.precondition.literals:
                assert lit.atom.is_ground(), (
                    f"variable in precondition of {action.name}: {lit.atom}"
                )

    def test_effects_contain_no_variables(self) -> None:
        for action in self.result.actions:
            for branch in action.effect.branches:
                vars_in_adds = _contains_variables(action.name, branch.adds)
                vars_in_dels = _contains_variables(action.name, branch.dels)
                assert not vars_in_adds, (
                    f"variables in adds of {action.name}: {vars_in_adds}"
                )
                assert not vars_in_dels, (
                    f"variables in dels of {action.name}: {vars_in_dels}"
                )

    def test_initial_state_matches_problem_init(self) -> None:
        expected = PDDLState(
            atoms=frozenset({
                Atom("clear", ("a",)),
                Atom("clear", ("b",)),
                Atom("handempty", ()),
            })
        )
        assert self.result.initial_state == expected

    def test_pick_a_precondition(self) -> None:
        pick_a = next(a for a in self.result.actions if a.name == "pick(a)")
        pre_atoms = {(lit.atom, lit.negated) for lit in pick_a.precondition.literals}
        assert pre_atoms == {
            (Atom("clear", ("a",)), False),
            (Atom("handempty", ()), False),
        }

    def test_pick_a_effect(self) -> None:
        pick_a = next(a for a in self.result.actions if a.name == "pick(a)")
        assert len(pick_a.effect.branches) == 1
        branch = pick_a.effect.branches[0]
        assert branch.adds == frozenset({Atom("holding", ("a",))})
        assert branch.dels == frozenset({
            Atom("clear", ("a",)),
            Atom("handempty", ()),
        })


# ---------------------------------------------------------------------------
# 2. Subtype assignability
# ---------------------------------------------------------------------------


class TestSubtypeAssignability:
    """Ground the subtype-test domain where parameters are supertype ``animal``
    but objects are declared as subtypes ``dog`` and ``cat``."""

    def setup_method(self) -> None:
        domain = parse_domain(FIXTURES / "subtype_domain.pddl")
        problem = parse_problem(FIXTURES / "subtype_problem.pddl")
        self.result = ground(domain, problem)

    def test_action_count(self) -> None:
        # adopt(?a - animal) × {rex, whiskers} = 2
        assert len(self.result.actions) == 2

    def test_action_names(self) -> None:
        names = [a.name for a in self.result.actions]
        assert names == ["adopt(rex)", "adopt(whiskers)"]

    def test_subtype_objects_are_valid_for_supertype_param(self) -> None:
        # rex is a dog, whiskers is a cat — both are animals
        adopt_rex = next(a for a in self.result.actions if a.name == "adopt(rex)")
        assert adopt_rex.args == ("rex",)

    def test_initial_state(self) -> None:
        assert self.result.initial_state.atoms == frozenset({
            Atom("friendly", ("rex",)),
            Atom("friendly", ("whiskers",)),
        })


# ---------------------------------------------------------------------------
# 3. Zero-parameter action
# ---------------------------------------------------------------------------


class TestZeroParameterAction:
    """Ground the toy-fond domain where all actions have zero parameters."""

    def setup_method(self) -> None:
        domain = parse_domain(FIXTURES / "toy_fond_domain.pddl")
        problem = parse_problem(FIXTURES / "toy_fond_problem.pddl")
        self.result = ground(domain, problem)

    def test_action_count(self) -> None:
        # finish, reset, try — each with zero parameters = 3 actions
        assert len(self.result.actions) == 3

    def test_action_names(self) -> None:
        names = [a.name for a in self.result.actions]
        # sorted by schema name (parser sorts action schemas)
        assert names == ["finish", "reset", "try"]

    def test_zero_param_actions_have_empty_args(self) -> None:
        for action in self.result.actions:
            assert action.args == ()


# ---------------------------------------------------------------------------
# 4. Empty object type produces zero grounded actions
# ---------------------------------------------------------------------------


class TestEmptyObjectType:
    """A schema whose parameter type has no compatible objects produces zero
    grounded actions, without raising an error."""

    def setup_method(self) -> None:
        domain = parse_domain(FIXTURES / "empty_type_domain.pddl")
        problem = parse_problem(FIXTURES / "empty_type_problem.pddl")
        self.result = ground(domain, problem)

    def test_sharpen_produces_zero_actions(self) -> None:
        # No objects of type 'weapon' -> sharpen schema produces nothing
        sharpen_actions = [a for a in self.result.actions if a.schema_name == "sharpen"]
        assert len(sharpen_actions) == 0

    def test_use_produces_one_action(self) -> None:
        # 'hammer' is a tool -> use schema produces use(hammer)
        use_actions = [a for a in self.result.actions if a.schema_name == "use"]
        assert len(use_actions) == 1
        assert use_actions[0].name == "use(hammer)"


# ---------------------------------------------------------------------------
# 5. Invalid init: arity mismatch
# ---------------------------------------------------------------------------


def test_invalid_init_arity_raises_grounding_error() -> None:
    domain = parse_domain(FIXTURES / "det_domain.pddl")
    problem = parse_problem(FIXTURES / "bad_init_arity_problem.pddl")
    with pytest.raises(GroundingError, match="expects 1"):
        ground(domain, problem)


# ---------------------------------------------------------------------------
# 6. Invalid init: unknown object
# ---------------------------------------------------------------------------


def test_invalid_init_unknown_object_raises_grounding_error() -> None:
    domain = parse_domain(FIXTURES / "det_domain.pddl")
    problem = parse_problem(FIXTURES / "bad_init_unknown_object_problem.pddl")
    with pytest.raises(GroundingError, match="undeclared object"):
        ground(domain, problem)


# ---------------------------------------------------------------------------
# 7. Invalid init: type mismatch
# ---------------------------------------------------------------------------


def test_invalid_init_type_mismatch_raises_grounding_error() -> None:
    domain = parse_domain(FIXTURES / "bad_init_type_domain.pddl")
    problem = parse_problem(FIXTURES / "bad_init_type_problem.pddl")
    with pytest.raises(GroundingError, match="not compatible"):
        ground(domain, problem)


# ---------------------------------------------------------------------------
# 8. Invalid grounded action: predicate type mismatch
# ---------------------------------------------------------------------------


def test_grounded_action_type_mismatch_raises_grounding_error() -> None:
    """An action schema that uses a vehicle-typed parameter inside a
    fruit-typed predicate must fail during grounding validation — not
    during parsing, and not during init validation.

    The domain defines ``(ripe ?f - fruit)`` and an action
    ``drive(?v - vehicle)`` whose effect includes ``(ripe ?v)``.
    Parsing succeeds because variable names carry no type semantics in
    the parser. Init is valid. But when grounding substitutes ``?v``
    with ``truck`` (a vehicle), the atom ``(ripe truck)`` violates the
    predicate signature, and GroundingError must be raised.
    """
    domain = parse_domain(FIXTURES / "bad_action_type_domain.pddl")
    problem = parse_problem(FIXTURES / "bad_action_type_problem.pddl")
    with pytest.raises(GroundingError, match="not compatible"):
        ground(domain, problem)


# ---------------------------------------------------------------------------
# 9. Deterministic ordering
# ---------------------------------------------------------------------------


def test_grounding_is_deterministic_across_runs() -> None:
    domain = parse_domain(FIXTURES / "det_domain.pddl")
    problem = parse_problem(FIXTURES / "det_problem.pddl")
    result_a = ground(domain, problem)
    result_b = ground(domain, problem)
    names_a = [a.name for a in result_a.actions]
    names_b = [a.name for a in result_b.actions]
    assert names_a == names_b


# ---------------------------------------------------------------------------
# 10. OneOf branch grounding
# ---------------------------------------------------------------------------


class TestOneOfBranchGrounding:
    """Verify every oneof branch is fully grounded with no variables."""

    def setup_method(self) -> None:
        domain = parse_domain(FIXTURES / "toy_fond_domain.pddl")
        problem = parse_problem(FIXTURES / "toy_fond_problem.pddl")
        self.result = ground(domain, problem)

    def test_try_has_two_branches(self) -> None:
        try_act = next(a for a in self.result.actions if a.name == "try")
        assert len(try_act.effect.branches) == 2

    def test_no_variables_in_any_branch(self) -> None:
        for action in self.result.actions:
            for branch in action.effect.branches:
                for atom in branch.adds | branch.dels:
                    assert atom.is_ground(), (
                        f"variable in branch of {action.name}: {atom}"
                    )

    def test_try_branch_content(self) -> None:
        try_act = next(a for a in self.result.actions if a.name == "try")
        branches = set(try_act.effect.branches)
        from kplan_io.pddl.ast import DeterministicEffect

        expected = {
            DeterministicEffect(
                adds=frozenset({Atom("at-mid", ())}),
                dels=frozenset({Atom("at-start", ())}),
            ),
            DeterministicEffect(
                adds=frozenset({Atom("broken", ())}),
                dels=frozenset({Atom("at-start", ())}),
            ),
        }
        assert branches == expected


# ---------------------------------------------------------------------------
# 11. OneOf branch grounding with parameters (fond_with_and_oneof)
# ---------------------------------------------------------------------------


class TestOneOfWithParameterGrounding:
    """Verify oneof branches are grounded when the action has parameters."""

    def setup_method(self) -> None:
        domain = parse_domain(FIXTURES / "fond_with_and_oneof_domain.pddl")
        # This domain has type 'block' and the grab action takes ?b - block.
        # We need a problem with block objects.
        # Reuse the det-toy problem which has objects a, b of type block —
        # but the domain name won't match. Instead, parse a custom problem.
        # The fond_with_and_oneof_domain expects block type, so let's create
        # inline.
        import tempfile
        from pathlib import Path

        prob = """\
(define (problem fond-and-oneof-1)
  (:domain fond-and-oneof)
  (:objects x - block)
  (:init (clear x) (handempty))
  (:goal (holding x)))
"""
        self.tmpdir = tempfile.mkdtemp()
        prob_path = Path(self.tmpdir) / "p.pddl"
        prob_path.write_text(prob)
        problem = parse_problem(prob_path)
        self.result = ground(domain, problem)

    def test_grab_has_two_branches_per_grounded_action(self) -> None:
        grab_x = next(a for a in self.result.actions if a.name == "grab(x)")
        assert len(grab_x.effect.branches) == 2

    def test_variables_replaced_in_branches(self) -> None:
        grab_x = next(a for a in self.result.actions if a.name == "grab(x)")
        for branch in grab_x.effect.branches:
            for atom in branch.adds | branch.dels:
                assert atom.is_ground(), f"variable in branch atom: {atom}"

    def test_deterministic_dels_distributed_and_grounded(self) -> None:
        grab_x = next(a for a in self.result.actions if a.name == "grab(x)")
        clear_x = Atom("clear", ("x",))
        handempty = Atom("handempty", ())
        for branch in grab_x.effect.branches:
            assert clear_x in branch.dels
            assert handempty in branch.dels
