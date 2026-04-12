"""Tests for kplan_io.pddl.parser.

Milestone 1A scope: parser only. No grounding, no PDDLProblem adapter.

The tests validate four invariants:

1. Successful parses produce only internal AST objects (no leakage of
   external ``pddl`` library types).
2. Deterministic effects are normalized to a single-branch ``OneOfEffect``.
3. ``oneof`` is normalized into a multi-branch ``OneOfEffect``, with any
   surrounding deterministic literals distributed into every branch.
4. Each unsupported feature in the v1 reject list raises
   ``UnsupportedPddlFeatureError``.
"""

from __future__ import annotations
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, cast

import pytest

from kplan_io.pddl import ast as pddl_ast
from kplan_io.pddl.errors import (
    PddlParseError,
    UnsupportedPddlFeatureError,
)
from kplan_io.pddl.parser import parse_domain, parse_problem


FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_internal_ast(obj: object) -> bool:
    """True if ``obj`` is an instance of a class defined in kplan_io.pddl.ast."""
    return type(obj).__module__ == pddl_ast.__name__


def _walk_for_external_types(obj: object, seen: set[int] | None = None) -> list[type]:
    """Recursively look for any value whose type is *not* defined in our AST.

    Returns a list of foreign types encountered. Used to assert that the
    parser never leaks an object from the external ``pddl`` library.
    """
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return []
    seen.add(id(obj))

    foreign: list[type] = []
    # Skip primitive leaves entirely.
    if isinstance(obj, (str, int, float, bool, type(None))):
        return foreign

    # Internal AST nodes: walk their __dict__-style fields.
    if _is_internal_ast(obj):
        assert is_dataclass(obj)
        for field_info in fields(obj):
            value = getattr(obj, field_info.name)
            foreign.extend(_walk_for_external_types(value, seen))
        return foreign

    # Containers: recurse into elements.
    if isinstance(obj, (list, tuple, set, frozenset)):
        iterable = cast(Iterable[Any], obj)
        for item in iterable:
            foreign.extend(_walk_for_external_types(item, seen))
        return foreign

    if isinstance(obj, dict):
        mapping = cast(Mapping[Any, Any], obj)
        for k, v in mapping.items():
            foreign.extend(_walk_for_external_types(k, seen))
            foreign.extend(_walk_for_external_types(v, seen))
        return foreign

    # Anything else is a foreign type.
    foreign.append(type(obj))
    return foreign


# ---------------------------------------------------------------------------
# Deterministic domain
# ---------------------------------------------------------------------------


class TestDeterministicDomain:
    def setup_method(self) -> None:
        self.domain = parse_domain(FIXTURES / "det_domain.pddl")
        self.problem = parse_problem(FIXTURES / "det_problem.pddl")

    def test_returns_internal_ast_types(self) -> None:
        assert isinstance(self.domain, pddl_ast.ParsedDomain)
        assert isinstance(self.problem, pddl_ast.ParsedProblem)

    def test_no_external_types_leak_in_domain(self) -> None:
        foreign = _walk_for_external_types(self.domain)
        assert foreign == [], f"foreign types leaked from parser: {foreign}"

    def test_no_external_types_leak_in_problem(self) -> None:
        foreign = _walk_for_external_types(self.problem)
        assert foreign == [], f"foreign types leaked from parser: {foreign}"

    def test_domain_metadata(self) -> None:
        assert self.domain.name == "det-toy"
        assert ":typing" in self.domain.requirements
        assert ":negative-preconditions" in self.domain.requirements

    def test_types_recorded(self) -> None:
        assert self.domain.types == (("block", None),)

    def test_predicate_schemas_sorted_and_typed(self) -> None:
        names = [p.name for p in self.domain.predicates]
        assert names == sorted(names), "predicates must be sorted by name"
        assert names == ["clear", "handempty", "holding"]
        clear = next(p for p in self.domain.predicates if p.name == "clear")
        assert clear.parameters == (("b", "block"),)
        handempty = next(p for p in self.domain.predicates if p.name == "handempty")
        assert handempty.parameters == ()

    def test_actions_sorted_by_name(self) -> None:
        names = [a.name for a in self.domain.actions]
        assert names == sorted(names)
        assert names == ["pick", "put"]

    def test_action_parameters_typed(self) -> None:
        pick = next(a for a in self.domain.actions if a.name == "pick")
        assert pick.parameters == (("b", "block"),)

    def test_deterministic_effect_is_single_branch_oneof(self) -> None:
        pick = next(a for a in self.domain.actions if a.name == "pick")
        assert isinstance(pick.effect, pddl_ast.OneOfEffect)
        assert len(pick.effect.branches) == 1
        branch = pick.effect.branches[0]
        assert branch.adds == frozenset(
            {pddl_ast.Atom("holding", ("?b",))}
        )
        assert branch.dels == frozenset(
            {
                pddl_ast.Atom("clear", ("?b",)),
                pddl_ast.Atom("handempty", ()),
            }
        )

    def test_precondition_is_normalized_and(self) -> None:
        pick = next(a for a in self.domain.actions if a.name == "pick")
        assert isinstance(pick.precondition, pddl_ast.AndPrecondition)
        atoms = {(lit.atom, lit.negated) for lit in pick.precondition.literals}
        assert atoms == {
            (pddl_ast.Atom("clear", ("?b",)), False),
            (pddl_ast.Atom("handempty", ()), False),
        }

    def test_single_literal_precondition_is_wrapped_in_and(self) -> None:
        put = next(a for a in self.domain.actions if a.name == "put")
        assert isinstance(put.precondition, pddl_ast.AndPrecondition)
        assert len(put.precondition.literals) == 1
        lit = put.precondition.literals[0]
        assert lit.negated is False
        assert lit.atom == pddl_ast.Atom("holding", ("?b",))

    def test_problem_metadata(self) -> None:
        assert self.problem.name == "det-toy-1"
        assert self.problem.domain_name == "det-toy"

    def test_problem_objects_sorted_and_typed(self) -> None:
        assert self.problem.objects == (("a", "block"), ("b", "block"))

    def test_problem_init_atoms_are_internal(self) -> None:
        assert self.problem.init == frozenset(
            {
                pddl_ast.Atom("clear", ("a",)),
                pddl_ast.Atom("clear", ("b",)),
                pddl_ast.Atom("handempty", ()),
            }
        )

    def test_problem_goal_is_normalized_and(self) -> None:
        assert isinstance(self.problem.goal, pddl_ast.AndPrecondition)
        assert self.problem.goal.literals == (
            pddl_ast.LiteralPrecondition(
                atom=pddl_ast.Atom("holding", ("a",)),
                negated=False,
            ),
        )


# ---------------------------------------------------------------------------
# Toy FOND domain (oneof at top of effect)
# ---------------------------------------------------------------------------


class TestToyFondDomain:
    def setup_method(self) -> None:
        self.domain = parse_domain(FIXTURES / "toy_fond_domain.pddl")
        self.problem = parse_problem(FIXTURES / "toy_fond_problem.pddl")

    def test_no_external_types_leak(self) -> None:
        assert _walk_for_external_types(self.domain) == []
        assert _walk_for_external_types(self.problem) == []

    def test_requirements_include_non_deterministic(self) -> None:
        assert ":non-deterministic" in self.domain.requirements

    def test_no_types_declared(self) -> None:
        assert self.domain.types == ()

    def test_try_action_has_two_branches(self) -> None:
        try_act = next(a for a in self.domain.actions if a.name == "try")
        assert isinstance(try_act.effect, pddl_ast.OneOfEffect)
        assert len(try_act.effect.branches) == 2

    def test_try_branches_normalized_correctly(self) -> None:
        try_act = next(a for a in self.domain.actions if a.name == "try")

        expected_branch_a = pddl_ast.DeterministicEffect(
            adds=frozenset({pddl_ast.Atom("at-mid", ())}),
            dels=frozenset({pddl_ast.Atom("at-start", ())}),
        )
        expected_branch_b = pddl_ast.DeterministicEffect(
            adds=frozenset({pddl_ast.Atom("broken", ())}),
            dels=frozenset({pddl_ast.Atom("at-start", ())}),
        )

        # Branch order is determined by the parser walking ext.operands in
        # iteration order; assert membership rather than position.
        assert set(try_act.effect.branches) == {expected_branch_a, expected_branch_b}

    def test_finish_action_is_single_branch(self) -> None:
        finish = next(a for a in self.domain.actions if a.name == "finish")
        assert len(finish.effect.branches) == 1
        branch = finish.effect.branches[0]
        assert branch.adds == frozenset({pddl_ast.Atom("at-goal", ())})
        assert branch.dels == frozenset({pddl_ast.Atom("at-mid", ())})

    def test_problem_initial_atom(self) -> None:
        assert self.problem.init == frozenset({pddl_ast.Atom("at-start", ())})

    def test_problem_goal_atom(self) -> None:
        assert self.problem.goal.literals == (
            pddl_ast.LiteralPrecondition(
                atom=pddl_ast.Atom("at-goal", ()),
                negated=False,
            ),
        )


# ---------------------------------------------------------------------------
# (and ... (oneof ...) ...) — distribution of deterministic literals
# ---------------------------------------------------------------------------


class TestAndPlusOneOfDistribution:
    def setup_method(self) -> None:
        self.domain = parse_domain(FIXTURES / "fond_with_and_oneof_domain.pddl")

    def test_grab_action_has_two_branches(self) -> None:
        grab = next(a for a in self.domain.actions if a.name == "grab")
        assert len(grab.effect.branches) == 2

    def test_deterministic_dels_distributed_into_every_branch(self) -> None:
        grab = next(a for a in self.domain.actions if a.name == "grab")
        clear_b = pddl_ast.Atom("clear", ("?b",))
        handempty = pddl_ast.Atom("handempty", ())
        # The surrounding (not (clear ?b)) and (not (handempty)) deletes
        # must appear in every branch's dels.
        for branch in grab.effect.branches:
            assert clear_b in branch.dels
            assert handempty in branch.dels

    def test_branch_specific_adds_isolated(self) -> None:
        grab = next(a for a in self.domain.actions if a.name == "grab")
        holding_b = pddl_ast.Atom("holding", ("?b",))
        slipped = pddl_ast.Atom("slipped", ())

        # The "success" branch adds only (holding ?b).
        success = next(b for b in grab.effect.branches if holding_b in b.adds)
        assert success.adds == frozenset({holding_b})

        # The "slip" branch adds only (slipped).
        slip = next(b for b in grab.effect.branches if slipped in b.adds)
        assert slip.adds == frozenset({slipped})

    def test_dels_are_branch_independent(self) -> None:
        grab = next(a for a in self.domain.actions if a.name == "grab")
        # Both branches share exactly the same dels (the deterministic body)
        # because the oneof branches in this fixture do not introduce any
        # branch-specific deletes.
        dels_per_branch = {b.dels for b in grab.effect.branches}
        assert len(dels_per_branch) == 1


def test_branch_add_del_conflict_is_rejected() -> None:
    """A oneof branch that re-adds an atom the surrounding (and ...) deletes
    must be rejected with PddlParseError. The parser must NOT silently merge
    the conflict.
    """
    with pytest.raises(PddlParseError):
        parse_domain(FIXTURES / "conflict_add_del_domain.pddl")


# ---------------------------------------------------------------------------
# Unsupported features
# ---------------------------------------------------------------------------


class TestUnsupportedFeatures:
    def test_or_in_precondition_is_rejected(self) -> None:
        with pytest.raises(UnsupportedPddlFeatureError) as info:
            parse_domain(FIXTURES / "unsupported_or_domain.pddl")
        # The disjunctive-preconditions requirement is rejected before we
        # ever look at the formula tree, so the message names the requirement.
        assert "disjunctive-preconditions" in str(info.value) or "or" in str(info.value)

    def test_when_conditional_effect_is_rejected(self) -> None:
        with pytest.raises(UnsupportedPddlFeatureError) as info:
            parse_domain(FIXTURES / "unsupported_when_domain.pddl")
        # The conditional-effects requirement is rejected at requirement
        # validation time.
        assert (
            "conditional-effects" in str(info.value)
            or "when" in str(info.value)
        )

    def test_constants_are_rejected(self) -> None:
        with pytest.raises(UnsupportedPddlFeatureError) as info:
            parse_domain(FIXTURES / "unsupported_constants_domain.pddl")
        assert "constants" in str(info.value)

    def test_equality_is_rejected(self) -> None:
        with pytest.raises(UnsupportedPddlFeatureError) as info:
            parse_domain(FIXTURES / "unsupported_equality_domain.pddl")
        assert "equality" in str(info.value)

    def test_double_oneof_is_rejected(self) -> None:
        with pytest.raises(UnsupportedPddlFeatureError) as info:
            parse_domain(FIXTURES / "unsupported_double_oneof_domain.pddl")
        assert "oneof" in str(info.value)


# ---------------------------------------------------------------------------
# Determinism / stability of parser output
# ---------------------------------------------------------------------------


def test_parser_output_is_stable_across_runs() -> None:
    """Parsing the same file twice yields equal ParsedDomain objects.

    This guards against accidental nondeterminism (e.g. iterating a set
    without sorting) that would otherwise produce a different action or
    predicate order between runs.
    """
    a = parse_domain(FIXTURES / "toy_fond_domain.pddl")
    b = parse_domain(FIXTURES / "toy_fond_domain.pddl")
    assert a == b
    # And the action ordering must be identical, not merely set-equal.
    assert [act.name for act in a.actions] == [act.name for act in b.actions]


def test_missing_file_raises_file_not_found() -> None:
    """``FileNotFoundError`` propagates unchanged so callers can distinguish
    a missing file from a malformed one."""
    with pytest.raises(FileNotFoundError):
        parse_domain(FIXTURES / "definitely_does_not_exist.pddl")

class TestPDDLStateHelpers:
    def test_holds_returns_true_only_for_present_atoms(self) -> None:
        at_start = pddl_ast.Atom("at-start", ())
        broken = pddl_ast.Atom("broken", ())
        state = pddl_ast.PDDLState(atoms=frozenset({at_start}))

        assert state.holds(at_start) is True
        assert state.holds(broken) is False

    def test_apply_returns_new_state_with_adds_and_dels_applied(self) -> None:
        at_start = pddl_ast.Atom("at-start", ())
        at_mid = pddl_ast.Atom("at-mid", ())
        state = pddl_ast.PDDLState(atoms=frozenset({at_start}))

        new_state = state.apply(
            adds=frozenset({at_mid}),
            dels=frozenset({at_start}),
        )

        assert new_state != state
        assert state.atoms == frozenset({at_start})
        assert new_state.atoms == frozenset({at_mid})


def test_oneof_without_non_deterministic_requirement_is_rejected() -> None:
    """Using `oneof` without declaring :non-deterministic must fail.

    The external `pddl` parser raises an error in this case, and our
    parser must translate it into UnsupportedPddlFeatureError
    (not leak the external exception type).
    """
    with pytest.raises(UnsupportedPddlFeatureError):
        parse_domain(FIXTURES / "unsupported_oneof_missing_requirement_domain.pddl")

def test_effect_application_sanity() -> None:
    """Verify that parsed deterministic effects contain correct symbolic structure.

    Since we are still at milestone 1A (no grounding),
    we validate that:
    - variables are preserved in the effect
    - add/delete sets are correctly extracted
    """

    from kplan_io.pddl.parser import parse_domain
    from kplan_io.pddl.ast import Atom

    domain = parse_domain(FIXTURES / "det_domain.pddl")

    action = next(a for a in domain.actions if a.name == "pick")
    branch = action.effect.branches[0]

    # Expected symbolic atoms (with variables, not grounded)
    atom_clear_var = Atom("clear", ("?b",))
    atom_holding_var = Atom("holding", ("?b",))
    atom_handempty = Atom("handempty", ())

    # Deletes
    assert atom_clear_var in branch.dels
    assert atom_handempty in branch.dels

    # Adds
    assert atom_holding_var in branch.adds