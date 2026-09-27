"""Leave-one-pair-out key predictor (ADR 0095): how well is a same-shape
task explained by a per-cell context key? Reports, per key, the number of
held-out train pairs predicted exactly and the mean cell accuracy."""
from collections import Counter, defaultdict
from typing import Dict, List, NamedTuple, Tuple

from src.curriculum.diagnostics.arc2_keys import KEYS, KeyMap
from src.curriculum.loader import TrainPair


class KeyFit(NamedTuple):
    exact_pairs: int
    cell_accuracy: float
    changed_recall: float


def _learn(pairs: List[TrainPair], key_maps: List[KeyMap]) -> Dict:
    votes = defaultdict(Counter)
    for pair, keys in zip(pairs, key_maps):
        for (r, c), key in keys.items():
            votes[key][pair.output[r][c]] += 1
    return {key: counter.most_common(1)[0][0] for key, counter in votes.items()}


def _score(table: Dict, pair: TrainPair, keys: KeyMap) -> Tuple[float, int, int]:
    """(cell accuracy, changed cells hit, changed cells). Unseen keys fall
    back to the cell's own color (identity)."""
    hits = changed = changed_hits = 0
    for (r, c), key in keys.items():
        ok = table.get(key, key[0]) == pair.output[r][c]
        hits += ok
        if pair.input[r][c] != pair.output[r][c]:
            changed += 1
            changed_hits += ok
    return hits / len(keys), changed_hits, changed


def fit_key(pairs: List[TrainPair], key_fn) -> KeyFit:
    key_maps = [key_fn(p.input) for p in pairs]
    exact, accuracies, hit_total, changed_total = 0, [], 0, 0
    for held in range(len(pairs)):
        rest = [i for i in range(len(pairs)) if i != held]
        table = _learn([pairs[i] for i in rest], [key_maps[i] for i in rest])
        score = _score(table, pairs[held], key_maps[held])
        accuracies.append(score[0])
        exact += score[0] == 1.0
        hit_total += score[1]
        changed_total += score[2]
    recall = hit_total / changed_total if changed_total else 1.0
    return KeyFit(exact, sum(accuracies) / len(accuracies), recall)


def fit_all_keys(pairs: List[TrainPair]) -> Dict[str, KeyFit]:
    return {name: fit_key(pairs, fn) for name, fn in KEYS.items()}
