"""Unit tests for the simplicity ranking used by the hit-rate analysis
and the two-attempt policy (BOOTSTRAP.md RF05, item 2/3 of the
2026-09-22 follow-up)."""
from pathlib import Path

from src.curriculum.loader import load_task
from src.curriculum.search.candidate_rank import (
    candidate_complexity,
    verified_candidates_ranked_by_simplicity,
)

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_ranked_candidates_are_sorted_by_step_count_ascending():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    ranked = verified_candidates_ranked_by_simplicity(task)

    assert ranked, "007bbfb7 is expected to have at least one verified candidate"
    complexities = [candidate_complexity(composition) for composition, _predictions in ranked]
    assert complexities == sorted(complexities)


def test_ranked_candidates_cover_both_main_and_object_pack_pools():
    task = load_task(TRAINING_DIR / "00d62c1b.json")
    ranked = verified_candidates_ranked_by_simplicity(task)

    from src.curriculum.search.rank import search_task

    combined = search_task(task)
    assert len(ranked) == len(combined.verified)


def test_candidate_complexity_is_deterministic_across_repeated_calls():
    task = load_task(TRAINING_DIR / "009d5c81.json")
    first = [candidate_complexity(c) for c, _ in verified_candidates_ranked_by_simplicity(task)]
    second = [candidate_complexity(c) for c, _ in verified_candidates_ranked_by_simplicity(task)]
    assert first == second
