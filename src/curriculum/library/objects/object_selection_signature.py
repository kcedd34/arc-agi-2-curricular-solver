"""Selection signature of an object selector on a task's train inputs
(ADR 0090, item 3a).

The role prefilter (ADR 0080) probes every content choice against every
selector. Content programs only see a selector through which objects it routes
to `selected_content` vs `not_selected_content`, in partition order. Two
selectors that route every object identically on every train input therefore
give identical prefilter outcomes for any content choice, so the outcome can be
computed once per signature. The signature is measured, not assumed: marker
Binds are placed in the two content slots and read back from the trace.
"""
from typing import Any, Dict, Optional, Tuple

from src.curriculum.library.objects import object_compose
from src.curriculum.loader import Task
from src.curriculum.spec import interpreter
from src.curriculum.spec import vocabulary as vocab

_MARKER = "__selection_marker"
_INPUT_REF = "g_in"

Signature = Tuple[Tuple[Any, ...], ...]


def _marker_steps(value: int) -> list:
    return [vocab.Bind(name=_MARKER, value=value)]


def _routing(trace: list) -> Tuple[Any, ...]:
    return tuple(
        entry["value"]
        for entry in trace
        if entry["op"] == "for_each" or (entry["op"] == "bind" and entry["result"] == _MARKER)
    )


def selection_signature(
    task: Task,
    connectivity: int,
    single_color: bool,
    background: int,
    selector_name: str,
    selector_params: Dict[str, Any],
) -> Optional[Signature]:
    """Per train pair, the object count and the selected/not-selected
    routing sequence; `None` when the probe fails (no sharing then)."""
    steps = object_compose.build_identity_canvas_composition(
        input_ref=_INPUT_REF,
        connectivity=connectivity,
        background=background,
        selector_name=selector_name,
        selected_content=_marker_steps(1),
        not_selected_content=_marker_steps(0),
        selector_params=selector_params or None,
        single_color=single_color,
        element_name="obj",
    )
    try:
        return tuple(_routing(interpreter.run(steps, pair.input)[1]) for pair in task.train)
    except (interpreter.InterpreterError, KeyError):
        return None
