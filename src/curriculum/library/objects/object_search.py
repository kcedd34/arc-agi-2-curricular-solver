"""Object-pack search (RN-CUR-36, object-pack.md Section 5.5): enumerates
the object pack's own layout x selector x content x
connectivity/single_color combinations for a task, verifies each
against every train pair exactly like `search/rank.py` does for the
main library, and exposes a "check with the package" entry point that
unions the object pack's verified candidates with the main library's
own `search_main_only` result under one shared ambiguity bar.

RN-CUR-31: reuses `object_params.py`'s pruning functions and
`object_compose.py`'s two composition builders rather than duplicating
inference or assembly logic; reuses `search/rank.py`'s train-pair
verification helpers (`_matches_all_train_pairs`, `_predict`), which are
generic over any step sequence, not specific to the main library's own
`Composition` type.

Promoted out of staging (ADR 0069 amendment; RN-CUR-36 condition 2 met
on 2026-09-22, see docs/curriculum/tasks/object-pack.md Phase 7):
`search/rank.py::search_task` now calls `check_with_object_pack` below,
so this module is on the canonical search path used by `probe.py`,
`regression.py`, `desk_check/run.py` and `cli.py`, not staging-only
anymore. `search/compose.py` still does not enumerate object
compositions directly (the two composition systems stay distinct); the
union happens one layer up, in `search/rank.py`.
"""
import itertools
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Tuple

from src.curriculum.grid import Grid
from src.curriculum.library.objects import object_compose
from src.curriculum.library.objects.object_content_registry import ALL_CONTENT_PIECES as OBJECT_CONTENT_PIECES
from src.curriculum.library.objects.object_content_filter import filter_content_for_role
from src.curriculum.library.objects.object_params import (
    background_candidates,
    connectivity_single_color_candidates,
    objects_of_color_candidates,
    recolor_target_color_candidates,
    should_include_crop_layout,
    should_include_identity_canvas,
    slide_direction_candidates,
)
from src.curriculum.library.objects._task_cache import cached_for_task
from src.curriculum.library.objects.object_selection_signature import selection_signature
from src.curriculum.library.objects.object_selector import SELECTOR_PIECES as OBJECT_SELECTOR_PIECES
from src.curriculum.loader import Task
from src.curriculum.grid import grids_equal
from src.curriculum.search.rank import search_main_only as search_main_library
from src.curriculum.spec import interpreter
from src.curriculum.spec import vocabulary as vocab

MAX_OBJECT_COMPOSITIONS_PER_TASK = 5000
SECOND_STAGE_OBJECT_CAP = 500
_INPUT_REF = "g_in"
_SLIDE_STOPS = ("border", "contact", "settle")
_IDENTITY_CANVAS_CONTENT_NAMES = tuple(
    name for name in OBJECT_CONTENT_PIECES if name != "crop_content"
)


class ObjectComposition(NamedTuple):
    layout_name: str
    connectivity: int
    single_color: bool
    background: int
    selector_name: str
    selector_params: Dict[str, Any]
    selected_content_name: str
    selected_content_params: Dict[str, Any]
    not_selected_content_name: str
    not_selected_content_params: Dict[str, Any]

    def describe(self) -> str:
        def _fmt(name: str, params: Dict[str, Any]) -> str:
            return f"{name}({params})" if params else name

        layout = (
            f"{self.layout_name}(connectivity={self.connectivity},"
            f"single_color={self.single_color},background={self.background})"
        )
        selector = _fmt(self.selector_name, self.selector_params)
        if self.layout_name == "crop_to_selected_object":
            return f"layout={layout} selector={selector}"
        selected = _fmt(self.selected_content_name, self.selected_content_params)
        not_selected = _fmt(self.not_selected_content_name, self.not_selected_content_params)
        return f"layout={layout} selector={selector} selected={selected} not_selected={not_selected}"


@dataclass
class ObjectSearchResult:
    status: str  # "solved" | "ambiguous" | "no_candidate"
    verified: List[ObjectComposition]
    predictions: Optional[List[Grid]]


@dataclass
class CombinedSearchResult:
    status: str  # "solved" | "ambiguous" | "no_candidate"
    main_verified: List[Any]
    object_verified: List[ObjectComposition]
    predictions: Optional[List[Grid]]


def _content_param_candidates(
    param_name: str, task: Task, connectivity: int, single_color: bool, background: int
) -> List[Any]:
    """Rodada 4 (ataque ao loop externo, multiplos fatores): `background`
    aqui e o mesmo papel semantico ja unificado pela ADR 0078
    (`erase_selected`/`slide_selected` repintam uma celula vazia com "a
    cor de fundo real da tarefa", a mesma pergunta que o layout ja
    respondeu). Reenumerar `background_candidates(task)` de novo aqui,
    independente do `background` ja escolhido pelo loop externo
    (`enumerate_object_compositions`), multiplicava o fanout dessas duas
    pecas de conteudo por esse mesmo fator uma segunda vez sem nenhuma
    justificativa semantica - nao ha caso em que "apagar" deveria revelar
    uma cor diferente da que o proprio layout ja identificou como fundo
    (uma cor de preenchimento distinta e exatamente o papel de
    `fill_bbox_selected`/`recolor_selected`, que usam `color`, nao
    `background`). Vinculado ao valor ja fixado, elimina o fator inteiro
    em vez de podar uma fracao dele."""
    if param_name == "background":
        return [background]
    if param_name in ("color", "halo_color"):
        return recolor_target_color_candidates(task)
    if param_name == "direction":
        return slide_direction_candidates(task, connectivity, single_color)
    if param_name == "stop":
        return list(_SLIDE_STOPS)
    raise ValueError(f"object pack: no candidate rule for content param {param_name!r}")


def _selector_param_candidates(param_name: str, task: Task) -> List[Any]:
    if param_name == "color":
        return objects_of_color_candidates(task)
    raise ValueError(f"object pack: no candidate rule for selector param {param_name!r}")


def _expand_content_pieces(
    names: Tuple[str, ...], task: Task, connectivity: int, single_color: bool, background: int
) -> List[Tuple[str, Dict[str, Any]]]:
    expanded: List[Tuple[str, Dict[str, Any]]] = []
    for name in names:
        piece = OBJECT_CONTENT_PIECES[name]
        if not piece.params:
            expanded.append((name, {}))
            continue
        candidate_lists = [
            _content_param_candidates(p, task, connectivity, single_color, background)
            for p in piece.params
        ]
        for combo in itertools.product(*candidate_lists):
            expanded.append((name, dict(zip(piece.params, combo))))
    return expanded


def _expand_selector_pieces(task: Task) -> List[Tuple[str, Dict[str, Any]]]:
    expanded: List[Tuple[str, Dict[str, Any]]] = []
    for name, piece in OBJECT_SELECTOR_PIECES.items():
        if not piece.params:
            expanded.append((name, {}))
            continue
        candidate_lists = [_selector_param_candidates(p, task) for p in piece.params]
        for combo in itertools.product(*candidate_lists):
            expanded.append((name, dict(zip(piece.params, combo))))
    return expanded


def _content_pair_eligible(
    selected: Tuple[str, Dict[str, Any]], not_selected: Tuple[str, Dict[str, Any]]
) -> bool:
    """Content x content compatibility (Rodada 2), the object pack's
    analog of `search/compose.py::_content_pair_eligible`.

    - Identical pair (same name and params): the selector's split has no
      behavioral effect, both branches emit the same steps regardless of
      which objects it routed where (decorative selection, domain
      knowledge item 7). Fase D's antifraud check already rejects this
      pattern, so excluding it here loses no candidate that could count
      as `solved`.
    - `slide_selected` on both branches: by far the largest content
      piece (3 free params: direction/stop/background), so pairing it
      with itself squares that fanout and dominates this term's size
      (Rodada 2 Fase A/B measurement: 50-75% of the content list, over
      half of content^2 in the measured cap-hit tasks). Kept as a
      pruning call, not a correctness claim: two independently sliding
      groups is not structurally impossible the way `draw_lines` on both
      branches is in the main library, so this exclusion is the round's
      main risk to watch (register in round-2.md, revisit if stagnation
      points here)."""
    if selected == not_selected:
        return False
    if selected[0] == "slide_selected" and not_selected[0] == "slide_selected":
        return False
    return True


def _role_filtered_contents(
    contents: List[Tuple[str, Dict[str, Any]]],
    task: Task,
    connectivity: int,
    single_color: bool,
    background: int,
    selector_name: str,
    selector_params: Dict[str, Any],
) -> Tuple[List[Tuple[str, Dict[str, Any]]], List[Tuple[str, Dict[str, Any]]]]:
    """Defers the content x content expansion until each content has passed
    a per-role local check against the train pairs (ADR 0080)."""
    args = (task, connectivity, single_color, background, selector_name, selector_params)
    selected = filter_content_for_role("selected", contents, *args)
    not_selected = filter_content_for_role("not_selected", contents, *args)
    return selected, not_selected


def _role_options_shared(
    by_signature: Dict[Any, Tuple[List, List]],
    contents: List[Tuple[str, Dict[str, Any]]],
    task: Task,
    connectivity: int,
    single_color: bool,
    background: int,
    selector_name: str,
    selector_params: Dict[str, Any],
) -> Tuple[List, List]:
    """Selectors that route every train object identically share one
    prefilter result (ADR 0090); a failed signature probe never shares."""
    signature = selection_signature(
        task, connectivity, single_color, background, selector_name, selector_params
    )
    if signature is not None and signature in by_signature:
        return by_signature[signature]
    options = _role_filtered_contents(
        contents, task, connectivity, single_color, background, selector_name, selector_params
    )
    if signature is not None:
        by_signature[signature] = options
    return options


def _identity_canvas_compositions(
    task: Task,
    connectivity: int,
    single_color: bool,
    background: int,
    selectors: List[Tuple[str, Dict[str, Any]]],
) -> Iterator[ObjectComposition]:
    contents = _expand_content_pieces(
        _IDENTITY_CANVAS_CONTENT_NAMES, task, connectivity, single_color, background
    )
    role_options_by_signature: Dict[Any, Tuple[List, List]] = {}
    for selector_name, selector_params in selectors:
        selected_options, not_selected_options = _role_options_shared(
            role_options_by_signature, contents, task, connectivity, single_color, background,
            selector_name, selector_params,
        )
        for selected_name, selected_params in selected_options:
            for not_selected_name, not_selected_params in not_selected_options:
                if not _content_pair_eligible(
                    (selected_name, selected_params), (not_selected_name, not_selected_params)
                ):
                    continue
                yield ObjectComposition(
                    layout_name="identity_canvas",
                    connectivity=connectivity,
                    single_color=single_color,
                    background=background,
                    selector_name=selector_name,
                    selector_params=selector_params,
                    selected_content_name=selected_name,
                    selected_content_params=selected_params,
                    not_selected_content_name=not_selected_name,
                    not_selected_content_params=not_selected_params,
                )


def _crop_compositions(
    connectivity: int,
    single_color: bool,
    background: int,
    selectors: List[Tuple[str, Dict[str, Any]]],
) -> Iterator[ObjectComposition]:
    for selector_name, selector_params in selectors:
        yield ObjectComposition(
            layout_name="crop_to_selected_object",
            connectivity=connectivity,
            single_color=single_color,
            background=background,
            selector_name=selector_name,
            selector_params=selector_params,
            selected_content_name="crop_content",
            selected_content_params={},
            not_selected_content_name="",
            not_selected_content_params={},
        )


def _enumerate_object_compositions(task: Task, cap: int) -> Iterator[ObjectComposition]:
    include_identity = should_include_identity_canvas(task)
    include_crop = should_include_crop_layout(task)

    def _generate() -> Iterator[ObjectComposition]:
        if not include_identity and not include_crop:
            return
        selectors = _expand_selector_pieces(task)
        for connectivity, single_color in connectivity_single_color_candidates(task):
            for background in background_candidates(task):
                if include_identity:
                    yield from _identity_canvas_compositions(
                        task, connectivity, single_color, background, selectors
                    )
                if include_crop:
                    yield from _crop_compositions(connectivity, single_color, background, selectors)

    yield from itertools.islice(_generate(), cap)


def enumerate_object_compositions(task: Task, cap: Optional[int] = None) -> Iterator[ObjectComposition]:
    """Enumerated once per task (ADR 0090): verdict, probe and scale test
    all walk the same list instead of re-running the role prefilter."""
    cap = MAX_OBJECT_COMPOSITIONS_PER_TASK if cap is None else cap
    compositions = cached_for_task(
        task, f"object_compositions:{cap}", lambda: list(_enumerate_object_compositions(task, cap))
    )
    return iter(compositions)


def build_object_composition_steps(composition: Any) -> List[vocab.Step]:
    from src.curriculum.library.grid.overlay_composition import OverlayComposition, build_overlay_steps
    from src.curriculum.library.panels.panel_composition import PanelComposition, build_panel_steps

    if isinstance(composition, OverlayComposition):
        return build_overlay_steps(composition)
    if isinstance(composition, PanelComposition):
        return build_panel_steps(composition)
    from src.curriculum.library.derived.lowering import build_derived_steps
    from src.curriculum.library.derived.model import DerivedComposition

    if isinstance(composition, DerivedComposition):
        return build_derived_steps(composition)
    if composition.layout_name == "crop_to_selected_object":
        return object_compose.build_crop_composition(
            input_ref=_INPUT_REF,
            connectivity=composition.connectivity,
            background=composition.background,
            selector_name=composition.selector_name,
            selector_params=composition.selector_params or None,
            single_color=composition.single_color,
        )
    selected_piece = OBJECT_CONTENT_PIECES[composition.selected_content_name]
    not_selected_piece = OBJECT_CONTENT_PIECES[composition.not_selected_content_name]
    selected_steps = selected_piece.builder(
        "obj", _INPUT_REF, **composition.selected_content_params
    )
    not_selected_steps = not_selected_piece.builder(
        "obj", _INPUT_REF, **composition.not_selected_content_params
    )
    return object_compose.build_identity_canvas_composition(
        input_ref=_INPUT_REF,
        connectivity=composition.connectivity,
        background=composition.background,
        selector_name=composition.selector_name,
        selected_content=selected_steps,
        not_selected_content=not_selected_steps,
        selector_params=composition.selector_params or None,
        single_color=composition.single_color,
    )


def _matches_all_train_pairs(steps: List[vocab.Step], task: Task) -> bool:
    """Same contract as `search/rank.py`'s helper of the same name, with
    one addition: `crop_to_selected_object` leaves `SELECTED_REF` unbound
    when its selector selects no object (a tie, no matching color, no
    object touching the border, ...), which surfaces as a raw `KeyError`
    from `ShapeOut`'s own `Ref` lookup rather than
    `interpreter.InterpreterError`. Both mean the same thing here: this
    composition produces no output for this input, so it is rejected
    exactly like any other interpreter failure."""
    for pair in task.train:
        try:
            output_grid, _trace = interpreter.run(steps, pair.input)
        except (interpreter.InterpreterError, KeyError):
            return False
        if not grids_equal(output_grid, pair.output):
            return False
    return True


def _predict(steps: List[vocab.Step], task: Task) -> Optional[List[Grid]]:
    """Mirrors `search/rank.py::_predict`, but a verified composition can
    still fail on a *test* input whose object structure differs from
    every train pair's (same unbound-`SELECTED_REF` case as above); that
    composition is then not usable as a prediction for this task."""
    try:
        return [interpreter.run(steps, grid)[0] for grid in task.test_inputs]
    except (interpreter.InterpreterError, KeyError):
        return None


def _object_pack_pairs(task: Task, cap: Optional[int]) -> List[Tuple[ObjectComposition, List[Grid]]]:
    pairs: List[Tuple[ObjectComposition, List[Grid]]] = []
    for composition in enumerate_object_compositions(task, cap):
        steps = build_object_composition_steps(composition)
        if not _matches_all_train_pairs(steps, task):
            continue
        predictions = _predict(steps, task)
        if predictions is None:
            continue
        pairs.append((composition, predictions))
    return pairs


def second_stage_object_candidates(task: Task) -> List[Tuple[Any, List[Grid]]]:
    """Bounded object-pack search for the second rule of a two-rule
    sequence (ADR 0101): capped composition count, no relational or toward
    families, so the whole sequence stage costs about one single-stage
    search instead of up to `MAX_FIRST_STAGE` of them."""
    from src.curriculum.library.grid.overlay_search import verified_overlay_candidates_with_predictions

    pairs = _object_pack_pairs(task, SECOND_STAGE_OBJECT_CAP)
    return pairs + verified_overlay_candidates_with_predictions(task)


def verified_object_candidates_with_predictions(task: Task) -> List[Tuple[ObjectComposition, List[Grid]]]:
    """Every object-pack composition that reproduces all train pairs and
    still predicts on every test input, paired with its own test
    predictions (item 2/3 of the 2026-09-22 follow-up: candidate-choice
    hit rate and the two-attempt policy both need per-candidate
    predictions, not just the aggregate status
    `search_task_with_object_pack` below collapses them into)."""
    pairs = _object_pack_pairs(task, None)
    from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
    from src.curriculum.library.grid.overlay_search import verified_overlay_candidates_with_predictions

    from src.curriculum.library.panels.panel_search import verified_panel_candidates_with_predictions

    return (
        pairs
        + verified_overlay_candidates_with_predictions(task)
        + verified_panel_candidates_with_predictions(task)
        + verified_derived_candidates_with_predictions(task)
    )


def search_task_with_object_pack(task: Task) -> ObjectSearchResult:
    pairs = verified_object_candidates_with_predictions(task)
    if not pairs:
        return ObjectSearchResult(status="no_candidate", verified=[], predictions=None)

    verified = [composition for composition, _predictions in pairs]
    first = pairs[0][1]
    if any(preds != first for _composition, preds in pairs[1:]):
        return ObjectSearchResult(status="ambiguous", verified=verified, predictions=None)

    return ObjectSearchResult(status="solved", verified=verified, predictions=first)


def check_with_object_pack(task: Task) -> CombinedSearchResult:
    """Section 5.5's "roda `check` com o pacote": the union of the main
    library's own verified candidates and the object pack's verified
    candidates, judged by one shared ambiguity bar (disagreement on any
    side makes the task ambiguous, not silently resolved by the other)."""
    main_result = search_main_library(task)
    object_result = search_task_with_object_pack(task)

    if main_result.status == "ambiguous" or object_result.status == "ambiguous":
        return CombinedSearchResult(
            "ambiguous", main_result.verified, object_result.verified, None
        )

    predictions_by_side: List[List[Grid]] = []
    if main_result.status == "solved":
        predictions_by_side.append(main_result.predictions)
    if object_result.status == "solved":
        predictions_by_side.append(object_result.predictions)

    if not predictions_by_side:
        return CombinedSearchResult(
            "no_candidate", main_result.verified, object_result.verified, None
        )

    first = predictions_by_side[0]
    if any(preds != first for preds in predictions_by_side[1:]):
        return CombinedSearchResult(
            "ambiguous", main_result.verified, object_result.verified, None
        )

    return CombinedSearchResult(
        "solved", main_result.verified, object_result.verified, first
    )
