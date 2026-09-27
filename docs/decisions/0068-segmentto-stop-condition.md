# 0068 - SegmentTo stop_condition generalization (border, any_obstacle)

Status: Accepted
Date: 2026-09-21

## Context

Task 4 diagnostic (`outputs/curriculum/task4-diagnostic.md`), subtypes
`raio_ate_borda` and `raio_ate_obstaculo` of the `draw_or_extend_lines`
concept, probe-pool anchors `d037b0a7`, `1bfc4729`, `1d398264`,
`97999447` (border) and `342ae2ed`, `52df9849`, `e5790162` (obstacle).
7 of 10 sampled probe-pool tasks in this concept fail for the same root
cause, category `condicao_de_parada_diferente`: `SegmentTo` (ADR 0066)
and its resolver `_resolve_segment_to` (`src/curriculum/spec/_regions.py`)
only implement one stop rule, "first non-background cell is the same
color as the origin and is itself isolated". Any other stop rule (reach
the border, stop at any obstacle regardless of color/isolation)
currently resolves to an empty region, so no candidate composition using
`draw_lines`/`keep` can ever match these tasks' train pairs.

ADR 0066 already named this exact gap as `SegmentTo`'s second plausible
use ("the same `raio_ate_borda`/`raio_ate_obstaculo` subtypes, which need
the same walk-until-condition mechanics with a border-reached or
first-obstacle stop predicate instead of a same-color-partner one"). Per
RN-CUR-31, generalizing the existing mechanism is required in preference
to adding new vocabulary or new pieces per subtype (`SegmentToBorder`,
`SegmentToObstacle` would be a per-task duplication, not a
generalization).

## Decision

Add one field to the existing `SegmentTo` region dataclass:
`stop_condition: str = "same_color_isolated"`, defaulting to ADR 0066's
original behavior so no existing composition changes meaning. Three
values are supported:

1. `"same_color_isolated"` (default, unchanged): stop only at a
   same-color, orthogonally-isolated cell; any other stop resolves
   empty.
2. `"border"` (`raio_ate_borda`): resolve to the between-region only if
   the scan exits the grid without hitting any obstacle; hitting an
   obstacle first resolves empty.
3. `"any_obstacle"` (`raio_ate_obstaculo`): resolve to the
   between-region as soon as any non-background cell is hit, regardless
   of color or isolation; reaching the border first resolves empty.

`_resolve_segment_to` is split into three small functions
(`_resolve_segment_to`, `_resolve_obstacle_stop`, `_resolve_border_stop`)
to keep each under the project's ~40-line/one-responsibility limit.
`draw_lines_content` (`src/curriculum/library/pieces/content.py`) gains
a `stop_condition` parameter threaded into all 4 emitted `SegmentTo`
regions; `CONTENT_PIECES["draw_lines"]`'s params tuple grows from
`("background",)` to `("background", "stop_condition")`. Search enumerates
all 3 values unconditionally (`search/params.py`'s
`_stop_condition_candidates`), since, unlike `background`/`scale`, this
parameter cannot be hard-pruned from a task's train pairs alone.

A necessary side fix: enumerating a third `stop_condition` value exposed
a pre-existing latent gap where `draw_lines` was being paired with
`block_grid` even though it reads the loop element's own `(row, col)` as
a real input-grid coordinate, valid only under `identity_canvas`'s
`Cells()` partition (same structural precondition already gated for the
`isolated_point` selector). This was harmless with 1 stop_condition value
on `007bbfb7` (coincidental 3x3 shape match) but became a real train/test
disagreement once `border` was added. Fixed by adding
`_content_eligible(layout_name, content_name)` in `search/compose.py`,
gating `draw_lines` to `identity_canvas` only, mirroring the existing
`_selector_eligible` pattern.

## Plausible uses (governance bar: at least 2 each)

- `stop_condition="border"`: (a) `raio_ate_borda` probe-pool anchors
  (`d037b0a7`, `1bfc4729`, `1d398264`, `97999447`), (b) any future
  same-size in-place-edit task whose rule is "extend a marker to the
  grid edge unless blocked".
- `stop_condition="any_obstacle"`: (a) `raio_ate_obstaculo` probe-pool
  anchors (`342ae2ed`, `52df9849`, `e5790162`), (b) any future task
  needing a ray that stops at the first occupied cell regardless of its
  color, e.g. collision/bounce-style rules.

## Consequences

- `spec/vocabulary.py`'s `SegmentTo` gains one new optional field,
  backward compatible with every existing construction site (keyword
  default preserves old positional/keyword call shape).
- `spec/_regions.py`, `library/pieces/content.py`, `search/params.py`,
  `search/compose.py` are the only modules touched to wire the new
  field through construction and enumeration.
- Regression-checked per RN-CUR-16/RF09: `python -m src.curriculum.cli
  validate` stays 3/3 green (`007bbfb7`, `00576224`, `ded97339`) after
  this change, including after the `_content_eligible` side fix.
- Empirically (see `docs/curriculum/learning-curve.md`'s v4 entry), this
  generalization alone does not cause the 7 named probe-pool tasks to
  newly solve via `search_task`: several of them need further concepts
  not requested by this task (e.g. `d037b0a7`'s rule fires in a single
  fixed direction only, not `draw_lines_content`'s unconditional 4
  directions; `1bfc4729` draws rectangular frames, not rays; `97999447`
  shows a periodic dash pattern). These are documented as open gaps, not
  silently absorbed into this ADR's scope, per RN-CUR-31 discipline
  against expanding a piece beyond the concept actually generalized.
- No change to `loader.py`'s `Task`/`TrainPair` structures or to the
  probe/evaluation gabarito-access restrictions (RN-CUR-03/RN-CUR-05).
