"""`select_where` step execution (ADR 0098). Separate from interpreter.py,
which is already large; it needs only the environment's `bound` and `log`."""
from typing import Any

from src.curriculum.spec import vocabulary as vocab
from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._expressions import eval_expr
from src.curriculum.spec._measures import select_where_items
from src.curriculum.spec._region_value import RegionValue


def exec_select_where(step: vocab.SelectWhere, env: Any) -> None:
    items = eval_expr(step.list_ref, env)
    if not isinstance(items, list) or not all(isinstance(i, RegionValue) for i in items):
        raise InterpreterError("select_where: list_ref is not a list of regions")
    value = eval_expr(step.value, env)
    selected = select_where_items(items, step.measure, value, eval_expr(step.arg, env))
    env.bound[step.result_name] = selected
    env.log(
        "select_where",
        region=step.measure,
        condition=value,
        result=step.result_name,
        value=len(selected),
    )
