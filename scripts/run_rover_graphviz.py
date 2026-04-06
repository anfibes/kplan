from algorithms.kplan_solver import KPlanSolver
from domains.rover.actions import RoverAction
from domains.rover.problem import RoverProblem
from domains.rover.state import RoverState
from visualization.graphviz_exporter import GraphvizExporter


def main() -> None:
    problem = RoverProblem(
        width=2,
        height=2,
        initial=RoverState(0, 0),
        goal=RoverState(1, 1),
    )

    solver = KPlanSolver[RoverState, RoverAction]()
    result = solver.solve(problem, k=1)

    exporter = GraphvizExporter[RoverState, RoverAction]()
    dot = exporter.export(problem, solver, result)

    print(dot)

    exporter.export_to_file(problem, solver, result, "kplan_graph.dot")
    print("\nFile kplan_graph.dot generato!")


if __name__ == "__main__":
    main()