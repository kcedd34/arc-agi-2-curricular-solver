from pathlib import Path

from src.curriculum.loader import Task, load_task, load_task_set

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_load_task_007bbfb7():
    task = load_task(TRAINING_DIR / "007bbfb7.json")
    assert task.task_id == "007bbfb7"
    assert len(task.train) == 5
    assert len(task.test_inputs) == 1


def test_task_has_no_test_output_field():
    """RN-CUR-03: the solver-facing Task type structurally has no way to
    hold a test-pair output; this is what makes the gabarito boundary a
    guarantee rather than a convention."""
    assert "test" not in Task._fields
    assert "test_inputs" in Task._fields
    assert not hasattr(Task, "test_outputs")


def test_load_task_set_returns_all_tasks():
    tasks = load_task_set(TRAINING_DIR)
    assert len(tasks) == 1000
    assert "007bbfb7" in tasks
