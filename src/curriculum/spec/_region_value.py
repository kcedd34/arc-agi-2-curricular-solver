"""Runtime region value produced by partition()/transform() (ADR 0062).

Kept separate from `_expressions.py` and `_regions.py` to avoid a circular
import between them (both need this type, `_regions.py` also needs
`_expressions.py`'s `eval_expr`).
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.curriculum.grid import Grid


@dataclass
class RegionContext:
    """The partition a region came from (ADR 0110): sibling regions, the
    region's own index and the source grid dimensions. Generated properties
    that compare a region with its siblings read it; `shared` caches group
    level results once per partition."""

    regions: List["RegionValue"]
    index: int
    dims: Tuple[int, int]
    shared: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class RegionValue:
    row0: int
    col0: int
    rows: int
    cols: int
    cells: Grid
    # Values already computed from this region (ADR 0090): a cache of results,
    # never a source of logic. `cells` is never mutated after construction.
    memo: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)
    ctx: Optional[RegionContext] = field(default=None, repr=False, compare=False)
