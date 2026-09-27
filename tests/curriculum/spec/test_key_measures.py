"""Key-cell measures (Round 21, ADR 0109) on synthetic regions."""
from src.curriculum.spec._key_measures import NO_KEY
from src.curriculum.spec._measures import measure_value
from src.curriculum.spec._region_value import RegionValue


def _region(cells, row0=0, col0=0):
    return RegionValue(row0=row0, col0=col0, rows=len(cells), cols=len(cells[0]), cells=cells)


def test_the_key_is_the_single_cell_of_a_colour_that_appears_once():
    region = _region([[None, 6, None], [1, 1, 1], [None, 1, None]])
    assert measure_value(region, "key_color") == 6
    assert (measure_value(region, "key_row"), measure_value(region, "key_col")) == (0, 1)


def test_a_single_cell_region_is_its_own_key():
    region = _region([[4]], row0=3, col0=5)
    assert measure_value(region, "key_color") == 4
    assert (measure_value(region, "key_row"), measure_value(region, "key_col")) == (0, 0)


def test_no_unique_single_cell_colour_means_no_key():
    two_keys = _region([[2, 3, 1], [1, 1, 1]])
    same_colour = _region([[1, 1], [1, 1]])
    for region in (two_keys, same_colour):
        assert measure_value(region, "key_color") == NO_KEY
        assert (measure_value(region, "key_row"), measure_value(region, "key_col")) == (0, 0)
