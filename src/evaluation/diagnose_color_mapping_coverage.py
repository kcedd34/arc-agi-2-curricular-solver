"""Diagnostic (not a new primitive): checks whether the color mapping
already implemented in `src/solvers/color_mapping.py` (an exact, globally
consistent, cell-position-verified substitution across ALL train pairs,
already wired into `baseline_solver.solve_task`) ever applies on the ADR
0034/0041 40-task validation sample, and if so, whether it would predict
the correct held-out output, and whether `baseline_solver`'s
MAX_PREDICTIONS cap ever suppresses a correct color-mapping prediction
behind geometric-transform candidates that filled the prediction slots
first. See ADR 0041 Section 2a/4 (item 1/2 clarification).

Usage: python -m src.evaluation.diagnose_color_mapping_coverage
"""
import json
from pathlib import Path

from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.baseline_solver import MAX_PREDICTIONS, _find_matching_geometric_transforms
from src.solvers.color_mapping import apply_color_mapping, infer_color_mapping
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "color_mapping_coverage_validation_tier.json"


def main() -> None:
    tasks = load_task_set(DATA_ROOT)
    sample = select_tier_tasks(tasks, "validation", seed=42)

    has_mapping = []
    correct_on_held_out = []
    suppressed_by_geo_cap = []

    for task_id, task in sorted(sample.items()):
        mapping = infer_color_mapping(task.train)
        if mapping is None:
            continue
        has_mapping.append(task_id)

        n_correct_pairs = sum(
            1 for pair in task.test if apply_color_mapping(pair.input, mapping) == pair.output
        )
        if n_correct_pairs > 0:
            correct_on_held_out.append({"task_id": task_id, "correct_pairs": n_correct_pairs, "total_pairs": len(task.test)})
            if len(_find_matching_geometric_transforms(task)) >= MAX_PREDICTIONS:
                suppressed_by_geo_cap.append(task_id)

    print(f"validation_sample_size={len(sample)}")
    print(f"tasks_with_exact_global_color_mapping={len(has_mapping)}")
    print(f"task_ids_with_mapping={has_mapping}")
    print(f"tasks_where_mapping_alone_correct_on_held_out={len(correct_on_held_out)}")
    print(f"detail={correct_on_held_out}")
    print(f"tasks_where_correct_mapping_suppressed_by_geo_cap={suppressed_by_geo_cap}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "validation_sample_size": len(sample),
                "tasks_with_exact_global_color_mapping": len(has_mapping),
                "task_ids_with_mapping": has_mapping,
                "tasks_where_mapping_alone_correct_on_held_out": len(correct_on_held_out),
                "detail": correct_on_held_out,
                "tasks_where_correct_mapping_suppressed_by_geo_cap": suppressed_by_geo_cap,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
