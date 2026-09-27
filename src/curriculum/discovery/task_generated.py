"""Generated selections for one task and region kind (ADR 0110).

Every library property (in library order) is evaluated over the train regions
of the task; a rule becomes a `Selection` only when its selected set is new
(not equal to a handwritten selection or an earlier generated one), is a
proper subset somewhere, and covers every changed cell. The library order is
the only thing a budget cuts, never the content of a property."""
from functools import lru_cache
from typing import List, Optional, Sequence, Set

import numpy as np

from src.curriculum.discovery.corpus import Corpus
from src.curriculum.discovery.cover_check import CoverCheck
from src.curriculum.discovery.evaluator import VectorEvaluator
from src.curriculum.discovery.library_store import load_library
from src.curriculum.discovery import session
from src.curriculum.discovery.profile import profile_key
from src.curriculum.discovery.selection_masks import is_proper_somewhere, selection_masks
from src.curriculum.library.derived.facts import train_regions
from src.curriculum.library.derived.model import RegionSpec, Selection, ValueRule
from src.curriculum.library.derived.selection_probe import select
from src.curriculum.library.objects._task_cache import cached_for_task
from src.curriculum.loader import Task
from src.curriculum.spec._gen_atoms import MAX_SIBLINGS
from src.curriculum.spec._generated import PREFIX

ENTRY_BUDGET = 200_000
MAX_SELECTIONS = 400


@lru_cache(maxsize=1)
def _entries():
    return load_library().entries


def _handwritten_mask(task: Task, spec: RegionSpec, regions, sel: Selection) -> Optional[bytes]:
    mask: List[bool] = []
    for pair, regs in zip(task.train, regions):
        picked = select(sel, regs, pair.input, spec)
        if picked is None:
            return None
        chosen = {id(r) for r in picked}
        mask += [id(r) in chosen for r in regs]
    return np.packbits(np.array(mask, dtype=bool)).tobytes()


def _handwritten_effects(task: Task, spec: RegionSpec, regions, handwritten: List[Selection]) -> Set[bytes]:
    effects = {_handwritten_mask(task, spec, regions, sel) for sel in handwritten}
    effects.discard(None)
    return effects


def _accept(corpus: Corpus, cover: CoverCheck, seen: Set[bytes], mask: np.ndarray) -> bool:
    key = np.packbits(mask).tobytes()
    if key in seen or not is_proper_somewhere(corpus, mask):
        return False
    seen.add(key)
    return cover.covers(mask)


def _budget_prefix(task: Task) -> Sequence[int]:
    """Library positions to evaluate for this task, in enumeration order."""
    registry = session.active_registry()
    if registry is None:
        return range(min(ENTRY_BUDGET, len(_entries())))
    profile = cached_for_task(task, "discovery_profile", lambda: profile_key(task))
    return registry.ordered_indices(profile)[:ENTRY_BUDGET]


def _collect(task: Task, corpus: Corpus, cover: CoverCheck, seen: Set[bytes]) -> List[Selection]:
    evaluator = VectorEvaluator(corpus)
    found: List[Selection] = []
    entries = _entries()
    prefix = _budget_prefix(task)
    used = 0
    for position in prefix:
        used += 1
        entry = entries[position]
        values = evaluator.value_of_text(entry.text)
        for op, literal, mask in selection_masks(corpus, values, entry.type):
            if _accept(corpus, cover, seen, mask):
                found.append(Selection(PREFIX + entry.text, ValueRule(op, literal=literal)))
        if len(found) >= MAX_SELECTIONS:
            break
    session.note_evaluated(list(prefix)[:used])
    session.note_effects(len(seen))
    return found


def generated_selections(task: Task, spec: RegionSpec, handwritten: List[Selection]) -> List[Selection]:
    regions = train_regions(task, spec)
    if regions is None or any(len(r) > MAX_SIBLINGS for r in regions):
        return []
    corpus = Corpus(regions)
    cover = CoverCheck(task, corpus)
    if corpus.n_groups != len(regions) or not cover.has_changes:
        return []
    return _collect(task, corpus, cover, _handwritten_effects(task, spec, regions, handwritten))
