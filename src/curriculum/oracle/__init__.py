"""ORACLE, DIAGNOSTIC ONLY (ADR 0111, Round 23).

This package measures the representation ceiling: it searches for a composition
that reproduces every train pair AND the test pair, with the gold test output
visible during the search. It is a measurement tool, never a solver.

Isolation contract:
- Nothing outside this package (and its tests) may import `src.curriculum.oracle`;
  `tests/curriculum/oracle/test_oracle_isolation.py` fails if anything does.
- The gold is read only from the raw task JSON, here, and never leaves this
  package: no hypothesis, prediction or score computed with it flows back into
  the solver, the submission builder or the discovery engine.
- It runs as its own command (`python -m src.curriculum.oracle.run`) and widens
  the solver budgets only inside that process.
"""
