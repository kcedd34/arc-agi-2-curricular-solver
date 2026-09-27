"""Primitive registry: named, parametrized step-sequence builders (ADR 0062).

Per ADR 0062's "Design principle" and "Governance > Forbidden pattern"
sections, a library primitive is just a Python function that returns a
List[vocab.Step] built from the existing vocabulary.py dataclasses; this
module only catalogues those builders by name, it holds no execution
logic of its own and never imports interpreter.py (RN-CUR-14 only
constrains spec/*.py, but there is no reason for this module to depend
on the interpreter either).
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Sequence

from src.curriculum.spec import vocabulary as vocab

PrimitiveBuilder = Callable[..., List[vocab.Step]]


@dataclass(frozen=True)
class Primitive:
    name: str
    params: Sequence[str]
    builder: PrimitiveBuilder
    description: str

    def build(self, **kwargs: Any) -> List[vocab.Step]:
        missing = set(self.params) - set(kwargs)
        if missing:
            raise ValueError(f"{self.name}: missing params {sorted(missing)}")
        return self.builder(**kwargs)


class PrimitiveRegistry:
    def __init__(self) -> None:
        self._primitives: Dict[str, Primitive] = {}

    def register(self, primitive: Primitive) -> None:
        if primitive.name in self._primitives:
            raise ValueError(f"primitive already registered: {primitive.name}")
        self._primitives[primitive.name] = primitive

    def get(self, name: str) -> Primitive:
        if name not in self._primitives:
            raise KeyError(f"unknown primitive: {name}")
        return self._primitives[name]

    def names(self) -> List[str]:
        return sorted(self._primitives)

    def build(self, name: str, **kwargs: Any) -> List[vocab.Step]:
        return self.get(name).build(**kwargs)


REGISTRY = PrimitiveRegistry()
