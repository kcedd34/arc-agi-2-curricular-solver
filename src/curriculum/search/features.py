"""Cheap, train-pairs-only features used to order parameter candidates.

Never reads test_inputs' content for anything beyond building a
prediction after a candidate is already train-pair-verified (RN-CUR-03:
even test_inputs holds no gabarito, but a solver still should not need
to peek at it to rank candidates, only to apply the winning one).
"""
from collections import Counter
from typing import List

from src.curriculum.loader import Task


def input_color_counts(task: Task) -> Counter:
    """Cell counts per color across every train-pair input grid."""
    counts: Counter = Counter()
    for pair in task.train:
        for row in pair.input:
            counts.update(row)
    return counts


def colors_by_frequency(task: Task) -> List[int]:
    """Colors seen in train-pair inputs, most frequent first.

    Used as the candidate order for a "background color" parameter: the
    background is usually (not always) the most common color, so trying
    it first finds a verified candidate faster without changing
    correctness (every candidate still gets fully train-pair-verified).
    """
    counts = input_color_counts(task)
    return [color for color, _ in counts.most_common()]
