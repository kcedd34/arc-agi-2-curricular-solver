"""Whole-grid overlay candidate (ADR 0094): the composition record and the
declarative steps it lowers to. The input is split into equal parts and
every output cell is a learned function of which parts are non-background
at that position."""
from typing import List, NamedTuple, Tuple

from src.curriculum.spec import vocabulary as vocab

INPUT_REF = "g_in"
OVERLAY_REF = "overlay"

MaskTable = Tuple[Tuple[Tuple[bool, ...], int], ...]


class OverlayComposition(NamedTuple):
    n_rows: int
    n_cols: int
    divider: bool
    background: int
    table: MaskTable

    def describe(self) -> str:
        rows = ",".join(f"{''.join('1' if f else '0' for f in mask)}->{color}" for mask, color in self.table)
        return (
            f"layout=overlay_parts(parts={self.n_rows}x{self.n_cols},divider={self.divider},"
            f"background={self.background}) table=[{rows}]"
        )


def build_overlay_steps(comp: OverlayComposition) -> List[vocab.Step]:
    op = vocab.OverlayParts(comp.n_rows, comp.n_cols, comp.divider, comp.background, comp.table)
    overlay = vocab.Ref(OVERLAY_REF)
    return [
        vocab.Bind(name=INPUT_REF, value=vocab.Ref("input")),
        vocab.Transform(region=vocab.WholeGrid(vocab.Ref(INPUT_REF)), op=op, result_name=OVERLAY_REF),
        vocab.ShapeOut(rows=vocab.Attr(overlay, "rows"), cols=vocab.Attr(overlay, "cols")),
        vocab.Emit(region=vocab.AtOrigin(region=vocab.RegionRef(OVERLAY_REF)), source=vocab.Copy(source=overlay)),
        vocab.Compose(default_color=comp.background),
    ]


def overlay_hypothesis_id(comp: OverlayComposition) -> str:
    """Deterministic id for the desk-check hypothesis directory."""
    masks = "_".join("".join("1" if f else "0" for f in m) + f"to{c}" for m, c in comp.table)
    return (
        f"overlay_parts-{comp.n_rows}x{comp.n_cols}_divider={comp.divider}_background={comp.background}__{masks}"
    )
