"""Probe 6: CLAUDE.md conflict points against the PRD, PRD Section 14 item 6.

Per the PRD's own preamble, it explicitly prevails over CLAUDE.md and
over ADRs 0001-0059 in any conflict. This module records the conflict
points identified by direct reading of CLAUDE.md's current content, so
Stage 0 can update CLAUDE.md with a clear, traceable list rather than a
vague "supersedes everything" note.
"""
from pathlib import Path

from src.curriculum.verification.types import STATUS_PRESENT, ProbeResult

CONFLICT_POINTS = [
    {
        "claude_md_section": "Section 3, Decided technical stack / Solver approach",
        "conflict": (
            "States the neural line (Qwen3-4B-Base + LoRA/Unsloth + per-task TTT) "
            "is again the primary development priority. The PRD explicitly "
            "excludes the neural pipeline, TTT, cross-task pretraining, "
            "augmentation, and decoding mitigations from the curricular restart."
        ),
    },
    {
        "claude_md_section": "Section 6, Current project state (Kaggle submissions)",
        "conflict": (
            "Documents 3 real, already-scored Kaggle leaderboard submissions "
            "(ref 56256382, 56314323, 56360554). The PRD prohibits any Kaggle "
            "action before Stage 7 of the curricular restart; these are historical "
            "facts of the prior approach line, not actions to repeat or build on."
        ),
    },
    {
        "claude_md_section": "Golden Rule 7 (smoke/sanity/validation layers, ADR 0015)",
        "conflict": (
            "Defines diagnostic sample tiers (2/8/40 tasks) for the old pipeline's "
            "own validation discipline. The PRD defines its own partition scheme "
            "(RN-CUR-05: curricular pool vs. probe pool, seeded, ~200-task probe "
            "pool), a different mechanism serving a different purpose (contamination "
            "control for the curricular line, not diagnostic sampling)."
        ),
    },
    {
        "claude_md_section": "Section 5/6, ADR 0060 (induce-verify-apply program induction)",
        "conflict": (
            "Records ADR 0060 as the most recent line of work, with a retry-vs-close "
            "decision left open. The PRD supersedes this entire approach line; it "
            "must not be resumed or extended under the curricular restart."
        ),
    },
    {
        "claude_md_section": "Section 4, Code conventions (no explicit contamination rule)",
        "conflict": (
            "Has no rule equivalent to RN-CUR-19 (evaluation-set tasks cited in "
            "ADRs 0001-0059 are contaminated and must be excluded from validation). "
            "This is not a contradiction but a gap the PRD fills; CLAUDE.md should "
            "record it going forward."
        ),
    },
    {
        "claude_md_section": "Standing instruction (top of Section 5)",
        "conflict": (
            "'Whenever we make a relevant decision together, update this file and "
            "create/update the corresponding ADR before moving on.' This procedural "
            "rule does not conflict with the PRD and stays in force for the "
            "curricular line too (RN-CUR-01 requires an ADR before implementation)."
        ),
    },
]


def check_claude_md_conflicts(repo_root: Path) -> ProbeResult:
    claude_md_path = repo_root / "CLAUDE.md"
    exists = claude_md_path.is_file()

    raw_output = [f"CLAUDE.md exists: {exists} ({claude_md_path})"]
    for entry in CONFLICT_POINTS:
        raw_output.append(f"- {entry['claude_md_section']}")
        raw_output.append(f"  {entry['conflict']}")

    real_conflicts = [c for c in CONFLICT_POINTS if "not a contradiction" not in c["conflict"] and "does not conflict" not in c["conflict"]]

    summary = (
        f"{len(real_conflicts)} real conflict points and {len(CONFLICT_POINTS) - len(real_conflicts)} "
        "gap/compatible notes identified by direct reading of CLAUDE.md against the PRD. "
        "CLAUDE.md still needs a top section declaring curricular mode and PRD precedence "
        "(pending Stage 0 task, not part of this probe)."
    )

    return ProbeResult(
        probe_id="probe6_claude_md_conflicts",
        title="CLAUDE.md conflict points versus the PRD",
        status=STATUS_PRESENT,
        summary=summary,
        raw_output=raw_output,
    )
