"""Eager grounding of PDDL action schemas over typed problem objects.

This module takes the output of :mod:`kplan_io.pddl.parser` (a
:class:`~kplan_io.pddl.ast.ParsedDomain` and
:class:`~kplan_io.pddl.ast.ParsedProblem`) and produces:

* a deterministic tuple of fully grounded :class:`~kplan_io.pddl.ast.GroundAction`
* a validated initial :class:`~kplan_io.pddl.ast.PDDLState`

Grounding runs **once**, eagerly. No grounding happens during search.

This module imports only from :mod:`kplan_io.pddl.ast` and
:mod:`kplan_io.pddl.errors` — it has no dependency on the external
``pddl`` library.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from kplan_io.pddl.ast import (
    ActionSchema,
    AndPrecondition,
    Atom,
    DeterministicEffect,
    GroundAction,
    LiteralPrecondition,
    OneOfEffect,
    PDDLState,
    ParsedDomain,
    ParsedProblem,
    PredicateSchema,
)
from kplan_io.pddl.errors import GroundingError


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GroundingResult:
    """The output of grounding: ground actions and validated initial state."""

    actions: tuple[GroundAction, ...]
    initial_state: PDDLState


def ground(domain: ParsedDomain, problem: ParsedProblem) -> GroundingResult:
    """Ground all action schemas over problem objects and validate the initial state.

    Raises:
        GroundingError: if validation fails (unknown types, arity mismatches,
            undeclared objects or predicates, type incompatibility, or
            leftover variables in grounded output).
    """
    predicate_index = _build_predicate_index(domain)
    type_closure = _build_type_closure(domain)
    object_types = _build_object_types(problem, type_closure)
    objects_by_type = _build_objects_by_type(problem, type_closure)

    initial_state = _validate_initial_state(problem, predicate_index, object_types, type_closure)

    actions: list[GroundAction] = []
    for schema in domain.actions:
        actions.extend(
            _ground_schema(schema, objects_by_type, predicate_index, object_types, type_closure)
        )

    return GroundingResult(
        actions=tuple(actions),
        initial_state=initial_state,
    )


# ---------------------------------------------------------------------------
# Type system helpers
# ---------------------------------------------------------------------------


def _is_variable(term: str) -> bool:
    return term.startswith("?")


def _build_type_closure(domain: ParsedDomain) -> dict[str, frozenset[str]]:
    """Build a mapping from each type to itself plus all transitive supertypes.

    ``"object"`` is always present as a root. Every declared type maps to a
    frozenset containing at least itself and ``"object"``.
    """
    parent: dict[str, str | None] = {"object": None}
    for sub, sup in domain.types:
        parent[sub] = sup  # sup is None for direct children of object

    closure: dict[str, frozenset[str]] = {}
    for t in parent:
        ancestors: set[str] = set()
        current: str | None = t
        while current is not None:
            if current in ancestors:
                raise GroundingError(f"cyclic type hierarchy detected at type '{current}'")
            ancestors.add(current)
            current = parent.get(current)
        closure[t] = frozenset(ancestors)

    return closure


def _is_type_compatible(
    obj_type: str,
    param_type: str,
    type_closure: dict[str, frozenset[str]],
) -> bool:
    """Return True if an object of ``obj_type`` satisfies a parameter of ``param_type``."""
    if obj_type not in type_closure:
        return False
    return param_type in type_closure[obj_type]


# ---------------------------------------------------------------------------
# Object index
# ---------------------------------------------------------------------------


def _build_object_types(
    problem: ParsedProblem,
    type_closure: dict[str, frozenset[str]],
) -> dict[str, str]:
    """Return a mapping from object name to its declared type.

    Raises ``GroundingError`` if an object uses an undeclared type.
    """
    obj_types: dict[str, str] = {}
    for obj_name, obj_type in problem.objects:
        if obj_type not in type_closure:
            raise GroundingError(
                f"object '{obj_name}' has undeclared type '{obj_type}'"
            )
        obj_types[obj_name] = obj_type
    return obj_types


def _build_objects_by_type(
    problem: ParsedProblem,
    type_closure: dict[str, frozenset[str]],
) -> dict[str, tuple[str, ...]]:
    """Return, for each type, the sorted tuple of objects assignable to it.

    An object declared as type ``dog`` is assignable to ``dog``, ``animal``,
    and ``object`` if ``dog <: animal <: object``.
    """
    by_type: dict[str, list[str]] = {t: [] for t in type_closure}
    for obj_name, obj_type in problem.objects:
        for ancestor in type_closure.get(obj_type, frozenset()):
            by_type.setdefault(ancestor, []).append(obj_name)

    return {t: tuple(sorted(objs)) for t, objs in by_type.items()}


# ---------------------------------------------------------------------------
# Predicate index
# ---------------------------------------------------------------------------


def _build_predicate_index(domain: ParsedDomain) -> dict[str, PredicateSchema]:
    """Return a mapping from predicate name to its schema."""
    return {p.name: p for p in domain.predicates}


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_ground_atom(
    atom: Atom,
    predicate_index: dict[str, PredicateSchema],
    object_types: dict[str, str],
    type_closure: dict[str, frozenset[str]],
    context: str,
) -> None:
    """Validate a ground atom against predicate signatures and object types.

    Checks:
    - predicate is declared
    - arity matches
    - all arguments are declared objects
    - each argument's type is compatible with the predicate parameter type
    - no variables remain
    """
    if atom.predicate not in predicate_index:
        raise GroundingError(
            f"undeclared predicate '{atom.predicate}' in {context}"
        )
    schema = predicate_index[atom.predicate]
    expected_arity = len(schema.parameters)
    if len(atom.args) != expected_arity:
        raise GroundingError(
            f"predicate '{atom.predicate}' expects {expected_arity} "
            f"argument(s) but got {len(atom.args)} in {context}"
        )
    for i, arg in enumerate(atom.args):
        if _is_variable(arg):
            raise GroundingError(
                f"variable '{arg}' found in grounded atom {atom} in {context}"
            )
        if arg not in object_types:
            raise GroundingError(
                f"undeclared object '{arg}' in atom {atom} in {context}"
            )
        _, param_type = schema.parameters[i]
        obj_type = object_types[arg]
        if not _is_type_compatible(obj_type, param_type, type_closure):
            raise GroundingError(
                f"object '{arg}' (type '{obj_type}') is not compatible with "
                f"parameter type '{param_type}' of predicate "
                f"'{atom.predicate}' in {context}"
            )


def _validate_initial_state(
    problem: ParsedProblem,
    predicate_index: dict[str, PredicateSchema],
    object_types: dict[str, str],
    type_closure: dict[str, frozenset[str]],
) -> PDDLState:
    """Construct and validate the initial PDDLState.

    Zero-arity predicates have no arguments to validate beyond the predicate
    name and arity check.
    """
    for atom in problem.init:
        _validate_ground_atom(atom, predicate_index, object_types, type_closure, ":init")
    return PDDLState(atoms=problem.init)


# ---------------------------------------------------------------------------
# Variable substitution
# ---------------------------------------------------------------------------


def _substitute_atom(atom: Atom, binding: dict[str, str]) -> Atom:
    """Replace every variable in ``atom.args`` using ``binding``."""
    new_args = tuple(binding.get(a, a) for a in atom.args)
    return Atom(predicate=atom.predicate, args=new_args)


def _substitute_precondition(
    precondition: AndPrecondition,
    binding: dict[str, str],
) -> AndPrecondition:
    return AndPrecondition(
        literals=tuple(
            LiteralPrecondition(
                atom=_substitute_atom(lit.atom, binding),
                negated=lit.negated,
            )
            for lit in precondition.literals
        )
    )


def _substitute_effect(effect: OneOfEffect, binding: dict[str, str]) -> OneOfEffect:
    return OneOfEffect(
        branches=tuple(
            DeterministicEffect(
                adds=frozenset(_substitute_atom(a, binding) for a in branch.adds),
                dels=frozenset(_substitute_atom(a, binding) for a in branch.dels),
            )
            for branch in effect.branches
        )
    )


# ---------------------------------------------------------------------------
# Grounded action validation
# ---------------------------------------------------------------------------


def _validate_ground_action(
    action: GroundAction,
    predicate_index: dict[str, PredicateSchema],
    object_types: dict[str, str],
    type_closure: dict[str, frozenset[str]],
) -> None:
    """Validate all atoms in a grounded action's precondition and effect."""
    context = f"grounded action '{action.name}'"

    for lit in action.precondition.literals:
        _validate_ground_atom(lit.atom, predicate_index, object_types, type_closure, context)

    for branch in action.effect.branches:
        for atom in branch.adds:
            _validate_ground_atom(atom, predicate_index, object_types, type_closure, context)
        for atom in branch.dels:
            _validate_ground_atom(atom, predicate_index, object_types, type_closure, context)


# ---------------------------------------------------------------------------
# Schema grounding
# ---------------------------------------------------------------------------


def _ground_schema(
    schema: ActionSchema,
    objects_by_type: dict[str, tuple[str, ...]],
    predicate_index: dict[str, PredicateSchema],
    object_types: dict[str, str],
    type_closure: dict[str, frozenset[str]],
) -> list[GroundAction]:
    """Ground a single action schema into all valid typed instantiations."""
    if not schema.parameters:
        # Zero-parameter action: exactly one grounded instance.
        action = GroundAction(
            name=schema.name,
            schema_name=schema.name,
            args=(),
            precondition=schema.precondition,
            effect=schema.effect,
        )
        _validate_ground_action(action, predicate_index, object_types, type_closure)
        return [action]

    # Build the list of candidate objects for each parameter position.
    param_candidates: list[tuple[str, ...]] = []
    for _, param_type in schema.parameters:
        if param_type not in type_closure:
            raise GroundingError(
                f"action '{schema.name}' has parameter with undeclared "
                f"type '{param_type}'"
            )
        candidates = objects_by_type.get(param_type, ())
        if not candidates:
            # No objects of this type -> no grounded actions from this schema.
            return []
        param_candidates.append(candidates)

    # Cartesian product of all parameter positions.
    result: list[GroundAction] = []
    for combo in itertools.product(*param_candidates):
        args = tuple(combo)
        binding: dict[str, str] = {}
        for (var_name, _), obj_name in zip(schema.parameters, args):
            binding[f"?{var_name}"] = obj_name

        name = f"{schema.name}({','.join(args)})"
        precondition = _substitute_precondition(schema.precondition, binding)
        effect = _substitute_effect(schema.effect, binding)

        action = GroundAction(
            name=name,
            schema_name=schema.name,
            args=args,
            precondition=precondition,
            effect=effect,
        )
        _validate_ground_action(action, predicate_index, object_types, type_closure)
        result.append(action)

    return result
