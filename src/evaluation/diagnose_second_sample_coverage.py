"""Re-runs the five existing measurable coverage diagnostics (color
mapping, crop/tile, depth-2 composition, object heuristics, symmetry
heuristics) against a SECOND, independently-seeded 40-task validation
sample, using the exact same ADR 0015 stratified method as every prior
ADR 0034/0041/0042/0043/0044/0045 measurement (which all used seed=42).

This script implements zero new heuristics or primitives. It only
imports and re-applies the already-tested `detect_*`/`infer_*`/
`find_*` functions from ADR 0042 (`color_mapping.py`), ADR 0043
(`crop_rules.py`/`tile_rules.py`), ADR 0044 (`composition_search.py`),
and ADR 0045 (`object_heuristics.py`/`symmetry_heuristics.py`) against a
different task sample, to check whether the near-total null pattern
measured on the seed=42 sample is specific to that sample or structural
to this benchmark.

ADR 0041/0042 item 1 (shape-as-content) is NOT re-run here: it was
closed by code inspection, not by sample measurement (`shape_rule.py`/
`fixed_shape_rule.py` return only a bool/shape tuple, never grid
content), so its conclusion does not depend on which task sample is
used and there is no `detect_*`/apply-content function to re-run.

Same ADR 0038 safety bar as every diagnostic reused here: a hypothesis
only counts as a task-level candidate if it reproduces 100% of that
task's train pairs; more than one distinct surviving hypothesis in the
same family makes the task ambiguous, never resolved by picking one
arbitrarily.

See ADR 0046. Usage: python -m src.evaluation.diagnose_second_sample_coverage
"""
import json
from pathlib import Path

from src.evaluation.sample_tiers import select_tier_tasks
from src.solvers.color_mapping import apply_color_mapping, infer_color_mapping
from src.solvers.composition_search import find_compositions
from src.solvers.crop_rules import apply_crop_hypothesis, detect_crop_hypotheses
from src.solvers.object_heuristics import apply_object_heuristic, detect_object_heuristics
from src.solvers.symmetry_heuristics import apply_symmetry_heuristic, detect_symmetry_heuristics
from src.solvers.tile_rules import apply_tile_hypothesis, detect_tile_hypotheses
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "second_sample_coverage_validation_tier.json"
SECOND_SAMPLE_SEED = 7


def _classify(candidates):
    if len(candidates) == 0:
        return "no_candidate"
    if len(candidates) > 1:
        return "ambiguous"
    return "candidate"


def _held_out(task, category, candidate, apply_fn):
    if category != "candidate":
        return None
    n_correct = sum(1 for pair in task.test if apply_fn(candidate, pair.input) == pair.output)
    return {"correct_pairs": n_correct, "total_pairs": len(task.test)}


def _classify_color_mapping(task):
    mapping = infer_color_mapping(task.train)
    category = "candidate" if mapping is not None else "no_candidate"
    held_out = None
    if category == "candidate":
        n_correct = sum(1 for pair in task.test if apply_color_mapping(pair.input, mapping) == pair.output)
        held_out = {"correct_pairs": n_correct, "total_pairs": len(task.test)}
    return {"category": category, "held_out": held_out}


def _classify_crop_tile(task):
    crop_hypotheses = detect_crop_hypotheses(task.train)
    tile_hypotheses = detect_tile_hypotheses(task.train)
    pool_size = len(crop_hypotheses) + len(tile_hypotheses)
    if pool_size == 0:
        category = "no_candidate"
    elif pool_size > 1:
        category = "ambiguous"
    elif crop_hypotheses:
        category = "crop_candidate"
    else:
        category = "tile_candidate"
    if category == "crop_candidate":
        held_out = _held_out(task, "candidate", crop_hypotheses[0], apply_crop_hypothesis)
    elif category == "tile_candidate":
        held_out = _held_out(task, "candidate", tile_hypotheses[0], apply_tile_hypothesis)
    else:
        held_out = None
    return {"category": category, "held_out": held_out}


def _classify_composition(task):
    compositions = find_compositions(task.train)
    category = _classify(compositions)
    held_out = None
    if category == "candidate":
        composition = compositions[0]
        n_correct = sum(1 for pair in task.test if composition.apply(pair.input) == pair.output)
        held_out = {"correct_pairs": n_correct, "total_pairs": len(task.test)}
    return {"category": category, "held_out": held_out}


def _classify_family(task, hypotheses, apply_fn):
    category = _classify(hypotheses)
    candidate = hypotheses[0] if hypotheses else None
    held_out = _held_out(task, category, candidate, apply_fn)
    return {"category": category, "held_out": held_out}


def _classify_task(task):
    return {
        "color_mapping": _classify_color_mapping(task),
        "crop_tile": _classify_crop_tile(task),
        "composition": _classify_composition(task),
        "object": _classify_family(task, detect_object_heuristics(task.train), apply_object_heuristic),
        "symmetry": _classify_family(task, detect_symmetry_heuristics(task.train), apply_symmetry_heuristic),
    }


def _summarize(by_task, family, categories):
    counts = {category: 0 for category in categories}
    correct = 0
    for entry in by_task.values():
        counts[entry[family]["category"]] += 1
        held_out = entry[family]["held_out"]
        if held_out is not None and held_out["correct_pairs"] > 0:
            correct += 1
    return counts, correct


def main() -> None:
    tasks = load_task_set(DATA_ROOT)
    sample = select_tier_tasks(tasks, "validation", seed=SECOND_SAMPLE_SEED)

    by_task = {task_id: _classify_task(task) for task_id, task in sorted(sample.items())}

    families = {
        "color_mapping": ["candidate", "no_candidate"],
        "crop_tile": ["crop_candidate", "tile_candidate", "ambiguous", "no_candidate"],
        "composition": ["candidate", "ambiguous", "no_candidate"],
        "object": ["candidate", "ambiguous", "no_candidate"],
        "symmetry": ["candidate", "ambiguous", "no_candidate"],
    }

    summary = {}
    print(f"second_sample_seed={SECOND_SAMPLE_SEED}")
    print(f"validation_sample_size={len(sample)}")
    for family, categories in families.items():
        counts, correct = _summarize(by_task, family, categories)
        summary[family] = {"counts": counts, "tasks_correct_on_held_out": correct}
        print(f"{family}: {counts}, tasks_correct_on_held_out={correct}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "second_sample_seed": SECOND_SAMPLE_SEED,
                "validation_sample_size": len(sample),
                "summary": summary,
                "by_task": by_task,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
