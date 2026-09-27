"""Region corpus for property discovery (ADR 0110): regions of many
partitions laid out contiguously (one group per partition), with the values of
every atom computed by the canonical scalar evaluator, as numpy arrays."""
from typing import Dict, List, Sequence, Tuple

import numpy as np

from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._gen_atoms import MAX_SIBLINGS
from src.curriculum.spec._generated import generated_measure
from src.curriculum.spec._region_value import RegionValue

Values = Tuple[np.ndarray, np.ndarray]  # (int32 values, bool invalid mask)


class Corpus:
    def __init__(self, partitions: Sequence[List[RegionValue]]) -> None:
        kept = [p for p in partitions if 0 < len(p) <= MAX_SIBLINGS]
        self.regions: List[RegionValue] = [r for p in kept for r in p]
        counts = np.array([len(p) for p in kept], dtype=np.int64)
        self.counts = counts
        self.starts = np.concatenate(([0], np.cumsum(counts)[:-1])).astype(np.int64) if len(kept) else counts
        self.gid = np.repeat(np.arange(len(kept), dtype=np.int64), counts)
        self.n = len(self.regions)
        self.n_groups = len(kept)
        self._atoms: Dict[str, Values] = {}

    def atom_values(self, name: str) -> Values:
        if name not in self._atoms:
            self._atoms[name] = self._compute_atom(name)
        return self._atoms[name]

    def _compute_atom(self, name: str) -> Values:
        vals = np.zeros(self.n, dtype=np.int32)
        bad = np.zeros(self.n, dtype=bool)
        for i, region in enumerate(self.regions):
            try:
                vals[i] = generated_measure(region, name)
            except InterpreterError:
                bad[i] = True
        return vals, bad
