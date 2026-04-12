"""PDDL-FOND I/O for kplan.

This package translates PDDL-FOND files into kplan's internal representation.
The external ``pddl`` PyPI package is the parser backend, but it is strictly
confined to :mod:`kplan_io.pddl.parser` — no other module imports from
``pddl.*``.

Public API for milestone 1A is intentionally limited to the parser layer:

* :func:`kplan_io.pddl.parser.parse_domain`
* :func:`kplan_io.pddl.parser.parse_problem`

Grounding and the :class:`core.problem.Problem` adapter come in later
milestones.
"""

from kplan_io.pddl.errors import (
    GroundingError,
    PddlError,
    PddlParseError,
    UnsupportedPddlFeatureError,
)

__all__ = [
    "GroundingError",
    "PddlError",
    "PddlParseError",
    "UnsupportedPddlFeatureError",
]
