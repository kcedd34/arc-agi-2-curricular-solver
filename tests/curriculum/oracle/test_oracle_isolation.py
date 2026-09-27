from pathlib import Path

SRC = Path("src")
ALLOWED = Path("src/curriculum/oracle")
NEEDLES = ("curriculum.oracle", "curriculum import oracle")


def _outside_files():
    return [p for p in SRC.rglob("*.py") if ALLOWED not in p.parents]


def test_no_production_module_imports_the_oracle():
    offenders = [
        str(p)
        for p in _outside_files()
        if any(needle in line for line in p.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith(("import ", "from ")) for needle in NEEDLES)
    ]
    assert offenders == []


def test_oracle_docstring_states_it_is_diagnostic_only():
    text = (ALLOWED / "__init__.py").read_text(encoding="utf-8")
    assert "DIAGNOSTIC ONLY" in text and "Nothing outside this package" in text


def test_gold_is_only_read_inside_the_oracle_package():
    offenders = [str(p) for p in _outside_files() if "oracle_task" in p.read_text(encoding="utf-8")]
    assert offenders == []
