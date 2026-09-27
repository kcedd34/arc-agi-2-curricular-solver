"""Piece-usage audit for the object pack's 9 pieces without a confirmed
win (item 4 of the 2026-09-22 follow-up request; the 9 names come from
`outputs/curriculum/object-pack-final-report.txt` line 10, the real
Phase 7 gate run's own "pecas sem uso" list): for each one, whether it
is ever enumerated at all across the curricular pool, or enumerated but
never a winning composition.

`enumerate_object_compositions` has no piece-level exclusion rule
anywhere in `object_search.py`/`object_selector.py` (confirmed by
reading; the 6 zero-param selector pieces are always instantiated by
`_expand_selector_pieces` whenever selector expansion runs at all, and
`erase_selected`/`slide_selected`'s own params always have a non-empty
fallback in `object_params.py`). Only two of the 9 names have a
parameter whose candidate list can legitimately come back empty for a
given task: `objects_of_color` (`infer_colors_common_to_every_input`)
and `fill_bbox_selected` (`infer_target_color_candidates`, the
`new_color_always_added`-but-no-common-color branch). This module
measures the real enumeration counts across the pool rather than
asserting the above from static reading alone (RN-CUR-30).

RN-CUR-03: only inspects `enumerate_object_compositions`'s own
combinatorics, never a gabarito.
"""
import functools
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.curriculum.cli_output import print_summary, write_detail
from src.curriculum.library.objects.object_search import enumerate_object_compositions
from src.curriculum.loader import load_task
from src.curriculum.object_pack_gate import DEFAULT_PARTITION_PATH, DEFAULT_STATE_PATH, not_yet_accepted_pool
from src.curriculum.parallel_batch import run_batch
from src.curriculum.select import load_curricular_pool
from src.curriculum.state import load_state

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
DEFAULT_REPORT_PATH = Path("outputs/curriculum/piece-usage-audit-detail.txt")

UNUSED_PIECES = (
    "objects_of_color",
    "objects_touching_border",
    "objects_not_touching_border",
    "all_objects",
    "unique_color_object",
    "largest_object",
    "erase_selected",
    "fill_bbox_selected",
    "slide_selected",
)


@dataclass
class PieceUsageTaskResult:
    task_id: str
    selector_counts: Dict[str, int]
    content_counts: Dict[str, int]
    error: Optional[str] = None


def _piece_usage_worker(task_id: str, training_dir: Path) -> PieceUsageTaskResult:
    try:
        task = load_task(training_dir / f"{task_id}.json")
        selector_counts: Counter = Counter()
        content_counts: Counter = Counter()
        for composition in enumerate_object_compositions(task):
            selector_counts[composition.selector_name] += 1
            content_counts[composition.selected_content_name] += 1
            if composition.not_selected_content_name:
                content_counts[composition.not_selected_content_name] += 1
        return PieceUsageTaskResult(task_id, dict(selector_counts), dict(content_counts))
    except Exception as exc:  # isolated per-task failure, RN-CUR-32 batch discipline
        return PieceUsageTaskResult(task_id, {}, {}, error=repr(exc))


def run_piece_usage_audit(
    task_ids: List[str], training_dir: Path = DEFAULT_TRAINING_DIR, max_workers: Optional[int] = None
) -> List[PieceUsageTaskResult]:
    worker = functools.partial(_piece_usage_worker, training_dir=training_dir)
    outcomes = run_batch(task_ids, worker, max_workers=max_workers)
    return [
        result if not isinstance(result, BaseException)
        else PieceUsageTaskResult(task_id, {}, {}, error=repr(result))
        for task_id, result in outcomes
    ]


def aggregate_enumeration_counts(results: List[PieceUsageTaskResult]) -> Dict[str, int]:
    totals: Counter = Counter()
    for r in results:
        for name, count in r.selector_counts.items():
            totals[name] += count
        for name, count in r.content_counts.items():
            totals[name] += count
    return dict(totals)


_PRUNING_RULE_BY_PIECE = {
    "objects_of_color": "object_params.objects_of_color_candidates -> search/pruning.infer_colors_common_to_every_input",
    "fill_bbox_selected": "object_params.recolor_target_color_candidates -> search/pruning.infer_target_color_candidates",
}


def classify_pieces(totals: Dict[str, int]) -> Dict[str, str]:
    classification = {}
    for name in UNUSED_PIECES:
        count = totals.get(name, 0)
        if count == 0:
            rule = _PRUNING_RULE_BY_PIECE.get(name, "no pruning rule found for this piece (see note)")
            classification[name] = f"blocked by pruning (0 enumerations pool-wide): {rule}"
        else:
            classification[name] = f"enumerated {count} times pool-wide, never a winning composition"
    return classification


def format_report(results: List[PieceUsageTaskResult], classification: Dict[str, str]) -> str:
    errors = [r.task_id for r in results if r.error is not None]
    lines = [f"Piece-usage audit over {len(results)} pool tasks (errors: {len(errors)})", ""]
    for name in UNUSED_PIECES:
        lines.append(f"{name}: {classification[name]}")
    if errors:
        lines.append("")
        lines.append(f"Errored tasks: {errors}")
    return "\n".join(lines)


def main(argv=None) -> int:
    state = load_state(DEFAULT_STATE_PATH)
    pool = load_curricular_pool(DEFAULT_PARTITION_PATH)
    task_ids = not_yet_accepted_pool(state, pool)

    results = run_piece_usage_audit(task_ids)
    totals = aggregate_enumeration_counts(results)
    classification = classify_pieces(totals)

    detail_path = write_detail(format_report(results, classification), DEFAULT_REPORT_PATH)
    print_summary(
        [f"{name}: {classification[name]}" for name in UNUSED_PIECES],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
