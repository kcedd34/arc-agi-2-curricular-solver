from pathlib import Path

import pytest

from src.curriculum.discovery.equivariance import check_equivariance
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import load_task

DATA = Path("data/ARC-AGI-2/data")
HAND_WRITTEN = ["17b866bd", "342dd610", "ad38a9d0", "d6e50e54"]


def _task(task_id):
    matches = list(DATA.rglob(f"{task_id}.json"))
    if not matches:
        pytest.skip("ARC-AGI-2 data not available")
    return load_task(matches[0])


@pytest.mark.parametrize("task_id", HAND_WRITTEN)
def test_hand_written_hits_pass_the_corrected_filter(task_id):
    task = _task(task_id)
    hits = verified_derived_candidates_with_predictions(task)
    assert hits
    assert all(check_equivariance(task, composition).passed for composition, _ in hits)
