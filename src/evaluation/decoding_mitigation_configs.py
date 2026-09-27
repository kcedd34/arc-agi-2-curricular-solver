"""Named NeuralSolverConfig variants for the decoding-mitigation smoke
comparison: each of the two failure-mode mitigations diagnosed in
docs/decisions/0028-timing-anomaly-and-task-complexity-investigation.md,
isolated and combined, so their individual and joint effect can be read
apart. See docs/decisions/0029-decoding-mitigations-repetition-hallucination.md.

repetition_penalty=1.3 and no_repeat_ngram_size=3 are the conservative
starting values suggested for this first test, just enough to break
literal repetition loops without distorting normal sampling.

ADR 0029's `repetition_only` bundles both parameters as one axis, per the
original request. ADR 0029 also found that axis regresses held-out
accuracy on tasks with no failure mode to fix, and could not attribute
that regression to either parameter individually. build_repetition_axis_split_configs()
below isolates each parameter on its own, to answer that follow-up
question; see docs/decisions/0030-splitting-repetition-mitigation-parameters.md.

Pure config construction, no GPU/model dependency, same pattern as
color_augmentation_configs.py/augmentation_configs.py.
"""
from dataclasses import replace
from typing import List, Tuple

from src.solvers.neural.config import NeuralSolverConfig

_REPETITION_PENALTY_VALUE = 1.3
_NO_REPEAT_NGRAM_SIZE = 3
# A gentler no_repeat_ngram_size, tried only after ADR 0030 found
# no_repeat_ngram_size=3 (not repetition_penalty) drives both the failure-
# mode fix and the held-out-accuracy regression, to see if a looser block
# still fixes the two target tasks with less collateral damage elsewhere.
_GENTLE_NO_REPEAT_NGRAM_SIZE = 5


def build_decoding_mitigation_configs() -> List[Tuple[str, NeuralSolverConfig]]:
    defaults = NeuralSolverConfig()
    baseline = replace(defaults)
    repetition_only = replace(
        defaults,
        repetition_penalty=_REPETITION_PENALTY_VALUE,
        no_repeat_ngram_size=_NO_REPEAT_NGRAM_SIZE,
    )
    stop_heuristic_only = replace(defaults, stop_on_second_input=True)
    both = replace(
        defaults,
        repetition_penalty=_REPETITION_PENALTY_VALUE,
        no_repeat_ngram_size=_NO_REPEAT_NGRAM_SIZE,
        stop_on_second_input=True,
    )
    return [
        ("baseline", baseline),
        ("repetition_only", repetition_only),
        ("stop_heuristic_only", stop_heuristic_only),
        ("both", both),
    ]


def build_repetition_axis_split_configs() -> List[Tuple[str, NeuralSolverConfig]]:
    """Splits ADR 0029's combined `repetition_only` axis into its two
    parameters in isolation, so each one's contribution to the failure-mode
    fix and its contribution to the held-out-accuracy regression on
    unaffected tasks can be told apart. See ADR 0030."""
    defaults = NeuralSolverConfig()
    penalty_only = replace(defaults, repetition_penalty=_REPETITION_PENALTY_VALUE)
    ngram_only = replace(defaults, no_repeat_ngram_size=_NO_REPEAT_NGRAM_SIZE)
    return [
        ("penalty_only", penalty_only),
        ("ngram_only", ngram_only),
    ]


def build_gentle_ngram_config() -> List[Tuple[str, NeuralSolverConfig]]:
    """A single looser no_repeat_ngram_size=5 config (no repetition_penalty),
    tried only after ADR 0030 confirmed no_repeat_ngram_size=3 alone drives
    both the failure-mode fix and the held-out-accuracy regression."""
    defaults = NeuralSolverConfig()
    ngram_gentle = replace(defaults, no_repeat_ngram_size=_GENTLE_NO_REPEAT_NGRAM_SIZE)
    return [("ngram_gentle", ngram_gentle)]
