from dataclasses import dataclass

from core.state import State


@dataclass(frozen=True)
class RoverState(State):
    x: int
    y: int