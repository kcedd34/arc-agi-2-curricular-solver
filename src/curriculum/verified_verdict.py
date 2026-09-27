"""Single source of truth for the `solved` verdict, correcting the
2026-09-22 bug where gate/probe/scale_test/desk_check all treated
unanimous agreement among verified candidates as if it were a real
gabarito match (see ADR for the correction and the 3 wrongly-accepted
tasks it reverted: 73ccf9c2, b230c067, f5aa3634).

Two concepts, kept apart everywhere downstream of this module:
- `unanimous`: every verified candidate predicts the same test output.
  A property of the candidate pool alone; never an acceptance criterion.
- `solved`: at least one of up to two distinct attempts (RN-CUR-04's
  two-attempt policy) matches the real gabarito, verified by
  `evaluator/exact_match.py`. The only acceptance criterion.

RN-CUR-03: candidate enumeration and ranking
(`search/candidate_rank.py::verified_candidates_ranked_by_simplicity`)
never touches a gabarito; only `compute_verified_verdict` does, and
only post-hoc, via `evaluator/solutions.py`, exactly like `probe.py`
and `two_attempt.py` already did before this module existed.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.curriculum.evaluator.exact_match import score_task
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.loader import load_task

DEFAULT_TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


@dataclass
class VerifiedVerdict:
    task_id: str
    num_verified_candidates: int
    main_verified_count: int
    object_verified_count: int
    unanimous: bool
    solved: bool
    attempt_1_match: Optional[bool]
    attempt_2_match: Optional[bool]
    error: Optional[str] = None
    sequence_verified_count: int = 0
    sequence_units: int = 0
    budget_hit: bool = False
    deadline_hit: bool = False

    @property
    def solved_at_1(self) -> bool:
        return bool(self.attempt_1_match)

    @property
    def solved_at_2(self) -> bool:
        return self.solved and not self.solved_at_1


def distinct_attempts(ranked) -> List[List]:
    """Up to two attempts from a simplicity-ranked candidate list,
    skipping any later candidate whose prediction is identical to
    attempt_1's (a redundant confirmation, not a second real guess)."""
    if not ranked:
        return []
    attempts = [ranked[0][1]]
    for _composition, predictions in ranked[1:]:
        if predictions != attempts[0]:
            attempts.append(predictions)
            break
    return attempts


def compute_verified_verdict(task_id: str, training_dir: Path = DEFAULT_TRAINING_DIR) -> VerifiedVerdict:
    """The one place that decides `solved`. Reuses the same candidate
    pool as `check_with_object_pack` (proven equivalent by construction:
    both union `verified_main_candidates_with_predictions` and
    `verified_object_candidates_with_predictions`), so this never
    diverges from what the gate itself enumerates."""
    from src.curriculum.search.all_candidates import all_verified_pairs
    from src.curriculum.search.candidate_rank import rank_by_simplicity

    try:
        task_path = training_dir / f"{task_id}.json"
        task = load_task(task_path)
        pools = all_verified_pairs(task)
        main_count, object_count = len(pools.main), len(pools.objects)
        ranked = rank_by_simplicity(pools.combined())
        budget_flags = dict(sequence_units=pools.sequence_units, budget_hit=pools.budget_hit,
                            deadline_hit=pools.deadline_hit)

        if not ranked:
            return VerifiedVerdict(task_id, 0, main_count, object_count, unanimous=False, solved=False,
                                    attempt_1_match=None, attempt_2_match=None, **budget_flags)

        attempts = distinct_attempts(ranked)
        unanimous = len(attempts) == 1
        solutions = load_task_solutions(task_path)

        def _matches(predictions) -> bool:
            return bool(score_task(predictions, solutions)["all_exact_match"])

        attempt_1_match = _matches(attempts[0])
        attempt_2_match = _matches(attempts[1]) if len(attempts) > 1 else None
        solved = attempt_1_match or bool(attempt_2_match)
        return VerifiedVerdict(task_id, len(ranked), main_count, object_count, unanimous, solved,
                                attempt_1_match, attempt_2_match, sequence_verified_count=len(pools.sequences),
                                **budget_flags)
    except Exception as exc:  # isolated per-task failure, RN-CUR-32 batch discipline
        return VerifiedVerdict(task_id, 0, 0, 0, unanimous=False, solved=False,
                                attempt_1_match=None, attempt_2_match=None, error=repr(exc))
