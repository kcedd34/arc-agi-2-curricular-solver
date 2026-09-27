"""Scores accepted hits against the gabarito (evaluator side, RN-CUR-03): the
official two-attempt rule, one attempt per distinct accepted hypothesis in
enumeration order."""
from pathlib import Path
from typing import List, NamedTuple, Optional

from src.curriculum.discovery.loop_tasks import TRAINING_DIR
from src.curriculum.discovery.run_task import Hit, TaskRun
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.grid import Grid

ATTEMPTS = 2


class Score(NamedTuple):
    solved: bool
    attempt: int  # 1 or 2 when solved, 0 otherwise
    winner: Optional[Hit]


def _distinct_attempts(hits: List[Hit]) -> List[Hit]:
    seen, attempts = [], []
    for hit in hits:
        if hit.accepted and hit.predictions not in seen:
            seen.append(hit.predictions)
            attempts.append(hit)
    return attempts[:ATTEMPTS]


def score_run(run: TaskRun, training_dir: Path = TRAINING_DIR) -> Score:
    gabarito: List[Grid] = load_task_solutions(training_dir / f"{run.task_id}.json")
    for number, hit in enumerate(_distinct_attempts(run.hits), start=1):
        if hit.predictions == gabarito:
            return Score(True, number, hit)
    return Score(False, 0, None)
