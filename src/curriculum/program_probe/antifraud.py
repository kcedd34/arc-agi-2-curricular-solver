"""Static antifraud for accepted programs (ADR 0113): task-specific constants do not count."""
import ast
from typing import List, Sequence

MIN_LITERAL_CELLS = 6


def _int_row(node: ast.AST):
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    values = [e.value for e in node.elts if isinstance(e, ast.Constant) and type(e.value) is int]
    return values if len(values) == len(node.elts) and values else None


def _int_matrix(node: ast.AST):
    if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
        return None
    rows = [_int_row(e) for e in node.elts]
    return rows if all(r is not None for r in rows) else None


def embedded_grids(tree: ast.AST) -> List[list]:
    """Every literal integer matrix with at least MIN_LITERAL_CELLS cells."""
    found = []
    for node in ast.walk(tree):
        rows = _int_matrix(node)
        if rows and sum(len(r) for r in rows) >= MIN_LITERAL_CELLS:
            found.append(rows)
    return found


def _is_len_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"


def _is_int_const(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and type(node.value) is int


def dimension_tests(tree: ast.AST) -> int:
    """Comparisons of len(...) against an integer constant with == or !=."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            sides = [node.left] + node.comparators
            count += any(_is_len_call(s) for s in sides) and any(_is_int_const(s) for s in sides)
    return count


def literal_comparisons(tree: ast.AST) -> int:
    """Comparisons of anything with a list/tuple literal of two or more elements."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            sides = [node.left] + node.comparators
            count += any(isinstance(s, (ast.List, ast.Tuple)) and len(s.elts) >= 2 for s in sides)
    return count


def big_constants(tree: ast.AST) -> List[int]:
    return sorted({n.value for n in ast.walk(tree) if _is_int_const(n) and n.value > 9})


def audit(code: str, known_grids: Sequence[list]) -> dict:
    """Flags for one program; `known_grids` are the train grids (no gold is passed in)."""
    tree = ast.parse(code)
    grids = embedded_grids(tree)
    known = [list(map(list, g)) for g in known_grids]
    flags = {
        "embedded_grid": len(grids),
        "embedded_known_grid": sum(g in known for g in grids),
        "dimension_tests": dimension_tests(tree),
        "literal_comparisons": literal_comparisons(tree),
        "big_constants": big_constants(tree),
    }
    flags["suspicious"] = bool(flags["embedded_grid"] or flags["dimension_tests"] or flags["literal_comparisons"])
    return flags
