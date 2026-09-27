"""Per-task features for the arc2_only diagnostic (ADR 0095). Train pairs
only; the result is a grouping, never a solver input."""
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

from src.curriculum.diagnostics.arc2_predictor import KeyFit, fit_all_keys
from src.curriculum.diagnostics.concept_signatures import load_train, missing_concept
from src.curriculum.loader import TrainPair

NEAR_MISS_ACCURACY = 0.95
NEAR_MISS_RECALL = 0.8
G_KEY = "mesma forma: explicada por chave local"
G_NEAR = "mesma forma: quase-acerto de chave (>=80% das celulas alteradas)"
G_STRUCT = "mesma forma: nao explicada por chave local (contextual/composta)"
G_SHAPE = "forma diferente"


@dataclass
class TaskFeatures:
    task_id: str
    label: str
    same_shape: bool
    num_pairs: int
    changed_fraction: float
    best_key: str
    best_exact_pairs: int
    best_cell_accuracy: float
    best_changed_recall: float
    group: str


def _same_shape(pairs: List[TrainPair]) -> bool:
    return all(len(p.input) == len(p.output) and len(p.input[0]) == len(p.output[0]) for p in pairs)


def _changed_fraction(pairs: List[TrainPair]) -> float:
    total = changed = 0
    for p in pairs:
        for row_in, row_out in zip(p.input, p.output):
            total += len(row_in)
            changed += sum(a != b for a, b in zip(row_in, row_out))
    return changed / total


def _best_key(fits: Dict[str, KeyFit], num_pairs: int):
    for name, fit in fits.items():
        if fit.exact_pairs == num_pairs:
            return name, fit
    return max(fits.items(), key=lambda item: item[1].changed_recall)


def _group(fit: KeyFit, num_pairs: int) -> str:
    if fit.exact_pairs == num_pairs:
        return G_KEY
    near = fit.cell_accuracy >= NEAR_MISS_ACCURACY and fit.changed_recall >= NEAR_MISS_RECALL
    return G_NEAR if near else G_STRUCT


def compute_features(task_id: str, train: List[dict]) -> TaskFeatures:
    pairs = [TrainPair(p["input"], p["output"]) for p in train]
    label = missing_concept(train)
    if not _same_shape(pairs):
        return TaskFeatures(task_id, label, False, len(pairs), 1.0, "-", 0, 0.0, 0.0, G_SHAPE)
    name, fit = _best_key(fit_all_keys(pairs), len(pairs))
    return TaskFeatures(
        task_id, label, True, len(pairs), _changed_fraction(pairs), name,
        fit.exact_pairs, fit.cell_accuracy, fit.changed_recall, _group(fit, len(pairs)),
    )


def features_for_ids(ids: List[str], training_dir: Path) -> List[TaskFeatures]:
    out = []
    for task_id in ids:
        try:
            out.append(compute_features(task_id, load_train(training_dir / f"{task_id}.json")))
        except Exception as exc:  # isolated per-task failure
            out.append(TaskFeatures(task_id, f"erro:{type(exc).__name__}", False, 0, 0.0, "-", 0, 0.0, 0.0, "erro"))
    return out


def to_dicts(features: List[TaskFeatures]) -> List[dict]:
    return [asdict(f) for f in features]
