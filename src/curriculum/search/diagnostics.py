"""Search-log instrumentation for a single task's hypothesis search.

Reuses the exact same enumeration/verification logic as `rank.search_task`
(no behavior change to production code), but records a per-candidate
classification instead of only the final aggregate result. This exists to
produce citable evidence for RN-CUR-30's acceptance review (Item 3.1 of the
governing acceptance-completion prompt): how many hypotheses were
enumerated, how many were discarded, and by which classification.

RN-CUR-33 step 2: candidates are now `Composition` records (layout x
selector x content), grouped "by family" (the 4 piece names, ignoring
their param values) instead of "by primitive", so the log shows which
shared pieces each task's composition draws on.
"""
from dataclasses import dataclass, field
from typing import Dict, List

from src.curriculum.grid import Grid, grids_equal
from src.curriculum.loader import Task
from src.curriculum.spec import interpreter
from src.curriculum.search.compose import Composition, build_composition_steps, enumerate_compositions


@dataclass
class CandidateLog:
    composition: Composition
    classification: str  # "verified" | "discarded_train_mismatch" | "discarded_interpreter_error"


@dataclass
class SearchLog:
    task_id: str
    total_enumerated: int
    verified_count: int
    discarded_count: int
    by_family: Dict[str, Dict[str, int]] = field(default_factory=dict)
    candidates: List[CandidateLog] = field(default_factory=list)
    final_status: str = "no_candidate"


def _family_key(composition: Composition) -> str:
    return (
        f"{composition.layout_name}+{composition.selector_name}+"
        f"{composition.selected_content_name}+{composition.not_selected_content_name}"
    )


def _classify(composition: Composition, task: Task) -> CandidateLog:
    steps = build_composition_steps(composition)
    for pair in task.train:
        try:
            output_grid, _trace = interpreter.run(steps, pair.input)
        except interpreter.InterpreterError:
            return CandidateLog(composition, "discarded_interpreter_error")
        if not grids_equal(output_grid, pair.output):
            return CandidateLog(composition, "discarded_train_mismatch")
    return CandidateLog(composition, "verified")


def _predict(steps, task: Task) -> List[Grid]:
    return [interpreter.run(steps, grid)[0] for grid in task.test_inputs]


def build_search_log(task: Task) -> SearchLog:
    log = SearchLog(task_id=task.task_id, total_enumerated=0, verified_count=0, discarded_count=0)
    predictions_by_verified: List[List[Grid]] = []

    for composition in enumerate_compositions(task):
        log.total_enumerated += 1
        candidate = _classify(composition, task)
        log.candidates.append(candidate)

        bucket = log.by_family.setdefault(
            _family_key(composition),
            {"verified": 0, "discarded_train_mismatch": 0, "discarded_interpreter_error": 0},
        )
        bucket[candidate.classification] += 1

        if candidate.classification == "verified":
            log.verified_count += 1
            steps = build_composition_steps(composition)
            predictions_by_verified.append(_predict(steps, task))
        else:
            log.discarded_count += 1

    if log.verified_count == 0:
        log.final_status = "no_candidate"
    else:
        first = predictions_by_verified[0]
        if any(preds != first for preds in predictions_by_verified[1:]):
            log.final_status = "ambiguous"
        else:
            log.final_status = "solved"

    return log


def format_search_log(log: SearchLog) -> str:
    lines = [
        f"Search log: {log.task_id}",
        f"Total hypotheses enumerated: {log.total_enumerated}",
        f"Verified (matched 100% of train pairs): {log.verified_count}",
        f"Discarded: {log.discarded_count}",
        f"Final status: {log.final_status}",
        "",
        "By family (layout+selector+selected+not_selected):",
    ]
    for name, counts in sorted(log.by_family.items()):
        lines.append(
            f"  {name}: enumerated={sum(counts.values())} "
            f"verified={counts['verified']} "
            f"discarded_train_mismatch={counts['discarded_train_mismatch']} "
            f"discarded_interpreter_error={counts['discarded_interpreter_error']}"
        )
    lines.append("")
    lines.append("Verified candidates:")
    for c in log.candidates:
        if c.classification == "verified":
            lines.append(f"  {c.composition.describe()}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from src.curriculum.cli_output import print_summary, write_detail
    from src.curriculum.loader import load_task

    task_id = sys.argv[1] if len(sys.argv) > 1 else "007bbfb7"
    task_path = Path("data/ARC-AGI-2/data/training") / f"{task_id}.json"
    task = load_task(task_path)
    result_log = build_search_log(task)
    detail_path = write_detail(
        format_search_log(result_log), Path(f"outputs/curriculum/search-log/{task_id}.txt")
    )
    print_summary(
        [
            f"Task: {result_log.task_id}",
            f"Total hypotheses enumerated: {result_log.total_enumerated}",
            f"Verified: {result_log.verified_count}",
            f"Discarded: {result_log.discarded_count}",
            f"Final status: {result_log.final_status}",
        ],
        detail_path,
    )
