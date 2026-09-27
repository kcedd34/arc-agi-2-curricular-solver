"""Named composite pieces (ADR 0110, Section 4). A composite is declared as an
ordered list of (kind, role, name) parts with free parameter slots; using it
in a chain folds those tokens into one node, and unfolding gives back the
identical tokens. The original pieces are untouched."""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Sequence, Tuple, Union

from src.curriculum.discovery.abs_mine import Key, Mined
from src.curriculum.discovery.abs_tokens import Token


class Composite(NamedTuple):
    name: str
    parts: Tuple[Key, ...]
    tasks: Tuple[str, ...]

    def spec(self) -> dict:
        return {
            "name": self.name,
            "parts": [{"kind": k, "role": r, "piece": n} for k, r, n in self.parts],
            "slots": "each part keeps its own free parameters",
            "expands_to": "the parts in order, unchanged",
            "source_tasks": list(self.tasks),
        }


class Folded(NamedTuple):
    composite: str
    tokens: Tuple[Token, ...]


Node = Union[Token, Folded]


def composite_name(parts: Sequence[Key]) -> str:
    label = "+".join(f"{r}={n}" for _, r, n in parts)
    digest = hashlib.sha1(json.dumps(list(parts)).encode("utf-8")).hexdigest()[:8]
    return f"abs[{label[:70]}]-{digest}"


def from_mined(mined: Sequence[Mined]) -> List[Composite]:
    return [Composite(composite_name(m.keys), m.keys, m.tasks) for m in mined]


def _match_at(keys: List[Key], start: int, composite: Composite) -> bool:
    n = len(composite.parts)
    return tuple(keys[start : start + n]) == composite.parts


def _longest(keys: List[Key], start: int, ordered: List[Composite]):
    return next((c for c in ordered if _match_at(keys, start, c)), None)


def fold(chain: Tuple[Token, ...], composites: Sequence[Composite]) -> List[Node]:
    """Greedy left to right, longest composite first."""
    ordered = sorted(composites, key=lambda c: -len(c.parts))
    keys = [t.key for t in chain]
    nodes: List[Node] = []
    i = 0
    while i < len(chain):
        hit = _longest(keys, i, ordered)
        if hit is None:
            nodes.append(chain[i])
            i += 1
        else:
            nodes.append(Folded(hit.name, chain[i : i + len(hit.parts)]))
            i += len(hit.parts)
    return nodes


def unfold(nodes: Sequence[Node]) -> Tuple[Token, ...]:
    tokens: List[Token] = []
    for node in nodes:
        tokens.extend(node.tokens if isinstance(node, Folded) else [node])
    return tuple(tokens)


def write_library(composites: Sequence[Composite], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([c.spec() for c in composites], indent=1), encoding="utf-8")
