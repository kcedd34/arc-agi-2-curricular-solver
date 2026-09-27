"""Official metric: exact match, up to 2 predictions per test input."""
from typing import List

from src.utils.grid_types import Grid


def scores_test_pair(predictions: List[Grid], expected: Grid) -> bool:
    return any(prediction == expected for prediction in predictions)
