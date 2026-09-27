from src.solvers.composition_search import find_compositions
from src.utils.task_loader import Pair


def test_finds_geometric_then_color_composition():
    # output = color_map(rotate90(input)), a genuine 2-stage case neither
    # geometry nor color mapping alone can express (rotate90 alone keeps
    # color 1, color mapping alone can't rotate).
    pairs = [
        Pair(input=[[1, 0], [0, 0]], output=[[0, 9], [0, 0]]),
        Pair(input=[[0, 1], [0, 0]], output=[[0, 0], [0, 9]]),
    ]
    compositions = find_compositions(pairs)
    labels = [c.label for c in compositions]
    assert any(label.startswith("rotate90->color:") for label in labels)


def test_finds_geometric_then_crop_composition():
    # output = crop(flip_horizontal(input)): flip alone changes shape not
    # at all here in the wrong way, crop alone (ADR 0043) never applies to
    # a flipped orientation.
    pairs = [
        Pair(input=[[1, 2, 9], [3, 4, 9]], output=[[2, 1]]),
        Pair(input=[[5, 6, 9], [7, 8, 9]], output=[[6, 5]]),
    ]
    compositions = find_compositions(pairs)
    labels = [c.label for c in compositions]
    assert any("flip_horizontal->crop:" in label for label in labels)
    match = next(c for c in compositions if "flip_horizontal->crop:" in c.label)
    assert match.apply([[1, 2, 9], [3, 4, 9]]) == [[2, 1]]


def test_no_candidate_when_nothing_composes():
    pairs = [
        Pair(input=[[1, 2], [3, 4]], output=[[7, 7, 7], [7, 7, 7], [7, 7, 7]]),
    ]
    assert find_compositions(pairs) == []


def test_ambiguous_when_multiple_compositions_fit():
    # A constant grid is invariant under every geometric stage1, so any
    # stage1 choice followed by the same color mapping fits equally well
    # - the pool must contain more than one distinct composition.
    pairs = [
        Pair(input=[[3, 3], [3, 3]], output=[[7, 7], [7, 7]]),
    ]
    compositions = find_compositions(pairs)
    assert len(compositions) > 1


def test_identity_stage1_is_never_used():
    pairs = [
        Pair(input=[[1, 2], [3, 4]], output=[[1, 2], [3, 4]]),
    ]
    compositions = find_compositions(pairs)
    assert all(not c.label.startswith("identity->") for c in compositions)
