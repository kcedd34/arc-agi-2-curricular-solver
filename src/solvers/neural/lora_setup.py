"""Attaches/detaches a fresh LoRA adapter for each ARC task.

Every task must start from the same frozen base weights, with no
leakage of one task's fine-tuning into the next (per-task TTT, ADR 0003).
"""
from unsloth import FastLanguageModel

from src.solvers.neural.config import NeuralSolverConfig


def attach_fresh_lora(model, config: NeuralSolverConfig):
    return FastLanguageModel.get_peft_model(
        model,
        r=config.lora_rank,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.lora_target_modules,
    )


def detach_lora(model):
    return model.unload()


def attach_pretrained_lora(model, config: NeuralSolverConfig, adapter_dir: str):
    """Loads a cross-task-pretrained LoRA adapter onto the frozen base
    model, trainable so per-task TTT can continue fine-tuning it on top of
    it (the warm-start counterpart of attach_fresh_lora), see
    docs/decisions/0036-piloto-pretreino-cross-task.md.

    Builds the adapter via attach_fresh_lora (not peft.PeftModel.from_pretrained
    directly) and loads the saved weights into it, so the warm-started model
    keeps Unsloth's fast training kernels: those are wired up inside
    FastLanguageModel.get_peft_model (which attach_fresh_lora calls), and a
    plain PeftModel.from_pretrained bypasses that patching entirely, which
    was found to cost a 55-70x per-step slowdown (measured 2026-09-14, pilot
    v2 run), see docs/decisions/0039-piloto-pretreino-v2-comparacao-pareada.md.
    """
    from peft import set_peft_model_state_dict
    from peft.utils import load_peft_weights

    peft_model = attach_fresh_lora(model, config)
    adapter_weights = load_peft_weights(adapter_dir)
    set_peft_model_state_dict(peft_model, adapter_weights)
    return peft_model
