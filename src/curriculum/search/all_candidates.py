"""Every verified candidate for a task, in one place (ADR 0097): main
library, object pack, and, only when neither has any, two-rule sequences
(Occam: a sequence is never searched when a single rule already fits)."""
from typing import Any, List, NamedTuple, Tuple

from src.curriculum.grid import Grid
from src.curriculum.loader import Task

Pairs = List[Tuple[Any, List[Grid]]]


class AllPairs(NamedTuple):
    main: Pairs
    objects: Pairs
    sequences: Pairs
    sequence_units: int = 0
    budget_hit: bool = False
    deadline_hit: bool = False

    def combined(self) -> Pairs:
        return self.main + self.objects + self.sequences


def all_verified_pairs(task: Task) -> AllPairs:
    from src.curriculum.library.objects.object_search import verified_object_candidates_with_predictions
    from src.curriculum.search.rank import verified_main_candidates_with_predictions
    from src.curriculum.search.sequence.search import sequence_search

    main = verified_main_candidates_with_predictions(task)
    objects = verified_object_candidates_with_predictions(task)
    if main or objects:
        return AllPairs(main, objects, [])
    outcome = sequence_search(task)
    return AllPairs(main, objects, outcome.pairs, outcome.units_used, outcome.budget_hit, outcome.deadline_hit)
