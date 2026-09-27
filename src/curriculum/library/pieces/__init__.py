"""Layout/selector/content pieces (ADR 0064, RN-CUR-31).

Each module here is one independently combinable axis of a primitive:
`layout.py` (how the output grid is partitioned/sized), `selector.py`
(which blocks get which content), `content.py` (what gets written into a
selected block). A primitive in `src/curriculum/library/primitives/` is
built by composing one piece from each axis, so a new task pattern is
solved by recombination first, per RN-CUR-31, before any new piece is
written.
"""
