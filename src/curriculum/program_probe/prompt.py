"""Prompts for the program-writing probe: chat messages for Instruct, raw text for Base."""
from typing import List, NamedTuple, Sequence

from src.curriculum.program_probe.render import render_examples

SIGNATURE = "def solve(grid: list[list[int]]) -> list[list[int]]:"
PLAIN = "plain"
GUIDED = "guided"
VARIANTS = (PLAIN, GUIDED)
FENCE = "```"

HEADER = (
    "Each example shows an input grid and its output grid side by side. "
    "Cells are digits 0-9 (color); a dot is the background (0)."
)
TASK = (
    "Write a Python function `def solve(grid: list[list[int]]) -> list[list[int]]` that maps "
    "every example input to its output and generalizes to new inputs. Use only the standard "
    "library (imports allowed: collections, itertools, math)."
)
PLAIN_RULE = "Reply with the code only, no explanation, and write no comments."
GUIDED_RULE = (
    "First write one comment line starting with `# Rule:` saying in one sentence what "
    "distinguishes the regions that change from those that do not, then write the function. "
    "Reply with that line and the code only, and write no other comments."
)
BASE_PREFILL = {PLAIN: SIGNATURE + "\n", GUIDED: "# Rule (one sentence): "}


class Prompt(NamedTuple):
    variant: str
    user_text: str
    base_text: str


def _user_text(pairs: Sequence[tuple], variant: str) -> str:
    rule = PLAIN_RULE if variant == PLAIN else GUIDED_RULE
    return f"{HEADER}\n\n{render_examples(pairs)}\n\n{TASK} {rule}"


def build_prompt(pairs: Sequence[tuple], variant: str) -> Prompt:
    user = _user_text(pairs, variant)
    base = f"{user}\n\n{FENCE}python\n{BASE_PREFILL[variant]}"
    return Prompt(variant, user, base)


def chat_messages(prompt: Prompt) -> List[dict]:
    return [{"role": "user", "content": prompt.user_text}]


def base_response_head(variant: str) -> str:
    """Text the Base prompt already contains after the opening fence (rejoined on extraction)."""
    return f"{FENCE}python\n{BASE_PREFILL[variant]}"
