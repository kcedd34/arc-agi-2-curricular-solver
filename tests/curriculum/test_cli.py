"""Tests for cli.py's subcommands, each delegating to an already-tested module."""
import argparse

import src.curriculum.cli as cli
from src.curriculum.library.primitives import tiling  # noqa: F401 (registers the primitive)
from src.curriculum.state import CurriculumState, PartitionRef, load_state


def _sample_state(**overrides) -> CurriculumState:
    defaults = dict(
        schema_version=1,
        updated_at="2026-09-21",
        current_stage="stage_0",
        stage_status="in_progress",
        partition_ref=PartitionRef(
            path="docs/curriculum/partition.json",
            seed=20260921,
            total_training_tasks=1000,
            curricular_pool_size=800,
            probe_pool_size=200,
            pinned_curricular_task_ids=["007bbfb7"],
        ),
        remaining_stage_0_items=[],
        blocked_on=[],
        solved_tasks=[],
        next_task="007bbfb7",
        probe_pool_checkpoints=[],
        library_version="v0",
        next_step=1,
    )
    defaults.update(overrides)
    return CurriculumState(**defaults)


def test_cmd_next_prints_a_curricular_task_id(capsys):
    cli.cmd_next(_sample_state(), argparse.Namespace())

    out = capsys.readouterr().out.strip()
    assert out != ""
    assert out != "No remaining curricular tasks."


def test_cmd_next_prints_message_when_pool_exhausted(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_curricular_pool", lambda path=None: ["007bbfb7"])

    cli.cmd_next(_sample_state(solved_tasks=["007bbfb7"]), argparse.Namespace())

    assert capsys.readouterr().out.strip() == "No remaining curricular tasks."


def test_cmd_check_reports_unanimous_status_for_007bbfb7(capsys):
    cli.cmd_check(_sample_state(), argparse.Namespace(task_id="007bbfb7"))

    out = capsys.readouterr().out
    assert "007bbfb7" in out
    assert "Unanimous" in out and "True" in out


def test_cmd_solve_marks_task_solved_and_persists_state(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(cli, "DEFAULT_STATE_PATH", state_path)

    cli.cmd_solve(_sample_state(), argparse.Namespace(task_id="007bbfb7"))

    saved = load_state(state_path)
    assert saved.solved_tasks == ["007bbfb7"]


def test_cmd_solve_does_not_write_state_when_not_solved(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(cli, "DEFAULT_STATE_PATH", state_path)
    monkeypatch.setattr(
        cli, "run_desk_check",
        lambda task: argparse.Namespace(status="no_candidate", unanimous=False, task_id=task.task_id, verified=[]),
    )
    monkeypatch.setattr(cli, "format_report", lambda report: "no candidate")
    monkeypatch.setattr(
        cli, "compute_verified_verdict",
        lambda task_id: argparse.Namespace(unanimous=False, solved=False),
    )

    cli.cmd_solve(_sample_state(), argparse.Namespace(task_id="007bbfb7"))

    assert not state_path.exists()


def test_cmd_solve_does_not_mark_solved_when_unanimous_but_wrong(tmp_path, monkeypatch):
    """Non-regression: unanimous agreement among candidates must never be
    enough to accept a task (the exact bug that wrongly accepted
    73ccf9c2, b230c067 and f5aa3634 on 2026-09-22)."""
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(cli, "DEFAULT_STATE_PATH", state_path)
    monkeypatch.setattr(
        cli, "run_desk_check",
        lambda task: argparse.Namespace(status="solved", unanimous=True, task_id=task.task_id, verified=["x"]),
    )
    monkeypatch.setattr(cli, "format_report", lambda report: "unanimous")
    monkeypatch.setattr(
        cli, "compute_verified_verdict",
        lambda task_id: argparse.Namespace(unanimous=True, solved=False),
    )

    cli.cmd_solve(_sample_state(), argparse.Namespace(task_id="007bbfb7"))

    assert not state_path.exists()


def test_cmd_validate_reports_valid_for_a_clean_state(capsys):
    cli.cmd_validate(_sample_state(), argparse.Namespace())

    lines = capsys.readouterr().out.strip().splitlines()
    assert "VALID" in lines


def test_cmd_probe_prints_checkpoint_and_persists_state(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(cli, "DEFAULT_STATE_PATH", state_path)
    monkeypatch.setattr(cli, "load_probe_pool", lambda: ["007bbfb7"])

    cli.cmd_probe(_sample_state(), argparse.Namespace(workers=None, sequential=False))

    out = capsys.readouterr().out
    assert "Probe checkpoint" in out
    saved = load_state(state_path)
    assert len(saved.probe_pool_checkpoints) == 1
    assert saved.probe_pool_checkpoints[0]["num_tasks"] == 1


def test_build_parser_dispatches_check_subcommand_to_task_id():
    args = cli.build_parser().parse_args(["check", "007bbfb7"])
    assert args.command == "check"
    assert args.task_id == "007bbfb7"


def test_main_next_runs_against_the_real_project_state():
    assert cli.main(["next"]) == 0
