"""Enumerate and build layout x selector x content compositions (RN-CUR-33
step 2, docs/curriculum/tasks/stage-3-prep.md).

Replaces per-primitive enumeration as the search's unit: a composition
names one layout piece, one selector piece, and one content piece per
selector branch (selected / not-selected), each independently
parametrized via `search/params.py`'s existing per-parameter-name
candidate lookup. Named registry primitives (`library/primitives/
tiling.py`, `tiling_mirror.py`) stay registered as documentation/
convenience builders, but the search itself (`search/rank.py`,
`search/diagnostics.py`) enumerates and verifies compositions, not
primitive names.

RN-CUR-33 step 3: layout candidates are already hard-pruned by
`search/params.py` (per-axis scale, palette). This module additionally
prunes layout/selector *pairings* that are structurally incompatible
regardless of parameter values (`_selector_eligible`), so a selector
that would always error against a given layout (e.g.
`input_cell_not_background` when the tile scale doesn't match the
input's own shape, `search/pruning.layout_matches_input_dims`) is never
enumerated in the first place.
"""
import itertools
from typing import Any, Dict, Iterator, List, NamedTuple, Sequence, Tuple

from src.curriculum.library.pieces.content import CONTENT_PIECES
from src.curriculum.library.pieces.layout import LAYOUT_PIECES
from src.curriculum.library.pieces.piece_spec import PieceSpec
from src.curriculum.library.pieces.selector import SELECTOR_PIECES
from src.curriculum.loader import Task
from src.curriculum.search.params import candidates_for_primitive
from src.curriculum.search.pruning import layout_matches_input_dims
from src.curriculum.spec import vocabulary as vocab

MAX_COMPOSITIONS_PER_TASK = 5000

_INPUT_REF = "g_in"


class Composition(NamedTuple):
    layout_name: str
    layout_params: Dict[str, Any]
    selector_name: str
    selector_params: Dict[str, Any]
    selected_content_name: str
    selected_content_params: Dict[str, Any]
    not_selected_content_name: str
    not_selected_content_params: Dict[str, Any]

    def describe(self) -> str:
        def _fmt(name: str, params: Dict[str, Any]) -> str:
            return f"{name}({params})" if params else name

        return (
            f"layout={_fmt(self.layout_name, self.layout_params)} "
            f"selector={_fmt(self.selector_name, self.selector_params)} "
            f"selected={_fmt(self.selected_content_name, self.selected_content_params)} "
            f"not_selected={_fmt(self.not_selected_content_name, self.not_selected_content_params)}"
        )


def _piece_param_combos(params: Sequence[str], task: Task) -> Iterator[Dict[str, Any]]:
    if not params:
        yield {}
        return
    candidate_lists = candidates_for_primitive(list(params), task)
    value_lists = [candidate_lists[p] for p in params]
    for combo in itertools.product(*value_lists):
        yield dict(zip(params, combo))


def _expand_pieces(
    registry: Dict[str, PieceSpec], task: Task
) -> List[Tuple[str, Dict[str, Any]]]:
    expanded = []
    for name, piece in registry.items():
        for params in _piece_param_combos(piece.params, task):
            expanded.append((name, params))
    return expanded


def _selector_eligible(
    layout_name: str, selector_name: str, layout_params: Dict[str, Any], task: Task
) -> bool:
    """Structural layout/selector compatibility, independent of which
    selector-own parameter (e.g. background) is later tried.

    `identity_canvas` has no scale params: its Cells() partition always
    makes the loop element's own (row, col) a real input coordinate, so
    both `input_cell_not_background` and `isolated_point` are trivially
    in-bounds against it. Against `block_grid`, only
    `input_cell_not_background` is checked (its existing scale-matches-
    input-dims precondition); `isolated_point` is never eligible there,
    since a block-grid element's (row, col) is an IndexGrid index, not a
    real input coordinate (ADR 0066)."""
    if selector_name == "input_cell_not_background":
        if layout_name == "identity_canvas":
            return True
        return layout_matches_input_dims(
            task, layout_params["scale_rows"], layout_params["scale_cols"]
        )
    if selector_name == "isolated_point":
        return layout_name == "identity_canvas"
    return True


def _content_eligible(layout_name: str, content_name: str) -> bool:
    """Structural layout/content compatibility, independent of the
    selector or any content-own parameter value.

    `draw_lines` reads the loop element's own (row, col) as a real input
    coordinate (via `CellAt`/`SegmentTo`), which only holds for
    `identity_canvas`'s Cells() partition - the same precondition
    `_selector_eligible` already enforces for the `isolated_point`
    selector (ADR 0066). Against `block_grid`, the element's (row, col)
    is an IndexGrid block index, not a real input coordinate, so
    `draw_lines` there scans nonsense coordinates: this was already
    latent before task 4 (ADR 0068), just not exposed as a train/test
    disagreement until `stop_condition` added more candidates
    (RN-CUR-16 regression fix). `keep` is a pure no-op regardless of
    layout, so it stays eligible everywhere."""
    if content_name == "draw_lines":
        return layout_name == "identity_canvas"
    return True


def _content_pair_eligible(
    selected: Tuple[str, Dict[str, Any]], not_selected: Tuple[str, Dict[str, Any]]
) -> bool:
    """Content x content compatibility (Rodada 2, on top of
    `_content_eligible`'s per-content/layout check): two exclusions on
    the (selected, not_selected) pair itself, independent of layout.

    - Identical pair (same name and same params): the selector's split
      has no behavioral effect, since both branches emit the exact same
      steps regardless of which cells it routed where (decorative
      selection, domain knowledge item 7, continuous-loop.md Section 2).
      Excluding it from generation loses nothing that could count as
      `solved`: Fase D's antifraud check already rejects this pattern.
    - `draw_lines` on both branches: `draw_lines_content` reads the
      loop element's own (row, col) as a genuine isolated marker
      (ADR 0066/0068's `SegmentTo` semantics); the not_selected branch
      is by construction the selector's complement of that marker set,
      so treating its cells as markers too contradicts the split that
      produced them. It is also the single largest driver of this
      term's size (its own two-parameter fanout squared, Rodada 2
      Fase A/B measurement)."""
    if selected == not_selected:
        return False
    if selected[0] == "draw_lines" and not_selected[0] == "draw_lines":
        return False
    return True


def _layout_selector_pairs(
    layouts: List[Tuple[str, Dict[str, Any]]],
    selectors: List[Tuple[str, Dict[str, Any]]],
    task: Task,
) -> Iterator[Tuple[Tuple[str, Dict[str, Any]], Tuple[str, Dict[str, Any]]]]:
    for layout in layouts:
        for selector in selectors:
            if _selector_eligible(layout[0], selector[0], layout[1], task):
                yield layout, selector


def enumerate_compositions(task: Task) -> Iterator[Composition]:
    layouts = _expand_pieces(LAYOUT_PIECES, task)
    selectors = _expand_pieces(SELECTOR_PIECES, task)
    contents = _expand_pieces(CONTENT_PIECES, task)
    pairs = _layout_selector_pairs(layouts, selectors, task)
    combos = (
        (layout, selector, selected, not_selected)
        for layout, selector in pairs
        for selected in contents
        if _content_eligible(layout[0], selected[0])
        for not_selected in contents
        if _content_eligible(layout[0], not_selected[0])
        and _content_pair_eligible(selected, not_selected)
    )
    for layout, selector, selected, not_selected in itertools.islice(
        combos, MAX_COMPOSITIONS_PER_TASK
    ):
        yield Composition(
            layout_name=layout[0],
            layout_params=layout[1],
            selector_name=selector[0],
            selector_params=selector[1],
            selected_content_name=selected[0],
            selected_content_params=selected[1],
            not_selected_content_name=not_selected[0],
            not_selected_content_params=not_selected[1],
        )


def build_composition_steps(composition: Composition) -> List[vocab.Step]:
    layout_piece = LAYOUT_PIECES[composition.layout_name]
    layout = layout_piece.builder(_INPUT_REF, **composition.layout_params)

    selected_piece = CONTENT_PIECES[composition.selected_content_name]
    not_selected_piece = CONTENT_PIECES[composition.not_selected_content_name]
    selected_steps = selected_piece.builder(
        layout.element_name, _INPUT_REF, **composition.selected_content_params
    )
    not_selected_steps = not_selected_piece.builder(
        layout.element_name, _INPUT_REF, **composition.not_selected_content_params
    )

    selector_piece = SELECTOR_PIECES[composition.selector_name]
    body = selector_piece.builder(
        layout.element_name,
        selected_content=selected_steps,
        not_selected_content=not_selected_steps,
        **composition.selector_params,
    )

    steps: List[vocab.Step] = [
        vocab.Bind(name=_INPUT_REF, value=vocab.Ref("input")),
        layout.shape_out,
    ]
    if layout.seed is not None:
        # identity_canvas: pre-fill the canvas as a copy of the input
        # before any selective overwrite (ADR 0066); block_grid has no
        # seed, every cell is covered by exactly one ForEach branch.
        steps.append(layout.seed)
    steps.append(layout.partition)
    steps.append(
        vocab.ForEach(
            list_ref=vocab.Ref(layout.partition.result_name),
            element_name=layout.element_name,
            body=body,
        )
    )
    # Every partition element is covered by exactly one of the two
    # content branches (selected or not_selected); for block_grid that
    # alone fully covers the canvas, so Compose's default fill never
    # actually applies to any cell either way.
    steps.append(vocab.Compose(default_color=0))
    return steps
