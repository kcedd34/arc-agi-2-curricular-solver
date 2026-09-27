"""Verification of overlay candidates against the train pairs (ADR 0094),
with the same contract as the object pack's verified candidates."""
from typing import List, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.grid.overlay_composition import OverlayComposition, build_overlay_steps
from src.curriculum.library.grid.overlay_enumerate import enumerate_overlay_compositions
from src.curriculum.library.objects._task_cache import cached_for_task
from src.curriculum.loader import Task


def verified_overlay_candidates_with_predictions(task: Task) -> List[Tuple[OverlayComposition, List[Grid]]]:
    from src.curriculum.library.objects.object_search import _matches_all_train_pairs, _predict

    compositions = cached_for_task(task, "overlay_compositions", lambda: list(enumerate_overlay_compositions(task)))
    pairs: List[Tuple[OverlayComposition, List[Grid]]] = []
    for composition in compositions:
        steps = build_overlay_steps(composition)
        if not _matches_all_train_pairs(steps, task):
            continue
        predictions = _predict(steps, task)
        if predictions is not None:
            pairs.append((composition, predictions))
    return pairs
