"""Expression trees of generated measures (ADR 0110): construction, typing,
text form and parsing. An expression is `atom` or `op(arg, ...)`; the text
form is canonical (no spaces) and is the identity of the property."""
from typing import NamedTuple, Optional, Sequence, Tuple

from src.curriculum.spec._errors import InterpreterError
from src.curriculum.spec._gen_atoms import BOOL, COLOR, INT, atom_type, is_atom

BINARY_OPS = ("add", "sub", "ratio", "eq", "lt")
COMMUTATIVE_OPS = ("add", "eq")
GROUP_OPS = ("rank", "same", "gmin", "gmax", "gsum", "gmode")
ALL_OPS = BINARY_OPS + GROUP_OPS
_NUMERIC = (INT, BOOL)


class Expr(NamedTuple):
    op: str  # an atom name or an operator
    args: Tuple["Expr", ...]
    text: str
    depth: int
    nodes: int
    type: str


def result_type(op: str, arg_types: Sequence[str]) -> Optional[str]:
    """The result type of `op` over `arg_types`, or None when illegal."""
    if op in ("add", "sub", "ratio"):
        return INT if len(arg_types) == 2 and all(t in _NUMERIC for t in arg_types) else None
    if op == "eq":
        return BOOL if len(arg_types) == 2 and arg_types[0] == arg_types[1] else None
    if op == "lt":
        return BOOL if len(arg_types) == 2 and all(t in _NUMERIC for t in arg_types) else None
    return _group_type(op, arg_types)


def _group_type(op: str, arg_types: Sequence[str]) -> Optional[str]:
    if len(arg_types) != 1:
        return None
    (t,) = arg_types
    if op in ("rank", "gmin", "gmax", "gsum"):
        return INT if t in _NUMERIC else None
    if op == "same":
        return INT
    if op == "gmode":
        return t
    return None


def atom(name: str) -> Expr:
    if not is_atom(name):
        raise InterpreterError(f"generated measure: unknown atom {name!r}")
    return Expr(name, (), name, 1, 1, atom_type(name))


def apply_op(op: str, *args: Expr) -> Expr:
    typ = result_type(op, [a.type for a in args])
    if typ is None:
        raise InterpreterError(f"generated measure: {op} does not accept {[a.type for a in args]}")
    text = f"{op}({','.join(a.text for a in args)})"
    return Expr(op, tuple(args), text, 1 + max(a.depth for a in args), 1 + sum(a.nodes for a in args), typ)


class _Parser:
    def __init__(self, text: str) -> None:
        self.text, self.pos = text, 0

    def _name(self) -> str:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == "_"):
            self.pos += 1
        if start == self.pos:
            raise InterpreterError(f"generated measure: expected a name at {start} in {self.text!r}")
        return self.text[start : self.pos]

    def expr(self) -> Expr:
        name = self._name()
        if self.pos < len(self.text) and self.text[self.pos] == "(":
            self.pos += 1
            args = [self.expr()]
            while self.text[self.pos] == ",":
                self.pos += 1
                args.append(self.expr())
            if self.text[self.pos] != ")":
                raise InterpreterError(f"generated measure: expected ')' in {self.text!r}")
            self.pos += 1
            return apply_op(name, *args)
        return atom(name)


_PARSED: dict = {}


def parse(text: str) -> Expr:
    cached = _PARSED.get(text)
    if cached is None:
        try:
            parser = _Parser(text)
            cached = parser.expr()
            if parser.pos != len(text):
                raise InterpreterError(f"generated measure: trailing text in {text!r}")
        except IndexError as exc:
            raise InterpreterError(f"generated measure: malformed {text!r}") from exc
        _PARSED[text] = cached
    return cached
