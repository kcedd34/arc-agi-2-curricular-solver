"""Detects the decode-level failure modes diagnosed in
docs/decisions/0028-timing-anomaly-and-task-complexity-investigation.md,
for the mitigation comparison in
docs/decisions/0029-decoding-mitigations-repetition-hallucination.md, plus
a fourth mode (topic drift) added in
docs/decisions/0056-mitigacao-4-modos-qwen3-base.md after it was observed
on Qwen3-4B-Base (ADR 0055).

Pure text analysis, no GPU/model dependency, host-testable.
"""
import re

from src.solvers.neural.completion_markers import SECOND_EXAMPLE_MARKER as _SECOND_EXAMPLE_MARKER

_DEFAULT_MIN_REPEATED_LINE_RUN = 10
_CODE_MARKERS = ("```", "def ", "import ")
_DEFAULT_MIN_NATURAL_LANGUAGE_WORDS = 4
_ALPHA_WORD_PATTERN = re.compile(r"[A-Za-z]+")


def has_hallucinated_second_example(raw_completion: str) -> bool:
    """True if the completion kept generating past a valid answer into a
    fabricated second Input:/Output: example (the 0934a4d8 pattern)."""
    return _SECOND_EXAMPLE_MARKER in raw_completion


def has_degenerate_repetition(raw_completion: str, min_run: int = _DEFAULT_MIN_REPEATED_LINE_RUN) -> bool:
    """True if the completion contains a run of at least min_run consecutive
    identical non-blank lines (the 13e47133 pattern: dozens of repeated
    identical rows instead of a terminating grid)."""
    lines = raw_completion.splitlines()
    run_length = 1
    for previous, current in zip(lines, lines[1:]):
        if current == previous and current.strip():
            run_length += 1
            if run_length >= min_run:
                return True
        else:
            run_length = 1
    return False


def has_topic_drift(raw_completion: str, min_natural_language_words: int = _DEFAULT_MIN_NATURAL_LANGUAGE_WORDS) -> bool:
    """True if the completion diverges into content unrelated to the grid
    task (the Qwen3-4B-Base 135a2760 pattern: a correct grid followed by an
    unrelated Python-code tangent). A real grid line is pure digits, so any
    line carrying several alphabetic words, or any of the common code
    markers, is already outside the expected grid format."""
    if any(marker in raw_completion for marker in _CODE_MARKERS):
        return True
    for line in raw_completion.splitlines():
        if len(_ALPHA_WORD_PATTERN.findall(line)) >= min_natural_language_words:
            return True
    return False
