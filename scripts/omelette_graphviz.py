import argparse
import subprocess
from pathlib import Path

from algorithms.kplan_solver import KPlanSolver
from domains.omelette.actions import OmeletteAction
from domains.omelette.problem import OmeletteProblem
from domains.omelette.state import OmeletteState
from visualization.graphviz_exporter import GraphvizExporter
from visualization.profiles.omelette_profile import OmeletteVisualizationProfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Graphviz files for the omelette domain."
    )

    parser.add_argument(
        "--total-eggs",
        type=int,
        default=4,
        help="Total number of available eggs.",
    )
    parser.add_argument(
        "--goal-good-eggs",
        type=int,
        default=2,
        help="Number of good eggs required to reach the goal.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=2,
        help="Maximum k value to compute.",
    )
    parser.add_argument(
        "--mode",
        choices=["full_graph", "policy_only"],
        default="policy_only",
        help="Rendering mode.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output DOT file path. If omitted, a name is generated automatically.",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Generate a PNG file using Graphviz.",
    )
    parser.add_argument(
        "--svg",
        action="store_true",
        help="Generate an SVG file using Graphviz.",
    )

    return parser.parse_args()


def default_dot_output_path(
    args: argparse.Namespace,
    initial_k: int,
) -> Path:
    filename = (
        f"omelette"
        f"_eggs{args.total_eggs}"
        f"_goal{args.goal_good_eggs}"
        f"_req{args.k}"
        f"_init{initial_k}"
        f"_{args.mode}.dot"
    )
    return Path("outputs/dot") / filename


def dot_to_image_path(dot_path: Path, suffix: str) -> Path:
    image_path = Path(str(dot_path).replace("outputs/dot", "outputs/images"))
    return image_path.with_suffix(suffix)


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def generate_graphviz_artifact(
    dot_path: Path,
    output_path: Path,
    format_name: str,
) -> None:
    ensure_parent_dir(output_path)

    subprocess.run(
        ["dot", f"-T{format_name}", str(dot_path), "-o", str(output_path)],
        check=True,
    )


def main() -> None:
    args = parse_args()

    problem = OmeletteProblem(
        total_eggs=args.total_eggs,
        goal_good_eggs=args.goal_good_eggs,
    )

    solver = KPlanSolver[OmeletteState, OmeletteAction]()
    result = solver.solve(problem, k=args.k)

    initial_k = result.k_values[problem.initial_state()]
    dot_path = (
        Path(args.output)
        if args.output
        else default_dot_output_path(args, initial_k)
    )
    ensure_parent_dir(dot_path)

    profile = OmeletteVisualizationProfile()

    exporter = GraphvizExporter[OmeletteState, OmeletteAction](
        mode=args.mode,
        simplify_action_labels=True,
        highlight_bad_outcomes=True,
        requested_k=args.k,
        profile=profile,
    )

    dot = exporter.export(problem, solver, result)
    print(dot)

    exporter.export_to_file(problem, solver, result, str(dot_path))
    print(f"\nDOT generato: {dot_path}")

    if args.png:
        png_path = dot_to_image_path(dot_path, ".png")
        generate_graphviz_artifact(dot_path, png_path, "png")
        print(f"PNG generato: {png_path}")

    if args.svg:
        svg_path = dot_to_image_path(dot_path, ".svg")
        generate_graphviz_artifact(dot_path, svg_path, "svg")
        print(f"SVG generato: {svg_path}")


if __name__ == "__main__":
    main()