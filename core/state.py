from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    """
    Base class for states.

    Must be:
    - immutable
    - hashable
    """
    pass