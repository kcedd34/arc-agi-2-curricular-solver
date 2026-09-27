from src.curriculum.diagnostics import sweep_aggregate as agg
from src.curriculum.diagnostics.origin import origin_of


def _rec(**kw):
    base = dict(num_candidates=1, num_distinct_predictions=1, solved=False, gabarito_rank=None,
                best_wrong_cells=3, top_description="", error=None)
    base.update(kw)
    return base


def test_near_miss_reason_ranking_beats_everything():
    assert agg.near_miss_reason(_rec(gabarito_rank=4)).startswith("ranking")


def test_near_miss_reason_shape_and_distance():
    assert "forma" in agg.near_miss_reason(_rec(best_wrong_cells=None))
    assert "quase" in agg.near_miss_reason(_rec(best_wrong_cells=agg.NEAR_CELLS))
    assert "longe" in agg.near_miss_reason(_rec(best_wrong_cells=agg.NEAR_CELLS + 1, num_distinct_predictions=2))


def test_group_by_label_puts_exclusive_examples_first():
    labels = {"a": "x", "b": "x", "c": "y"}
    origins = {"a": "arc1_training", "b": "arc2_only", "c": "arc2_only"}
    rows = agg.group_by_label(["a", "b", "c"], labels, origins)
    assert rows[0]["label"] == "x" and rows[0]["examples"] == ["b", "a"]
    assert rows[0]["exclusive"] == 1 and rows[0]["inherited"] == 1


def test_solved_by_origin_counts():
    records = {"a": _rec(solved=True), "b": _rec()}
    out = agg.solved_by_origin(["a", "b"], records, {"a": "arc2_only", "b": "arc2_only"})
    assert out["arc2_only"]["tasks"] == 2 and out["arc2_only"]["solved"] == 1


def test_origin_of_prefers_arc1_training():
    arc1 = {"arc1_training": {"a"}, "arc1_evaluation": {"b"}}
    assert origin_of("a", arc1) == "arc1_training"
    assert origin_of("b", arc1) == "arc1_evaluation"
    assert origin_of("c", arc1) == "arc2_only"
