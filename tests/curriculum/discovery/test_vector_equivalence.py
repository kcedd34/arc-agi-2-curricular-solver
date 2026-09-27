"""The numpy vector evaluator must agree exactly with the canonical scalar
`gen:` evaluator on every valid region, and flag exactly the same regions as
invalid (ADR 0110)."""
import random

import numpy as np

from src.curriculum.discovery.corpus import Corpus
from src.curriculum.discovery.corpus_sources import partitions_of
from src.curriculum.discovery.enumerate_gen import enumerate_library
from src.curriculum.discovery.evaluator import VectorEvaluator
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._gen_atoms import INT
from src.curriculum.spec._generated import generated_measure


def _random_grid(rng: random.Random):
    h, w = rng.randint(3, 9), rng.randint(3, 9)
    colors = rng.sample(range(1, 10), rng.randint(1, 3))
    return [[rng.choice(colors) if rng.random() < 0.3 else 0 for _ in range(w)] for _ in range(h)]


def _corpus(seed: int, n_grids: int = 12) -> Corpus:
    rng = random.Random(seed)
    parts = []
    for _ in range(n_grids):
        parts += partitions_of(_random_grid(rng))
    return Corpus(parts)


def _scalar(region, text):
    try:
        return generated_measure(region, text), False
    except InterpreterError:
        return 0, True


def _check(corpus: Corpus, ev: VectorEvaluator, text: str) -> None:
    vals, bad = ev.value_of_text(text)
    for i, region in enumerate(corpus.regions):
        value, invalid = _scalar(region, text)
        assert bool(bad[i]) == invalid, (text, i)
        if not invalid:
            assert int(vals[i]) == value, (text, i, int(vals[i]), value)


def test_depth_two_library_matches_scalar():
    corpus = _corpus(1)
    assert corpus.n > 50
    entries, _ = enumerate_library(corpus, max_depth=2)
    ev = VectorEvaluator(corpus)
    for entry in entries[:1500]:
        _check(corpus, ev, entry.text)


def test_random_depth_three_matches_scalar():
    corpus = _corpus(2)
    entries, _ = enumerate_library(corpus, max_depth=2)
    ev = VectorEvaluator(corpus)
    rng = random.Random(3)
    depth2 = [e.text for e in entries if e.depth == 2 and e.type == INT]
    atoms = [e.text for e in entries if e.depth == 1 and e.type == INT]
    for _ in range(300):
        op = rng.choice(["add", "sub", "ratio", "lt", "eq"])
        _check(corpus, ev, f"{op}({rng.choice(depth2)},{rng.choice(atoms)})")


def test_signature_is_deterministic():
    corpus = _corpus(4)
    first, stats1 = enumerate_library(corpus, max_depth=2)
    second, stats2 = enumerate_library(_corpus(4), max_depth=2)
    assert [e.text for e in first] == [e.text for e in second]
    assert stats1 == stats2
    assert np.all(corpus.counts > 0)
