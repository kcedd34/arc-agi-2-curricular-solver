"""Candidate enumeration for the panel pack (ADR 0106). Train inputs only:
every train input must be cut into panels by separator lines (inventory
pruning); the verifier then decides which operation reproduces the outputs."""
from typing import Iterator

from src.curriculum.library.objects.object_params import background_candidates
from src.curriculum.library.panels.panel_composition import SUMMARY, SWAP, PanelComposition
from src.curriculum.loader import Task
from src.curriculum.spec._panels import find_panels

AXES = ("row", "col")


def every_train_input_has_panels(task: Task) -> bool:
    return all(find_panels(pair.input) is not None for pair in task.train)


def _same_shape(task: Task) -> bool:
    return all(
        len(p.input) == len(p.output) and len(p.input[0]) == len(p.output[0]) for p in task.train
    )


def enumerate_panel_compositions(task: Task) -> Iterator[PanelComposition]:
    if not every_train_input_has_panels(task):
        return
    if _same_shape(task):
        for axis in AXES:
            yield PanelComposition(SWAP, axis, 0)
        return
    for fill in background_candidates(task):
        yield PanelComposition(SUMMARY, "none", fill)
