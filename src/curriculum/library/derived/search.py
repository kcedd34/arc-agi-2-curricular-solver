"""Verification of derived-family candidates against the train pairs
(ADR 0107), with the same contract as the other candidate packs."""
from typing import List, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.derived.enumerate import enumerate_derived_compositions
from src.curriculum.library.derived.lowering import build_derived_steps
from src.curriculum.library.derived.model import DerivedComposition
from src.curriculum.loader import Task


def verified_derived_candidates_with_predictions(task: Task) -> List[Tuple[DerivedComposition, List[Grid]]]:
    from src.curriculum.library.objects.object_search import _matches_all_train_pairs, _predict

    pairs: List[Tuple[DerivedComposition, List[Grid]]] = []
    for composition in enumerate_derived_compositions(task):
        steps = build_derived_steps(composition)
        if not _matches_all_train_pairs(steps, task):
            continue
        predictions = _predict(steps, task)
        if predictions is not None:
            pairs.append((composition, predictions))
    return pairs
