"""Adapter exposing a grounded PDDL-FOND problem as a :class:`core.problem.Problem`.

This module is the junction between the PDDL I/O layer (parser + grounder)
and the kplan core. It does no parsing and no grounding of its own: it
consumes a :class:`~kplan_io.pddl.ast.ParsedDomain` and
:class:`~kplan_io.pddl.ast.ParsedProblem`, invokes
:func:`kplan_io.pddl.grounder.ground` once eagerly, and then implements the
four methods of :class:`core.problem.Problem` over the cached grounded
actions and goal.

Semantic notes
--------------

* Every branch of an action's :class:`~kplan_io.pddl.ast.OneOfEffect`
  becomes a successor. No distinction between nominal and adverse branches
  is made here — that mapping is a pending design decision and belongs in a
  later milestone, not in this adapter.
* Applicability is evaluated against the stored
  :class:`~kplan_io.pddl.ast.AndPrecondition` using closed-world semantics:
  a positive literal holds iff its atom is in the state; a negative literal
  holds iff its atom is *not* in the state.
"""

from __future__ import annotations

from kplan_io.pddl.ast import (
    AndPrecondition,
    GroundAction,
    PDDLState,
    ParsedDomain,
    ParsedProblem,
)
from kplan_io.pddl.grounder import ground


class PDDLProblem:
    """Problem adapter over grounded PDDL-FOND.

    Satisfies the :class:`core.problem.Problem` protocol with
    ``StateT = PDDLState`` and ``ActionT = GroundAction``.
    """

    def __init__(self, domain: ParsedDomain, problem: ParsedProblem) -> None:
        grounding = ground(domain, problem)
        self._actions: tuple[GroundAction, ...] = grounding.actions
        self._initial_state: PDDLState = grounding.initial_state
        self._goal: AndPrecondition = problem.goal

    def initial_state(self) -> PDDLState:
        return self._initial_state

    def get_actions(self, state: PDDLState) -> set[GroundAction]:
        return {
            action
            for action in self._actions
            if _precondition_holds(action.precondition, state)
        }

    def get_successors(self, state: PDDLState, action: GroundAction) -> set[PDDLState]:
        return {
            state.apply(branch.adds, branch.dels)
            for branch in action.effect.branches
        }

    def is_goal(self, state: PDDLState) -> bool:
        return _precondition_holds(self._goal, state)


def _precondition_holds(precondition: AndPrecondition, state: PDDLState) -> bool:
    """Return True iff every literal in the conjunction is satisfied in ``state``."""
    for literal in precondition.literals:
        present = state.holds(literal.atom)
        if literal.negated:
            if present:
                return False
        else:
            if not present:
                return False
    return True
