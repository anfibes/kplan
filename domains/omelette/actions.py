from enum import Enum, auto


class OmeletteAction(Enum):
    BREAK_EGG = auto()
    EMPTY_PAN = auto()

    def __str__(self) -> str:
        return self.name