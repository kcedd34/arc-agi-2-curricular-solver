"""Staging area for package pieces not yet promoted into the main search
space (RN-CUR-36, ADR 0069, docs/curriculum/tasks/object-pack.md).

Pieces here are excluded from `search/compose.py`'s enumeration by
construction: that module never imports this package. A package is
promoted (its pieces moved under `library/pieces/` and wired into
`search/compose.py`) only once its own staging report meets RN-CUR-36's
gate (>= 2 validated curricular-pool hits with no additional teaching).
"""
