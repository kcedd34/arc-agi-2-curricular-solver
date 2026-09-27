"""Candidate record and step dispatch for a two-rule sequence (ADR 0097):
the output grid of `first` is the input grid of `second`."""
from typing import Any, List, NamedTuple, Optional, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.grid.overlay_composition import OverlayComposition
from src.curriculum.library.panels.panel_composition import PanelComposition
from src.curriculum.library.derived.model import DerivedComposition
from src.curriculum.library.objects.object_search import ObjectComposition, build_object_composition_steps
from src.curriculum.search.compose import build_composition_steps
from src.curriculum.spec import interpreter
from src.curriculum.spec import vocabulary as vocab


class SequenceComposition(NamedTuple):
    first: Any
    second: Any

    def describe(self) -> str:
        return f"sequence[ {self.first.describe()} ] then [ {self.second.describe()} ]"


def build_stage_steps(candidate: Any) -> List[vocab.Step]:
    if isinstance(candidate, (ObjectComposition, OverlayComposition, PanelComposition, DerivedComposition)):
        return build_object_composition_steps(candidate)
    return build_composition_steps(candidate)


def run_steps(steps: List[vocab.Step], grid: Grid) -> Optional[Grid]:
    """The rule's output for `grid`, or None when the rule yields no output
    (same failure modes the single-stage verification already rejects)."""
    try:
        return interpreter.run(steps, grid)[0]
    except (interpreter.InterpreterError, KeyError):
        return None


def sequence_steps(candidate: SequenceComposition) -> List[List[vocab.Step]]:
    return [build_stage_steps(candidate.first), build_stage_steps(candidate.second)]


def run_candidate(candidate: Any, grid: Grid) -> Tuple[Grid, List]:
    """Run any candidate type; a sequence runs its two stages in order and
    concatenates their traces. Raises like `interpreter.run`."""
    if not isinstance(candidate, SequenceComposition):
        return interpreter.run(build_stage_steps(candidate), grid)
    mid, trace_one = interpreter.run(build_stage_steps(candidate.first), grid)
    out, trace_two = interpreter.run(build_stage_steps(candidate.second), mid)
    return out, list(trace_one) + list(trace_two)
