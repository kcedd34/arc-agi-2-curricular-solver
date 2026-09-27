"""Scalar (canonical) evaluator of generated measures (ADR 0110).

`generated_measure(region, text)` is what the interpreter runs for a measure
named `gen:<text>`; the numpy evaluator used by discovery must agree with it
exactly (checked by a test). Results are cached in `region.memo`; group level
values (over every region of the partition) in `region.ctx.shared`.
"""
from collections import Counter
from typing import List

from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._gen_atoms import MAX_SIBLINGS, atom_value
from src.curriculum.spec._gen_expr import Expr, parse
from src.curriculum.spec._region_value import RegionValue

PREFIX = "gen:"


def generated_measure(region: RegionValue, text: str) -> int:
    return _eval(parse(text), region)


def _eval(expr: Expr, region: RegionValue) -> int:
    key = PREFIX + expr.text
    if key in region.memo:
        return _unwrap(region.memo[key])
    try:
        value = _compute(expr, region)
    except InterpreterError as exc:
        region.memo[key] = exc
        raise
    region.memo[key] = value
    return value


def _unwrap(cached):
    if isinstance(cached, InterpreterError):
        raise cached
    return cached


def _compute(expr: Expr, region: RegionValue) -> int:
    if not expr.args:
        return atom_value(region, expr.op)
    if expr.op in _BINARY:
        return _BINARY[expr.op](_eval(expr.args[0], region), _eval(expr.args[1], region))
    return _group_value(expr, region)


def _ratio(a: int, b: int) -> int:
    if b == 0:
        raise InterpreterError("ratio: division by zero")
    return a // b


_BINARY = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "ratio": _ratio,
    "eq": lambda a, b: 1 if a == b else 0,
    "lt": lambda a, b: 1 if a < b else 0,
}


def _group_values(expr: Expr, region: RegionValue) -> List[int]:
    ctx = region.ctx
    if ctx is None:
        raise InterpreterError(f"{expr.op}: region has no partition context")
    if len(ctx.regions) > MAX_SIBLINGS:
        raise InterpreterError(f"{expr.op}: more than {MAX_SIBLINGS} regions")
    return [_eval(expr.args[0], s) for s in ctx.regions]


def _mode(values: List[int]) -> int:
    ranked = Counter(values).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise InterpreterError("gmode: tie for the most frequent value")
    return ranked[0][0]


def _group_value(expr: Expr, region: RegionValue) -> int:
    values = _group_values(expr, region)
    own = values[region.ctx.index]
    if expr.op == "rank":
        return len({v for v in values if v < own})
    if expr.op == "same":
        return sum(1 for v in values if v == own)
    return {"gmin": min, "gmax": max, "gsum": sum, "gmode": _mode}[expr.op](values)
