"""Budget of the two-rule sequence stage (ADR 0101): a deterministic count
of work units (interpreter runs weighted by input cells) is the primary limit; the wall-clock deadline is only a
safety net and every cut by it is reported."""
from typing import Any, List, NamedTuple, Optional

SEQUENCE_UNIT_BUDGET: Optional[int] = 60_000_000
SEQUENCE_DEADLINE_SECONDS = 300.0


class SequenceOutcome(NamedTuple):
    pairs: List[Any]
    units_used: int
    budget_hit: bool
    deadline_hit: bool
