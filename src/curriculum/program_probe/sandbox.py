"""Parent side of the sandbox: static screen, subprocess launch, and failure containment."""
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence

CHILD = Path(__file__).with_name("sandbox_child.py")
PER_CALL_SECONDS = 5.0
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "globals", "locals", "getattr", "setattr", "input", "vars"}


class CallResult(NamedTuple):
    ok: bool
    grid: Optional[list]
    error: str


def static_problem(code: str) -> Optional[str]:
    """A reason to refuse the program before running it, or None."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError) as exc:
        return f"syntax error: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            return f"banned name {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return f"banned attribute {node.attr}"
    return None


def _failures(count: int, reason: str) -> List[CallResult]:
    return [CallResult(False, None, reason) for _ in range(count)]


def _decode(stdout: str, count: int) -> List[CallResult]:
    try:
        raw = json.loads(stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return _failures(count, "no result from subprocess")
    return [CallResult(r["ok"], r.get("grid"), r.get("error", "")) for r in raw]


def run_program(code: str, grids: Sequence[list], seconds: float = PER_CALL_SECONDS) -> List[CallResult]:
    """Run `solve` on each grid in an isolated process; never raises."""
    problem = static_problem(code)
    if problem:
        return _failures(len(grids), problem)
    request = json.dumps({"code": code, "grids": list(grids), "seconds": seconds})
    try:
        done = subprocess.run(
            [sys.executable, "-I", str(CHILD)], input=request, capture_output=True, text=True,
            timeout=seconds * len(grids) + 5, env={},
        )
    except subprocess.TimeoutExpired:
        return _failures(len(grids), "timeout")
    if done.returncode != 0:
        return _failures(len(grids), f"subprocess exit {done.returncode}")
    return _decode(done.stdout, len(grids))
