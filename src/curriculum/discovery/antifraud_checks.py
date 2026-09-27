"""The four automated antifraud checks (ADR 0110), each a pure function of a
task and a verified composition. A check returns a reason string when the hit
looks fraudulent, None when it passes."""
from math import comb
from typing import Iterator, List, Optional

from src.curriculum.library.derived.facts import task_changes, train_regions
from src.curriculum.library.derived.lowering import build_derived_steps
from src.curriculum.library.derived.model import Action, DerivedComposition, Selection
from src.curriculum.library.derived.selection_probe import select
from src.curriculum.loader import Task

MIN_INFORMATIVE_PAIRS = 2


def _matches(composition: DerivedComposition, task: Task) -> bool:
    from src.curriculum.library.objects.object_search import _matches_all_train_pairs

    return _matches_all_train_pairs(build_derived_steps(composition), task)


def _replace_selection(composition: DerivedComposition, index: int) -> DerivedComposition:
    actions = list(composition.actions)
    old = actions[index]
    actions[index] = Action(old.name, old.param, None, old.target, old.extra)
    return DerivedComposition(composition.region, tuple(actions))


def _matches_without_selection(composition: DerivedComposition, index: int, task: Task) -> bool:
    """Actions that need a selection to be expressible (stamp) cannot run on
    every region, so dropping it proves nothing."""
    try:
        return _matches(_replace_selection(composition, index), task)
    except AttributeError:
        return False


def decorative_selection(task: Task, composition: DerivedComposition) -> Optional[str]:
    """A selection is decorative when the same action applied to every region
    still reproduces all train outputs."""
    for index, action in enumerate(composition.actions):
        if action.selection is not None and _matches_without_selection(composition, index, task):
            return f"selection of action {index} is decorative"
    return None


def ignored_pair(task: Task, composition: DerivedComposition) -> Optional[str]:
    """A hypothesis is only tested by the pairs that change something."""
    informative = sum(1 for change in task_changes(task) if change.cells)
    if informative < MIN_INFORMATIVE_PAIRS:
        return f"only {informative} train pair(s) change anything"
    return None


def _degenerate_table(action: Action) -> bool:
    if action.param is None or action.param.kind not in ("table", "shift"):
        return False
    _, table = action.param.value
    values = {value for _, value in table}
    return len(table) >= 2 and len(values) == 1


def identical_branches(task: Task, composition: DerivedComposition) -> Optional[str]:
    """Branches that do the same thing: a table whose keys all map to one
    value, or two actions that differ only in the selection."""
    seen = set()
    for action in composition.actions:
        if _degenerate_table(action):
            return "table with identical branches"
        key = (action.name, action.param)
        if key in seen:
            return "two actions with identical effect"
        seen.add(key)
    return None


def _selections(composition: DerivedComposition) -> Iterator[Selection]:
    for action in composition.actions:
        if action.selection is not None:
            yield action.selection


def selection_chance(task: Task, composition: DerivedComposition) -> float:
    """Probability that a uniformly random selection of the same sizes matches
    every pair: the product of 1/C(n, k) over selections and pairs."""
    regions = train_regions(task, composition.region)
    if regions is None:
        return 1.0
    chance = 1.0
    for selection in _selections(composition):
        for pair, regs in zip(task.train, regions):
            picked = select(selection, regs, pair.input, composition.region)
            chance /= comb(len(regs), len(picked)) if picked else 1
    return chance


def size_coincidence(task: Task, composition: DerivedComposition, effects_tested: int) -> Optional[str]:
    """Expected number of chance matches among the effects tested, at least 1."""
    if not any(True for _ in _selections(composition)):
        return None
    expected = selection_chance(task, composition) * max(1, effects_tested)
    if expected >= 1.0:
        return f"expected chance matches {expected:.2f} >= 1"
    return None


def all_reasons(task: Task, composition: DerivedComposition, effects_tested: int) -> List[str]:
    checks = (
        decorative_selection(task, composition),
        ignored_pair(task, composition),
        identical_branches(task, composition),
        size_coincidence(task, composition, effects_tested),
    )
    return [reason for reason in checks if reason]
