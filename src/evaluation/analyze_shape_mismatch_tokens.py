"""Token-count side of the ADR 0024 shape-mismatch analysis (question 3:
did generation stop via EOS or hit the max_new_tokens cap?).

Needs the OLMo-2-1124-7B tokenizer only (already cached locally in the
WSL venv from prior real runs, no new download, no model/GPU load).
Run inside the WSL venv:

    wsl -e bash -lc "cd /mnt/d/Projetos/kaggle_contest && source .venv312/bin/activate && python -m src.evaluation.analyze_shape_mismatch_tokens"

Retokenizes each raw completion .txt (already decoded with
skip_special_tokens=True, so any EOS token is not present in the text
itself). If the retokenized length is well below max_new_tokens (1024),
generation must have stopped before the cap, i.e. via EOS. If it lands
at or very near the cap, the cap was almost certainly hit instead
(EOS never fired within budget).
"""
from pathlib import Path

from transformers import AutoTokenizer

from src.solvers.neural.config import NeuralSolverConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "outputs" / "raw_generations" / "sanity_current_config" / "evaluation"

# The specific kept-prediction files identified by analyze_shape_mismatch.py
# for the 10 shape-mismatched held-out test pairs (task_id, filename).
FILES = [
    "current_config_0934a4d8_test_0_0.txt",
    "current_config_0934a4d8_test_0_1.txt",
    "current_config_135a2760_test_0_0.txt",
    "current_config_135a2760_test_0_1.txt",
    "current_config_136b0064_test_0_0.txt",
    "current_config_136b0064_test_0_1.txt",
    "current_config_13e47133_test_0_2.txt",
    "current_config_13e47133_test_0_4.txt",
    "current_config_13e47133_test_1_2.txt",
    "current_config_13e47133_test_1_3.txt",
    "current_config_142ca369_test_0_0.txt",
    "current_config_142ca369_test_0_1.txt",
    "current_config_142ca369_test_1_0.txt",
    "current_config_142ca369_test_1_1.txt",
    "current_config_16b78196_test_0_0.txt",
    "current_config_16b78196_test_0_2.txt",
    "current_config_16de56c4_test_0_1.txt",
    "current_config_16de56c4_test_0_2.txt",
    "current_config_16de56c4_test_1_1.txt",
    "current_config_16de56c4_test_1_2.txt",
    "current_config_1818057f_test_0_0.txt",
    "current_config_1818057f_test_0_1.txt",
]


def main():
    config = NeuralSolverConfig()
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    cap = config.max_new_tokens
    near_cap_threshold = cap - 10  # small margin for the char-slice boundary

    for fname in FILES:
        text = (RAW_DIR / fname).read_text(encoding="utf-8")
        token_count = len(tokenizer.encode(text))
        verdict = "HIT_CAP" if token_count >= near_cap_threshold else "stopped_early(EOS)"
        print(f"{fname}\ttokens={token_count}\tcap={cap}\t{verdict}")


if __name__ == "__main__":
    main()
