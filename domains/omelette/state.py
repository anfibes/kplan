from dataclasses import dataclass

from core.state import State


@dataclass(frozen=True)
class OmeletteState(State):
    eggs_in_pan: int
    has_bad_egg_in_pan: bool
    discarded_eggs: int

    def __str__(self) -> str:
        quality = "T" if self.has_bad_egg_in_pan else "F"
        return f"{self.eggs_in_pan} {quality} {self.discarded_eggs}"