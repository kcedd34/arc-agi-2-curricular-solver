"""Tests for Item 3.4's automated specificity sweep.

The real-library test proves the current primitive library has zero task
id literals and zero unexplained numeric constants (RN-CUR-30's own
acceptance bar). The synthetic tests prove the scanner's own logic is
correct in isolation: it must flag a code-level task id or magic number,
but never flag the same string/number when it only appears inside a
docstring (prose referencing a task as a worked example is not the same
as depending on it).
"""
from pathlib import Path

from src.curriculum.library.specificity_sweep import _scan_source, sweep_library


def test_sweep_library_is_clean_on_real_primitives():
    result = sweep_library()

    assert any(f.endswith("tiling.py") for f in result.files_scanned)
    assert result.clean
    assert result.findings == []


def test_scan_flags_task_id_literal_in_code_but_not_in_docstring():
    source = '''"""Docstring mentioning 007bbfb7 as a worked example, not a dependency."""
TASK_ID = "007bbfb7"
'''
    findings = _scan_source(source, Path("fake_primitive.py"))

    assert len(findings) == 1
    assert findings[0].kind == "task_id_literal"
    assert findings[0].value == "007bbfb7"


def test_scan_flags_unexplained_numeric_literal_but_allows_structural_ones():
    source = """
def build_something(background):
    fixed_scale = 3
    zero = 0
    one = 1
    minus_one = -1
    return [fixed_scale, zero, one, minus_one, background]
"""
    findings = _scan_source(source, Path("fake_primitive.py"))

    assert len(findings) == 1
    assert findings[0].kind == "unexplained_numeric_literal"
    assert findings[0].value == "3"


def test_scan_ignores_numeric_literal_inside_docstring():
    source = '''def build_something(background):
    """Uses a 3x3 block in the worked example, this is prose not code."""
    return [background]
'''
    findings = _scan_source(source, Path("fake_primitive.py"))

    assert findings == []
