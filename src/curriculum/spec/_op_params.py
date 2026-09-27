"""Parametric transform operands (ADR 0107).

A transform's colour and shift fields may hold an `Expr` (a derived
parameter) instead of a literal. They are resolved against the environment
right before the op is applied, so the op itself keeps operating on plain
integers and stays unaware of the derivation layer.
"""
import dataclasses
from functools import lru_cache
from typing import Any, Tuple

PARAM_FIELDS = ("color", "dr", "dc")


@lru_cache(maxsize=None)
def _param_names(op_type: type) -> Tuple[str, ...]:
    if not dataclasses.is_dataclass(op_type):
        return ()
    return tuple(f.name for f in dataclasses.fields(op_type) if f.name in PARAM_FIELDS)


def resolve_op_params(op: Any, env: Any) -> Any:
    names = _param_names(type(op))
    if not names:
        return op
    updates = {}
    for name in names:
        value = getattr(op, name)
        if not isinstance(value, int):
            from src.curriculum.spec._expressions import eval_expr

            updates[name] = eval_expr(value, env)
    return dataclasses.replace(op, **updates) if updates else op
