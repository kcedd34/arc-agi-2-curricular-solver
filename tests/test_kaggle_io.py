import json

from src.utils.kaggle_io import NO_OUTPUT_PLACEHOLDER, load_challenges
from src.utils.task_loader import Pair


def _write_challenges(tmp_path, raw):
    path = tmp_path / "challenges.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_load_challenges_reads_multiple_tasks_from_one_file(tmp_path):
    raw = {
        "t1": {"train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]]}]},
        "t2": {"train": [{"input": [[4]], "output": [[5]]}], "test": [{"input": [[6]]}]},
    }
    tasks = load_challenges(_write_challenges(tmp_path, raw))

    assert set(tasks) == {"t1", "t2"}


def test_load_challenges_preserves_train_pairs_and_test_inputs(tmp_path):
    raw = {
        "t1": {
            "train": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test": [{"input": [[3, 4]]}, {"input": [[5, 6]]}],
        }
    }
    tasks = load_challenges(_write_challenges(tmp_path, raw))
    task = tasks["t1"]

    assert task.task_id == "t1"
    assert task.train == [Pair(input=[[1, 2]], output=[[2, 1]])]
    assert [pair.input for pair in task.test] == [[[3, 4]], [[5, 6]]]


def test_load_challenges_test_pairs_use_placeholder_output(tmp_path):
    raw = {"t1": {"train": [{"input": [[1]], "output": [[1]]}], "test": [{"input": [[9]]}]}}
    tasks = load_challenges(_write_challenges(tmp_path, raw))

    assert tasks["t1"].test[0].output == NO_OUTPUT_PLACEHOLDER
