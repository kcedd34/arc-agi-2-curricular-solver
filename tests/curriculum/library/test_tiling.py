"""Tests for the block_tile_by_background primitive against real 007bbfb7 data.

Proves the registry-built primitive reproduces the exact result the
hand-written ADR 0062 acceptance fixture already proved correct
(tests/curriculum/spec/test_interpreter.py), via the reusable,
parametrized registry path instead of a hardcoded step list.
"""
from pathlib import Path

from src.curriculum.library.primitives import tiling  # noqa: F401 (registers the primitive)
from src.curriculum.library.registry import REGISTRY
from src.curriculum.loader import load_task
from src.curriculum.spec import interpreter

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_block_tile_by_background_registered():
    assert "block_tile_by_background" in REGISTRY.names()


def test_block_tile_by_background_matches_007bbfb7():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    steps = REGISTRY.build(
        "block_tile_by_background", background=0, scale_rows=3, scale_cols=3
    )
    for pair in task.train:
        output_grid, trace = interpreter.run(steps, pair.input)
        assert output_grid == pair.output
        assert trace[0]["op"] == "bind"
        assert trace[-1]["op"] == "compose"
