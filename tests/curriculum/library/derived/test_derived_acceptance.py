"""ADR 0107 refactor test: the acceptance tasks of the dedicated families
are solved by combinations of the generic layer, checked against the public
solutions (training split only)."""
import json
from pathlib import Path

import pytest

from src.curriculum.desk_check.persist import hypothesis_id
from src.curriculum.library.derived.enumerate import derived_hypothesis_counts
from src.curriculum.library.derived.lowering import build_derived_steps
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import load_task
from src.curriculum.search.candidate_rank import candidate_complexity

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")
ACCEPTANCE = ("5ad8a7c0", "d6e50e54", "ad38a9d0", "342dd610", "1b59e163", "e734a0e8")


def _gold(task_id):
    return [t["output"] for t in json.loads((TRAINING_DIR / f"{task_id}.json").read_text())["test"]]


@pytest.mark.parametrize("task_id", ACCEPTANCE)
def test_acceptance_task_is_solved_by_a_generic_combination(task_id):
    task = load_task(TRAINING_DIR / f"{task_id}.json")
    found = verified_derived_candidates_with_predictions(task)
    assert any(preds == _gold(task_id) for _comp, preds in found)


@pytest.mark.parametrize("task_id", ACCEPTANCE)
def test_prune_reduces_hypotheses(task_id):
    counts = derived_hypothesis_counts(load_task(TRAINING_DIR / f"{task_id}.json"))
    assert 0 < counts.after < counts.before


def test_ids_are_unique_and_ranking_counts_steps():
    task = load_task(TRAINING_DIR / "5ad8a7c0.json")
    comps = [c for c, _ in verified_derived_candidates_with_predictions(task)]
    assert len({hypothesis_id(c) for c in comps}) == len(comps)
    assert candidate_complexity(comps[0])[0] == len(build_derived_steps(comps[0]))
