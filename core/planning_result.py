from dataclasses import dataclass
from typing import Dict, Generic, TypeVar

from core.state import State
from core.policy import Policy

StateT = TypeVar("StateT", bound=State)
ActionT = TypeVar("ActionT")


@dataclass
class PlanningResult(Generic[StateT, ActionT]):
    policy: Policy[StateT, ActionT]
    k_values: Dict[StateT, int]