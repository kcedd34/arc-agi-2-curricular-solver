"""Selection effects of generated properties, evaluated for all regions of a
corpus at once (ADR 0110). A rule has no answer (None) when the property is
invalid on any region of a partition, exactly like the scalar selection probe."""
from typing import Iterator, Tuple

import numpy as np

from src.curriculum.discovery.corpus import Corpus, Values
from src.curriculum.spec._gen_atoms import BOOL, INT

EQUALS_LITERALS = {INT: (0, 1, 2), BOOL: (1, 0)}


def _extreme_mask(corpus: Corpus, vals: np.ndarray, mode: str) -> np.ndarray:
    reduce = np.minimum if mode == "min" else np.maximum
    per_group = reduce.reduceat(vals, corpus.starts)
    return vals == per_group[corpus.gid]


def _rules_for(typ: str) -> Iterator[Tuple[str, int]]:
    if typ == INT:
        yield from (("min", 0), ("max", 0))
    for literal in EQUALS_LITERALS.get(typ, ()):
        yield ("equals", literal)


def selection_masks(corpus: Corpus, values: Values, typ: str) -> Iterator[Tuple[str, int, np.ndarray]]:
    """(rule op, literal, boolean mask over the corpus regions) per rule."""
    vals, bad = values
    if bad.any() or typ not in EQUALS_LITERALS:
        return
    for op, literal in _rules_for(typ):
        mask = _extreme_mask(corpus, vals, op) if op != "equals" else vals == literal
        yield op, literal, mask


def is_proper_somewhere(corpus: Corpus, mask: np.ndarray) -> bool:
    chosen = np.add.reduceat(mask.astype(np.int64), corpus.starts)
    return bool(np.any((chosen > 0) & (chosen < corpus.counts)))
