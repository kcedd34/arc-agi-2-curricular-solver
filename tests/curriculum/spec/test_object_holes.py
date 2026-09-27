from src.curriculum.spec._object_holes import enclosed_positions, has_hole

N = None


def test_ring_has_one_enclosed_cell():
    cells = [[1, 1, 1], [1, N, 1], [1, 1, 1]]
    assert enclosed_positions(cells) == {(1, 1)}
    assert has_hole(cells)


def test_solid_object_has_no_hole():
    assert not has_hole([[1, 1], [1, 1]])


def test_open_cup_is_not_a_hole():
    cells = [[1, N, 1], [1, N, 1], [1, 1, 1]]
    assert not has_hole(cells)


def test_diagonal_gap_leaks_only_through_4_neighbours():
    cells = [[N, 1, N], [1, N, 1], [N, 1, N]]
    assert enclosed_positions(cells) == {(1, 1)}


def test_two_holes_are_both_reported():
    cells = [[1, 1, 1, 1, 1], [1, N, 1, N, 1], [1, 1, 1, 1, 1]]
    assert enclosed_positions(cells) == {(1, 1), (1, 3)}


def test_multi_cell_hole_and_open_corner():
    cells = [[N, 1, 1, 1], [1, N, N, 1], [1, 1, 1, 1]]
    assert enclosed_positions(cells) == {(1, 1), (1, 2)}
