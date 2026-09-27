import json

from src.evaluation.build_kaggle_submission import build_and_write


def test_build_and_write_produces_a_valid_submission_file(tmp_path):
    raw = {
        "t1": {
            "train": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test": [{"input": [[3, 4]]}],
        },
        "t2": {
            "train": [{"input": [[1]], "output": [[9]]}],
            "test": [{"input": [[5]]}],
        },
    }
    challenges_path = tmp_path / "arc-agi_test_challenges.json"
    challenges_path.write_text(json.dumps(raw), encoding="utf-8")
    output_path = tmp_path / "submission.json"

    summary = build_and_write(challenges_path, output_path)

    assert summary["task_count"] == 2
    assert output_path.exists()

    submission = json.loads(output_path.read_text(encoding="utf-8"))
    assert set(submission) == {"t1", "t2"}
    for entries in submission.values():
        for entry in entries:
            assert set(entry) == {"attempt_1", "attempt_2"}


def test_build_and_write_solves_a_flipped_geometric_task(tmp_path):
    raw = {
        "t1": {
            "train": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test": [{"input": [[3, 4]]}],
        }
    }
    challenges_path = tmp_path / "arc-agi_test_challenges.json"
    challenges_path.write_text(json.dumps(raw), encoding="utf-8")
    output_path = tmp_path / "submission.json"

    build_and_write(challenges_path, output_path)

    submission = json.loads(output_path.read_text(encoding="utf-8"))
    assert submission["t1"][0]["attempt_1"] == [[4, 3]]
