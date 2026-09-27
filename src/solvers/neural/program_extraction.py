"""Extracts a candidate transform(g) program body from a raw model
completion (ADR 0060).

The induction prompt ends exactly at 'def transform(g):\\n', so the
completion is the body the model continued with; this module decides
where that body actually ends.
"""
from typing import Optional

_MAX_BODY_LINES = 40  # matches CLAUDE.md's own function-length convention


def _is_body_line(line: str) -> bool:
    return line.strip() == "" or line[:1] in (" ", "\t")


def extract_program_body(completion: str, max_lines: int = _MAX_BODY_LINES) -> Optional[str]:
    """Keeps only the leading indented/blank lines (the function body) and
    stops at the first unindented line, whatever it is: a new top-level
    statement, hallucinated commentary, or a second example. Returns None
    if no indented body line is found at all.
    """
    body_lines = []
    for line in completion.splitlines():
        if len(body_lines) >= max_lines or not _is_body_line(line):
            break
        body_lines.append(line)
    while body_lines and body_lines[-1].strip() == "":
        body_lines.pop()
    return "\n".join(body_lines) if body_lines else None


def build_program_source(body: str) -> str:
    return f"def transform(g):\n{body}\n"
