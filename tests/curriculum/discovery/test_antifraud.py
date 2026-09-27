from src.curriculum.discovery.antifraud import judge
from src.curriculum.discovery.antifraud_checks import (
    decorative_selection,
    identical_branches,
    ignored_pair,
    selection_chance,
    size_coincidence,
)
from src.curriculum.discovery.augment import GEOMETRIC
from src.curriculum.discovery.equivariance import check_equivariance, demos_invariant
from src.curriculum.library.derived.model import Action, DerivedComposition, ParamSource, RegionSpec, Selection, ValueRule
from src.curriculum.library.derived.search import verified_derived_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair

SPEC = RegionSpec("objects", 4, True, 0)
LAYOUTS = [
    [(0, 0, 3, 3), (5, 5, 1, 2), (8, 1, 1, 1)],
    [(1, 1, 2, 4), (6, 6, 2, 2), (0, 8, 1, 1)],
    [(2, 2, 4, 4), (0, 0, 1, 1), (8, 7, 2, 2)],
    [(0, 0, 2, 2), (4, 4, 3, 3), (9, 0, 1, 1)],
]


def _paint(objects, recolored):
    grid = [[0] * 10 for _ in range(10)]
    for index, (r, c, h, w) in enumerate(objects):
        for i in range(h):
            for j in range(w):
                grid[r + i][c + j] = 2 if index in recolored else 5
    return grid


def _task(recolor_rule) -> Task:
    pairs = []
    for objects in LAYOUTS:
        areas = [h * w for _, _, h, w in objects]
        pairs.append(TrainPair(_paint(objects, set()), _paint(objects, recolor_rule(areas))))
    return Task("syn", pairs, [])


def _largest(areas):
    return {areas.index(max(areas))}


def _recolor(selection):
    return DerivedComposition(SPEC, (Action("recolor_selected", ParamSource("literal", 2), selection),))


LARGEST = Selection("size", ValueRule("max"))


def test_largest_object_rule_is_accepted():
    task = _task(_largest)
    assert judge(task, _recolor(LARGEST), effects_tested=5).accepted


def test_decorative_selection_detected_when_every_object_changes():
    task = _task(lambda areas: set(range(len(areas))))
    assert decorative_selection(task, _recolor(LARGEST)) is not None


def test_genuine_selection_is_not_decorative():
    assert decorative_selection(_task(_largest), _recolor(LARGEST)) is None


def test_ignored_pair_flags_single_informative_pair():
    task = _task(_largest)
    quiet = Task("syn", [task.train[0]] + [TrainPair(p.input, p.input) for p in task.train[1:]], [])
    assert ignored_pair(quiet, _recolor(LARGEST)) is not None
    assert ignored_pair(task, _recolor(LARGEST)) is None


def test_identical_branches_detects_degenerate_table():
    table = ParamSource("table", (("size",), ((((1,), 3)), ((2,), 3))))
    action = Action("recolor_selected", table, None)
    assert identical_branches(_task(_largest), DerivedComposition(SPEC, (action,))) is not None


def test_chance_is_product_of_binomials():
    chance = selection_chance(_task(_largest), _recolor(LARGEST))
    assert abs(chance - (1 / 3) ** 4) < 1e-12


def test_size_coincidence_scales_with_effects_tested():
    task = _task(_largest)
    assert size_coincidence(task, _recolor(LARGEST), 1) is None
    assert size_coincidence(task, _recolor(LARGEST), 500) is not None


def _closed_task(task: Task) -> Task:
    pairs = [TrainPair(fn(p.input), fn(p.output)) for p in task.train for fn in [lambda g: g] + list(GEOMETRIC.values())]
    return Task(task.task_id, pairs, [])


def _table_verdicts(task: Task):
    return [
        check_equivariance(task, composition)
        for composition, _ in verified_derived_candidates_with_predictions(task)
        if composition.actions[0].param is not None and composition.actions[0].param.kind == "table"
    ]


def test_filter_rejects_when_demos_are_closed_and_transformed_rule_fails(monkeypatch):
    monkeypatch.setattr("src.curriculum.discovery.equivariance._matches", lambda composition, task: task.task_id == "closed")
    closed = _closed_task(_task(_largest))
    verdict = check_equivariance(closed._replace(task_id="closed-x"), _recolor(LARGEST))
    assert not verdict.passed and set(GEOMETRIC) <= set(verdict.failed)


def test_filter_does_not_apply_when_demos_are_not_closed_under_symmetry():
    task = _task(_largest)
    assert not demos_invariant(task, GEOMETRIC["rot90"])
    assert all(v.passed for v in _table_verdicts(task))


def test_demos_invariant_needs_every_transformed_pair_present():
    task = _closed_task(_task(_largest))
    assert all(demos_invariant(task, fn) for fn in GEOMETRIC.values())


def test_literal_colour_rule_survives_colour_permutation():
    assert check_equivariance(_task(_largest), _recolor(LARGEST)).passed


def test_decorative_check_skips_actions_that_need_a_selection(monkeypatch):
    def _cannot_lower(composition, task):
        raise AttributeError("'NoneType' object has no attribute 'rule'")

    monkeypatch.setattr("src.curriculum.discovery.antifraud_checks._matches", _cannot_lower)
    composition = DerivedComposition(
        RegionSpec("objects", 8, True, 0),
        (Action("stamp", ParamSource("literal", 3), Selection("size", ValueRule("max"))),),
    )
    assert decorative_selection(_task(lambda a: a), composition) is None
