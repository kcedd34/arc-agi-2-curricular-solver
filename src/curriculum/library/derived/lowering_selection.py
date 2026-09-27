"""Selection lowering shared by the derived actions (ADR 0107): the rule value
is bound, then `SelectWhere` keeps the regions whose measure equals it."""
from typing import List, Optional

from src.curriculum.library.derived import expressions as ex
from src.curriculum.library.derived.model import Selection
from src.curriculum.spec import vocabulary as vocab


def selection_steps(
    sel: Selection, source: str, result: str, tag: str, background: int, target: Optional[str] = None
) -> List[vocab.Step]:
    value = ex.rule_value(sel, source, background, target)
    arg = ex.measure_arg(sel.measure, target)
    if sel.rule.op == "equals":
        return [vocab.SelectWhere(vocab.Ref(source), sel.measure, value, result, arg)]
    bound = f"m_{tag}"
    return [
        vocab.Bind(bound, value),
        vocab.SelectWhere(vocab.Ref(source), sel.measure, vocab.Ref(bound), result, arg),
    ]
