"""Internal AST for PDDL-FOND, independent of any external parser library.

Every type in this module is a frozen, hashable dataclass. The shapes here
are the *only* representation that the rest of kplan ever sees: the parser
in :mod:`kplan_io.pddl.parser` is responsible for translating the external
``pddl`` library's classes into these types and never re-exposing them.

Design notes
------------

* :class:`Atom` is shared between schema-level and grounded forms. The
  difference is purely conventional: a term beginning with ``"?"`` is a
  schema variable, otherwise it is a constant. Grounded atoms are produced
  by substituting variables with object names during grounding (milestone 1B).

* :class:`PDDLState` extends :class:`core.state.State` so it slots into the
  existing :class:`core.problem.Problem` protocol unchanged in milestone 1B.

* Preconditions are normalized to a single :class:`AndPrecondition`, even
  for actions whose precondition is a single literal. This eliminates a case
  split for downstream consumers.

* Effects are normalized to a single :class:`OneOfEffect`. A deterministic
  action becomes a one-branch ``OneOfEffect``. A FOND action with ``oneof``
  becomes a multi-branch ``OneOfEffect``. Each branch is a flat
  :class:`DeterministicEffect`. The parser is responsible for distributing
  any surrounding conjunction into the branches.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.state import State


@dataclass(frozen=True)
class Atom:
    """A predicate atom.

    The ``args`` tuple holds either schema variables (strings prefixed with
    ``"?"``, e.g. ``"?b"``) or object/constant names (no prefix). Both
    forms share this class — there is no separate ``GroundAtom`` type.

    Atoms are immutable and hashable so they can be stored in
    :class:`PDDLState`'s ``frozenset`` and used as dict keys.
    """

    predicate: str
    args: tuple[str, ...]

    def __str__(self) -> str:
        if not self.args:
            return f"({self.predicate})"
        return f"({self.predicate} {' '.join(self.args)})"

    def is_ground(self) -> bool:
        return all(not a.startswith("?") for a in self.args)


@dataclass(frozen=True)
class PDDLState(State):
    """A PDDL world state: a set of ground atoms under closed-world semantics.

    The set is stored as a :class:`frozenset` so the state itself is
    hashable, which is required by :class:`algorithms.kplan_solver.KPlanSolver`.
    """

    atoms: frozenset[Atom]

    def __str__(self) -> str:
        ordered = sorted(self.atoms, key=lambda a: (a.predicate, a.args))
        return "".join(str(a) for a in ordered)
    
    def holds(self, atom: Atom) -> bool:
        """Return True if the given ground atom is present in the state."""
        return atom in self.atoms

    def apply(self, adds: frozenset[Atom], dels: frozenset[Atom]) -> "PDDLState":
        """Return a new state produced by applying add/delete effects.

        The caller is responsible for passing a semantically valid effect:
        this method does not enforce grounding, predicate validity, or
        add/delete conflict checks.
        """
        return PDDLState(atoms=(self.atoms - dels) | adds)


@dataclass(frozen=True)
class LiteralPrecondition:
    """A single (possibly negated) atomic precondition literal."""

    atom: Atom
    negated: bool


@dataclass(frozen=True)
class AndPrecondition:
    """A conjunction of literals.

    A precondition or goal that is syntactically a single literal is wrapped
    in a one-element ``AndPrecondition`` by the parser, so consumers never
    need to handle a non-conjunctive case.
    """

    literals: tuple[LiteralPrecondition, ...]


@dataclass(frozen=True)
class DeterministicEffect:
    """A flat add/delete effect.

    ``adds`` and ``dels`` are disjoint by construction (the parser checks
    this when it normalizes the effect tree). Empty sets are allowed and
    represent a no-op effect.
    """

    adds: frozenset[Atom]
    dels: frozenset[Atom]


@dataclass(frozen=True)
class OneOfEffect:
    """The normalized wrapper for any action effect.

    Even fully deterministic actions are represented as a one-branch
    ``OneOfEffect``. Each branch is a flat :class:`DeterministicEffect` with
    any surrounding conjunction already distributed into it.
    """

    branches: tuple[DeterministicEffect, ...]


@dataclass(frozen=True)
class PredicateSchema:
    """The signature of a domain predicate.

    Used by the grounder (milestone 1B) and by the parser to validate that
    every atom in init/goal references a declared predicate.
    """

    name: str
    parameters: tuple[tuple[str, str], ...]
    """A tuple of ``(variable_name, type_name)`` pairs, in declaration order.

    Variable names are stored without the leading ``"?"``. The type name is
    ``"object"`` if no explicit type was given.
    """


@dataclass(frozen=True)
class ActionSchema:
    """A parameterized action schema as it appears in a domain file."""

    name: str
    parameters: tuple[tuple[str, str], ...]
    """``(variable_name, type_name)`` pairs without the leading ``"?"``."""

    precondition: AndPrecondition
    effect: OneOfEffect


@dataclass(frozen=True)
class GroundAction:
    """A fully grounded action, produced by the grounder in milestone 1B.

    Defined here so the public AST surface is stable from milestone 1A
    onward. Not constructed by the parser.
    """

    name: str
    schema_name: str
    args: tuple[str, ...]
    precondition: AndPrecondition
    effect: OneOfEffect

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ParsedDomain:
    """A parsed PDDL domain in kplan's internal representation.

    All collections are tuples (not lists or sets) so the dataclass remains
    hashable and so iteration order is deterministic across runs — important
    for reproducible test snapshots and stable visualization output.
    """

    name: str
    requirements: frozenset[str]
    types: tuple[tuple[str, str | None], ...]
    """``(subtype, supertype)`` pairs. ``supertype`` is ``None`` when the
    subtype's parent is the implicit root ``object``."""

    predicates: tuple[PredicateSchema, ...]
    actions: tuple[ActionSchema, ...]


@dataclass(frozen=True)
class ParsedProblem:
    """A parsed PDDL problem in kplan's internal representation."""

    name: str
    domain_name: str
    objects: tuple[tuple[str, str], ...]
    """``(object_name, type_name)`` pairs. The type is ``"object"`` if the
    object was declared without an explicit type."""

    init: frozenset[Atom]
    goal: AndPrecondition
