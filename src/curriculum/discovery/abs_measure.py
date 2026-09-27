"""Effective depth gain, held-out reuse and exact equivalence of composite
pieces (ADR 0110, Section 4)."""
import statistics
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from src.curriculum.discovery.abs_composite import Composite, Folded, fold, from_mined, unfold
from src.curriculum.discovery.abs_mine import mine
from src.curriculum.discovery.abs_rebuild import rebuild
from src.curriculum.discovery.abs_tokens import Token, base_length, chain_of
from src.curriculum.loader import load_task
from src.curriculum.search.sequence.composition import run_candidate

Chains = Dict[str, Tuple[Token, ...]]


def _node_weight(node) -> int:
    return len(node.tokens) if isinstance(node, Folded) else 1


def _nodes_after(chain: Tuple[Token, ...], composites: Sequence[Composite]) -> Tuple[int, int]:
    """(search nodes, base pieces in the widest node), a `then` marker being free."""
    nodes = [n for n in fold(chain, composites) if not (isinstance(n, Token) and n.role == "then")]
    return len(nodes), max((_node_weight(n) for n in nodes), default=0)


def depth_gain(chains: Chains, composites: Sequence[Composite]) -> Dict[str, float]:
    before = [base_length(c) for c in chains.values()]
    after = [_nodes_after(c, composites) for c in chains.values()]
    return {
        "tasks": len(chains),
        "mean_nodes_before": round(statistics.fmean(before), 3),
        "mean_nodes_after": round(statistics.fmean(n for n, _ in after), 3),
        "max_pieces_per_node": max(w for _, w in after),
        "tasks_using_composite": sum(1 for n, w in after if w > 1),
    }


def held_out_reuse(chains: Chains) -> Dict[str, float]:
    """Leave one task out: does a composite mined from the others fold its chain?"""
    reused = 0
    for task_id, chain in chains.items():
        others = {t: c for t, c in chains.items() if t != task_id}
        _, widest = _nodes_after(chain, from_mined(mine(others)))
        reused += widest > 1
    return {"tasks": len(chains), "reused_by_held_out": reused, "rate": round(reused / max(len(chains), 1), 3)}


def _equal_outputs(a: Any, b: Any, task) -> bool:
    for pair in task.train:
        left, right = run_candidate(a, pair.input)[0], run_candidate(b, pair.input)[0]
        if left != right:
            return False
    return True


def check_equivalence(candidates: Dict[str, Any], composites: Sequence[Composite], data_dir: Path) -> List[str]:
    """Empty list = the folded then unfolded candidate is identical (same
    candidate value, hence same steps) and reproduces every train output."""
    problems = []
    for task_id, candidate in candidates.items():
        rebuilt = rebuild(unfold(fold(chain_of(candidate), composites)))
        if rebuilt != candidate:
            problems.append(f"{task_id}: candidate differs")
            continue
        task = load_task(next(data_dir.rglob(f"{task_id}.json")))
        if not _equal_outputs(candidate, rebuilt, task):
            problems.append(f"{task_id}: outputs differ")
    return problems
