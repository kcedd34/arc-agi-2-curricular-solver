"""Lowering of the stamp action (ADR 0109): copy every template region onto
each anchor region. The offset pins the template's key cell (or its bbox
origin) to the anchor's; pairing restricts templates to those whose key
colour is the anchor's colour. Regions are erased first, then painted, so a
copy is never erased by a later erase."""
from typing import List, Tuple

from src.curriculum.library.derived import expressions as ex
from src.curriculum.library.derived.lowering_selection import selection_steps
from src.curriculum.library.derived.lowering_shift import MOVED
from src.curriculum.library.derived.model import Action
from src.curriculum.spec import vocabulary as vocab

ANCHOR = "anc"
TEMPLATE = "tpl"
KEY_ALIGN, ORIGIN_ALIGN = "key", "origin"
BY_KEY, ALL_PAIRS = "by_key", "all"
ERASE_NONE, ERASE_TEMPLATES, ERASE_ALL = "none", "templates", "all"
ALIGNS = (KEY_ALIGN, ORIGIN_ALIGN)
PAIRINGS = (BY_KEY, ALL_PAIRS)
ERASES = (ERASE_NONE, ERASE_TEMPLATES, ERASE_ALL)


def _pin(name: str, axis: str, align: str) -> vocab.Expr:
    base = vocab.Attr(vocab.Ref(name), axis)
    if align == ORIGIN_ALIGN:
        return base
    key = vocab.Measure(vocab.RegionRef(name), f"key_{axis}", 0)
    return vocab.BinOp("+", base, key)


def stamp_offsets(align: str) -> Tuple[vocab.Expr, vocab.Expr]:
    dr = vocab.BinOp("-", _pin(ANCHOR, "row", align), _pin(TEMPLATE, "row", align))
    dc = vocab.BinOp("-", _pin(ANCHOR, "col", align), _pin(TEMPLATE, "col", align))
    return dr, dc


def _paint_body(align: str) -> List[vocab.Step]:
    dr, dc = stamp_offsets(align)
    return [
        vocab.Transform(region=vocab.RegionRef(TEMPLATE), op=vocab.Translate(dr, dc), result_name=MOVED),
        vocab.Emit(region=vocab.RegionRef(MOVED), source=vocab.Copy(source=vocab.Ref(MOVED))),
    ]


def _erase_body(background: int) -> List[vocab.Step]:
    elem = vocab.RegionRef(ex.ELEMENT)
    erased = f"{ex.ELEMENT}_erased"
    return [
        vocab.Transform(region=elem, op=vocab.Erase(background=background), result_name=erased),
        vocab.Emit(region=elem, source=vocab.Copy(source=vocab.Ref(erased))),
    ]


def _erase_steps(erase: str, templates: str, background: int) -> List[vocab.Step]:
    if erase == ERASE_NONE:
        return []
    source = vocab.Ref(templates if erase == ERASE_TEMPLATES else ex.REGIONS_REF)
    return [vocab.ForEach(source, _erase_body(background), element_name=ex.ELEMENT)]


def _anchor_body(align: str, pairing: str, templates: str, tag: str) -> List[vocab.Step]:
    paint = _paint_body(align)
    if pairing == ALL_PAIRS:
        return [vocab.ForEach(vocab.Ref(templates), paint, element_name=TEMPLATE)]
    matched = f"K_{tag}"
    anchor_key = vocab.Measure(vocab.RegionRef(ANCHOR), "key_color", 0)
    return [
        vocab.SelectWhere(vocab.Ref(templates), "key_color", anchor_key, matched),
        vocab.ForEach(vocab.Ref(matched), paint, element_name=TEMPLATE),
    ]


def stamp_steps(action: Action, tag: str, background: int) -> List[vocab.Step]:
    align, pairing, erase = action.param.value
    templates, anchors = f"T_{tag}", f"A_{tag}"
    steps = selection_steps(action.selection, ex.REGIONS_REF, templates, f"t{tag}", background)
    steps += selection_steps(action.target, ex.REGIONS_REF, anchors, f"a{tag}", background)
    steps += _erase_steps(erase, templates, background)
    body = _anchor_body(align, pairing, templates, tag)
    return steps + [vocab.ForEach(vocab.Ref(anchors), body, element_name=ANCHOR)]
