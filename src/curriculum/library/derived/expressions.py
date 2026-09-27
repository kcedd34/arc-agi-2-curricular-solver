"""Lowers the derived-parameter model to `spec/vocabulary.py` expressions."""
from typing import Optional

from src.curriculum.library.derived.candidates import CORNER_MEASURE
from src.curriculum.library.derived.model import ParamSource, Selection
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._measures import GRID_ARG_MEASURES

INPUT_REF = "g_in"
REGIONS_REF = "R"
ELEMENT = "seg"


def measure_arg(measure: str, target_ref: Optional[str]) -> vocab.Expr:
    if measure in GRID_ARG_MEASURES:
        return vocab.Ref(INPUT_REF)
    if measure == "distance_to":
        return vocab.Ref(target_ref)
    return 0


def rule_value(selection: Selection, source_ref: str, background: int, target_ref: Optional[str]) -> vocab.Expr:
    rule = selection.rule
    if rule.op == "equals":
        return rule.literal
    source = vocab.Ref(source_ref)
    if rule.op == "total":
        arg = vocab.Derive(vocab.Ref(INPUT_REF), rule.color_op, background=background) if rule.color_op else 0
        return vocab.Derive(source, "total", rule.over, arg)
    return vocab.Derive(source, rule.op, selection.measure, measure_arg(selection.measure, target_ref))


def element_measure(name: str, element: str) -> vocab.Expr:
    if name == "color":
        return vocab.Attr(vocab.Ref(element), "color")
    return vocab.Measure(vocab.RegionRef(element), name, vocab.Ref(INPUT_REF) if name in GRID_ARG_MEASURES else 0)


def param_expr(param: ParamSource, background: int, element: str = ELEMENT) -> vocab.Expr:
    if param.kind == "literal":
        return param.value
    if param.kind == "corner_marker":
        return element_measure(CORNER_MEASURE, element)
    if param.kind == "element":
        return element_measure(param.value, element)
    if param.kind == "derived":
        return vocab.Derive(vocab.Ref(INPUT_REF), param.value, background=background)
    measures, table = param.value
    return vocab.TableLookup(tuple(element_measure(m, element) for m in measures), table)
