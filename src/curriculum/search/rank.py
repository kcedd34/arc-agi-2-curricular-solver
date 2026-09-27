"""Verify enumerated candidates against train pairs, apply the ambiguity bar.

Same discipline the prior solver line already used repeatedly (ADR
0038/0043/0044): a candidate is only trusted once it reproduces every
train pair exactly, and if more than one verified candidate disagrees
on a test input, no answer is chosen arbitrarily - the task is reported
ambiguous instead. Verified candidates that happen to agree on every
test input are not ambiguous, they are redundant confirmations of the
same answer.

RN-CUR-33 step 2: the search unit is now a layout x selector x content
`Composition` (search/compose.py), not a named registry primitive.

RN-CUR-36 promotion (2026-09-22, object-pack.md Phase 7): `search_task`
below is the canonical entry point used by `probe.py`, `regression.py`,
`desk_check/run.py` and `cli.py`. It unions `search_main_only`'s
main-library candidates with the object pack's own candidates by
delegating to `library/objects/object_search.py::check_with_object_pack`,
which already implements that union and its shared ambiguity bar
(RN-CUR-31: reused, not duplicated here). `verified` can therefore hold
a mix of `Composition` and `ObjectComposition` instances; the one
consumer that inspects individual elements (`desk_check/run.py`)
dispatches on type.
"""
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from src.curriculum.grid import Grid, grids_equal
from src.curriculum.loader import Task
from src.curriculum.search.compose import Composition, build_composition_steps, enumerate_compositions
from src.curriculum.spec import interpreter


@dataclass
class SearchResult:
    status: str  # "solved" | "ambiguous" | "no_candidate"
    verified: List[Any]  # Composition and/or ObjectComposition
    predictions: Optional[List[Grid]]


def _matches_all_train_pairs(steps, task: Task) -> bool:
    for pair in task.train:
        try:
            output_grid, _trace = interpreter.run(steps, pair.input)
        except interpreter.InterpreterError:
            return False
        if not grids_equal(output_grid, pair.output):
            return False
    return True


def _predict(steps, task: Task) -> List[Grid]:
    return [interpreter.run(steps, grid)[0] for grid in task.test_inputs]


def verified_main_candidates_with_predictions(task: Task) -> List[Tuple[Composition, List[Grid]]]:
    """Every main-library composition that reproduces all train pairs,
    paired with its own test predictions (item 2/3 of the 2026-09-22
    follow-up: candidate-choice hit rate and the two-attempt policy both
    need per-candidate predictions, not just the aggregate status
    `search_main_only` below collapses them into)."""
    pairs: List[Tuple[Composition, List[Grid]]] = []
    for composition in enumerate_compositions(task):
        steps = build_composition_steps(composition)
        if not _matches_all_train_pairs(steps, task):
            continue
        pairs.append((composition, _predict(steps, task)))
    return pairs


def search_main_only(task: Task) -> SearchResult:
    """Main-library search only (pre-Phase-7 behaviour), kept as a
    standalone entry point so `object_search.py` can reuse it as its
    "main library" side without recursing into the combined
    `search_task` below (that would union the object pack with itself)."""
    pairs = verified_main_candidates_with_predictions(task)
    if not pairs:
        return SearchResult(status="no_candidate", verified=[], predictions=None)

    verified = [composition for composition, _predictions in pairs]
    first = pairs[0][1]
    if any(preds != first for _composition, preds in pairs[1:]):
        return SearchResult(status="ambiguous", verified=verified, predictions=None)

    return SearchResult(status="solved", verified=verified, predictions=first)


def search_task(task: Task) -> SearchResult:
    """Canonical search: main library unioned with the object pack.

    Deferred import breaks the module cycle: `object_search.py` imports
    `search_main_only` from this module at its own top level, so this
    module cannot import `object_search` at its own top level too.
    """
    from src.curriculum.library.objects.object_search import check_with_object_pack

    combined = check_with_object_pack(task)
    verified: List[Any] = [*combined.main_verified, *combined.object_verified]
    if combined.status == "no_candidate":
        return _sequence_result(task) or SearchResult("no_candidate", verified, None)
    return SearchResult(status=combined.status, verified=verified, predictions=combined.predictions)


def _sequence_result(task: Task) -> Optional[SearchResult]:
    """Two-rule fallback (ADR 0097), only when no single rule fits."""
    from src.curriculum.search.sequence.search import sequence_candidates_with_predictions

    pairs = sequence_candidates_with_predictions(task)
    if not pairs:
        return None
    first = pairs[0][1]
    verified = [candidate for candidate, _ in pairs]
    if any(preds != first for _c, preds in pairs[1:]):
        return SearchResult("ambiguous", verified, None)
    return SearchResult("solved", verified, first)
