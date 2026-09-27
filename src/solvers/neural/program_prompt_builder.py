"""Builds the few-shot rule-induction prompt (ADR 0060).

Unlike build_inference_prompt (prompt_builder.py), which shows the model
only the test input with no examples, this prompt shows every train pair
and asks for an executable rule, def transform(g), instead of a grid.
Raw completion format, not a chat template (ADR 0054 already refuted the
chat-template path for this model family).

**Retry design, 2026-09-19** (ADR 0060 "Real smoke test result" section):
the original version of this module was zero-shot (no solved example
before the target task) and encoded each grid as one string with escaped
"\\n" separators. Neither choice was tested against an alternative before
the first smoke test ran; both are corrected here:

- A worked example (a different, hand-written, genuinely solved task) now
  precedes the target task's own examples, giving a Base model (raw
  completion, no instruction-tuning) a concrete pattern to continue
  rather than an isolated, hanging function signature.
- Grids are encoded as a Python list of row strings (via grid_to_rows),
  matching the exact List[str] shape run_program_on_grid already passes
  into the sandbox, instead of one string with embedded "\\n" escapes.
  This is closer to idiomatic Python the model saw in pretraining and
  avoids the escaping indirection entirely.
"""
from src.solvers.neural.grid_serialization import grid_to_rows
from src.utils.grid_types import Grid
from src.utils.task_loader import Pair, Task

_WORKED_EXAMPLE = (
    "# Worked example task, already solved.\n"
    "examples = [\n"
    "    (['120', '034'],\n"
    "     ['021', '430']),\n"
    "]\n\n"
    "def transform(g):\n"
    "    return [row[::-1] for row in g]\n\n\n"
)
_PREAMBLE = (
    "# Now a new ARC-AGI-2 task. Each grid is a list of row strings; each\n"
    "# row is a string of digits 0-9, one digit per cell. The same rule maps\n"
    "# every example input to its example output.\n\n"
    "examples = [\n"
)
_POSTAMBLE = (
    "]\n\n"
    "# transform(g) takes the input grid as a list of digit-string rows and\n"
    "# returns the output grid in the same form. It reproduces every example\n"
    "# above exactly.\n"
    "def transform(g):\n"
)


def _grid_literal(grid: Grid) -> str:
    return repr(grid_to_rows(grid))


def _format_example(pair: Pair) -> str:
    return f"    ({_grid_literal(pair.input)},\n     {_grid_literal(pair.output)}),\n"


def build_induction_prompt(task: Task) -> str:
    examples = "".join(_format_example(pair) for pair in task.train)
    return _WORKED_EXAMPLE + _PREAMBLE + examples + _POSTAMBLE
