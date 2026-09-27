"""Per-task oracle verdict (diagnostic only, ADR 0111): does any composition
explain the train pairs, and does any also explain the gold test pair?"""
import time
from pathlib import Path
from typing import List, NamedTuple, Optional

from src.curriculum.discovery import session
from src.curriculum.discovery.antifraud import judge
from src.curriculum.library.derived.model import DerivedComposition
from src.curriculum.loader import Task, load_task
from src.curriculum.oracle.budget import widened_budgets
from src.curriculum.oracle.candidates import Candidate, all_candidates
from src.curriculum.oracle.gold import TRAINING_DIR, load_gold, oracle_task


class Verdict(NamedTuple):
    task_id: str
    seconds: float
    train_hits: int
    test_hits: int
    clean_train: bool
    clean_test: bool
    example: str
    error: Optional[str] = None

    @property
    def explains_train(self) -> bool:
        return self.train_hits > 0

    @property
    def explains_test(self) -> bool:
        return self.test_hits > 0


def _describe(composition) -> str:
    text = composition.describe() if hasattr(composition, "describe") else repr(composition)
    return text[:240]


def is_clean(task: Task, composition, effects: int) -> bool:
    """Non-derived families are hand-written, so only derived hits go through the antifraud judge."""
    return not isinstance(composition, DerivedComposition) or judge(task, composition, effects).accepted


def _any_clean(task: Task, candidates: List[Candidate], effects: int) -> bool:
    return any(is_clean(task, c.composition, effects) for c in candidates)


def _explaining_test(task: Task, gold, train_found: List[Candidate]) -> List[Candidate]:
    """Train-verified compositions whose prediction is the gold, plus any found by
    searching with the test pair as one more demonstration. Every composition that
    explains train+test also explains train, so the second search only runs when
    the first found something."""
    by_prediction = [c for c in train_found if c.predictions == gold]
    if not train_found:
        return by_prediction
    return by_prediction + all_candidates(oracle_task(task, gold))


def assess_task(task: Task, gold) -> Verdict:
    start = time.perf_counter()
    session.begin_trace()
    train_found = all_candidates(task)
    effects = session.effects_tested()
    test_found = _explaining_test(task, gold, train_found)
    best = (test_found or train_found or [None])[0]
    example = _describe(best.composition) if best else ""
    return Verdict(
        task.task_id, time.perf_counter() - start, len(train_found), len(test_found),
        _any_clean(task, train_found, effects), _any_clean(task, test_found, effects), example,
    )


def assess_id(task_id: str, directory: Path = TRAINING_DIR) -> Verdict:
    task = load_task(directory / f"{task_id}.json")
    try:
        with widened_budgets():
            return assess_task(task, load_gold(task_id, directory))
    except Exception as exc:  # a crash is a task result, never a batch abort
        return Verdict(task_id, 0.0, 0, 0, False, False, "", f"{type(exc).__name__}: {exc}")
