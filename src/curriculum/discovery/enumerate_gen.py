"""Typed enumeration of generated properties with signature dedup (ADR 0110).

Level `d` holds the expressions of depth `d` whose value signature is new.
Two properties with the same values on every corpus region (and the same
invalid mask) are the same property; the one with the fewest nodes (then the
smallest text) is kept. Operands of a depth-3 expression are a depth-2
expression and an atom, which bounds the level (a full depth-2 x depth-2
product is quadratic in the level size)."""
import hashlib
from typing import Dict, Iterable, Iterator, List, NamedTuple, Tuple

from src.curriculum.discovery.corpus import Corpus, Values
from src.curriculum.discovery.evaluator import VectorEvaluator
from src.curriculum.spec._gen_atoms import ATOM_NAMES
from src.curriculum.spec._gen_expr import BINARY_OPS, COMMUTATIVE_OPS, GROUP_OPS, Expr, apply_op, atom, result_type


class Entry(NamedTuple):
    text: str
    depth: int
    nodes: int
    type: str
    group_constant: bool  # same value on every region of each partition


class GenerationStats(NamedTuple):
    generated: int  # typed candidates evaluated
    valid: int  # candidates with at least one valid value and not constant
    unique: int  # kept after signature dedup (atoms included)
    per_depth_generated: Tuple[int, ...]
    per_depth_unique: Tuple[int, ...]

    @property
    def dedup_rate(self) -> float:
        return 1.0 - self.unique / self.valid if self.valid else 0.0


def signature(values: Values) -> bytes:
    vals, bad = values
    return hashlib.blake2b(vals.tobytes() + bad.tobytes(), digest_size=12).digest()


def _is_group_constant(corpus: Corpus, values: Values) -> bool:
    import numpy as np

    vals, bad = values
    lo = np.minimum.reduceat(vals, corpus.starts)
    hi = np.maximum.reduceat(vals, corpus.starts)
    return bool(np.all(lo == hi))


def _is_degenerate(values: Values) -> bool:
    vals, bad = values
    ok = ~bad
    if not ok.any():
        return True
    return bool((vals[ok] == vals[ok][0]).all())


def _unary_candidates(level: List[Expr]) -> Iterator[Expr]:
    for child in level:
        for op in GROUP_OPS:
            if result_type(op, [child.type]) is not None:
                yield apply_op(op, child)


def _binary_candidates(left: Iterable[Expr], right: List[Expr], both_orders: bool) -> Iterator[Expr]:
    for a in left:
        for b in right:
            for op in BINARY_OPS:
                if result_type(op, [a.type, b.type]) is None:
                    continue
                yield apply_op(op, a, b)
                if both_orders and op not in COMMUTATIVE_OPS and a.text != b.text:
                    yield apply_op(op, b, a)


def _candidates(depth: int, levels: Dict[int, List[Expr]]) -> Iterator[Expr]:
    below = levels[depth - 1]
    yield from _unary_candidates(below)
    if depth == 2:
        yield from _binary_candidates(levels[1], levels[1], both_orders=False)
    else:
        yield from _binary_candidates(below, levels[1], both_orders=True)


class _Level:
    def __init__(self) -> None:
        self.best: Dict[bytes, Expr] = {}
        self.generated = 0
        self.valid = 0

    def offer(self, expr: Expr, sig: bytes) -> None:
        kept = self.best.get(sig)
        if kept is None or (expr.nodes, expr.text) < (kept.nodes, kept.text):
            self.best[sig] = expr


def _run_level(depth: int, levels: Dict[int, List[Expr]], seen: set, ev: VectorEvaluator) -> _Level:
    level = _Level()
    for expr in _candidates(depth, levels):
        level.generated += 1
        values = ev.value(expr)
        if _is_degenerate(values):
            continue
        level.valid += 1
        sig = signature(values)
        if sig not in seen:
            level.offer(expr, sig)
    return level


def enumerate_library(corpus: Corpus, max_depth: int = 3) -> Tuple[List[Entry], GenerationStats]:
    ev = VectorEvaluator(corpus)
    seen: set = set()
    levels: Dict[int, List[Expr]] = {}
    entries: List[Entry] = []
    per_generated, per_unique = [], []
    total_generated = total_valid = 0
    for depth in range(1, max_depth + 1):
        if depth == 1:
            level = _atom_level(corpus, ev)
        else:
            level = _run_level(depth, levels, seen, ev)
        kept = sorted(level.best.values(), key=lambda e: (e.nodes, e.text))
        seen |= set(level.best)
        levels[depth] = kept
        entries += [_entry(corpus, ev, e) for e in kept]
        per_generated.append(level.generated)
        per_unique.append(len(kept))
        total_generated += level.generated
        total_valid += level.valid
    stats = GenerationStats(total_generated, total_valid, len(entries), tuple(per_generated), tuple(per_unique))
    return entries, stats


def _atom_level(corpus: Corpus, ev: VectorEvaluator) -> _Level:
    level = _Level()
    for name in ATOM_NAMES:
        expr = atom(name)
        level.generated += 1
        values = ev.value(expr)
        if _is_degenerate(values):
            continue
        level.valid += 1
        level.offer(expr, signature(values))
    return level


def _entry(corpus: Corpus, ev: VectorEvaluator, expr: Expr) -> Entry:
    return Entry(expr.text, expr.depth, expr.nodes, expr.type, _is_group_constant(corpus, ev.value(expr)))
