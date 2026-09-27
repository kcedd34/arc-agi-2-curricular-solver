"""CLI orchestrator for the Stage 0 verification routine, PRD Section 14.

Runs all six probes without aborting on the first failure, writes
docs/curriculum/verification.md, and exits non-zero if any probe is
inconclusive (a hard gate on Stage 0).
"""
import sys
from pathlib import Path

from src.curriculum.verification.claude_md_conflicts import check_claude_md_conflicts
from src.curriculum.verification.contamination import check_contamination
from src.curriculum.verification.dataset_integrity import check_dataset_integrity
from src.curriculum.verification.environment import check_environment
from src.curriculum.verification.report import write_report
from src.curriculum.verification.reuse_candidates import check_reuse_candidates
from src.curriculum.verification.task_presence import check_task_presence
from src.curriculum.verification.types import STATUS_INCONCLUSIVE, ProbeResult

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data" / "ARC-AGI-2" / "data"
REPORT_PATH = REPO_ROOT / "docs" / "curriculum" / "verification.md"
CONTAMINATION_PATH = REPO_ROOT / "docs" / "curriculum" / "evaluation-contamination.json"


def _run_probe_safely(name: str, func, *args) -> ProbeResult:
    """Run one probe, never letting an exception abort the whole routine."""
    try:
        return func(*args)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see module docstring
        return ProbeResult(
            probe_id=name,
            title=name,
            status=STATUS_INCONCLUSIVE,
            summary=f"Probe raised an unhandled exception: {exc!r}",
            raw_output=[repr(exc)],
        )


def run_all_probes() -> list:
    results = [
        _run_probe_safely("probe1_dataset_integrity", check_dataset_integrity, DATA_ROOT),
        _run_probe_safely("probe2_task_presence", check_task_presence, DATA_ROOT, "007bbfb7"),
        _run_probe_safely("probe3_environment", check_environment, REPO_ROOT),
        _run_probe_safely("probe4_reuse_candidates", check_reuse_candidates, REPO_ROOT),
        _run_probe_safely("probe5_contamination", check_contamination, REPO_ROOT, CONTAMINATION_PATH),
        _run_probe_safely("probe6_claude_md_conflicts", check_claude_md_conflicts, REPO_ROOT),
    ]
    return results


def main() -> int:
    results = run_all_probes()
    write_report(results, REPORT_PATH)

    any_inconclusive = any(r.status == STATUS_INCONCLUSIVE for r in results)
    print(f"Verification report written to: {REPORT_PATH}")
    for result in results:
        print(f"  {result.probe_id}: {result.status}")

    if any_inconclusive:
        print("BLOCKED: at least one probe is inconclusive, Stage 0 cannot proceed.")
        return 1
    print("PASSED: no inconclusive probe, Stage 0 may proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
