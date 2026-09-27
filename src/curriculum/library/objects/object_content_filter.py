"""Role-wise content prefilter for the object pack (Round 5, ADR 0080).

Seed copies the input and each object's content only writes its own
cells, so a content piece run against one role (the other role set to
`keep`) must already match the expected output on every cell it changes.

Round 6 (ADR 0081): a content that changes no cell in any train pair is
train-equivalent to `keep` (which is always enumerated), so it is dropped
as a duplicate instead of surviving vacuously.
"""
from typing import Any, Dict, List, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.objects import object_compose
from src.curriculum.library.objects.object_content_registry import ALL_CONTENT_PIECES
from src.curriculum.loader import Task, TrainPair
from src.curriculum.spec import interpreter
from src.curriculum.spec import vocabulary as vocab

ContentChoice = Tuple[str, Dict[str, Any]]

_INPUT_REF = "g_in"
_ELEMENT = "obj"


def _probe_steps(
    role: str,
    choice: ContentChoice,
    connectivity: int,
    single_color: bool,
    background: int,
    selector_name: str,
    selector_params: Dict[str, Any],
) -> List[vocab.Step]:
    name, params = choice
    content = ALL_CONTENT_PIECES[name].builder(_ELEMENT, _INPUT_REF, **params)
    selected, not_selected = (content, []) if role == "selected" else ([], content)
    return object_compose.build_identity_canvas_composition(
        input_ref=_INPUT_REF,
        connectivity=connectivity,
        background=background,
        selector_name=selector_name,
        selected_content=selected,
        not_selected_content=not_selected,
        selector_params=selector_params or None,
        single_color=single_color,
        element_name=_ELEMENT,
    )


def _changed_cells_match(predicted: Grid, source: Grid, expected: Grid) -> bool:
    if len(source) != len(expected) or len(source[0]) != len(expected[0]):
        return False
    for p_row, s_row, e_row in zip(predicted, source, expected):
        for p, s, e in zip(p_row, s_row, e_row):
            if p != s and p != e:
                return False
    return True


_INVALID = "invalid"
_NOOP = "noop"
_WRITES = "writes"


def _probe_outcome(steps: List[vocab.Step], pairs: List[TrainPair]) -> str:
    """`invalid` if the content contradicts a train output, `noop` if it
    changes no cell in any train pair, `writes` otherwise. The verdict does
    not depend on pair order, so a pair that rejected a content is moved to
    the front (ADR 0090): the next content is likely rejected by it too."""
    wrote = False
    for index, pair in enumerate(pairs):
        try:
            predicted, _trace = interpreter.run(steps, pair.input)
            consistent = _changed_cells_match(predicted, pair.input, pair.output)
        except (interpreter.InterpreterError, KeyError):
            consistent = False
        if not consistent:
            pairs.insert(0, pairs.pop(index))
            return _INVALID
        wrote = wrote or predicted != pair.input
    return _WRITES if wrote else _NOOP


def filter_content_for_role(
    role: str,
    choices: List[ContentChoice],
    task: Task,
    connectivity: int,
    single_color: bool,
    background: int,
    selector_name: str,
    selector_params: Dict[str, Any],
) -> List[ContentChoice]:
    survivors: List[ContentChoice] = []
    pairs = list(task.train)
    for choice in choices:
        steps = _probe_steps(
            role, choice, connectivity, single_color, background, selector_name, selector_params
        )
        outcome = _probe_outcome(steps, pairs)
        if outcome == _WRITES or (outcome == _NOOP and choice[0] == "keep"):
            survivors.append(choice)
    return survivors
