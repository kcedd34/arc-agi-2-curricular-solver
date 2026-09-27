"""Vector evaluation of expression trees over a corpus, with memoisation of
shallow nodes (ADR 0110). Depth-3 nodes are never operands, so they are not
cached: only their signature or selection effect is kept."""
from typing import Dict

from src.curriculum.discovery.corpus import Corpus, Values
from src.curriculum.discovery.vector_ops import apply_op
from src.curriculum.spec._gen_expr import Expr, parse

CACHE_MAX_DEPTH = 2


class VectorEvaluator:
    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus
        self._cache: Dict[str, Values] = {}

    def value(self, expr: Expr) -> Values:
        cached = self._cache.get(expr.text)
        if cached is not None:
            return cached
        if not expr.args:
            result = self.corpus.atom_values(expr.op)
        else:
            result = apply_op(self.corpus, expr.op, tuple(self.value(a) for a in expr.args))
        if expr.depth <= CACHE_MAX_DEPTH:
            self._cache[expr.text] = result
        return result

    def value_of_text(self, text: str) -> Values:
        return self.value(parse(text))
