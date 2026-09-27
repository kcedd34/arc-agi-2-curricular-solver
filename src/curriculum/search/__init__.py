"""Bounded search over declarative-step programs, PRD Section 9.1.

Enumerates (primitive, params) candidates from library/registry.py,
verifies each against 100% of a task's train pairs before ever touching
a test input (the same discipline every accepted symbolic primitive in
the prior solver line already followed), and applies an ADR-0038-style
ambiguity bar: more than one verified candidate disagreeing on a test
input yields no answer, never an arbitrary pick.

- features.py: cheap train-pairs-only signals (e.g. color frequency).
- params.py: candidate values per parameter name, given a task.
- enumerate.py: cartesian product of one primitive's own parameters,
  bounded per primitive (never composes primitives, never unbounded).
- rank.py: train-pair verification, ambiguity resolution, prediction.
"""
