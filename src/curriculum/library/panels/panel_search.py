"""Verification of panel candidates against the train pairs (ADR 0106),
with the same contract as the overlay and object-pack candidates. Candidates
that differ only in `fill` and predict the same grids are kept once (a fill that
no cell uses is a decorative parameter)."""
from typing import List, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.objects._task_cache import cached_for_task
from src.curriculum.library.panels.panel_composition import PanelComposition, build_panel_steps
from src.curriculum.library.panels.panel_enumerate import enumerate_panel_compositions
from src.curriculum.loader import Task


def verified_panel_candidates_with_predictions(task: Task) -> List[Tuple[PanelComposition, List[Grid]]]:
    from src.curriculum.library.objects.object_search import _matches_all_train_pairs, _predict

    compositions = cached_for_task(task, "panel_compositions", lambda: list(enumerate_panel_compositions(task)))
    pairs: List[Tuple[PanelComposition, List[Grid]]] = []
    seen = set()
    for composition in compositions:
        steps = build_panel_steps(composition)
        if not _matches_all_train_pairs(steps, task):
            continue
        predictions = _predict(steps, task)
        key = (composition.mode, composition.axis, repr(predictions))
        if predictions is not None and key not in seen:
            seen.add(key)
            pairs.append((composition, predictions))
    return pairs
