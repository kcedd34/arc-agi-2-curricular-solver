"""Stamp/copy signature on train pairs (Round 21): output changes are mostly
translated copies of input objects. A heuristic label, spot-checked, never solver code."""
from collections import Counter
from typing import Dict, List, Set, Tuple

from src.curriculum.diagnostics.stamp_copies import find_copies, original_kept, places
from src.curriculum.diagnostics.stamp_objects import components

MIN_COVERAGE = 0.6


def _changed(inp, out) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(len(inp)) for c in range(len(inp[0])) if inp[r][c] != out[r][c]]


def _backgrounds(grid) -> List[int]:
    return [v for v, _ in Counter(v for row in grid for v in row).most_common(2)]


def _explain(inp, out, bg: int, changed: List) -> Tuple[Set, int, bool]:
    covered, copies, kept = set(), 0, False
    for obj in components(inp, bg):
        found = find_copies(inp, out, obj, changed, bg)
        for offset in found:
            covered |= set(places(obj, offset))
            copies += 1
        kept = kept or (bool(found) and original_kept(out, obj))
    return covered & set(changed), copies, kept


def pair_signature(pair: Dict) -> Dict:
    inp, out = pair["input"], pair["output"]
    if len(inp) != len(out) or len(inp[0]) != len(out[0]):
        return {"stamp": False, "why": "shape"}
    changed = _changed(inp, out)
    if not changed:
        return {"stamp": False, "why": "identical"}
    best = {"stamp": False, "coverage": 0.0, "copies": 0}
    for bg in _backgrounds(inp):
        covered, copies, kept = _explain(inp, out, bg, changed)
        coverage = len(covered) / len(changed)
        if coverage > best["coverage"]:
            best = {"coverage": coverage, "copies": copies, "kept": kept,
                    "structural": copies >= 2 or kept, "stamp": coverage >= MIN_COVERAGE and (copies >= 2 or kept)}
    return best


def task_signature(train: List[Dict]) -> Dict:
    pairs = [pair_signature(p) for p in train]
    coverage = min(p.get("coverage", 0.0) for p in pairs)
    structural = all(p.get("structural", False) for p in pairs)
    return {"stamp": all(p["stamp"] for p in pairs), "min_coverage": round(coverage, 3), "structural": structural,
            "stamp_pairs": sum(p["stamp"] for p in pairs), "pairs": len(pairs)}
