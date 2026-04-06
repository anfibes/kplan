from typing import Protocol, TypeVar, Set

from core.state import State

StateT = TypeVar("StateT", bound=State)
ActionT = TypeVar("ActionT")


class Problem(Protocol[StateT, ActionT]):
    def initial_state(self) -> StateT:
        ...

    def get_actions(self, state: StateT) -> Set[ActionT]:
        ...

    def get_successors(self, state: StateT, action: ActionT) -> Set[StateT]:
        ...

    def is_goal(self, state: StateT) -> bool:
        ...