"""Probe 4: evaluate reuse candidates from the old pipeline, PRD Section 14 item 4.

Per RN-CUR-02, no old component is reused without an explicit,
documented verification. This module records the decision (reuse vs.
reimplement) for each of the three candidates identified in the old
codebase: task_loader.py, submission_format.py, sample_tiers.py.

Decisions here are recorded as fact (already checked by direct source
reading in this session), not re-derived at run time, since the
justification depends on reading source code, not on executing it.
"""
from pathlib import Path

from src.curriculum.verification.types import STATUS_PRESENT, ProbeResult

REUSE_DECISIONS = [
    {
        "candidate": "src/utils/task_loader.py (load_task, load_task_set)",
        "decision": "partial reuse",
        "justification": (
            "load_task reads Pair(input, output) directly from the raw JSON's "
            "'test' split, including the real gabarito. Per RN-CUR-03 the solver "
            "loader must not expose test outputs, guaranteed by construction, so "
            "this loader cannot be reused as-is on the solver side. It is safe to "
            "reuse on the evaluator side only (the one component allowed to read "
            "gabaritos), and a new, structurally output-blind loader will be built "
            "for the solver in src/curriculum/loader.py."
        ),
    },
    {
        "candidate": "src/evaluation/submission_format.py (validate_submission, _validate_grid)",
        "decision": "reimplement (minimal subset)",
        "justification": (
            "This module's scope is the Kaggle ADR-0006 submission structure "
            "(attempt_1/attempt_2 per task id), which is out of bounds until "
            "Stage 7. Only its grid-validity check (_validate_grid: rectangular, "
            "cells 0-9) is relevant now, and that is small enough to reimplement "
            "directly inside src/curriculum/grid.py for isolation from the "
            "Kaggle-specific submission code (RF01)."
        ),
    },
    {
        "candidate": "src/evaluation/sample_tiers.py (select_tier_tasks, _stratified_sample)",
        "decision": "reimplement (minimal subset)",
        "justification": (
            "This module's purpose is output-size-stratified diagnostic tiers "
            "(smoke/sanity/validation) for the old neural/symbolic pipeline. The "
            "PRD's need is different and simpler: one-time deterministic seeded "
            "partition of the full training set into a curricular pool and a "
            "probe pool (RN-CUR-05, ~200 tasks). A minimal seeded split will be "
            "implemented directly in src/curriculum/partition.py rather than "
            "adapting this module's stratification machinery."
        ),
    },
]


def check_reuse_candidates(repo_root: Path) -> ProbeResult:
    raw_output = []
    all_files_exist = True
    for entry in REUSE_DECISIONS:
        candidate_path = entry["candidate"].split(" ", 1)[0]
        exists = (repo_root / candidate_path).is_file()
        all_files_exist = all_files_exist and exists
        raw_output.append(f"- {entry['candidate']}")
        raw_output.append(f"  exists: {exists}")
        raw_output.append(f"  decision: {entry['decision']}")
        raw_output.append(f"  justification: {entry['justification']}")

    summary = (
        f"{len(REUSE_DECISIONS)} reuse candidates evaluated by direct source reading: "
        "task_loader.py (partial reuse, evaluator side only), submission_format.py "
        "and sample_tiers.py (reimplement minimal subsets in src/curriculum/). "
        f"All referenced source files exist: {all_files_exist}."
    )

    return ProbeResult(
        probe_id="probe4_reuse_candidates",
        title="Reuse candidates: task loader, format validator, stratified sampler",
        status=STATUS_PRESENT,
        summary=summary,
        raw_output=raw_output,
    )
