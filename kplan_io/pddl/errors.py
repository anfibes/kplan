"""Domain-specific exceptions raised by the PDDL I/O layer.

These are the only exception types that callers outside ``kplan_io.pddl``
should need to catch. Internal helpers may raise standard Python exceptions
(``ValueError``, ``TypeError``, etc.) but the public boundary normalizes
errors into one of the classes defined here.
"""

from __future__ import annotations


class PddlError(Exception):
    """Base class for all errors raised by the PDDL I/O layer."""


class PddlParseError(PddlError):
    """Raised when an input file cannot be parsed as PDDL.

    This wraps lower-level parser exceptions (lark errors, validation errors
    from the external ``pddl`` package, etc.) into a single, stable error
    type that the rest of kplan can rely on.
    """


class UnsupportedPddlFeatureError(PddlError):
    """Raised when an input file uses a PDDL feature outside the v1 subset.

    The message identifies the offending feature and, when possible, the
    location (action name, formula context) where it appeared.
    """

    def __init__(self, feature: str, location: str | None = None) -> None:
        self.feature = feature
        self.location = location
        if location is None:
            message = f"unsupported PDDL feature: {feature}"
        else:
            message = f"unsupported PDDL feature: {feature} (in {location})"
        super().__init__(message)


class GroundingError(PddlError):
    """Raised when grounding a parsed domain or problem fails.

    Reserved for the next milestone (1B). Defined here so the public error
    surface is stable from milestone 1A onward.
    """
