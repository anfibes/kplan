from typing import Protocol, TypeVar

from core.state import State
from core.problem import Problem
from core.planning_result import PlanningResult

StateT = TypeVar("StateT", bound=State)
ActionT = TypeVar("ActionT")


class Planner(Protocol[StateT, ActionT]):
    def solve(self, problem: Problem[StateT, ActionT], k: int) -> PlanningResult[StateT, ActionT]:
        ...