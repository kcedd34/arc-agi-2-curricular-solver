"""Simplicity ranking for verified candidates, main library and object
pack combined (BOOTSTRAP.md RF05 / RN-CUR-10-12; item 2/3 of the
2026-09-22 follow-up request).

No "order survivors by simplicity" ranking existed yet in the search
pipeline. Complexity here is the number of vocabulary Steps in the
candidate's own lowered program: fewer steps is a simpler program, and
step count is already produced identically by each side's own existing
builder (RN-CUR-31: reuses `build_composition_steps` and
`build_object_composition_steps`, no new lowering path). Ties break on
the candidate's own `describe()` string, so the ranking is a
deterministic total order that never depends on enumeration order or on
which process a parallel batch run computed it in.
"""
from typing import Any, List, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.grid.overlay_composition import OverlayComposition
from src.curriculum.library.panels.panel_composition import PanelComposition
from src.curriculum.library.derived.model import DerivedComposition
from src.curriculum.library.objects.object_search import ObjectComposition, build_object_composition_steps
from src.curriculum.loader import Task
from src.curriculum.search.all_candidates import all_verified_pairs
from src.curriculum.search.compose import build_composition_steps
from src.curriculum.search.sequence.composition import SequenceComposition, sequence_steps

CandidatePrediction = Tuple[Any, List[Grid]]


def candidate_complexity(composition: Any) -> Tuple[int, str]:
    """Lower is simpler. A `(step_count, describe())` pair, so equal step
    counts still resolve to one deterministic order instead of a tie."""
    if isinstance(composition, SequenceComposition):
        count = sum(len(steps) for steps in sequence_steps(composition))
        return (count, composition.describe())
    if isinstance(composition, (ObjectComposition, OverlayComposition, PanelComposition, DerivedComposition)):
        steps = build_object_composition_steps(composition)
    else:
        steps = build_composition_steps(composition)
    return (len(steps), composition.describe())


def rank_by_simplicity(pairs: List[CandidatePrediction]) -> List[CandidatePrediction]:
    """Simplest first; lets callers that already hold the verified pairs
    rank them without re-running the searches (ADR 0090)."""
    return sorted(pairs, key=lambda pair: candidate_complexity(pair[0]))


def verified_candidates_ranked_by_simplicity(task: Task) -> List[CandidatePrediction]:
    """Every verified candidate for `task` (main library and object pack
    combined), paired with its own test predictions, simplest first."""
    return rank_by_simplicity(all_verified_pairs(task).combined())
