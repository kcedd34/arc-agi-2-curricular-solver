"""Vector form of the derived prune's `covers_changes` (ADR 0110): every cell a
train pair changes must lie in the bounding box of a selected region."""
from typing import List

import numpy as np

from src.curriculum.discovery.corpus import Corpus
from src.curriculum.library.derived.facts import task_changes
from src.curriculum.loader import Task


class CoverCheck:
    def __init__(self, task: Task, corpus: Corpus) -> None:
        self._slices = []
        offset = 0
        for change, size in zip(task_changes(task), corpus.counts):
            regions = corpus.regions[offset : offset + int(size)]
            cells = sorted(change.cells)
            self._slices.append((offset, int(size), self._matrix(cells, regions)))
            offset += int(size)
        self.has_changes = any(m.shape[0] for _, _, m in self._slices)

    @staticmethod
    def _matrix(cells: List, regions: List) -> np.ndarray:
        matrix = np.zeros((len(cells), len(regions)), dtype=bool)
        for j, region in enumerate(regions):
            for i, (r, c) in enumerate(cells):
                matrix[i, j] = region.row0 <= r < region.row0 + region.rows and region.col0 <= c < region.col0 + region.cols
        return matrix

    def covers(self, mask: np.ndarray) -> bool:
        for offset, size, matrix in self._slices:
            if matrix.shape[0] and not (matrix & mask[offset : offset + size]).any(axis=1).all():
                return False
        return True
