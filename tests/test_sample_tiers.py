from src.evaluation.sample_tiers import select_tier_tasks
from src.utils.task_loader import Pair, Task


def _task_with_output_size(task_id: str, height: int, width: int) -> Task:
    output = [[0] * width for _ in range(height)]
    pair = Pair(input=[[1]], output=output)
    return Task(task_id=task_id, train=[pair], test=[pair])


def _mixed_size_task_pool(small=6, medium=6, large=6):
    tasks = {}
    for i in range(small):
        task_id = f"s{i:02d}"
        tasks[task_id] = _task_with_output_size(task_id, 5, 5)
    for i in range(medium):
        task_id = f"m{i:02d}"
        tasks[task_id] = _task_with_output_size(task_id, 15, 15)
    for i in range(large):
        task_id = f"l{i:02d}"
        tasks[task_id] = _task_with_output_size(task_id, 30, 30)
    return tasks


def _size_band_of(task_id: str) -> str:
    return {"s": "small", "m": "medium", "l": "large"}[task_id[0]]


def test_smoke_tier_takes_first_two_sorted_tasks():
    tasks = _mixed_size_task_pool()
    sample = select_tier_tasks(tasks, "smoke")
    assert list(sample.keys()) == sorted(tasks.keys())[:2]


def test_sanity_tier_takes_first_eight_sorted_tasks():
    tasks = _mixed_size_task_pool()
    sample = select_tier_tasks(tasks, "sanity")
    assert list(sample.keys()) == sorted(tasks.keys())[:8]


def test_validation_tier_covers_all_three_size_bands():
    tasks = _mixed_size_task_pool(small=10, medium=10, large=10)
    sample = select_tier_tasks(tasks, "validation", size_override=15)
    bands_present = {_size_band_of(task_id) for task_id in sample}
    assert bands_present == {"small", "medium", "large"}


def test_validation_tier_is_proportional_to_band_population():
    tasks = _mixed_size_task_pool(small=20, medium=10, large=5)
    sample = select_tier_tasks(tasks, "validation", size_override=14)
    counts = {"small": 0, "medium": 0, "large": 0}
    for task_id in sample:
        counts[_size_band_of(task_id)] += 1
    assert counts["small"] > counts["medium"] > counts["large"]


def test_validation_tier_never_drops_a_populated_band_to_zero():
    tasks = _mixed_size_task_pool(small=50, medium=2, large=1)
    sample = select_tier_tasks(tasks, "validation", size_override=10)
    counts = {"small": 0, "medium": 0, "large": 0}
    for task_id in sample:
        counts[_size_band_of(task_id)] += 1
    assert counts["medium"] >= 1
    assert counts["large"] >= 1


def test_validation_tier_is_deterministic_for_a_fixed_seed():
    tasks = _mixed_size_task_pool()
    first = select_tier_tasks(tasks, "validation", seed=7, size_override=10)
    second = select_tier_tasks(tasks, "validation", seed=7, size_override=10)
    assert list(first.keys()) == list(second.keys())


def test_validation_tier_caps_at_available_population():
    tasks = _mixed_size_task_pool(small=2, medium=2, large=2)
    sample = select_tier_tasks(tasks, "validation", size_override=100)
    assert len(sample) == 6


def test_unknown_tier_raises():
    tasks = _mixed_size_task_pool()
    try:
        select_tier_tasks(tasks, "bogus")
        assert False, "expected ValueError"
    except ValueError:
        pass
