"""External-parser boundary for PDDL-FOND.

This module is the **only** place in the project allowed to import from the
``pddl`` PyPI package or any of its submodules. Every public function here
returns kplan's internal AST types from :mod:`kplan_io.pddl.ast`; no
external object ever escapes this file.

The conversion is intentionally strict: any feature outside the v1 supported
subset (see the project design doc) raises
:class:`kplan_io.pddl.errors.UnsupportedPddlFeatureError` with a message
that names the feature and, when possible, the surrounding action.
"""
# pyright: reportMissingTypeStubs=false
from __future__ import annotations

from pathlib import Path
from typing import Any

# All external-library imports live in this file ONLY. Do not re-export.
# The `pddl` package ships without a py.typed marker, so each first-import
# from one of its submodules carries an `# type: ignore[import-untyped]`.
from pddl import parse_domain as _ext_parse_domain  # type: ignore[import-untyped]
from pddl import parse_problem as _ext_parse_problem  # type: ignore[import-untyped]
from pddl.action import Action as _ExtAction  # type: ignore[import-untyped]
from pddl.core import Domain as _ExtDomain  # type: ignore[import-untyped]
from pddl.core import Problem as _ExtProblem
from pddl.logic.base import And as _ExtAnd  # type: ignore[import-untyped]
from pddl.logic.base import ExistsCondition as _ExtExists
from pddl.logic.base import ForallCondition as _ExtForall
from pddl.logic.base import Imply as _ExtImply
from pddl.logic.base import Not as _ExtNot
from pddl.logic.base import OneOf as _ExtOneOf
from pddl.logic.base import Or as _ExtOr
from pddl.logic.effects import Forall as _ExtEffectForall  # type: ignore[import-untyped]
from pddl.logic.effects import When as _ExtWhen
from pddl.logic.predicates import EqualTo as _ExtEqualTo  # type: ignore[import-untyped]
from pddl.logic.predicates import Predicate as _ExtPredicate
from pddl.logic.terms import Constant as _ExtConstant  # type: ignore[import-untyped]
from pddl.logic.terms import Variable as _ExtVariable
from pddl.exceptions import PDDLMissingRequirementError  # type: ignore[import-untyped]
from kplan_io.pddl.ast import (
    ActionSchema,
    AndPrecondition,
    Atom,
    DeterministicEffect,
    LiteralPrecondition,
    OneOfEffect,
    ParsedDomain,
    ParsedProblem,
    PredicateSchema,
)
from kplan_io.pddl.errors import (
    PddlParseError,
    UnsupportedPddlFeatureError,
)
from typing import Callable, cast

# Type aliases for external parser functions (pddl has no type hints)
_ExtParseProblem = Callable[[str], object]
_ExtParseDomain = Callable[[str], object]

_ext_parse_problem = cast(_ExtParseProblem, _ext_parse_problem)
_ext_parse_domain = cast(_ExtParseDomain, _ext_parse_domain)

# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def parse_domain(path: str | Path) -> ParsedDomain:
    """Parse a PDDL domain file into kplan's internal AST.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        PddlParseError: if the file cannot be parsed as PDDL.
        UnsupportedPddlFeatureError: if the file uses a feature outside the
            v1 supported subset.
    """
    ext_domain = _safe_external_call(lambda: _ext_parse_domain(str(path)), path)
    return _convert_domain(ext_domain)


def parse_problem(path: str | Path) -> ParsedProblem:
    """Parse a PDDL problem file into kplan's internal AST.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        PddlParseError: if the file cannot be parsed as PDDL.
        UnsupportedPddlFeatureError: if the file uses a feature outside the
            v1 supported subset.
    """
    ext_problem = _safe_external_call(lambda: _ext_parse_problem(str(path)), path)
    return _convert_problem(ext_problem)


# ---------------------------------------------------------------------------
# External-call wrapper
# ---------------------------------------------------------------------------


def _safe_external_call(thunk: Any, path: str | Path) -> Any:
    """Run ``thunk`` and normalize external parser failures.

    ``FileNotFoundError`` is intentionally allowed to propagate so callers
    can distinguish "file is missing" from "file is malformed".

    If the external parser reports a missing PDDL requirement, convert that
    into ``UnsupportedPddlFeatureError`` so the public API consistently
    exposes domain-specific feature/requirement failures through our own
    exception hierarchy.
    """
    try:
        return thunk()
    except FileNotFoundError:
        raise
    except UnsupportedPddlFeatureError:
        raise
    except PDDLMissingRequirementError as exc:
        raise UnsupportedPddlFeatureError(str(exc)) from exc
    except Exception as exc:
        raise PddlParseError(f"failed to parse {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Domain conversion
# ---------------------------------------------------------------------------


_SUPPORTED_REQUIREMENTS: frozenset[str] = frozenset(
    {
        ":strips",
        ":typing",
        ":negative-preconditions",
        ":non-deterministic",
    }
)


def _convert_domain(ext: _ExtDomain) -> ParsedDomain:
    location = f"domain {ext.name!r}"

    requirements = _convert_requirements(ext.requirements, location)
    _reject_constants(ext, location)
    _reject_derived_predicates(ext, location)

    types = _convert_types(ext.types)
    predicates = _convert_predicate_schemas(ext.predicates)
    actions = tuple(
        _convert_action(action) for action in sorted(ext.actions, key=lambda a: a.name)
    )

    return ParsedDomain(
        name=str(ext.name),
        requirements=requirements,
        types=types,
        predicates=predicates,
        actions=actions,
    )


def _convert_requirements(
    ext_requirements: Any,
    location: str,
) -> frozenset[str]:
    """Translate the external Requirements enum into canonical PDDL strings.

    Each external requirement becomes ``":<value>"`` (e.g.
    ``Requirements.TYPING -> ":typing"``). Anything outside the v1 supported
    set raises :class:`UnsupportedPddlFeatureError`.
    """
    canonical: set[str] = set()
    for req in ext_requirements:
        name = f":{req.value}"
        canonical.add(name)
    unsupported = canonical - _SUPPORTED_REQUIREMENTS
    if unsupported:
        # Sort for a deterministic message — important for tests.
        first = sorted(unsupported)[0]
        raise UnsupportedPddlFeatureError(
            feature=f"requirement {first}",
            location=location,
        )
    return frozenset(canonical)


def _reject_constants(ext: _ExtDomain, location: str) -> None:
    if ext.constants:
        raise UnsupportedPddlFeatureError(
            feature="(:constants ...)",
            location=location,
        )


def _reject_derived_predicates(ext: _ExtDomain, location: str) -> None:
    if ext.derived_predicates:
        raise UnsupportedPddlFeatureError(
            feature="(:derived ...)",
            location=location,
        )


def _convert_types(ext_types: Any) -> tuple[tuple[str, str | None], ...]:
    """Convert the external types mapping into a sorted tuple of pairs.

    The external mapping uses ``None`` for the implicit ``object`` root, and
    we preserve that convention. Sorting by subtype name guarantees stable
    output across runs.
    """
    pairs: list[tuple[str, str | None]] = []
    for subtype, supertype in ext_types.items():
        sub_name = str(subtype)
        super_name = str(supertype) if supertype is not None else None
        pairs.append((sub_name, super_name))
    pairs.sort(key=lambda p: p[0])
    return tuple(pairs)


def _convert_predicate_schemas(ext_predicates: Any) -> tuple[PredicateSchema, ...]:
    schemas: list[PredicateSchema] = []
    for pred in ext_predicates:
        params: list[tuple[str, str]] = []
        for term in pred.terms:
            if not isinstance(term, _ExtVariable):
                # Predicate schemas should only contain variables. If a
                # constant ever appears, treat it as malformed input.
                raise PddlParseError(
                    f"predicate {pred.name!r} declares a non-variable term: {term!r}"
                )
            params.append(_variable_to_param(term))
        schemas.append(
            PredicateSchema(
                name=str(pred.name),
                parameters=tuple(params),
            )
        )
    schemas.sort(key=lambda s: s.name)
    return tuple(schemas)


def _variable_to_param(var: Any) -> tuple[str, str]:
    """Return a ``(variable_name, type_name)`` pair for an external Variable.

    The leading ``"?"`` is *not* included in the variable name. If the
    variable has no explicit type, the type name defaults to ``"object"``.
    Variables with multiple type tags (PDDL ``either`` syntax) are rejected.
    """
    name = str(var.name)
    tags = tuple(var.type_tags)
    if len(tags) == 0:
        type_name = "object"
    elif len(tags) == 1:
        type_name = str(tags[0])
    else:
        raise UnsupportedPddlFeatureError(
            feature="(either ...) type union",
            location=f"variable ?{name}",
        )
    return (name, type_name)


# ---------------------------------------------------------------------------
# Action conversion
# ---------------------------------------------------------------------------


def _convert_action(ext: _ExtAction) -> ActionSchema:
    location = f"action {ext.name!r}"
    parameters = tuple(_variable_to_param(p) for p in ext.parameters)
    precondition = _convert_precondition(ext.precondition, location)
    effect = _convert_effect(ext.effect, location)
    return ActionSchema(
        name=str(ext.name),
        parameters=parameters,
        precondition=precondition,
        effect=effect,
    )


# ---------------------------------------------------------------------------
# Precondition / goal conversion
# ---------------------------------------------------------------------------


def _convert_precondition(formula: Any, location: str) -> AndPrecondition:
    """Convert a precondition or goal formula into a normalized AndPrecondition.

    The accepted shapes are:

    * a single predicate atom -> wrapped in a one-literal AndPrecondition;
    * a single ``(not (atom))`` -> wrapped in a one-literal AndPrecondition;
    * a (possibly nested) ``and`` of the above -> flattened.

    Anything else (``or``, ``forall``, ``exists``, ``imply``, ``=``,
    ``oneof``) raises :class:`UnsupportedPddlFeatureError`.
    """
    literals: list[LiteralPrecondition] = []
    _collect_literals(formula, literals, location)
    return AndPrecondition(literals=tuple(literals))


def _collect_literals(
    formula: Any,
    sink: list[LiteralPrecondition],
    location: str,
) -> None:
    if isinstance(formula, _ExtAnd):
        for operand in formula.operands:
            _collect_literals(operand, sink, location)
        return

    if isinstance(formula, _ExtPredicate):
        sink.append(LiteralPrecondition(atom=_atom_from_predicate(formula), negated=False))
        return

    if isinstance(formula, _ExtNot):
        inner = formula.argument
        if not isinstance(inner, _ExtPredicate):
            raise UnsupportedPddlFeatureError(
                feature="non-literal under (not ...)",
                location=location,
            )
        sink.append(LiteralPrecondition(atom=_atom_from_predicate(inner), negated=True))
        return

    if isinstance(formula, _ExtOr):
        raise UnsupportedPddlFeatureError(feature="(or ...)", location=location)
    if isinstance(formula, _ExtForall):
        raise UnsupportedPddlFeatureError(feature="(forall ...)", location=location)
    if isinstance(formula, _ExtExists):
        raise UnsupportedPddlFeatureError(feature="(exists ...)", location=location)
    if isinstance(formula, _ExtImply):
        raise UnsupportedPddlFeatureError(feature="(imply ...)", location=location)
    if isinstance(formula, _ExtEqualTo):
        raise UnsupportedPddlFeatureError(feature="equality (=)", location=location)
    if isinstance(formula, _ExtOneOf):
        raise UnsupportedPddlFeatureError(
            feature="(oneof ...) in precondition",
            location=location,
        )

    raise UnsupportedPddlFeatureError(
        feature=f"precondition node {type(formula).__name__}",
        location=location,
    )


def _atom_from_predicate(pred: Any) -> Atom:
    """Build an internal Atom from an external Predicate node.

    Variables are emitted as ``"?name"`` (with the leading ``?``); constants
    keep their bare name. This convention matches :meth:`Atom.is_ground`.
    """
    args: list[str] = []
    for term in pred.terms:
        if isinstance(term, _ExtVariable):
            args.append(f"?{term.name}")
        elif isinstance(term, _ExtConstant):
            args.append(str(term.name))
        else:
            raise PddlParseError(
                f"predicate {pred.name!r} contains an unrecognized term: {term!r}"
            )
    return Atom(predicate=str(pred.name), args=tuple(args))


# ---------------------------------------------------------------------------
# Effect conversion
# ---------------------------------------------------------------------------


def _convert_effect(formula: Any, location: str) -> OneOfEffect:
    """Convert an action's effect tree into a normalized OneOfEffect.

    Accepted shapes:

    * a single literal (atomic add or ``(not atom)`` delete);
    * an ``(and ...)`` of literals;
    * a top-level ``(oneof ...)`` whose branches are literals or
      ``(and ...)`` of literals;
    * an ``(and ...)`` containing literals plus exactly one ``(oneof ...)``,
      in which case the surrounding deterministic literals are distributed
      into every branch.

    Multiple ``oneof`` constructs in the same effect, nested ``oneof``,
    ``when``, and ``forall`` are rejected.
    """
    deterministic_lits, oneof_node = _split_top_effect(formula, location)

    base_adds, base_dels = _literals_to_addel(deterministic_lits, location)

    if oneof_node is None:
        return OneOfEffect(branches=(DeterministicEffect(adds=base_adds, dels=base_dels),))

    branches: list[DeterministicEffect] = []
    for branch in oneof_node.operands:
        branch_lits = _flat_literal_effect(branch, location, allow_oneof=False)
        branch_adds, branch_dels = _literals_to_addel(branch_lits, location)
        merged_adds = base_adds | branch_adds
        merged_dels = base_dels | branch_dels
        if merged_adds & merged_dels:
            raise PddlParseError(
                f"effect in {location} both adds and deletes the same atom"
            )
        branches.append(DeterministicEffect(adds=merged_adds, dels=merged_dels))

    return OneOfEffect(branches=tuple(branches))


def _split_top_effect(
    formula: Any,
    location: str,
) -> tuple[list[tuple[Atom, bool]], Any | None]:
    """Split an effect into its deterministic literals plus at most one oneof.

    Returns a list of ``(atom, is_delete)`` pairs and the oneof node (or
    ``None`` if there is no oneof at the top level). Raises if more than one
    oneof appears in the same effect or if a non-literal/non-oneof node is
    encountered at the top level.
    """
    deterministic: list[tuple[Atom, bool]] = []
    oneof_node: Any | None = None

    operands: list[Any]
    if isinstance(formula, _ExtAnd):
        operands = list(formula.operands)
    else:
        operands = [formula]

    for operand in operands:
        if isinstance(operand, _ExtOneOf):
            if oneof_node is not None:
                raise UnsupportedPddlFeatureError(
                    feature="multiple (oneof ...) in a single effect",
                    location=location,
                )
            oneof_node = operand
        elif isinstance(operand, _ExtPredicate):
            deterministic.append((_atom_from_predicate(operand), False))
        elif isinstance(operand, _ExtNot):
            inner = operand.argument
            if not isinstance(inner, _ExtPredicate):
                raise UnsupportedPddlFeatureError(
                    feature="non-literal under (not ...) in effect",
                    location=location,
                )
            deterministic.append((_atom_from_predicate(inner), True))
        elif isinstance(operand, _ExtAnd):
            # An (and ...) nested directly inside the top-level (and ...);
            # flatten by recursing.
            sub_lits, sub_oneof = _split_top_effect(operand, location)
            deterministic.extend(sub_lits)
            if sub_oneof is not None:
                if oneof_node is not None:
                    raise UnsupportedPddlFeatureError(
                        feature="multiple (oneof ...) in a single effect",
                        location=location,
                    )
                oneof_node = sub_oneof
        elif isinstance(operand, _ExtWhen):
            raise UnsupportedPddlFeatureError(
                feature="(when ...) conditional effect",
                location=location,
            )
        elif isinstance(operand, _ExtEffectForall):
            raise UnsupportedPddlFeatureError(
                feature="(forall ...) effect",
                location=location,
            )
        else:
            raise UnsupportedPddlFeatureError(
                feature=f"effect node {type(operand).__name__}",
                location=location,
            )

    return deterministic, oneof_node


def _flat_literal_effect(
    formula: Any,
    location: str,
    *,
    allow_oneof: bool,
) -> list[tuple[Atom, bool]]:
    """Collect a flat list of literal effects from a (single literal or AND).

    Used to walk the *body* of a oneof branch — anything other than literals
    and conjunctions of literals is rejected. ``allow_oneof`` is False here,
    so nested ``oneof`` raises ``UnsupportedPddlFeatureError``.
    """
    out: list[tuple[Atom, bool]] = []

    operands: list[Any]
    if isinstance(formula, _ExtAnd):
        operands = list(formula.operands)
    else:
        operands = [formula]

    for operand in operands:
        if isinstance(operand, _ExtPredicate):
            out.append((_atom_from_predicate(operand), False))
        elif isinstance(operand, _ExtNot):
            inner = operand.argument
            if not isinstance(inner, _ExtPredicate):
                raise UnsupportedPddlFeatureError(
                    feature="non-literal under (not ...) in effect",
                    location=location,
                )
            out.append((_atom_from_predicate(inner), True))
        elif isinstance(operand, _ExtAnd):
            out.extend(_flat_literal_effect(operand, location, allow_oneof=allow_oneof))
        elif isinstance(operand, _ExtOneOf):
            if not allow_oneof:
                raise UnsupportedPddlFeatureError(
                    feature="nested (oneof ...) in oneof branch",
                    location=location,
                )
            raise UnsupportedPddlFeatureError(
                feature="multiple (oneof ...) in a single effect",
                location=location,
            )
        elif isinstance(operand, _ExtWhen):
            raise UnsupportedPddlFeatureError(
                feature="(when ...) conditional effect",
                location=location,
            )
        elif isinstance(operand, _ExtEffectForall):
            raise UnsupportedPddlFeatureError(
                feature="(forall ...) effect",
                location=location,
            )
        else:
            raise UnsupportedPddlFeatureError(
                feature=f"effect node {type(operand).__name__}",
                location=location,
            )

    return out


def _literals_to_addel(
    literals: list[tuple[Atom, bool]],
    location: str,
) -> tuple[frozenset[Atom], frozenset[Atom]]:
    """Partition a list of literal effects into add and delete sets.

    Raises ``PddlParseError`` if the same atom is both added and deleted in
    the same deterministic context.
    """
    adds: set[Atom] = set()
    dels: set[Atom] = set()
    for atom, is_delete in literals:
        if is_delete:
            dels.add(atom)
        else:
            adds.add(atom)
    overlap = adds & dels
    if overlap:
        raise PddlParseError(
            f"effect in {location} both adds and deletes the same atom: {next(iter(overlap))}"
        )
    return frozenset(adds), frozenset(dels)


# ---------------------------------------------------------------------------
# Problem conversion
# ---------------------------------------------------------------------------


def _convert_problem(ext: _ExtProblem) -> ParsedProblem:
    location = f"problem {ext.name!r}"

    objects = _convert_objects(ext.objects)
    init = _convert_init(ext.init, location)
    goal = _convert_precondition(ext.goal, f"{location} goal")

    return ParsedProblem(
        name=str(ext.name),
        domain_name=str(ext.domain_name),
        objects=objects,
        init=init,
        goal=goal,
    )


def _convert_objects(ext_objects: Any) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for obj in ext_objects:
        if not isinstance(obj, _ExtConstant):
            raise PddlParseError(f"unexpected non-constant object: {obj!r}")
        tags = tuple(obj.type_tags)
        if len(tags) == 0:
            type_name = "object"
        elif len(tags) == 1:
            type_name = str(tags[0])
        else:
            raise UnsupportedPddlFeatureError(
                feature="(either ...) type union",
                location=f"object {obj.name}",
            )
        pairs.append((str(obj.name), type_name))
    pairs.sort(key=lambda p: p[0])
    return tuple(pairs)


def _convert_init(ext_init: Any, location: str) -> frozenset[Atom]:
    atoms: set[Atom] = set()
    for fact in ext_init:
        if isinstance(fact, _ExtPredicate):
            atoms.add(_atom_from_predicate(fact))
        elif isinstance(fact, _ExtNot):
            # Closed-world: negative facts in :init are unusual and outside
            # the v1 subset.
            raise UnsupportedPddlFeatureError(
                feature="(not ...) in :init",
                location=location,
            )
        else:
            raise UnsupportedPddlFeatureError(
                feature=f"init fact {type(fact).__name__}",
                location=location,
            )
    return frozenset(atoms)
