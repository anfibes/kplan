from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    """
    Represents an action in the domain.
    """
    name: str