"""Reusable declarative-step library, PRD Section 9.1 (UC04).

Implemented per ADR 0062's "Design principle" section: named library
primitives are fixed sequences of the vocabulary.py steps, never new
interpreter/vocabulary operations (the vocabulary must stay small and
grow much more slowly than this library). registry.py holds the
lookup/registration mechanism; library/primitives/* holds the builder
functions themselves, one file per primitive family.
"""
