"""Solution chains for abstraction extraction (ADR 0110, Section 4): every
accepted hypothesis becomes an ordered chain of stage tokens. A token keeps
its parameters so the chain can be rebuilt exactly; only (kind, role, name)
takes part in matching across tasks."""
from typing import Any, Dict, List, NamedTuple, Tuple

from src.curriculum.library.derived.model import Action, DerivedComposition
from src.curriculum.library.grid.overlay_composition import OverlayComposition
from src.curriculum.library.objects.object_search import ObjectComposition
from src.curriculum.library.panels.panel_composition import PanelComposition
from src.curriculum.search.compose import Composition
from src.curriculum.search.sequence.composition import SequenceComposition

CROP = "crop_to_selected_object"
THEN = "then"


class Token(NamedTuple):
    kind: str
    role: str
    name: str
    params: Tuple[Tuple[str, Any], ...]

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.kind, self.role, self.name)

    def param_dict(self) -> Dict[str, Any]:
        return dict(self.params)


def _tok(kind: str, role: str, name: str, params: Dict[str, Any]) -> Token:
    return Token(kind, role, name, tuple(params.items()))


def _main_chain(c: Composition) -> List[Token]:
    return [
        _tok("main", "layout", c.layout_name, c.layout_params),
        _tok("main", "selector", c.selector_name, c.selector_params),
        _tok("main", "selected", c.selected_content_name, c.selected_content_params),
        _tok("main", "not_selected", c.not_selected_content_name, c.not_selected_content_params),
    ]


def _object_chain(c: ObjectComposition) -> List[Token]:
    layout = {"connectivity": c.connectivity, "single_color": c.single_color, "background": c.background}
    contents = [
        _tok("object", "selected", c.selected_content_name, c.selected_content_params),
        _tok("object", "not_selected", c.not_selected_content_name, c.not_selected_content_params),
    ]
    if c.layout_name == CROP:
        layout["_contents"] = tuple(contents)
        contents = []
    return [_tok("object", "layout", c.layout_name, layout), _tok("object", "selector", c.selector_name, c.selector_params)] + contents


def _overlay_chain(c: OverlayComposition) -> List[Token]:
    layout = {"n_rows": c.n_rows, "n_cols": c.n_cols, "divider": c.divider, "background": c.background}
    return [_tok("overlay", "layout", "overlay_parts", layout), _tok("overlay", "table", "mask_table", {"table": c.table})]


def _panel_chain(c: PanelComposition) -> List[Token]:
    return [_tok("panel", "layout", "panel_grid", {"mode": c.mode, "axis": c.axis, "fill": c.fill})]


def _action_token(a: Action) -> Token:
    params = {"param": a.param, "selection": a.selection, "target": a.target, "extra": a.extra}
    return _tok("derived", "action", a.name, params)


def _derived_chain(c: DerivedComposition) -> List[Token]:
    r = c.region
    region = {"connectivity": r.connectivity, "single_color": r.single_color, "background": r.background}
    return [_tok("derived", "region", r.kind, region)] + [_action_token(a) for a in c.actions]


def chain_of(candidate: Any) -> Tuple[Token, ...]:
    if isinstance(candidate, SequenceComposition):
        return chain_of(candidate.first) + (Token("sequence", THEN, THEN, ()),) + chain_of(candidate.second)
    builders = {
        Composition: _main_chain, ObjectComposition: _object_chain, OverlayComposition: _overlay_chain,
        PanelComposition: _panel_chain, DerivedComposition: _derived_chain,
    }
    return tuple(builders[type(candidate)](candidate))


def base_length(chain: Tuple[Token, ...]) -> int:
    return sum(1 for t in chain if t.role != THEN)
