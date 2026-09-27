from pathlib import Path

from src.curriculum.partition import partition_training_tasks

TRAINING_DIR = Path("data/ARC-AGI-2/data/training")


def test_partition_is_deterministic():
    p1 = partition_training_tasks(TRAINING_DIR)
    p2 = partition_training_tasks(TRAINING_DIR)
    assert p1 == p2


def test_partition_disjoint_and_covers_all_tasks():
    partition = partition_training_tasks(TRAINING_DIR)
    probe = set(partition["probe_pool"])
    curricular = set(partition["curricular_pool"])
    assert probe.isdisjoint(curricular)
    assert len(probe) + len(curricular) == partition["total_training_tasks"]


def test_probe_pool_size_default_200():
    partition = partition_training_tasks(TRAINING_DIR)
    assert partition["probe_pool_size"] == 200


def test_007bbfb7_pinned_to_curricular_pool():
    partition = partition_training_tasks(TRAINING_DIR)
    assert "007bbfb7" in partition["curricular_pool"]
    assert "007bbfb7" not in partition["probe_pool"]


def test_different_seed_gives_different_partition():
    p1 = partition_training_tasks(TRAINING_DIR, seed=1)
    p2 = partition_training_tasks(TRAINING_DIR, seed=2)
    assert p1["probe_pool"] != p2["probe_pool"]
