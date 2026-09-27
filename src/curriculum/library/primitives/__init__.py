"""Primitive builder modules, one file per primitive family (ADR 0062).

Importing this package registers every primitive into
`src.curriculum.library.registry.REGISTRY` as a side effect (each
`primitives/*.py` module calls `REGISTRY.register(...)` at import time).
"""
from src.curriculum.library.primitives import tiling  # noqa: F401
from src.curriculum.library.primitives import tiling_mirror  # noqa: F401
