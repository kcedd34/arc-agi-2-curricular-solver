"""Item 3.4 (RN-CUR-30 acceptance review): automated specificity sweep.

Scans every library module under `library/primitives/`, `library/pieces/`
and `library/objects/` (Rodada 2 pre-round fix: the sweep originally only
covered `primitives/`, missing `pieces/content.py`, the file ADR 0075's
Rodada 1 pruning package actually changed) for two signs that code was
tailored to one task instead of learned as a general rule: (1) a string
literal shaped like an ARC task id (8 lowercase hex characters), and (2) a
numeric literal in the module's executable code (function bodies, argument
defaults, module-level constants) other than the structural constants
0, 1, -1, which a genuine primitive should never need since every
task-specific value (block size, background color, ...) is a search-
inferred parameter, not a fixed number. Docstrings are excluded: citing a
task id as a worked example in prose (as tiling.py's own docstring does)
is documentation, not a hardcoded dependency. For numeric literals only,
one further exemption applies: a literal nested inside the right-hand
side of a module-level assignment to an UPPER_SNAKE_CASE name (e.g.
`MAX_COMPOSITIONS_PER_TASK = 5000`) is excluded, since it is a named,
grep-able constant rather than a value hidden inline, so a domain
constant (a connectivity value, a modulus) only needs naming, not an
allowlist entry, to read as documented. Task id string literals get no
such exemption: naming one `TASK_ID = "007bbfb7"` does not make it any
less a hardcoded dependency on that one task.
"""
import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

LIBRARY_DIRS = [
    Path("src/curriculum/library/primitives"),
    Path("src/curriculum/library/pieces"),
    Path("src/curriculum/library/objects"),
]
_TASK_ID_PATTERN = re.compile(r"^[0-9a-f]{8}$")
_ALLOWED_NUMERIC_LITERALS = {0, 1, -1}
_UPPER_SNAKE_CASE = re.compile(r"^_?[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class SpecificityFinding:
    file: str
    line: int
    kind: str  # "task_id_literal" or "unexplained_numeric_literal"
    value: str


@dataclass(frozen=True)
class SpecificitySweepResult:
    files_scanned: List[str]
    findings: List[SpecificityFinding] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.findings


def _library_source_files() -> List[Path]:
    files = [
        p for library_dir in LIBRARY_DIRS for p in library_dir.glob("*.py") if p.name != "__init__.py"
    ]
    return sorted(files)


def _docstring_constant_ids(tree: ast.AST) -> Set[int]:
    """Identity-set of every module/function/class docstring's Constant node."""
    ids = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            ids.add(id(first.value))
    return ids


def _classify_constant(node: ast.Constant, path: Path, named_ids: Set[int]) -> List[SpecificityFinding]:
    """A task id literal is a violation regardless of naming (naming it
    `TASK_ID = "..."` does not make the dependency any less real); only
    numeric literals get the named-constant exemption, since those are
    the domain/engineering constants the exemption is meant for."""
    value = node.value
    if isinstance(value, str) and _TASK_ID_PATTERN.match(value):
        return [SpecificityFinding(str(path), node.lineno, "task_id_literal", value)]
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value not in _ALLOWED_NUMERIC_LITERALS
        and id(node) not in named_ids
    ):
        return [
            SpecificityFinding(
                str(path), node.lineno, "unexplained_numeric_literal", repr(value)
            )
        ]
    return []


def _named_constant_ids(tree: ast.AST) -> Set[int]:
    """Identity-set of every Constant nested in the right-hand side of an
    assignment to an UPPER_SNAKE_CASE name: a named constant is
    documentation by naming, the same reason docstring text is excluded."""
    ids: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if value is None or not any(isinstance(t, ast.Name) and _UPPER_SNAKE_CASE.match(t.id) for t in targets):
            continue
        for sub in ast.walk(value):
            if isinstance(sub, ast.Constant):
                ids.add(id(sub))
    return ids


def _scan_source(source: str, path: Path) -> List[SpecificityFinding]:
    tree = ast.parse(source, filename=str(path))
    docstring_ids = _docstring_constant_ids(tree)
    named_ids = _named_constant_ids(tree)
    findings: List[SpecificityFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and id(node) not in docstring_ids:
            findings.extend(_classify_constant(node, path, named_ids))
    return findings


def sweep_library() -> SpecificitySweepResult:
    files = _library_source_files()
    findings: List[SpecificityFinding] = []
    for path in files:
        findings.extend(_scan_source(path.read_text(encoding="utf-8"), path))
    return SpecificitySweepResult(files_scanned=[str(p) for p in files], findings=findings)


def format_report(result: SpecificitySweepResult) -> str:
    lines = [f"Files scanned: {len(result.files_scanned)}"]
    lines.extend(f"  - {f}" for f in result.files_scanned)
    if result.clean:
        lines.append("Result: CLEAN (0 findings, no task id literal, no unexplained numeric constant)")
    else:
        lines.append(f"Result: {len(result.findings)} finding(s)")
        for finding in result.findings:
            lines.append(f"  [{finding.kind}] {finding.file}:{finding.line} = {finding.value}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(sweep_library()))
