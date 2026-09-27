"""Evaluator package: the only code in src/curriculum/ authorized to read
gabaritos (test-pair outputs), per RN-CUR-03.

- solutions.py loads test outputs from disk, kept separate from
  loader.py's solver-facing Task type so no gabarito ever reaches
  solver code structurally.
- exact_match.py compares a solver's predicted grids against solutions
  loaded here, honest exact-match only, no partial credit.
"""
