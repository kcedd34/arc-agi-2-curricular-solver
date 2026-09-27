"""RN-CUR-37: default 6 workers, env var, CLI parameter, precedence."""
import argparse

import pytest

from src.curriculum import parallel_batch as pb
from src.curriculum.timing import summarize_durations
from src.curriculum.timing_report import timing_line


def _cores(monkeypatch, n):
    monkeypatch.setattr(pb.os, "cpu_count", lambda: n)


def test_default_is_six_on_eight_cores(monkeypatch):
    monkeypatch.delenv(pb.WORKERS_ENV, raising=False)
    _cores(monkeypatch, 8)
    assert pb.default_worker_count() == 6 == pb.DEFAULT_WORKERS


def test_default_is_capped_by_core_count(monkeypatch):
    monkeypatch.delenv(pb.WORKERS_ENV, raising=False)
    _cores(monkeypatch, 2)
    assert pb.default_worker_count() == 2


def test_env_var_overrides_default(monkeypatch):
    _cores(monkeypatch, 8)
    monkeypatch.setenv(pb.WORKERS_ENV, "3")
    assert pb.default_worker_count() == 3


@pytest.mark.parametrize("bad", ["0", "-2", "abc"])
def test_invalid_env_var_is_rejected(monkeypatch, bad):
    monkeypatch.setenv(pb.WORKERS_ENV, bad)
    with pytest.raises(ValueError):
        pb.default_worker_count()


def test_cli_beats_env_and_sequential_beats_cli(monkeypatch):
    _cores(monkeypatch, 8)
    monkeypatch.setenv(pb.WORKERS_ENV, "3")
    assert pb.resolve_workers(5) == 5
    assert pb.resolve_workers(5, sequential=True) == 1
    assert pb.resolve_workers() == 3


def test_cli_rejects_non_positive():
    with pytest.raises(ValueError):
        pb.resolve_workers(0)


def test_parser_arguments():
    parser = argparse.ArgumentParser()
    pb.add_worker_arguments(parser)
    args = parser.parse_args(["--workers", "4"])
    assert (args.workers, args.sequential) == (4, False)
    assert parser.parse_args(["--sequential"]).sequential is True


def test_timing_line_reports_workers():
    timing = summarize_durations({"a": 1.0, "b": 3.0}, 4.0)
    assert timing_line(timing, 6).endswith("workers=6")
    assert "workers" not in timing_line(timing)
