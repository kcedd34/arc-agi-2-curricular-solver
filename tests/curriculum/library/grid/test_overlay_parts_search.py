from src.curriculum.library.grid.overlay_composition import build_overlay_steps
from src.curriculum.library.grid.overlay_enumerate import learn_table, split_shapes
from src.curriculum.library.grid.overlay_search import verified_overlay_candidates_with_predictions
from src.curriculum.loader import Task, TrainPair
from src.curriculum.spec import interpreter


def _xor_pair(left, right, divider=1):
    """Two 2x2 parts (optionally divider column of 5s) -> 3 where exactly one is set."""
    rows = []
    for a, b in zip(left, right):
        rows.append(list(a) + ([5] if divider else []) + list(b))
    out = [[3 if (x != 0) != (y != 0) else 0 for x, y in zip(a, b)] for a, b in zip(left, right)]
    return TrainPair(rows, out)


def _task():
    train = [
        _xor_pair([[1, 0], [0, 1]], [[1, 1], [0, 0]]),
        _xor_pair([[0, 0], [1, 1]], [[0, 1], [1, 0]]),
        _xor_pair([[1, 1], [1, 0]], [[0, 1], [0, 0]]),
    ]
    test = [_xor_pair([[1, 0], [1, 0]], [[0, 0], [1, 1]]).input]
    return Task("synthetic", train, test)


def test_split_shapes_finds_divider_split():
    assert (1, 2, True) in split_shapes(_task())


def test_learn_table_is_xor():
    table = learn_table(_task(), (1, 2, True), 0)
    assert dict(table) == {(False, False): 0, (True, False): 3, (False, True): 3, (True, True): 0}


def test_learn_table_rejects_conflict():
    task = _task()
    bad = Task("bad", task.train + [TrainPair([[1, 5, 1]], [[3]])], task.test_inputs)
    assert learn_table(bad, (1, 2, True), 0) is None


def test_verified_candidate_predicts_test():
    pairs = verified_overlay_candidates_with_predictions(_task())
    assert pairs
    assert pairs[0][1] == [[[3, 0], [0, 3]]]


def test_steps_run_through_interpreter():
    comp = verified_overlay_candidates_with_predictions(_task())[0][0]
    out, _trace = interpreter.run(build_overlay_steps(comp), _task().train[0].input)
    assert out == _task().train[0].output


def test_unseen_mask_is_an_error_not_a_guess():
    train = [TrainPair([[1, 5, 0], [0, 5, 0]], [[3], [0]]), TrainPair([[0, 5, 1], [1, 5, 0]], [[3], [3]])]
    task = Task("unseen", train, [[[1, 5, 1]]])
    pairs = verified_overlay_candidates_with_predictions(task)
    assert all(p[0].table for p in pairs) and pairs == []
