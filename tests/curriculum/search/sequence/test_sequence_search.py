"""End-to-end tests for two-rule composition (ADR 0097): a synthetic task
that needs two rules (largest object -> 9, smallest -> 8, middle kept)
is found only as a sequence, and single-rule tasks never reach the
sequence search."""
from src.curriculum.library.objects.object_search import check_with_object_pack
from src.curriculum.loader import Task, TrainPair
from src.curriculum.search.all_candidates import all_verified_pairs
from src.curriculum.search.candidate_rank import candidate_complexity
from src.curriculum.search.rank import search_task
from src.curriculum.search.sequence.composition import SequenceComposition, run_candidate
from src.curriculum.search.sequence.search import derived_task, sequence_candidates_with_predictions
from src.curriculum.search.sequence.stage_one import admissible_first_stages


def _build(layout):
    grid = [[0] * 9 for _ in range(9)]
    for r, c, h, w in layout:
        for i in range(h):
            for j in range(w):
                grid[r + i][c + j] = 5
    return grid


def _expected(layout):
    grid = _build(layout)
    sizes = [h * w for _r, _c, h, w in layout]
    for r, c, h, w in layout:
        color = 9 if h * w == max(sizes) else 8 if h * w == min(sizes) else 5
        for i in range(h):
            for j in range(w):
                grid[r + i][c + j] = color
    return grid


# The fourth layout breaks every size/height/width lookup table, so no derived
# single rule fits and only the two-rule sequence explains the pairs.
LAYOUTS = [
    [(0, 0, 3, 3), (5, 0, 2, 2), (7, 6, 1, 1)],
    [(0, 5, 2, 2), (4, 0, 3, 2), (8, 8, 1, 1)],
    [(1, 1, 3, 2), (6, 5, 2, 2), (0, 8, 1, 1)],
    [(0, 0, 2, 2), (4, 0, 1, 2), (7, 7, 1, 1)],
]
TEST_LAYOUT = [(0, 0, 2, 4), (4, 4, 2, 2), (8, 0, 1, 1)]


def _two_rule_task() -> Task:
    train = [TrainPair(_build(l), _expected(l)) for l in LAYOUTS]
    return Task("synthetic_two_rule", train, [_build(TEST_LAYOUT)])


def test_no_single_rule_solves_the_two_rule_task():
    assert check_with_object_pack(_two_rule_task()).status == "no_candidate"


def test_sequence_search_finds_the_two_rule_answer():
    pairs = sequence_candidates_with_predictions(_two_rule_task())
    assert pairs
    assert all(isinstance(c, SequenceComposition) for c, _ in pairs)
    assert any(preds == [_expected(TEST_LAYOUT)] for _c, preds in pairs)


def test_every_sequence_reproduces_all_train_pairs():
    task = _two_rule_task()
    pairs = sequence_candidates_with_predictions(task)
    for candidate, _preds in pairs[:5]:
        for pair in task.train:
            assert run_candidate(candidate, pair.input)[0] == pair.output


def test_search_task_falls_back_to_sequences():
    result = search_task(_two_rule_task())
    assert result.status in ("solved", "ambiguous")
    assert all(isinstance(c, SequenceComposition) for c in result.verified)


def test_sequence_is_never_searched_when_a_single_rule_fits():
    layout = [(1, 1, 2, 2), (5, 5, 1, 1)]
    out = _build(layout)
    for r in range(1, 3):
        for c in range(1, 3):
            out[r][c] = 9
    task = Task("single", [TrainPair(_build(layout), out)], [_build(layout)])
    pools = all_verified_pairs(task)
    assert pools.main or pools.objects
    assert pools.sequences == []


def test_sequence_complexity_sums_both_stages():
    pairs = sequence_candidates_with_predictions(_two_rule_task())
    candidate = pairs[0][0]
    single = candidate_complexity(candidate.first)[0]
    second = candidate_complexity(candidate.second)[0]
    assert candidate_complexity(candidate)[0] == single + second


def test_describe_names_both_rules():
    candidate = sequence_candidates_with_predictions(_two_rule_task())[0][0]
    text = candidate.describe()
    assert text.startswith("sequence[ ") and "] then [" in text


def test_derived_task_feeds_first_output_as_second_input():
    task = _two_rule_task()
    stage = admissible_first_stages(task)[0]
    derived = derived_task(task, stage)
    assert [p.input for p in derived.train] == stage.train_grids
    assert [p.output for p in derived.train] == [p.output for p in task.train]
    assert derived.test_inputs == stage.test_grids
