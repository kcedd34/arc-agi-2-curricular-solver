"""One-off host-Python analysis for ADR 0024 (shape mismatch root cause).

Reuses persisted artifacts from the ADR 0023 sanity run:
- outputs/diagnostics/sanity_current_config/evaluation/current_config_<task_id>.json
- outputs/raw_generations/sanity_current_config/evaluation/current_config_<task_id>_<split>_<pair_index>_<attempt_index>.txt

No GPU/model re-run. Answers, per shape-mismatched held-out test pair:
(1) is the task's output-size rule fixed or variable across train pairs?
(2) does the predicted shape match the shape of any of the task's own
    train outputs (evidence of "copying a seen size")?
(3) which raw attempt file(s) produced the kept prediction(s), for a
    later token-count check (EOS vs. max_new_tokens cap).
"""
import json
from pathlib import Path

from src.evaluation.pair_diagnostics import dimension_match
from src.solvers.neural.grid_serialization import text_to_grid
from src.utils.task_loader import load_task

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
DIAG_DIR = PROJECT_ROOT / "outputs" / "diagnostics" / "sanity_current_config" / "evaluation"
RAW_DIR = PROJECT_ROOT / "outputs" / "raw_generations" / "sanity_current_config" / "evaluation"
CONFIG_NAME = "current_config"

TASK_IDS = [
    "0934a4d8", "135a2760", "136b0064", "13e47133",
    "142ca369", "16b78196", "16de56c4", "1818057f",
]


def shape_of(grid):
    if not grid:
        return None
    return (len(grid), len(grid[0]) if grid[0] else 0)


def load_diag_rows(task_id):
    path = DIAG_DIR / f"{CONFIG_NAME}_{task_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def reconstruct_kept_predictions(task_id, split, pair_index, attempts_tried):
    """Mirror generate_with_counts' dedup logic by reparsing raw .txt files
    in attempt order. Returns list of (attempt_index, grid) for kept preds."""
    kept = []
    for attempt_index in range(attempts_tried):
        path = RAW_DIR / f"{CONFIG_NAME}_{task_id}_{split}_{pair_index}_{attempt_index}.txt"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        grid = text_to_grid(text)
        if grid is not None and grid not in [g for _, g in kept]:
            kept.append((attempt_index, grid))
    return kept


def classify_size_rule(task):
    train_out_shapes = [shape_of(p.output) for p in task.train]
    train_in_shapes = [shape_of(p.input) for p in task.train]
    fixed_output = len(set(train_out_shapes)) == 1
    same_as_input = all(o == i for o, i in zip(train_out_shapes, train_in_shapes))
    return {
        "train_in_shapes": train_in_shapes,
        "train_out_shapes": train_out_shapes,
        "fixed_output_shape": fixed_output,
        "output_always_equals_input_shape": same_as_input,
    }


def main():
    for task_id in TASK_IDS:
        task = load_task(DATA_DIR / f"{task_id}.json")
        size_rule = classify_size_rule(task)
        diag_rows = load_diag_rows(task_id)
        test_rows = [r for r in diag_rows if r["split"] == "test"]

        print(f"=== {task_id} ===")
        print(f"  train input shapes:  {size_rule['train_in_shapes']}")
        print(f"  train output shapes: {size_rule['train_out_shapes']}")
        print(f"  fixed_output_shape={size_rule['fixed_output_shape']} "
              f"output_always_equals_input_shape={size_rule['output_always_equals_input_shape']}")

        for row in test_rows:
            pair_index = row["pair_index"]
            expected = task.test[pair_index].output
            expected_shape = shape_of(expected)
            shape_ok = row["shape_matches_expected"]
            kept = reconstruct_kept_predictions(
                task_id, "test", pair_index, row["attempts_tried"]
            )
            print(f"  test[{pair_index}] expected_shape={expected_shape} "
                  f"shape_matches_expected(from ADR0023)={shape_ok}")
            for attempt_index, grid in kept:
                pred_shape = shape_of(grid)
                matches_any_train_out = any(
                    dimension_match(grid, p.output) for p in task.train
                )
                smaller_rows = pred_shape[0] < expected_shape[0]
                smaller_cols = pred_shape[1] < expected_shape[1]
                fname = f"{CONFIG_NAME}_{task_id}_test_{pair_index}_{attempt_index}.txt"
                print(f"    attempt={attempt_index} file={fname} "
                      f"pred_shape={pred_shape} matches_a_train_output_shape={matches_any_train_out} "
                      f"smaller_than_expected(rows,cols)=({smaller_rows},{smaller_cols})")
        print()


if __name__ == "__main__":
    main()
