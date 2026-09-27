"""Interpreter error type, in its own module so `_measures.py` and
`_expressions.py` can both raise it without a circular import."""


class InterpreterError(ValueError):
    pass
