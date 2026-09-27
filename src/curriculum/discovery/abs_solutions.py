"""Re-derive the top accepted hypothesis of every solved task as a token chain
(ADR 0110, Section 4). Solutions are not stored by the solver, so they are
recomputed with the ordinary search and cached."""
import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.curriculum.discovery.abs_tokens import Token, chain_of
from src.curriculum.discovery.library_store import LIBRARY_DIR
from src.curriculum.loader import load_task
from src.curriculum.search.all_candidates import all_verified_pairs

STATE = Path("outputs/curriculum/state.json")
CACHE = LIBRARY_DIR / "solution-candidates-v1.pkl"
DATA = Path("data/ARC-AGI-2/data")


def solved_task_ids() -> list:
    return sorted(json.loads(STATE.read_text(encoding="utf-8"))["solved_tasks"])


def top_candidate(task_id: str) -> Optional[Any]:
    path = next(DATA.rglob(f"{task_id}.json"))
    found = all_verified_pairs(load_task(path))
    for pairs in (found.main, found.objects, found.sequences):
        if pairs:
            return pairs[0][0]
    return None


def collect_candidates(task_ids) -> Dict[str, Any]:
    found = {}
    for task_id in task_ids:
        candidate = top_candidate(task_id)
        if candidate is not None:
            found[task_id] = candidate
    return found


def load_candidates(refresh: bool = False) -> Dict[str, Any]:
    if CACHE.exists() and not refresh:
        return pickle.loads(CACHE.read_bytes())
    found = collect_candidates(solved_task_ids())
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps(found))
    return found


def chains_of(candidates: Dict[str, Any]) -> Dict[str, Tuple[Token, ...]]:
    return {task_id: chain_of(c) for task_id, c in candidates.items()}
