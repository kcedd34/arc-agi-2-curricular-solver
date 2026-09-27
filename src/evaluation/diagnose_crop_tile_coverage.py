"""Diagnostic (not a primitive yet): measures how many of the ADR 0034/
0041/0042 40-task validation sample have a crop hypothesis
(`src/solvers/crop_rules.py`) and/or a tile hypothesis
(`src/solvers/tile_rules.py`) that fits 100% of that task's own train
pairs, using ONLY train pairs, before ever looking at test input.

Classification per task, mirroring the ADR 0038/0042 safety bar (a
hypothesis only counts if it is the UNIQUE explanation of the train
data): all crop and tile hypotheses that independently fit every train
pair are pooled together; if the pool has more than one distinct
hypothesis, the task is "ambiguous" (never resolved by picking one
arbitrarily); if it has exactly one, the task is a "crop_candidate" or
"tile_candidate"; if it has none, "no_candidate". For each
non-ambiguous candidate, held-out test-pair correctness is also
recorded, purely as extra signal, never to change the classification.

See ADR 0043. Usage: python -m src.evaluation.diagnose_crop_tile_coverage
"""
import json
from pathlib import Path

from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.crop_rules import apply_crop_hypothesis, detect_crop_hypotheses
from src.solvers.tile_rules import apply_tile_hypothesis, detect_tile_hypotheses
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "crop_tile_coverage_validation_tier.json"


def _classify(crop_hypotheses, tile_hypotheses):
    pool_size = len(crop_hypotheses) + len(tile_hypotheses)
    if pool_size == 0:
        return "no_candidate"
    if pool_size > 1:
        return "ambiguous"
    if crop_hypotheses:
        return "crop_candidate"
    return "tile_candidate"


def _held_out_correctness(task, category, crop_hypotheses, tile_hypotheses):
    if category == "crop_candidate":
        apply_fn, hypothesis = apply_crop_hypothesis, crop_hypotheses[0]
    elif category == "tile_candidate":
        apply_fn, hypothesis = apply_tile_hypothesis, tile_hypotheses[0]
    else:
        return None
    n_correct = sum(1 for pair in task.test if apply_fn(hypothesis, pair.input) == pair.output)
    return {"correct_pairs": n_correct, "total_pairs": len(task.test)}


def _classify_task(task):
    crop_hypotheses = detect_crop_hypotheses(task.train)
    tile_hypotheses = detect_tile_hypotheses(task.train)
    category = _classify(crop_hypotheses, tile_hypotheses)
    held_out = _held_out_correctness(task, category, crop_hypotheses, tile_hypotheses)
    return category, held_out


def main() -> None:
    tasks = load_task_set(DATA_ROOT)
    sample = select_tier_tasks(tasks, "validation", seed=42)

    counts = {"crop_candidate": 0, "tile_candidate": 0, "ambiguous": 0, "no_candidate": 0}
    by_task = {}

    for task_id, task in sorted(sample.items()):
        category, held_out = _classify_task(task)
        counts[category] += 1
        by_task[task_id] = {"category": category, "held_out": held_out}

    n_correct_on_held_out = sum(
        1
        for entry in by_task.values()
        if entry["held_out"] is not None and entry["held_out"]["correct_pairs"] > 0
    )

    print(f"validation_sample_size={len(sample)}")
    print(f"crop_candidate={counts['crop_candidate']}")
    print(f"tile_candidate={counts['tile_candidate']}")
    print(f"ambiguous={counts['ambiguous']}")
    print(f"no_candidate={counts['no_candidate']}")
    print(f"tasks_correct_on_held_out={n_correct_on_held_out}")
    print(f"detail={json.dumps(by_task, indent=2)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "validation_sample_size": len(sample),
                "counts": counts,
                "tasks_correct_on_held_out": n_correct_on_held_out,
                "by_task": by_task,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
