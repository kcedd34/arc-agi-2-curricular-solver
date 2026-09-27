"""Runs a model-generated transform(g) program against one grid inside a
restricted, isolated subprocess (ADR 0060).

See program_sandbox_runner.py for the sandboxed side (restricted
builtins, no imports). This module owns the process boundary: a hard
timeout via subprocess.run, and strict validation of whatever comes back
so a malformed or malicious result can never reach the caller as if it
were trustworthy.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

_RUNNER_PATH = Path(__file__).with_name("program_sandbox_runner.py")
DEFAULT_TIMEOUT_SECONDS = 5.0


def _is_grid_text(result) -> bool:
    return isinstance(result, list) and all(isinstance(row, str) for row in result)


def _parse_runner_output(completed) -> Optional[List[str]]:
    if completed.returncode != 0:
        return None
    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    result = output.get("result")
    return result if _is_grid_text(result) else None


def run_program(
    program_source: str,
    grid_input: List[str],
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Optional[List[str]]:
    """Returns the program's output grid (digit-string rows) on success, or
    None on any failure: timeout, non-zero exit, malformed output, wrong
    type, or an exception raised inside the candidate program itself. A
    candidate program is never trusted, only ever attempted.
    """
    payload = json.dumps({"program_source": program_source, "grid_input": grid_input})
    try:
        completed = subprocess.run(
            [sys.executable, "-I", str(_RUNNER_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return None
    return _parse_runner_output(completed)
