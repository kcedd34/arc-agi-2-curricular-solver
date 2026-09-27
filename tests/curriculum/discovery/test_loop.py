"""Learned prioritization and the loop plumbing (ADR 0110): credit only from
accepted hits, positions follow the registry order, scoring uses the two
attempt rule on distinct accepted hypotheses."""
from src.curriculum.discovery import session
from src.curriculum.discovery.library_index import generated_texts
from src.curriculum.discovery.loop_batches import credit_registry, split_batches
from src.curriculum.discovery.loop_report import batch_series
from src.curriculum.discovery.loop_scoring import _distinct_attempts
from src.curriculum.discovery.registry import Registry
from src.curriculum.discovery.run_task import Hit, TaskRun, enumeration_positions

PROFILE = "11111"


def _hit(indices, accepted=True, generated=True, predictions=None, positions=None):
    return Hit("d", generated, indices, positions or [], accepted, [], predictions or [[[1]]])


def _run(task_id, hits, units=10):
    return TaskRun(task_id, PROFILE, 1.0, units, hits)


def test_generated_texts_reads_nested_expressions():
    text = "fill on [gen:eq(add(size,1),height) == 1]; recolor on [gen:colors == total(size)]"
    assert generated_texts(text) == ["eq(add(size,1),height)", "colors"]


def test_only_accepted_hits_are_credited():
    registry = Registry(30)
    credit_registry(registry, [_run("a", [_hit([5]), _hit([6], accepted=False)])])
    assert registry.hits[5] == 1 and registry.hits[6] == 0
    assert registry.ordered_indices(PROFILE)[0] == 5


def test_crediting_is_independent_of_batch_order():
    runs = [_run("b", [_hit([9])]), _run("a", [_hit([7])])]
    first, second = Registry(30), Registry(30)
    credit_registry(first, runs)
    credit_registry(second, list(reversed(runs)))
    assert list(first.ordered_indices(PROFILE)) == list(second.ordered_indices(PROFILE))


def test_positions_follow_the_registry_order():
    registry = Registry(30)
    registry.record_task(PROFILE, [1, 2], [20])
    session.set_registry(registry)
    try:
        assert enumeration_positions([20, 0], PROFILE) == [0, 1]
    finally:
        session.set_registry(None)


def test_learning_lowers_the_position_series():
    registry = Registry(30)
    first = [_run("a", [_hit([20], positions=[20])])]
    credit_registry(registry, first)
    later = [_run("b", [_hit([20], positions=[int(list(registry.ordered_indices(PROFILE)).index(20))])])]
    series = batch_series([first, later])
    assert series[0]["mean_position"] > series[1]["mean_position"]


def test_attempts_are_distinct_accepted_hypotheses_capped_at_two():
    hits = [_hit([1], predictions=[[[1]]]), _hit([2], predictions=[[[1]]]), _hit([3], accepted=False),
            _hit([4], predictions=[[[2]]]), _hit([5], predictions=[[[3]]])]
    assert [h.indices for h in _distinct_attempts(hits)] == [[1], [4]]


def test_split_batches_keeps_order_and_covers_everything():
    ids = [str(i) for i in range(7)]
    assert sum(split_batches(ids, 3), []) == ids
