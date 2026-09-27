"""Stratified, seeded sample of arc2_only training tasks nobody has taught or hand-solved."""
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Set

from src.curriculum.discovery.loop_tasks import arc2_only_task_ids, taught_task_ids
from src.curriculum.program_probe.census import DRAW, ERASE, MIXED, MOVE, RECOLOR, SHAPE, task_category
from src.curriculum.program_probe.prompt import PLAIN, build_prompt
from src.curriculum.program_probe.verify import TRAINING_DIR, load_pairs

QUOTA = {MIXED: 8, SHAPE: 7, DRAW: 6, RECOLOR: 5, MOVE: 4}
MAX_PROMPT_CHARS = 3200
SEED = 24
MECHANISMS = Path("docs/curriculum/arc2-mechanisms.md")
SAMPLE_FILE = Path("outputs/curriculum/program_probe/sample.json")
ID_RE = re.compile(r"\b[0-9a-f]{8}\b")


def cited_ids(path: Path = MECHANISMS) -> Set[str]:
    return set(ID_RE.findall(path.read_text(encoding="utf-8"))) if path.exists() else set()


def eligible_ids(directory: Path = TRAINING_DIR) -> List[str]:
    blocked = taught_task_ids() | cited_ids()
    return [t for t in arc2_only_task_ids(directory) if t not in blocked]


def describe(task_id: str, directory: Path = TRAINING_DIR) -> dict:
    pairs = load_pairs(task_id, directory)["train"]
    prompt = build_prompt(pairs, PLAIN)
    return {"task_id": task_id, "category": task_category(pairs), "prompt_chars": len(prompt.base_text)}


def by_category(ids: List[str], directory: Path = TRAINING_DIR) -> Dict[str, List[dict]]:
    groups: Dict[str, List[dict]] = {}
    for task_id in ids:
        info = describe(task_id, directory)
        if info["prompt_chars"] <= MAX_PROMPT_CHARS:
            groups.setdefault(info["category"], []).append(info)
    return groups


def _fill(groups: Dict[str, List[dict]], rng: random.Random) -> List[dict]:
    chosen: List[dict] = []
    for category, quota in QUOTA.items():
        pool = sorted(groups.get(category, []), key=lambda i: i["task_id"])
        chosen += rng.sample(pool, min(quota, len(pool)))
    return chosen


def _top_up(chosen: List[dict], groups: Dict[str, List[dict]], rng: random.Random) -> List[dict]:
    taken = {i["task_id"] for i in chosen}
    rest = sorted((i for g in groups.values() for i in g if i["task_id"] not in taken), key=lambda i: i["task_id"])
    missing = sum(QUOTA.values()) - len(chosen)
    return chosen + rng.sample(rest, max(0, min(missing, len(rest))))


def build_sample(directory: Path = TRAINING_DIR) -> List[dict]:
    rng = random.Random(SEED)
    groups = by_category(eligible_ids(directory), directory)
    return sorted(_top_up(_fill(groups, rng), groups, rng), key=lambda i: i["task_id"])


def save_sample(sample: List[dict], path: Path = SAMPLE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sample, indent=1), encoding="utf-8")


def load_sample(path: Path = SAMPLE_FILE) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))
