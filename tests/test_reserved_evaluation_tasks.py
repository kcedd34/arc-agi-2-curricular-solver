from src.evaluation.reserved_evaluation_tasks import reserved_evaluation_task_ids


def test_reserved_task_ids_is_union_of_sanity_and_validation_at_default_seed():
    reserved = reserved_evaluation_task_ids(seed=42)
    # Real ADR 0034 sample size is 40, ADR 0017/0023/0026/0027's is 8, but
    # the two tiers are not disjoint (validation samples from the full
    # evaluation pool without excluding the sanity 8), so the union is
    # smaller than the sum.
    assert len(reserved) == 44


def test_reserved_task_ids_includes_known_overlap_between_sanity_and_validation():
    reserved = reserved_evaluation_task_ids(seed=42)
    # Confirmed by direct computation: these 4 task ids are selected by
    # both the sanity and the validation tier at the default seed.
    for task_id in ("0934a4d8", "135a2760", "142ca369", "16de56c4"):
        assert task_id in reserved


def test_reserved_task_ids_is_deterministic_across_calls():
    assert reserved_evaluation_task_ids(seed=42) == reserved_evaluation_task_ids(seed=42)


def test_reserved_task_ids_changes_with_a_different_seed():
    default_seed_ids = reserved_evaluation_task_ids(seed=42)
    other_seed_ids = reserved_evaluation_task_ids(seed=7)
    assert default_seed_ids != other_seed_ids
