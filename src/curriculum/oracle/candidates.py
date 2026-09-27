"""Every verified composition of a task across all families, with no Occam cut
(diagnostic only, ADR 0111): main, object pack (which carries derived, overlay
and panel) and two-rule sequences are all searched, whether or not a single
rule already fits."""
from typing import Any, List, NamedTuple

from src.curriculum.grid import Grid
from src.curriculum.loader import Task
from src.curriculum.oracle.budget import FIRST_STAGE_LIMIT


class Candidate(NamedTuple):
    composition: Any
    predictions: List[Grid]


def all_candidates(task: Task) -> List[Candidate]:
    from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
    from src.curriculum.search.rank import verified_main_candidates_with_predictions
    from src.curriculum.search.sequence.search import sequence_search

    found = verified_main_candidates_with_predictions(task) + verified_object_candidates_with_predictions(task)
    found += sequence_search(task, FIRST_STAGE_LIMIT).pairs
    return [Candidate(composition, predictions) for composition, predictions in found]
