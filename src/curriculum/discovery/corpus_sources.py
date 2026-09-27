"""Builds the discovery corpus from the public training tasks (ADR 0110):
input grids only, never outputs, never the evaluation split. Every partition
family the derived layer can use contributes one partition per input."""
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Sequence

from src.curriculum.grid import Grid
from src.curriculum.loader import load_task
from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._region_value import RegionValue
from src.curriculum.spec.interpreter import _partition_grid

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def background_of(grid: Grid) -> int:
    counts = Counter(v for row in grid for v in row)
    top = counts.most_common()
    return top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else 0


def partition_kinds(background: int) -> List[vocab.PartitionKind]:
    return [
        vocab.Objects(4, background, True),
        vocab.Objects(8, background, True),
        vocab.Objects(8, background, False),
        vocab.Rows(),
        vocab.Cols(),
        vocab.RowSegments(background=background),
        vocab.ColSegments(background=background),
    ]


def partitions_of(grid: Grid) -> List[List[RegionValue]]:
    found = []
    for kind in partition_kinds(background_of(grid)):
        try:
            found.append(_partition_grid(grid, kind))
        except (InterpreterError, ValueError):
            continue
    return found


def sample_task_paths(stride: int, directory: Path = TRAINING_DIR) -> List[Path]:
    return sorted(directory.glob("*.json"))[::stride]


def corpus_partitions(paths: Iterable[Path]) -> List[List[RegionValue]]:
    parts: List[List[RegionValue]] = []
    for path in paths:
        for pair in load_task(path).train:
            parts += partitions_of(pair.input)
    return parts


def describe_sample(paths: Sequence[Path]) -> dict:
    return {"source": str(TRAINING_DIR), "n_tasks": len(paths), "task_ids": [p.stem for p in paths]}
