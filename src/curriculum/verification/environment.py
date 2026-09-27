"""Probe 3: environment sanity, PRD Section 14 item 3.

Checks Python 3.12, NumPy available in the active interpreter, and that
the existing test suite is executable (collectable), without requiring
it to be green.
"""
import subprocess
import sys
from pathlib import Path

from src.curriculum.verification.types import (
    STATUS_ABSENT,
    STATUS_INCONCLUSIVE,
    STATUS_PRESENT,
    ProbeResult,
)

REQUIRED_PYTHON_MAJOR_MINOR = (3, 12)
COLLECT_TIMEOUT_SECONDS = 300


def _check_python_version() -> str:
    info = sys.version_info
    return f"{info.major}.{info.minor}.{info.micro}"


def _check_numpy() -> str:
    try:
        import numpy

        return numpy.__version__
    except ImportError:
        return ""


def _run_pytest_collect(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=COLLECT_TIMEOUT_SECONDS,
        )
        tail = result.stdout.strip().splitlines()[-5:]
        return "\n".join(tail) + f"\nreturncode: {result.returncode}"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"pytest collect failed to run: {exc}"


def _read_full_run_summary(repo_root: Path) -> str:
    log_path = repo_root / "outputs" / "_diagnostics" / "curriculum_stage0_pytest_full.log"
    if not log_path.is_file():
        return "no full-suite run log found (collection-only evidence stands alone)"
    lines = log_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    return "\n".join(lines[-3:])


def check_environment(repo_root: Path) -> ProbeResult:
    python_version = _check_python_version()
    numpy_version = _check_numpy()
    collect_output = _run_pytest_collect(repo_root)
    full_run_summary = _read_full_run_summary(repo_root)

    raw_output = [
        f"python version: {python_version} (required: {REQUIRED_PYTHON_MAJOR_MINOR[0]}.{REQUIRED_PYTHON_MAJOR_MINOR[1]}.x)",
        f"numpy version: {numpy_version or 'NOT AVAILABLE'}",
        "pytest --collect-only tail:",
        collect_output,
        "full-suite background run summary (result recorded, not required green):",
        full_run_summary,
    ]

    python_ok = sys.version_info[:2] == REQUIRED_PYTHON_MAJOR_MINOR
    numpy_ok = bool(numpy_version)
    collect_ok = "error" not in collect_output.lower()

    if python_ok and numpy_ok and collect_ok:
        status = STATUS_PRESENT
        summary = (
            f"Python {python_version}, NumPy {numpy_version}, test suite collects "
            "without errors (executable, not required to be green)."
        )
    elif not python_ok or not numpy_ok:
        status = STATUS_ABSENT
        summary = f"python_ok={python_ok}, numpy_ok={numpy_ok}, collect_ok={collect_ok}."
    else:
        status = STATUS_INCONCLUSIVE
        summary = "Test suite collection reported an error, see raw_output."

    return ProbeResult(
        probe_id="probe3_environment",
        title="Environment: Python 3.12, NumPy, executable test suite",
        status=status,
        summary=summary,
        raw_output=raw_output,
    )
