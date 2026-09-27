"""Data model of the derived-parameter family (ADR 0107).

A composition is: one region kind, then one or more actions. Every action is
`selection x use x parameter source`, where the parameter (a colour, a shift,
a target) is a derived value: a literal, a colour resource of the grid, a
property of the acted region, or a table learned between demonstration pairs.
Selection, action and parameter source are independent axes.
"""
import hashlib
from typing import Any, NamedTuple, Optional, Tuple


class RegionSpec(NamedTuple):
    kind: str  # objects | row_segments | col_segments
    connectivity: int
    single_color: bool
    background: int

    def describe(self) -> str:
        text = f"{self.kind}(background={self.background}"
        if self.kind == "objects":
            text += f",connectivity={self.connectivity},single_color={self.single_color}"
        return text + ")"


class ValueRule(NamedTuple):
    """How the value a selection compares against is derived.
    `min`/`max`: extremum of the selection measure over the regions;
    `total`: sum of measure `over` (with `color_op` naming a grid colour
    resource as its argument) over the regions; `equals`: a literal."""

    op: str  # min | max | total | equals
    over: str = ""
    color_op: str = ""
    literal: int = 0


class Selection(NamedTuple):
    measure: str
    rule: ValueRule

    def describe(self) -> str:
        r = self.rule
        if r.op == "equals":
            return f"{self.measure} == {r.literal}"
        if r.op == "total":
            arg = f", {r.color_op}" if r.color_op else ""
            return f"{self.measure} == total({r.over}{arg})"
        return f"{self.measure} == {r.op}({self.measure})"


class ParamSource(NamedTuple):
    kind: str  # literal | element | derived | table
    value: Any = None  # literal colour | measure name | grid op | (measures, table)

    def describe(self) -> str:
        if self.kind in ("table", "shift"):
            measures, table = self.value
            return f"{self.kind}[{'+'.join(measures)}]={dict(table)}"
        return f"{self.kind}:{self.value}"


class Action(NamedTuple):
    name: str  # a content piece name, or "slide_toward"
    param: Optional[ParamSource]
    selection: Optional[Selection]  # None = every region
    target: Optional[Selection] = None  # slide_toward: the regions slid toward
    extra: Optional[Selection] = None  # slide_toward: regions advancing one more step

    def describe(self) -> str:
        where = self.selection.describe() if self.selection else "all"
        param = f"({self.param.describe()})" if self.param else ""
        text = f"{self.name}{param} on [{where}]"
        if self.target:
            text += f" toward [{self.target.describe()}]"
        if self.extra:
            text += f" extra [{self.extra.describe()}]"
        return text


class DerivedComposition(NamedTuple):
    region: RegionSpec
    actions: Tuple[Action, ...]

    def describe(self) -> str:
        acts = "; ".join(a.describe() for a in self.actions)
        return f"layout=identity_canvas; partition input as {self.region.describe()} -> R; {acts}"


def derived_hypothesis_id(comp: DerivedComposition) -> str:
    full = comp.describe()
    text = "".join(ch if ch.isalnum() or ch in "=-_.+" else "_" for ch in full)
    return f"derived-{text[:90]}-{hashlib.sha1(full.encode('utf-8')).hexdigest()[:12]}"
