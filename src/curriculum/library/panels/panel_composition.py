"""Panel-grid candidate (ADR 0106): the composition record and the
declarative steps it lowers to. The input is cut into panels by separator
lines and one panel-level operation produces the output."""
from typing import List, NamedTuple

from src.curriculum.spec import vocabulary as vocab

INPUT_REF = "g_in"
PANELS_REF = "panels"
SUMMARY = "summary"
SWAP = "swap"


class PanelComposition(NamedTuple):
    mode: str
    axis: str
    fill: int

    def describe(self) -> str:
        return f"layout=panel_grid(mode={self.mode},axis={self.axis},fill={self.fill})"


def _panel_op(comp: PanelComposition):
    if comp.mode == SUMMARY:
        return vocab.PanelSummary(comp.fill)
    return vocab.PanelSwap(comp.axis)


def build_panel_steps(comp: PanelComposition) -> List[vocab.Step]:
    result = vocab.Ref(PANELS_REF)
    return [
        vocab.Bind(name=INPUT_REF, value=vocab.Ref("input")),
        vocab.Transform(region=vocab.WholeGrid(vocab.Ref(INPUT_REF)), op=_panel_op(comp), result_name=PANELS_REF),
        vocab.ShapeOut(rows=vocab.Attr(result, "rows"), cols=vocab.Attr(result, "cols")),
        vocab.Emit(region=vocab.AtOrigin(region=vocab.RegionRef(PANELS_REF)), source=vocab.Copy(source=result)),
        vocab.Compose(default_color=comp.fill),
    ]


def panel_hypothesis_id(comp: PanelComposition) -> str:
    return f"panel_grid-{comp.mode}_axis={comp.axis}_fill={comp.fill}"
