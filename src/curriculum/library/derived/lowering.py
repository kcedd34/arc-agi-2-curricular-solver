"""Lowers a `DerivedComposition` to declarative steps (ADR 0107).

Each action becomes: optional selection (rule value bound, then
`SelectWhere`), then a `ForEach` whose body is the action's use of the
parameter. Selection, use and parameter source are lowered independently.
"""
from typing import List

from src.curriculum.library.derived import expressions as ex
from src.curriculum.library.derived.lowering_selection import selection_steps
from src.curriculum.library.derived.lowering_shift import translate_steps
from src.curriculum.library.derived.lowering_stamp import stamp_steps
from src.curriculum.library.derived.model import Action, DerivedComposition, RegionSpec
from src.curriculum.library.derived.pieces import DERIVED_PIECES
from src.curriculum.library.objects.object_compose import settle_order
from src.curriculum.library.objects.object_content_registry import ALL_CONTENT_PIECES
from src.curriculum.spec import vocabulary as vocab

FILL_BETWEEN = "fill_between"
SLIDE_TOWARD = "slide_toward"
TRANSLATE = "translate_selected"
STAMP = "stamp"
SEGMENT_KINDS = ("row_segments", "col_segments")


def partition_kind(region: RegionSpec) -> vocab.PartitionKind:
    if region.kind == "row_segments":
        return vocab.RowSegments(background=region.background)
    if region.kind == "col_segments":
        return vocab.ColSegments(background=region.background)
    return vocab.Objects(region.connectivity, region.background, region.single_color)


def _fill_between_body(action: Action, background: int) -> List[vocab.Step]:
    color = ex.param_expr(action.param, background)
    return [vocab.Emit(region=vocab.Between(vocab.RegionRef(ex.ELEMENT)), source=vocab.Fill(color=color))]


def _piece_body(action: Action, background: int) -> List[vocab.Step]:
    piece = DERIVED_PIECES.get(action.name) or ALL_CONTENT_PIECES[action.name]
    kwargs = {}
    if "color" in piece.params:
        kwargs["color"] = ex.param_expr(action.param, background)
    if "background" in piece.params:
        kwargs["background"] = background
    if "clear" in piece.params:
        kwargs["clear"] = action.param.value
    return piece.builder(ex.ELEMENT, ex.INPUT_REF, **kwargs)


def _action_body(action: Action, background: int) -> List[vocab.Step]:
    if action.name == FILL_BETWEEN:
        return _fill_between_body(action, background)
    return _piece_body(action, background)


def _slide_steps(action: Action, tag: str, background: int) -> List[vocab.Step]:
    targets, movers, extreme = f"T_{tag}", f"M_{tag}", f"d_{tag}"
    steps = selection_steps(action.target, ex.REGIONS_REF, targets, f"t{tag}", background)
    steps += selection_steps(action.selection, ex.REGIONS_REF, movers, f"s{tag}", background)
    extra: vocab.Expr = 0
    if action.extra is not None:
        rule = action.extra.rule
        steps.append(vocab.Bind(extreme, vocab.Derive(vocab.Ref(movers), rule.op, action.extra.measure, vocab.Ref(targets))))
        elem = vocab.RegionRef(ex.ELEMENT)
        extra = vocab.BinOp("==", vocab.Measure(elem, action.extra.measure, vocab.Ref(targets)), vocab.Ref(extreme))
    body = _slide_body(background, targets, extra)
    steps.append(vocab.ForEach(vocab.Ref(movers), body, element_name=ex.ELEMENT))
    return steps


def _slide_body(background: int, targets: str, extra: vocab.Expr) -> List[vocab.Step]:
    elem = vocab.RegionRef(ex.ELEMENT)
    erased = f"{ex.ELEMENT}_erased"
    slide = vocab.SlideTo(
        region=elem, grid=vocab.Ref(ex.INPUT_REF), background=background,
        direction="toward", stop="contact", target=vocab.Ref(targets), extra=extra,
    )
    return [
        vocab.Transform(region=elem, op=vocab.Erase(background=background), result_name=erased),
        vocab.Emit(region=elem, source=vocab.Copy(source=vocab.Ref(erased))),
        vocab.Emit(region=slide, source=vocab.Copy(source=vocab.Ref(ex.ELEMENT))),
    ]


def _use_steps(action: Action, tag: str, background: int) -> List[vocab.Step]:
    source = ex.REGIONS_REF
    steps: List[vocab.Step] = []
    if action.selection is not None:
        source = f"S_{tag}"
        steps += selection_steps(action.selection, ex.REGIONS_REF, source, tag, background)
    body = _action_body(action, background)
    steps.append(vocab.ForEach(vocab.Ref(source), body, element_name=ex.ELEMENT, order=settle_order(body)))
    return steps


def build_derived_steps(comp: DerivedComposition) -> List[vocab.Step]:
    bg = comp.region.background
    g_in = vocab.Ref(ex.INPUT_REF)
    steps: List[vocab.Step] = [
        vocab.Bind(name=ex.INPUT_REF, value=vocab.Ref("input")),
        vocab.ShapeOut(rows=vocab.Attr(g_in, "rows"), cols=vocab.Attr(g_in, "cols")),
        vocab.Seed(source=g_in),
        vocab.Partition(source=g_in, kind=partition_kind(comp.region), result_name=ex.REGIONS_REF),
    ]
    for index, action in enumerate(comp.actions):
        tag = str(index)
        builder = {SLIDE_TOWARD: _slide_steps, TRANSLATE: translate_steps, STAMP: stamp_steps}.get(action.name, _use_steps)
        steps += builder(action, tag, bg)
    steps.append(vocab.Compose(default_color=bg))
    return steps
