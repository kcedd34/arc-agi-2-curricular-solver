"""Guards the context-hygiene rule in CLAUDE.md Section 1: this file
must stay small and stable so every session loads it cheaply. See
ADR 0065.
"""

import pathlib

MAX_CLAUDE_MD_BYTES = 12 * 1024

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CLAUDE_MD_PATH = REPO_ROOT / "CLAUDE.md"


def test_claude_md_stays_under_12kb():
    size = CLAUDE_MD_PATH.stat().st_size
    assert size <= MAX_CLAUDE_MD_BYTES, (
        f"CLAUDE.md is {size} bytes, over the {MAX_CLAUDE_MD_BYTES} byte "
        "limit. Do not summarize ADR content into CLAUDE.md to fix this; "
        "cut content instead, or add a one-line entry to "
        "docs/decisions/README.md if this growth is a new ADR reference."
    )
