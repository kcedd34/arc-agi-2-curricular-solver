"""Declarative-step vocabulary and trace interpreter, PRD Section 9.1 (UC04).

Implemented per ADR 0062: vocabulary.py (the frozen-dataclass step/
predicate/expression AST), interpreter.py (execution, RN-CUR-14: never
imports src.curriculum.library), and _expressions.py/_regions.py/
_region_value.py (supporting runtime types). The interpreter's acceptance
test is ADR 0062's own "Worked example: 007bbfb7" section, reproduced in
tests/curriculum/spec/test_interpreter.py.
"""
