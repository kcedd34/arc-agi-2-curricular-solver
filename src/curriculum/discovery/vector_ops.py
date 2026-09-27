"""Vectorised operators over a `Corpus` (ADR 0110). Each mirrors the scalar
semantics of `spec/_generated.py` exactly: an operand that is invalid makes the
result invalid; a group operator is invalid for the whole group when any member
is. Invalid entries hold value 0 so signatures are canonical."""
from typing import Callable, Dict, Tuple

import numpy as np

from src.curriculum.discovery.corpus import Corpus, Values

_BIG = 1 << 24
_OFFSET = 1 << 22


def _clean(vals: np.ndarray, bad: np.ndarray) -> Values:
    return np.where(bad, 0, vals).astype(np.int32), bad


def _binary(fn: Callable[[np.ndarray, np.ndarray], np.ndarray]):
    def run(corpus: Corpus, a: Values, b: Values) -> Values:
        bad = a[1] | b[1]
        return _clean(fn(a[0].astype(np.int64), b[0].astype(np.int64)), bad)
    return run


def _ratio(corpus: Corpus, a: Values, b: Values) -> Values:
    bad = a[1] | b[1] | (b[0] == 0)
    safe = np.where(b[0] == 0, 1, b[0]).astype(np.int64)
    return _clean(a[0].astype(np.int64) // safe, bad)


def _group_bad(corpus: Corpus, bad: np.ndarray) -> np.ndarray:
    per_group = np.add.reduceat(bad.astype(np.int64), corpus.starts) > 0
    return per_group[corpus.gid]


def _broadcast(corpus: Corpus, per_group: np.ndarray, bad: np.ndarray) -> Values:
    return _clean(per_group[corpus.gid], _group_bad(corpus, bad))


def _gmin(corpus: Corpus, a: Values) -> Values:
    return _broadcast(corpus, np.minimum.reduceat(a[0], corpus.starts), a[1])


def _gmax(corpus: Corpus, a: Values) -> Values:
    return _broadcast(corpus, np.maximum.reduceat(a[0], corpus.starts), a[1])


def _gsum(corpus: Corpus, a: Values) -> Values:
    return _broadcast(corpus, np.add.reduceat(a[0].astype(np.int64), corpus.starts), a[1])


def _keys(corpus: Corpus, vals: np.ndarray) -> np.ndarray:
    return corpus.gid * _BIG + (vals.astype(np.int64) + _OFFSET)


def _same(corpus: Corpus, a: Values) -> Values:
    _, inverse, counts = np.unique(_keys(corpus, a[0]), return_inverse=True, return_counts=True)
    return _clean(counts[inverse], _group_bad(corpus, a[1]))


def _rank(corpus: Corpus, a: Values) -> Values:
    unique_keys, inverse = np.unique(_keys(corpus, a[0]), return_inverse=True)
    first = np.searchsorted(unique_keys // _BIG, corpus.gid, side="left")
    return _clean(inverse.reshape(-1) - first, _group_bad(corpus, a[1]))


def _gmode(corpus: Corpus, a: Values) -> Values:
    keys, counts = np.unique(_keys(corpus, a[0]), return_counts=True)
    key_group = keys // _BIG
    edges = np.flatnonzero(np.concatenate(([True], key_group[1:] != key_group[:-1])))
    top = np.maximum.reduceat(counts, edges)
    lens = np.diff(np.concatenate((edges, [len(keys)])))
    is_top = counts == np.repeat(top, lens)
    ties = np.add.reduceat(is_top.astype(np.int64), edges) > 1
    order = np.where(is_top, np.arange(len(keys)), len(keys))
    first_top = np.minimum.reduceat(order, edges)
    mode_vals = (keys[first_top] % _BIG) - _OFFSET
    bad = _group_bad(corpus, a[1]) | ties[corpus.gid]
    return _clean(mode_vals[corpus.gid], bad)


BINARY_IMPL: Dict[str, Callable] = {
    "add": _binary(lambda x, y: x + y),
    "sub": _binary(lambda x, y: x - y),
    "ratio": _ratio,
    "eq": _binary(lambda x, y: (x == y).astype(np.int64)),
    "lt": _binary(lambda x, y: (x < y).astype(np.int64)),
}
GROUP_IMPL: Dict[str, Callable] = {
    "gmin": _gmin, "gmax": _gmax, "gsum": _gsum, "same": _same, "rank": _rank, "gmode": _gmode,
}


def apply_op(corpus: Corpus, op: str, args: Tuple[Values, ...]) -> Values:
    if op in BINARY_IMPL:
        return BINARY_IMPL[op](corpus, args[0], args[1])
    return GROUP_IMPL[op](corpus, args[0])
