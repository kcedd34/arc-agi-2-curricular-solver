"""Deterministic work meter (ADR 0101)."""
import pytest

from src.curriculum.spec import interpreter, work_meter
from src.curriculum.spec import vocabulary as vocab


def test_charge_outside_metered_is_a_no_op():
    work_meter.charge(10**9)
    assert work_meter.units_used() == 0


def test_unit_limit_raises_and_records_work():
    with work_meter.metered(10, None):
        work_meter.charge(10)
        with pytest.raises(work_meter.WorkBudgetExceeded):
            work_meter.charge(1)
        assert work_meter.tripped() == work_meter.WORK


def test_deadline_raises_and_records_deadline():
    with work_meter.metered(None, 0.0):
        with pytest.raises(work_meter.WorkBudgetExceeded):
            work_meter.charge(1)
        assert work_meter.tripped() == work_meter.DEADLINE


def test_metered_restores_previous_state():
    with work_meter.metered(5, None):
        work_meter.charge(3)
    assert work_meter.units_used() == 0 and work_meter.tripped() is None


def test_exceeded_is_not_swallowed_by_generic_exception_handlers():
    with work_meter.metered(0, None):
        try:
            try:
                work_meter.charge(1)
            except Exception:
                pytest.fail("generic handler must not catch the budget signal")
        except work_meter.WorkBudgetExceeded:
            pass


def test_interpreter_run_charges_input_area():
    steps = [
        vocab.Bind(name="g_in", value=vocab.Ref("input")),
        vocab.ShapeOut(rows=vocab.Attr(vocab.Ref("g_in"), "rows"), cols=vocab.Attr(vocab.Ref("g_in"), "cols")),
        vocab.Seed(source=vocab.Ref("g_in")),
        vocab.Compose(default_color=0),
    ]
    with work_meter.metered(None, None):
        interpreter.run(steps, [[1, 2, 3], [4, 5, 6]])
        interpreter.run(steps, [[1]])
        assert work_meter.units_used() == 7
