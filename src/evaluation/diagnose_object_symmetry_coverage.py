"""Diagnostic (not a primitive yet): measures how many of the ADR 0034/
0041/0042/0043/0044 40-task validation sample have a candidate under
cheap connected-component heuristics (ADR 0041 item 4) and a cheap
symmetry-break-and-repair heuristic (ADR 0041 item 5), using ONLY train
pairs, before committing to either full primitive build.

Two independent classifications per task, same ADR 0038 safety bar as
every other diagnostic in this project: every heuristic variant that
fits 100% of a task's train pairs is pooled per family; more than one
distinct survivor means the task is "ambiguous" for that family (never
resolved by picking one arbitrarily); exactly one means "candidate";
none means "no_candidate". For each non-ambiguous candidate, held-out
test-pair correctness is also recorded, purely as extra signal, never
to change the classification.

See ADR 0045. Usage: python -m src.evaluation.diagnose_object_symmetry_coverage
"""
import json
from pathlib import Path

from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.object_heuristics import apply_object_heuristic, detect_object_heuristics
from src.solvers.symmetry_heuristics import apply_symmetry_heuristic, detect_symmetry_heuristics
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "object_symmetry_coverage_validation_tier.json"


def _classify(candidates):
    if len(candidates) == 0:
        return "no_candidate"
    if len(candidates) > 1:
        return "ambiguous"
    return "candidate"


def _held_out_correctness(task, category, candidate, apply_fn):
    if category != "candidate":
        return None
    n_correct = sum(1 for pair in task.test if apply_fn(candidate, pair.input) == pair.output)
    return {"correct_pairs": n_correct, "total_pairs": len(task.test)}


def _classify_family(task, hypotheses, apply_fn):
    category = _classify(hypotheses)
    candidate = hypotheses[0] if hypotheses else None
    held_out = _held_out_correctness(task, category, candidate, apply_fn)
    return {"category": category, "held_out": held_out, "labels": [str(h) for h in hypotheses]}


def _classify_task(task):
    return {
        "object": _classify_family(task, detect_object_heuristics(task.train), apply_object_heuristic),
        "symmetry": _classify_family(task, detect_symmetry_heuristics(task.train), apply_symmetry_heuristic),
    }


def _summarize(by_task, family):
    counts = {"candidate": 0, "ambiguous": 0, "no_candidate": 0}
    correct = 0
    for entry in by_task.values():
        counts[entry[family]["category"]] += 1
        held_out = entry[family]["held_out"]
        if held_out is not None and held_out["correct_pairs"] > 0:
            correct += 1
    return counts, correct


def main() -> None:
    tasks = load_task_set(DATA_ROOT)
    sample = select_tier_tasks(tasks, "validation", seed=42)

    by_task = {task_id: _classify_task(task) for task_id, task in sorted(sample.items())}

    object_counts, object_correct = _summarize(by_task, "object")
    symmetry_counts, symmetry_correct = _summarize(by_task, "symmetry")

    print(f"validation_sample_size={len(sample)}")
    print(f"object: {object_counts}, tasks_correct_on_held_out={object_correct}")
    print(f"symmetry: {symmetry_counts}, tasks_correct_on_held_out={symmetry_correct}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "validation_sample_size": len(sample),
                "object": {"counts": object_counts, "tasks_correct_on_held_out": object_correct},
                "symmetry": {"counts": symmetry_counts, "tasks_correct_on_held_out": symmetry_correct},
                "by_task": by_task,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
