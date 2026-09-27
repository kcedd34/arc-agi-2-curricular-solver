"""Declarative-step vocabulary v1, data definitions only (ADR 0062).

Every operation, predicate, and expression is a plain frozen dataclass so
a step sequence is fully inspectable for a desk check (RN-CUR-14) without
executing any code. This module holds structure only; execution lives in
`interpreter.py`.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


# --- Expressions -------------------------------------------------------
# Integer arithmetic only, over in.rows/in.cols, partition counts, and
# previously bind-named values. No loops, no arbitrary function calls.

@dataclass(frozen=True)
class Ref:
    name: str


@dataclass(frozen=True)
class Attr:
    base: "Expr"
    attr: str  # "rows" or "cols"


@dataclass(frozen=True)
class Count:
    list_ref: "Expr"


@dataclass(frozen=True)
class BinOp:
    op: str  # "+", "-", "*", "//", "%", "==" (1 when equal, else 0)
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class CellAt:
    """Reads a single cell's color from `grid` at (`row`, `col`).

    RN-CUR-33 step 2: once a block-grid layout always partitions a
    synthetic `IndexGrid` (`arrangement` removed from `block_grid_layout`),
    its loop element carries no real input-cell color (interpreter.py's
    `_partition_grid` gives `IndexGrid` entries placeholder cells); a
    selector that needs the real input cell at the block's own position
    must look it up explicitly instead of reading the loop element itself.
    No existing expression read a grid cell by explicit coordinate outside
    of a RegionValue's own bound `.cells` before this (RN-CUR-31 exhaustion
    evidence: `Attr` only ever exposed a RegionValue's own row0/col0 or a
    grid's rows/cols, never arbitrary cell content).
    """

    grid: "Expr"
    row: "Expr"
    col: "Expr"


@dataclass(frozen=True)
class Measure:
    """A pure integer property of one region (ADR 0098). `name` is one of
    `spec/_measures.py::MEASURE_NAMES`; `arg` is the grid for
    `border_distance` and the color for `count_color`, unused otherwise."""

    region: "Region"
    name: str
    arg: "Expr" = 0


@dataclass(frozen=True)
class Extremum:
    """The min or max (`mode`) of `name` over every region in `list_ref`
    (ADR 0098). An empty list is an interpreter error."""

    list_ref: "Expr"
    name: str
    mode: str  # "min" or "max"
    arg: "Expr" = 0


@dataclass(frozen=True)
class Derive:
    """A parameter derived from a set (ADR 0107). Region operators (`min`,
    `max`, `unique`, `mode`, `total`) fold measure `name` over every region in
    `source`; grid operators (`rarest_color`, `common_color`) read the colour
    resources of the grid `source`, ignoring `background`. An operator with no
    single answer is an interpreter error, never a guess."""

    source: "Expr"
    op: str
    name: str = "size"
    arg: "Expr" = 0
    background: "Expr" = 0


@dataclass(frozen=True)
class TableLookup:
    """Value learned between demonstration pairs: `table` maps a key tuple to
    a value; `keys` are evaluated per use. A key never seen in the
    demonstrations is an interpreter error (ADR 0107)."""

    keys: Tuple["Expr", ...]
    table: Tuple[Tuple[Tuple[int, ...], int], ...]


Expr = Union[Ref, Attr, Count, BinOp, CellAt, Measure, Extremum, Derive, TableLookup, int, str]


# --- Partition kinds -----------------------------------------------------

@dataclass(frozen=True)
class Cells:
    pass


@dataclass(frozen=True)
class Rows:
    pass


@dataclass(frozen=True)
class Cols:
    pass


@dataclass(frozen=True)
class Blocks:
    h: int
    w: int


@dataclass(frozen=True)
class Objects:
    connectivity: int  # 4 or 8
    background: int
    single_color: bool = True


@dataclass(frozen=True)
class ColorLayers:
    pass


@dataclass(frozen=True)
class IndexGrid:
    """A synthetic R x C grid of block indices, sized by rows/cols directly
    rather than by partitioning any real grid's own shape. Needed when a
    layout's block count is driven by an inferred scale factor decoupled
    from the input's own dimensions (RN-CUR-31 exhaustion evidence,
    docs/curriculum/tasks/00576224.md)."""

    rows: int
    cols: int


@dataclass(frozen=True)
class RowSegments:
    """Every row with exactly two non-`background` cells, as one region: the
    span between them, endpoints included, interior cells non-member (ADR
    0098). Ordered top to bottom."""

    background: int


@dataclass(frozen=True)
class ColSegments:
    """Column analogue of `RowSegments`, ordered left to right."""

    background: int


PartitionKind = Union[
    Cells, Rows, Cols, Blocks, Objects, ColorLayers, IndexGrid, RowSegments, ColSegments
]

CORRESPOND_BY_VALUES = ("index", "position", "color", "size_rank")


# --- transform() operations -----------------------------------------------

@dataclass(frozen=True)
class Rotate:
    k: int


@dataclass(frozen=True)
class Flip:
    axis: str  # "horizontal" or "vertical"


@dataclass(frozen=True)
class Transpose:
    pass


@dataclass(frozen=True)
class Recolor:
    color_map: Dict[int, int]


@dataclass(frozen=True)
class CropToContent:
    background: int


@dataclass(frozen=True)
class RecolorObject:
    """Repaints every cell that belongs to the region's own object (a
    non-None cell, object pack Section 3.3's `recolor(region, color)`) to
    `color`, leaving non-member cells (None, outside the object's actual
    shape but inside its bounding box) untouched. Distinct from `Recolor`,
    which remaps colors by value across every cell of a region regardless
    of object membership."""

    color: "Expr"


@dataclass(frozen=True)
class Erase:
    """Repaints every cell of the region's own object to `background`
    (object pack Section 3.3's `erase(region, background)`). Kept as its
    own op, not just `RecolorObject(background)`, so a desk-check trace
    reads "erase" rather than an equivalent-but-opaque recolor call
    (RN-CUR-14); both share `_paint_object_cells` internally."""

    background: int


@dataclass(frozen=True)
class FillBbox:
    """Repaints every cell of the region's bounding box, including
    non-member (None) cells, to `color` (object pack Section 3.3's
    `fill_bbox(region, color)`) - unlike `RecolorObject`/`Erase`, this
    also fills in the object's own "holes"/background gaps within its own
    bbox."""

    color: "Expr"


@dataclass(frozen=True)
class RecolorObjectPart:
    """Repaints only one part of the region's own object to `color`:
    `part="border"` (member cells with a 4-neighbour outside the object)
    or `part="interior"` (member cells fully surrounded by members). Never
    touches non-member (None) cells (ADR 0081, `objeto_contorno`)."""

    part: str
    color: "Expr"


@dataclass(frozen=True)
class FillEnclosed:
    """Paints the region's own object holes (non-member bbox cells not
    4-reachable from outside the bbox without crossing the object) with
    `color`; every other cell becomes None so nothing else is written
    (ADR 0082, `topologia_dentro`)."""

    color: "Expr"


@dataclass(frozen=True)
class Halo:
    """The ring of cells around the region's own object (4-adjacent, or
    8-adjacent with `diagonal`), painted `color` only where the output grid
    currently holds `background`. Returns the padded, grid-clipped box with
    None everywhere else, so an `Emit` of it never touches the object or
    any other object (ADR 0084, `objeto_halo`)."""

    color: "Expr"
    diagonal: bool
    background: int


@dataclass(frozen=True)
class Translate:
    """Shifts a region's position by (`dr`, `dc`) without changing its
    cells (object pack Section 3.3's `translate(region, dr, dc)`).
    Out-of-bounds placement is not checked here; `emit()` raises if the
    translated region would land outside the output grid."""

    dr: "Expr"
    dc: "Expr"


@dataclass(frozen=True)
class OverlayParts:
    """Splits the region into `n_rows x n_cols` equal parts (separated by a
    one-cell divider when `divider`), then writes, per part position, the
    color the `table` assigns to the tuple of flags "part cell !=
    `background`" (ADR 0094, `sobreposicao_booleana_subgrids`). `table` is a
    tuple of `(mask, color)` pairs; a mask absent from it is an error."""

    n_rows: int
    n_cols: int
    divider: bool
    background: int
    table: Tuple[Tuple[Tuple[bool, ...], int], ...]


@dataclass(frozen=True)
class PanelSummary:
    """Cuts the region into panels by full separator lines and returns one
    pixel per panel over the bounding box of the uniform (single-color)
    panels; a non-uniform panel inside that box becomes `fill` (ADR 0106)."""

    fill: int


@dataclass(frozen=True)
class PanelSwap:
    """Cuts the region into panels by full separator lines; along `axis`
    ("row": left/right pair, "col": top/bottom pair) each panel takes its
    partner's shape mask repainted in the partner's background (ADR 0106)."""

    axis: str


TransformOp = Union[
    Rotate, Flip, Transpose, Recolor, CropToContent, RecolorObject, Erase,
    FillBbox, RecolorObjectPart, FillEnclosed, Halo, Translate, OverlayParts,
    PanelSummary, PanelSwap,
]


# --- emit() sources --------------------------------------------------------

@dataclass(frozen=True)
class Copy:
    source: Expr


@dataclass(frozen=True)
class Fill:
    color: Expr


EmitSource = Union[Copy, Fill]


# --- Region references (where emit()/transform() act) ----------------------

@dataclass(frozen=True)
class RegionRef:
    """A previously bound or partitioned region, by name."""
    name: str


@dataclass(frozen=True)
class BlockAt:
    """The output-grid block aligned with partition element (row, col).

    Block size is inferred from shape_out divided by the row/col extent of
    the partition currently being iterated (see interpreter.py). This is an
    RN-CUR-27 implementation decision, not part of the ADR 0062 worked
    example's own step list.
    """
    row: Expr
    col: Expr


@dataclass(frozen=True)
class SegmentTo:
    """The strictly-between span from (from_row, from_col) scanning one
    step at a time along `direction`, stopping according to
    `stop_condition` (task 4 generalization, ADR 0068, RN-CUR-31: same
    concept, not a new Region per stopping rule). `direction` is one of
    "up", "down", "left", "right" (ADR 0066); a caller wanting all four
    directions from one origin issues four separate SegmentTo/Emit pairs,
    since ForEach only iterates over partitioned/corresponded lists, not
    literal direction enumerations.

    `stop_condition` is one of:
    - "same_color_isolated" (default, ADR 0066's original behavior):
      resolves to the between-region only if the first non-background
      cell hit is the same color as the origin and is itself orthogonally
      isolated; any other stop (border, different color, non-isolated
      same color) resolves to an empty (0x0) region.
    - "border" (task 4, `raio_ate_borda`): resolves to the between-region
      only if the scan leaves the grid without ever hitting a
      non-background cell; hitting any obstacle before the border
      resolves to an empty region instead.
    - "any_obstacle" (task 4, `raio_ate_obstaculo`): resolves to the
      between-region as soon as any non-background cell is hit,
      regardless of its color or isolation; reaching the border without
      any obstacle resolves to an empty region instead.
    """

    grid: Expr
    from_row: Expr
    from_col: Expr
    direction: str
    background: Expr
    stop_condition: str = "same_color_isolated"


@dataclass(frozen=True)
class SlideTo:
    """The region reached by sliding `region`'s own object one step at a
    time along `direction` (object pack Section 3.3's
    `slide(region, direction, stop)`), stopping according to `stop`:

    - "border": slides as far as possible while staying inside `grid`'s
      bounds; never stops early for an obstacle.
    - "contact": slides until moving one more step would overlap a
      non-`background` cell in `grid` that is not part of the sliding
      object's own (pre-slide) cells, or until the border, whichever
      comes first.
    - "settle": like "contact", but the collision scene is the output
      grid under construction (ADR 0091), so objects already moved
      block later ones and stack up.

    The object's own original cells are excluded from the contact check
    so an object never "collides" with the trail of cells it is vacating
    (e.g. a wide object sliding by less than its own width would
    otherwise immediately register contact with itself).
    """

    region: "Region"
    grid: Expr
    background: Expr
    direction: str
    stop: str
    target: Optional[Expr] = None
    extra: Expr = 0


@dataclass(frozen=True)
class AtOrigin:
    """`region` repositioned so its own row0/col0 become 0, keeping its
    rows/cols/cells unchanged (object pack Section 3.4's `crop_content`
    piece: pairs with `crop_to_selected_object`'s canvas, which is sized
    exactly to the selected object's own bounding box, so the object's
    input-relative position must be dropped before `emit()` places it)."""

    region: "Region"


@dataclass(frozen=True)
class WholeGrid:
    """The full extent of the grid `grid` evaluates to, as a region at the
    origin (ADR 0094): lets a whole-grid transform act on a bound grid."""

    grid: "Expr"


@dataclass(frozen=True)
class Between:
    """The strictly-interior span of a one-row or one-column `region` (ADR
    0098): every cell except its two extremes, all as members. A span with
    no interior (length 2 or less) resolves to an empty (0x0) region, which
    `emit` skips."""

    region: "Region"


@dataclass(frozen=True)
class CornerCell:
    """The single cell diagonally outside the top-left corner of `region`'s
    bbox (Round 20): a 1x1 region, or an empty (0x0) one when that cell falls
    outside the output grid, which `emit` skips."""

    region: "Region"


Region = Union[RegionRef, BlockAt, SegmentTo, SlideTo, AtOrigin, WholeGrid, Between, CornerCell]


# --- Predicates --------------------------------------------------------

@dataclass(frozen=True)
class IsBackground:
    value: Expr
    background: Expr


@dataclass(frozen=True)
class ColorEq:
    a: Expr
    b: Expr


@dataclass(frozen=True)
class ColorIn:
    color: Expr
    color_set: Expr


@dataclass(frozen=True)
class CountEq:
    list_ref: Expr
    n: Expr


@dataclass(frozen=True)
class SizeGt:
    region: Region
    n: Expr


@dataclass(frozen=True)
class TouchesBorder:
    region: Region
    grid: Expr


@dataclass(frozen=True)
class IsLargest:
    region: Region
    list_ref: Expr


@dataclass(frozen=True)
class IsSmallest:
    region: Region
    list_ref: Expr


@dataclass(frozen=True)
class SizeEq:
    """True iff `region`'s own object size (count of cells that are part
    of the object, not the bounding-box area) equals `n` (object pack
    Section 3.3's `size_eq(n)`)."""

    region: Region
    n: Expr


@dataclass(frozen=True)
class ObjectColorEq:
    """True iff `region`'s own object is monochromatic (a single color
    across every one of its cells, object pack Section 3.2's object
    representation) and that color equals `color` (Section 3.3's
    `color_eq(c)`). False for a multi-color object, never a majority-vote
    guess - distinct from the generic `ColorEq`/`_scalar_color`, which
    resolves an ambiguous region to its dominant color for unrelated,
    already-in-use cases (e.g. `correspond(..., by="color")`)."""

    region: Region
    color: Expr


@dataclass(frozen=True)
class HasUniqueColor:
    """True iff `region`'s own object is monochromatic and no other
    object in `list_ref` shares that color (object pack Section 3.2.5:
    ties/shared colors return no selection, never resolved silently;
    Section 3.3's `has_unique_color`)."""

    region: Region
    list_ref: Expr


@dataclass(frozen=True)
class HasInterior:
    """True iff `region`'s own object has at least one interior cell, that
    is a member cell whose 4 neighbours are all members (ADR 0081)."""

    region: Region


@dataclass(frozen=True)
class HasHole:
    """True iff `region`'s own object encloses at least one hole (ADR 0082)."""

    region: Region


@dataclass(frozen=True)
class IsIsolated:
    """True iff (row, col) in `grid` is non-background and has no
    orthogonally-adjacent cell of the same color (ADR 0066). No existing
    predicate tests a single input cell's own local neighborhood at 1:1
    granularity (RN-CUR-31 exhaustion evidence,
    docs/curriculum/tasks/ded97339.md)."""

    grid: Expr
    row: Expr
    col: Expr
    background: Expr


Predicate = Union[
    IsBackground, ColorEq, ColorIn, CountEq, SizeGt, TouchesBorder,
    IsLargest, IsSmallest, IsIsolated, SizeEq, ObjectColorEq, HasUniqueColor,
    HasInterior, HasHole,
]


# --- Steps ---------------------------------------------------------------

@dataclass(frozen=True)
class Bind:
    name: str
    value: Expr


@dataclass(frozen=True)
class ShapeOut:
    rows: Expr
    cols: Expr


@dataclass(frozen=True)
class Partition:
    source: Expr
    kind: PartitionKind
    result_name: str


@dataclass(frozen=True)
class Correspond:
    list_a: Expr
    list_b: Expr
    by: str
    result_name: str


@dataclass(frozen=True)
class ForEach:
    list_ref: Expr
    body: List["Step"]
    element_name: str = "item"
    order: Optional[str] = None


@dataclass(frozen=True)
class Test:
    predicate: Predicate
    result_name: str


@dataclass(frozen=True)
class Branch:
    condition_name: str
    then_steps: List["Step"]
    else_steps: List["Step"]


@dataclass(frozen=True)
class Emit:
    region: Region
    source: EmitSource


@dataclass(frozen=True)
class Transform:
    region: Region
    op: TransformOp
    result_name: Optional[str] = None


@dataclass(frozen=True)
class Compose:
    default_color: Expr


@dataclass(frozen=True)
class Seed:
    """Initializes the output grid from a real grid's cells (e.g. a copy
    of the task's own input) instead of leaving every cell as None until
    compose()'s flat default_color fallback (ADR 0066). No existing step
    can pre-fill the canvas from a grid; `Compose.default_color` only
    ever fills remaining None cells with one flat color (RN-CUR-31
    exhaustion evidence, docs/curriculum/tasks/ded97339.md)."""

    source: Expr


@dataclass(frozen=True)
class SelectWhere:
    """Binds `result_name` to EVERY region of `list_ref` whose `measure`
    equals `value` (ADR 0098). A tie selects all tied regions, unlike
    `IsLargest`/`IsSmallest`, which select nothing on a tie."""

    list_ref: Expr
    measure: str
    value: Expr
    result_name: str
    arg: Expr = 0


Step = Union[
    Bind, ShapeOut, Partition, Correspond, ForEach, Test, Branch, Emit,
    Transform, Compose, Seed, SelectWhere,
]
