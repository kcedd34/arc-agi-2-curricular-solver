"""Search-space pruning: infer per-axis tile-scale, palette, and
layout/selector compatibility from a task's demonstrations, before
enumeration (RN-CUR-33 step 3, docs/curriculum/tasks/stage-3-prep.md).

Used by `search/params.py` (hard-prune candidate lists) and
`search/compose.py` (hard-prune incompatible layout/selector pairings),
so `enumerate_compositions` never yields a hypothesis the demonstrations
already rule out.
"""
from typing import List, Optional

from src.curriculum.loader import Task
from src.curriculum.perception.change_inventory import build_pair_inventory, build_task_inventory
from src.curriculum.search.features import colors_by_frequency


def infer_consistent_axis_scale(task: Task, axis: str) -> Optional[int]:
    """The single output/input scale factor for `axis` ("row" or "col"),
    if every train pair agrees on the same integer multiplier; None when
    they disagree or don't divide evenly, since no safe cut can be made
    in that case (search/params.py then falls back to a bounded range,
    still verified against every train pair by search/rank.py)."""
    consistent = None
    for pair in task.train:
        in_size = len(pair.input) if axis == "row" else len(pair.input[0])
        out_size = len(pair.output) if axis == "row" else len(pair.output[0])
        if in_size == 0 or out_size % in_size != 0:
            return None
        scale = out_size // in_size
        if scale < 1:
            return None
        if consistent is None:
            consistent = scale
        elif consistent != scale:
            return None
    return consistent


def infer_palette(task: Task) -> List[int]:
    """Colors observed in the train-pair input grids, most frequent
    first. A color never demonstrated is not a plausible background/fill
    value, so callers use this as a hard candidate list, not just an
    ordering hint."""
    return colors_by_frequency(task)


def layout_matches_input_dims(task: Task, scale_rows: int, scale_cols: int) -> bool:
    """True when every train pair's own input shape equals
    `(scale_rows, scale_cols)`.

    This is the structural precondition the `input_cell_not_background`
    selector relies on: it looks up the input grid at the block's own
    `(row, col)` index via `vocab.CellAt`, which is only in-bounds when
    the `IndexGrid` partition's block count (`scale_rows x scale_cols`)
    equals the input's own shape. When it does not (e.g. 00576224, whose
    2x2 input is smaller than its own 3x3 tile scale), every candidate in
    that selector family is a guaranteed out-of-bounds `InterpreterError`
    regardless of the guessed background - so the pairing is pruned
    before enumeration instead of discovered one interpreter error at a
    time.
    """
    return all(
        len(pair.input) == scale_rows and len(pair.input[0]) == scale_cols
        for pair in task.train
    )


def infer_target_color_candidates(task: Task) -> List[int]:
    """Hard-prune candidates for a "target color" parameter (a color a
    piece writes into the output, e.g. a recolor action), from the
    change inventory (object-pack.md Section 3.5 rule 1 / Section 3.6
    `new_color_always_added` row).

    If every train pair adds at least one new color and they share a
    common one, candidates are restricted to that intersection (the
    piece almost certainly paints with a color the demonstrations
    themselves introduce). Otherwise falls back to every color observed
    in any train output: still hard-pruned from the demonstrations, just
    not narrowed to "added" colors, since guessing a specific one beyond
    that would not be conservative (object-pack.md Section 3.6's own
    "only discard what is impossible" rule)."""
    inventory = build_task_inventory(task)
    pair_inventories = [build_pair_inventory(pair) for pair in task.train]
    if inventory.new_color_always_added:
        common = None
        for pair_inv in pair_inventories:
            common = pair_inv.added_colors if common is None else (common & pair_inv.added_colors)
        return sorted(common)
    every_output_color = {c for pair_inv in pair_inventories for c in pair_inv.out_palette}
    return sorted(every_output_color)


def infer_colors_common_to_every_input(task: Task) -> List[int]:
    """Hard-prune candidates for a "selection color" parameter (a color a
    piece selects by, e.g. `objects_of_color`), to colors present in
    every train pair's input (object-pack.md Section 3.5 rule 2): a
    color absent from even one input can never be the rule's fixed
    selection color. Falls back to the full observed palette in the
    degenerate case of an empty train set."""
    pair_inventories = [build_pair_inventory(pair) for pair in task.train]
    if not pair_inventories:
        return list(infer_palette(task))
    common = pair_inventories[0].in_palette
    for pair_inv in pair_inventories[1:]:
        common = common & pair_inv.in_palette
    return sorted(common)
