"""Tests for the block_tile_alternating_mirror primitive against real
00576224 data.

Proves the registry-built primitive, composed from block_grid_layout +
row_parity_selected_body + copy_content/flip_content (ADR 0064,
docs/curriculum/tasks/00576224.md, RN-CUR-33 step 2), reproduces both
train pairs and the held-out test pair exactly.
"""
import json
from pathlib import Path

from src.curriculum.library.primitives import tiling_mirror  # noqa: F401 (registers the primitive)
from src.curriculum.library.registry import REGISTRY
from src.curriculum.loader import load_task
from src.curriculum.spec import interpreter

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_block_tile_alternating_mirror_registered():
    assert "block_tile_alternating_mirror" in REGISTRY.names()


def test_block_tile_alternating_mirror_matches_00576224_train():
    task = load_task(TRAINING_DIR / "00576224.json")
    steps = REGISTRY.build("block_tile_alternating_mirror", scale_rows=3, scale_cols=3)
    for pair in task.train:
        output_grid, trace = interpreter.run(steps, pair.input)
        assert output_grid == pair.output
        assert trace[0]["op"] == "bind"
        assert trace[-1]["op"] == "compose"


def test_block_tile_alternating_mirror_matches_00576224_test():
    """Reads the task JSON directly for the test pair's output: `Task`
    deliberately exposes only `test_inputs` (no outputs, see
    src/curriculum/loader.py), so a solver can never see the held-out
    answer. This is a primitive/interpreter verification test, not solver
    code, so reading the raw gabarito here to check correctness is
    legitimate and does not violate that boundary.
    """
    raw = json.loads((TRAINING_DIR / "00576224.json").read_text())
    steps = REGISTRY.build("block_tile_alternating_mirror", scale_rows=3, scale_cols=3)
    for pair in raw["test"]:
        output_grid, _trace = interpreter.run(steps, pair["input"])
        assert output_grid == pair["output"]
