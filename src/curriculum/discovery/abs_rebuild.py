"""Inverse of `abs_tokens.chain_of`: a token chain back to the exact candidate
(ADR 0110, Section 4). Equality of the rebuilt candidate with the original is
the equivalence proof for any abstraction that folds and unfolds to the same
chain."""
from typing import Any, Dict, List, Tuple

from src.curriculum.discovery.abs_tokens import CROP, THEN, Token
from src.curriculum.library.derived.model import Action, DerivedComposition, RegionSpec
from src.curriculum.library.grid.overlay_composition import OverlayComposition
from src.curriculum.library.objects.object_search import ObjectComposition
from src.curriculum.library.panels.panel_composition import PanelComposition
from src.curriculum.search.compose import Composition
from src.curriculum.search.sequence.composition import SequenceComposition


def _by_role(tokens: List[Token]) -> Dict[str, Token]:
    return {t.role: t for t in tokens}


def _main(tokens: List[Token]) -> Composition:
    r = _by_role(tokens)
    return Composition(
        r["layout"].name, r["layout"].param_dict(), r["selector"].name, r["selector"].param_dict(),
        r["selected"].name, r["selected"].param_dict(), r["not_selected"].name, r["not_selected"].param_dict(),
    )


def _object_contents(r: Dict[str, Token]) -> Tuple[Token, Token]:
    if r["layout"].name == CROP:
        return r["layout"].param_dict()["_contents"]
    return r["selected"], r["not_selected"]


def _object(tokens: List[Token]) -> ObjectComposition:
    r = _by_role(tokens)
    layout = r["layout"].param_dict()
    sel, nsel = _object_contents(r)
    return ObjectComposition(
        r["layout"].name, layout["connectivity"], layout["single_color"], layout["background"],
        r["selector"].name, r["selector"].param_dict(), sel.name, sel.param_dict(), nsel.name, nsel.param_dict(),
    )


def _overlay(tokens: List[Token]) -> OverlayComposition:
    r = _by_role(tokens)
    p = r["layout"].param_dict()
    return OverlayComposition(p["n_rows"], p["n_cols"], p["divider"], p["background"], r["table"].param_dict()["table"])


def _panel(tokens: List[Token]) -> PanelComposition:
    p = tokens[0].param_dict()
    return PanelComposition(p["mode"], p["axis"], p["fill"])


def _action(t: Token) -> Action:
    p = t.param_dict()
    return Action(t.name, p["param"], p["selection"], p["target"], p["extra"])


def _derived(tokens: List[Token]) -> DerivedComposition:
    p = tokens[0].param_dict()
    region = RegionSpec(tokens[0].name, p["connectivity"], p["single_color"], p["background"])
    return DerivedComposition(region, tuple(_action(t) for t in tokens[1:]))


_STAGE = {"main": _main, "object": _object, "overlay": _overlay, "panel": _panel, "derived": _derived}


def _split_stages(chain: Tuple[Token, ...]) -> List[List[Token]]:
    stages: List[List[Token]] = [[]]
    for token in chain:
        if token.role == THEN:
            stages.append([])
        else:
            stages[-1].append(token)
    return stages


def rebuild(chain: Tuple[Token, ...]) -> Any:
    stages = [_STAGE[s[0].kind](s) for s in _split_stages(chain)]
    if len(stages) == 1:
        return stages[0]
    return SequenceComposition(stages[0], stages[1])
