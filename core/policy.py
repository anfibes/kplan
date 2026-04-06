from typing import Optional, Protocol, TypeVar

from core.state import State

StateT_contra = TypeVar("StateT_contra", bound=State, contravariant=True)
ActionT_co = TypeVar("ActionT_co", covariant=True)


class Policy(Protocol[StateT_contra, ActionT_co]):
    def get_action(self, state: StateT_contra) -> Optional[ActionT_co]:
        ...