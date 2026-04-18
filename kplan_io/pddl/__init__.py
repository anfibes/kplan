"""
Public API for the PDDL integration layer of kplan.

The module provides a validated and grounded PDDL front-end that can be
used directly with the solver through the PDDLProblem adapter.

Current capabilities:

- parsing PDDL domain files
- parsing PDDL problem files
- validation of a restricted PDDL subset
- conversion to an internal AST independent of the external parser
- eager grounding of ActionSchema into GroundAction
- validation of grounded actions and initial state
- integration with the solver via PDDLProblem

Architecture:

    PDDL files
        ↓
    parser.py → internal AST
        ↓
    grounder.py → grounded actions + initial state
        ↓
    problem.py → PDDLProblem (core.problem.Problem adapter)
        ↓
    KPlanSolver

The module enforces a strict boundary with the external `pddl` package:
no external types are exposed outside the parser layer.

Limitations:

- only a restricted subset of PDDL is supported
- no CLI interface yet
- no advanced optimizations (lazy grounding, indexing, etc.)
"""

from kplan_io.pddl.errors import (
    GroundingError,
    PddlError,
    PddlParseError,
    UnsupportedPddlFeatureError,
)
from kplan_io.pddl.problem import PDDLProblem

__all__ = [
    "GroundingError",
    "PDDLProblem",
    "PddlError",
    "PddlParseError",
    "UnsupportedPddlFeatureError",
]
