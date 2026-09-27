"""Diagnostic (not a primitive yet): measures how many of the ADR 0034/
0041/0042/0043 40-task validation sample are solved by a depth-2
composition of the existing primitive library
(`src/solvers/composition_search.py`), using ONLY train pairs, before
ever looking at test input.

Classification per task, same ADR 0038 safety bar as every other
diagnostic in this project: every composition that fits 100% of a
task's train pairs is pooled; more than one distinct composition means
the task is "ambiguous" (never resolved by picking one arbitrarily);
exactly one means "composition_candidate"; none means "no_candidate".
For each non-ambiguous candidate, held-out test-pair correctness is also
recorded, purely as extra signal, never to change the classification.

See ADR 0044. Usage: python -m src.evaluation.diagnose_composition_coverage
"""
import json
from pathlib import Path

from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.composition_search import find_compositions
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "composition_coverage_validation_tier.json"


def _classify(compositions):
    if len(compositions) == 0:
        return "no_candidate"
    if len(compositions) > 1:
        return "ambiguous"
    return "composition_candidate"


def _held_out_correctness(task, category, compositions):
    if category != "composition_candidate":
        return None
    composition = compositions[0]
    n_correct = sum(1 for pair in task.test if composition.apply(pair.input) == pair.output)
    return {"correct_pairs": n_correct, "total_pairs": len(task.test)}


def _classify_task(task):
    compositions = find_compositions(task.train)
    category = _classify(compositions)
    held_out = _held_out_correctness(task, category, compositions)
    labels = [c.label for c in compositions]
    return category, held_out, labels


def main() -> None:
    tasks = load_task_set(DATA_ROOT)
    sample = select_tier_tasks(tasks, "validation", seed=42)

    counts = {"composition_candidate": 0, "ambiguous": 0, "no_candidate": 0}
    by_task = {}

    for task_id, task in sorted(sample.items()):
        category, held_out, labels = _classify_task(task)
        counts[category] += 1
        by_task[task_id] = {"category": category, "held_out": held_out, "labels": labels}

    n_correct_on_held_out = sum(
        1
        for entry in by_task.values()
        if entry["held_out"] is not None and entry["held_out"]["correct_pairs"] > 0
    )

    print(f"validation_sample_size={len(sample)}")
    print(f"composition_candidate={counts['composition_candidate']}")
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
