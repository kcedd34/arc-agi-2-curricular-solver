"""Tag refinement by signature (ADR 0085)."""
from src.curriculum.tag_refinement import diff_report, refined_ids, tag_counts


def _grid(cells, n=5):
    out = [[0] * n for _ in range(n)]
    for (r, c), v in cells.items():
        out[r][c] = v
    return out


def _halo_train():
    a = _grid({(2, 2): 5})
    return [{"input": a, "output": _grid({(2, 2): 5, (1, 2): 1, (3, 2): 1, (2, 1): 1, (2, 3): 1})}]


def test_position_tag_is_replaced_by_the_halo_family_and_ray_tag_dropped():
    ids = refined_ids(_halo_train(), ["objeto_posicao", "raio_ate_borda", "segmentacao_4"])
    assert ids == ["objeto_halo", "segmentacao_4"]


def test_tags_without_a_confirming_signature_are_left_alone():
    train = [{"input": _grid({(0, 0): 1}), "output": _grid({(0, 0): 1, (4, 3): 2, (2, 4): 9})}]
    ids = ["objeto_posicao", "contagem_mais_frequente"]
    assert refined_ids(train, ids) == ids


def test_refinement_is_idempotent():
    once = refined_ids(_halo_train(), ["objeto_posicao"])
    assert refined_ids(_halo_train(), once) == once


def test_diff_report_lists_only_changed_counts():
    before = {"tags": {"t": [{"concept_id": "a"}, {"concept_id": "b"}]}}
    after = {"tags": {"t": [{"concept_id": "b"}, {"concept_id": "c"}]}}
    rows = diff_report(before, after)
    assert tag_counts(after) == {"b": 1, "c": 1}
    assert any("| a | 1 | 0 |" in r for r in rows) and not any("| b |" in r for r in rows)
