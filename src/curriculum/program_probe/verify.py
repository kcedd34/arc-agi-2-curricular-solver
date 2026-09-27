"""Exact verification of a generated program: train pairs first, test gold only afterwards."""
import json
from pathlib import Path
from typing import List, NamedTuple, Optional

from src.curriculum.program_probe.antifraud import audit
from src.curriculum.program_probe.sandbox import CallResult, run_program

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


class Verdict(NamedTuple):
    executes: bool
    train_ok: bool
    test_ok: Optional[bool]
    error: str
    flags: Optional[dict]


def load_pairs(task_id: str, directory: Path = TRAINING_DIR) -> dict:
    """Train pairs and test inputs (the solver-facing view, no gold)."""
    raw = json.loads((directory / f"{task_id}.json").read_text(encoding="utf-8"))
    return {
        "train": [(p["input"], p["output"]) for p in raw["train"]],
        "test_inputs": [p["input"] for p in raw["test"]],
    }


def load_test_gold(task_id: str, directory: Path = TRAINING_DIR) -> List[list]:
    """Test outputs, read only after a program has reproduced every train pair."""
    raw = json.loads((directory / f"{task_id}.json").read_text(encoding="utf-8"))
    return [p["output"] for p in raw["test"]]


def _all_match(results: List[CallResult], expected: List[list]) -> bool:
    return len(results) == len(expected) and all(r.ok and r.grid == e for r, e in zip(results, expected))


def _first_error(results: List[CallResult]) -> str:
    return next((r.error for r in results if not r.ok), "")


def verify_program(code: str, task_id: str, directory: Path = TRAINING_DIR) -> Verdict:
    pairs = load_pairs(task_id, directory)
    train_in = [a for a, _ in pairs["train"]]
    results = run_program(code, train_in + pairs["test_inputs"])
    train_res, test_res = results[: len(train_in)], results[len(train_in):]
    executes = all(r.ok for r in train_res)
    train_ok = _all_match(train_res, [b for _, b in pairs["train"]])
    if not train_ok:
        return Verdict(executes, False, None, _first_error(train_res), None)
    flags = audit(code, [g for pair in pairs["train"] for g in pair])
    test_ok = _all_match(test_res, load_test_gold(task_id, directory))
    return Verdict(executes, True, test_ok, "", flags)
