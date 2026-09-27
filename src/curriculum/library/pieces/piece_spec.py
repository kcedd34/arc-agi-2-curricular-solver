"""Shared piece-registry record used by layout/selector/content pieces
(RN-CUR-33 step 2, docs/curriculum/tasks/stage-3-prep.md).

Kept separate from `library/registry.py`'s `Primitive`/`PrimitiveRegistry`,
whose `.build` only takes the search-enumerated `**kwargs`: a piece
builder also needs fixed, composition-time context (the loop element
name, the input ref, the selected/not-selected content) that is not part
of the search-enumerated params, so `search/compose.py` calls each piece
kind's builder directly instead of through a validating `.build` method.
"""
from typing import Any, Callable, NamedTuple, Sequence


class PieceSpec(NamedTuple):
    name: str
    params: Sequence[str]
    builder: Callable[..., Any]
