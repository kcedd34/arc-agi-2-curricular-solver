"""Unit tests for the Fase A round-report summary logic, without running
the real search (that is covered by test_candidate_probe.py)."""
from pathlib import Path

from src.curriculum.diagnostics.candidate_probe import CandidateProbeResult
from src.curriculum.diagnostics.round_report import _summarize, output_path


def _result(task_id, num_verified=0, solved=False, error=None, main_cap=False, object_cap=False):
    return CandidateProbeResult(
        task_id=task_id, num_verified_candidates=num_verified, main_verified_count=num_verified,
        object_verified_count=0, solved=solved, unanimous=False, main_cap_hit=main_cap,
        object_cap_hit=object_cap, error=error,
    )


def test_summarize_buckets_tasks_correctly():
    results = [
        _result("a", num_verified=0),
        _result("b", num_verified=3, solved=False),
        _result("c", num_verified=1, solved=True),
        _result("d", error="boom"),
        _result("e", main_cap=True),
    ]
    summary = _summarize(results)
    assert summary["num_tasks"] == 5
    assert summary["no_candidate"] == 2  # "a" and "e" (cap_hit but zero verified)
    assert summary["wrong_candidate"] == 1  # "b"
    assert summary["solved_now"] == ["c"]
    assert summary["errored"] == ["d"]
    assert summary["cap_hit"] == 1


def test_output_path_names_the_round():
    path = output_path(3, output_dir=Path("outputs/curriculum/rounds"))
    assert path == Path("outputs/curriculum/rounds/round-3-diagnosis.json")
