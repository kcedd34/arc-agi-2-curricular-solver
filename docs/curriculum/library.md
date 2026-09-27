# Library (v6)

One line per piece, per BOOTSTRAP.md's artifact layout. Created at v5
(2026-09-22, object-pack.md Phase 7 promotion); no version before v5
ever wrote this file, so main-library pieces from v1-v4 are listed
here for the first time, not re-derived per version.

## Main library (`src/curriculum/library/pieces/`)

Layout (`layout.py`):
- `block_grid(scale_rows, scale_cols)` - partitions a synthetic `IndexGrid` into a rows x cols block tiling.
- `identity_canvas()` - same-size passthrough canvas (introduced with task 3, `ded97339`).

Selector (`selector.py`):
- `input_cell_not_background(...)` - selects the real input cell at a block's position when it is not `background`.
- `row_parity()` - selects by block-row parity (even/odd row of the tiling).
- `isolated_point(background)` - selects a cell whose value is not `background` and has no same-colored neighbor.

Content (`content.py`):
- `copy()` - copies the selected source unchanged.
- `fill(fill_color)` - fills the region with `fill_color` (renamed from
  `background` in Round 1 of the continuous cycle, ADR 0075: this is a
  write-role parameter, distinct from `input_cell_not_background`'s and
  `draw_lines`'s detection-role `background`).
- `flip(axis)` - mirrors the selected source along `axis`.
- `draw_lines(background, stop_condition)` - draws a ray from a seed to `stop_condition` (`border`/`same_color_isolated`/`any_obstacle`).
- `keep()` - passes the region through unmodified (no-op content, used as an explicit "leave as is" arm).

## Object pack (`src/curriculum/library/objects/`, promoted 2026-09-22, RN-CUR-36)

Layout (`object_layout.py`):
- `identity_canvas(connectivity, single_color, background)` - same-size canvas over an object-segmented grid.
- `crop_to_selected_object(connectivity, single_color, background)` - output is the selected object's bounding-box crop.

Selector (`object_selector.py`):
- `largest_object()` - selects the object with the most cells.
- `smallest_object()` - selects the object with the fewest cells.
- `unique_color_object()` - selects the one object whose color is not shared by any other object.
- `objects_of_color(color)` - selects every object of a given color.
- `objects_touching_border()` - selects objects with at least one cell on the grid border.
- `objects_not_touching_border()` - selects objects with no cell on the grid border.
- `all_objects()` - selects every object.
- `objects_with_interior()` / `objects_without_interior()` - selects objects that have (or lack) at least one interior cell (ADR 0081).
- `objects_with_hole()` / `objects_without_hole()` - selects objects that enclose (or do not enclose) at least one hole, i.e. a non-member bbox cell not 4-reachable from outside the bbox (ADR 0082; predicate `HasHole`).

Content (`object_content.py`):
- `keep()` - passes the region through unmodified.
- `erase_selected(background)` - replaces the selected object's cells with `background`.
- `recolor_selected(color)` - recolors the selected object's cells to `color`.
- `fill_bbox_selected(color)` - fills the selected object's bounding box with `color`.
- `slide_selected(direction, stop, background)` - slides the selected object in `direction` until `stop` (`border`/`contact`/`settle`). `settle` collides with the output under construction and iterates objects nearest-to-destination first (ADR 0091), so objects stack.
- `recolor_border_selected(color)` / `recolor_interior_selected(color)` - repaints only the border (or only the interior) cells of the selected object (ADR 0081).
- `fill_holes_selected(color)` - paints only the enclosed hole cells of the selected object with `color` (ADR 0082; op `FillEnclosed`).
- `halo4_selected(color, background)` / `halo8_selected(color, background)` - paints the 4-adjacent (halo4) or 8-adjacent (halo8) ring of background cells around the selected object with `color`, clipped to the grid and never overwriting other objects (ADR 0084; op `Halo`, helper `spec/_object_halo.py`).
- `fill_holes_erase_selected(color, background)` / `fill_holes_halo8_selected(halo_color, color, background)` - composite contents: fill the enclosed holes, then erase the object or paint its 8-adjacent halo (ADR 0086; `object_content_composite.py`, registered via `object_content_registry.ALL_CONTENT_PIECES`). Roughly doubles object-search enumeration time on the slowest tasks (ADR 0089).
- `hollow_selected(background)` / `peel_selected(background)` - interior (or border) cells of the selected object become `background` (ADR 0081).
- `crop_content()` - the crop-layout's own content (used only with `crop_to_selected_object`).

Params/pruning (`object_params.py`, not search candidates themselves, RN-CUR-31 Section 3.5): `background_candidates`, `recolor_target_color_candidates`, `objects_of_color_candidates`, `slide_direction_candidates`, `connectivity_single_color_candidates`, `should_include_identity_canvas`, `should_include_crop_layout`.

Grid pack (`library/grid/`, ADR 0094): `overlay_parts` - splits the input into `n_rows x n_cols` equal parts (optionally divided by one-cell lines), learns from the train pairs a table mapping "which parts are non-background at this position" to an output color, and paints the part-sized output (op `OverlayParts`, region `WholeGrid`; candidate `OverlayComposition`, enumerated by `overlay_enumerate.py`, verified by `overlay_search.py`, merged into `verified_object_candidates_with_predictions`). An unseen mask on a test input makes the candidate unusable rather than guessing.

Relational pack (`library/relational/`, ADR 0098): `ExtremumComposition` - partition the
input into regions, compute a `measure` per region, take the `extremum` (min or max),
`select_where` the regions equal to it (ties select all; a task-wide constant selection is
pruned) and apply an existing object action. `TowardComposition` adds the `distance_to`
measure and `SlideTo direction="toward"`. Independent interpreter ops, equivalence-tested
against the library (RN-CUR-14).

Sequence pack (`search/sequence/`, ADR 0097/0101): `SequenceComposition` - one monotone
first rule then a single-rule search on the derived task; runs only when no single rule
has a candidate. Bounded by a deterministic work budget (`spec/work_meter.py`, 60M
interpreter-area units) with a 300s safety deadline; `budget_hit` and `deadline_hit` are
reported per task.

Panel pack (`library/panels/`, ADR 0106): `PanelComposition(mode, axis, fill)` - the input
is cut into panels by full separator lines (`spec/_panels.py`, `find_panels`); mode
`summary` (bounding box of the uniform panels, one pixel each, `fill` for the rest) or
`swap` (two partner panels on one axis exchange shape masks, repainted with the source
background). Pruned by inventory: enumerated only when every train input has separator
lines. Candidates differing only in `fill` and predicting the same grids are kept once.

Derived pack (`library/derived/`, ADR 0107, v6): one enumerator over regions x selection x
action x parameter source, replacing `library/relational/`. Properties are pure region
functions in a single registry (`spec/_measures.py`: size, width, height, gap, colors,
hole_cells, border_distance, count_color, color, distance_to, row/col parity, dominant
color). Derivation operators (`spec/_derive.py`) are independent: min/max extremum (ties
select all), total, unique value, mode, rare/common grid color, learned table. Uses are
decoupled: region selection, action color (literal, table or derived), shift (table by
color/size/height/width), slide-toward with an extra step for the distance extremum, fill
between segments, bbox/border/interior/holes. Learned tables need consistency, keys that
recur at least twice on average and more than one value; an unseen key at test time is an
interpreter error. Pruned by inventory before any verification (13.1M -> 66k hypotheses over
1000 training tasks). Not covered: stacking of movers, marker-into-container rules, panels.

## Derived layer additions (library v6, Round 20)

New region properties: `corner_nw_color` (cell diagonally up-left of a region, 0 outside the
grid), `closed` (has holes or zero gap), `multi_cell` (size > 1), plus the `CornerCell`
region. New derived piece `recolor_clear_corner_nw` (recolor the region with the marker
colour and clear the marker cell to a colour learned from the train outputs), flag
selections (`closed`, `multi_cell` equals 0/1) and the `corner_marker` parameter source.
Search space 13.1M -> 16.3M unpruned, 66k -> 72k pruned over 1000 training tasks.

## Stamp action (library v7, Round 21)

New derived action `stamp` (`library/derived/lowering_stamp.py`, `stamp_predict.py`,
`stamp_enumerate.py`): templates and anchors are two disjoint proper selections of a
multicolour objects partition; the template key cell (the unique-count colour) or its bbox
origin is pinned to the anchor's. Options: align (key, origin), pairing (by key colour, all),
erase (none, templates, all). New measures `key_color`, `key_row`, `key_col`. A pure-Python
pre-filter predicts the train outputs and the interpreter verifies survivors; partitions with
more than 48 regions skip the stamp. Search space over 1000 training tasks: 72,458 -> 72,548
pruned, 90 stamp survivors in 6 tasks; mean enumeration 0.87 s, max 79.8 s.
