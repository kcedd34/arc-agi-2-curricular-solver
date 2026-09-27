"""Deterministic concept classifier for the scale sweep (ADR 0093).

Assigns each task ONE label, the narrowest rule family whose signature
every train pair satisfies, in a fixed priority order. Labels are
concept-map ids (`outputs/curriculum/concept-map.json`) plus a few
extras with no map entry (`periodico_completar`, `remocao_por_propriedade`,
and the `outro_*` residuals). Train pairs only (RN-CUR-03/05); it is a
heuristic labeller, its precision is spot-checked, never assumed.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.curriculum import tag_signatures as sig
from src.curriculum.diagnostics import sig_geometry, sig_layout, sig_movement, sig_regions
from src.curriculum.library.objects.object_rearrangement import is_rearrangement_task
from src.curriculum.loader import Task, TrainPair

def load_train(task_path: Path) -> List[Dict]:
    with task_path.open(encoding="utf-8") as f:
        return json.load(f)["train"]


def _rearrangement(train: List[Dict]) -> bool:
    task = Task("t", [TrainPair(p["input"], p["output"]) for p in train], [])
    return is_rearrangement_task(task)


def _different_shape_label(train: List[Dict]) -> str:
    for detector in (sig_layout.enlargement_family, sig_layout.subgrid_overlay_family):
        label = detector(train)
        if label:
            return label
    if sig_layout.is_scalar_output(train):
        return "contagem_mais_frequente"
    if sig_layout.is_crop_family(train):
        return "recorte"
    return "outro_forma_diferente"


def _same_shape_addition_label(train: List[Dict]) -> str:
    if sig_regions.is_enclosed_fill_family(train):
        return "preencher_regiao_fechada"
    if sig_regions.is_ray_family(train):
        return "raio_ate_borda"
    if sig_regions.is_colored_line_family(train):
        return "objeto_linha_marcadores"
    return "outro_adicao"


def _narrow_family_label(train: List[Dict]) -> Optional[str]:
    if sig.is_halo_family(train):
        return "objeto_halo"
    if sig.is_connect_family(train):
        return "ligar_pontos_mesma_cor"
    if sig.is_translation_family(train):
        return "transladar"
    extreme = sig.paints_frequency_extreme(train)
    return "cor_extrema_frequencia" if extreme else None


def _movement_label(train: List[Dict]) -> Optional[str]:
    if not _rearrangement(train):
        return None
    return "cair_gravidade" if sig_movement.is_cell_gravity_family(train) else "mover_objetos"


def _same_shape_label(train: List[Dict]) -> str:
    label = _narrow_family_label(train) or _movement_label(train) or sig_geometry.completion_family(train)
    if label:
        return label
    return {
        "add": _same_shape_addition_label(train),
        "remove": "remocao_por_propriedade",
        "recolor": "recolorir_por_propriedade",
    }.get(sig.diff_kind(train), "outro_misto")


def missing_concept(train: List[Dict]) -> str:
    geometric = sig_geometry.geometric_family(train)
    if geometric:
        return geometric
    if sig.diff_kind(train) == "reshape":
        return _different_shape_label(train)
    return _same_shape_label(train)
