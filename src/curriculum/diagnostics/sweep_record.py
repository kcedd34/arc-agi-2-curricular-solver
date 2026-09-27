"""Per-task record of the scale sweep (ADR 0093): the standard verdict
plus what is needed to explain a miss (rank of the first correct
candidate, wrong-cell count of the best attempt)."""
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from src.curriculum.diagnostics.sweep_metrics import best_attempt_wrong_cells, first_matching_rank
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.loader import load_task
from src.curriculum.verified_verdict import distinct_attempts

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


@dataclass
class SweepRecord:
    task_id: str
    num_candidates: int = 0
    num_distinct_predictions: int = 0
    solved: bool = False
    solved_at_1: bool = False
    unanimous: bool = False
    gabarito_rank: Optional[int] = None
    best_wrong_cells: Optional[int] = None
    top_description: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _distinct_count(ranked) -> int:
    seen = []
    for _composition, predictions in ranked:
        if predictions not in seen:
            seen.append(predictions)
    return len(seen)


def _ranked_candidates(task):
    from src.curriculum.search.all_candidates import all_verified_pairs
    from src.curriculum.search.candidate_rank import rank_by_simplicity

    return rank_by_simplicity(all_verified_pairs(task).combined())


def _record_from_ranked(task_id: str, ranked, solutions) -> SweepRecord:
    attempts = distinct_attempts(ranked)
    rank = first_matching_rank(ranked, solutions)
    solved = rank is not None and any(a == ranked[rank - 1][1] for a in attempts)
    return SweepRecord(
        task_id=task_id,
        num_candidates=len(ranked),
        num_distinct_predictions=_distinct_count(ranked),
        solved=solved,
        solved_at_1=solved and attempts[0] == ranked[rank - 1][1],
        unanimous=len(attempts) == 1,
        gabarito_rank=rank,
        best_wrong_cells=best_attempt_wrong_cells(attempts, solutions),
        top_description=ranked[0][0].describe()[:200],
    )


def build_sweep_record(task_id: str, training_dir: Path = DEFAULT_TRAINING_DIR) -> SweepRecord:
    try:
        path = training_dir / f"{task_id}.json"
        ranked = _ranked_candidates(load_task(path))
        if not ranked:
            return SweepRecord(task_id=task_id)
        return _record_from_ranked(task_id, ranked, load_task_solutions(path))
    except Exception as exc:  # isolated per-task failure (RN-CUR-32)
        return SweepRecord(task_id=task_id, error=repr(exc))
