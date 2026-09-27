# 0014 - Replace the base model with an OSAID-compliant alternative

**Status:** Accepted (2026-09-07)

## Context

[ADR 0012](0012-base-model-license-check.md) found that `Qwen/Qwen3-4B`
does not meet the Open Source AI Definition (OSAID) checklist required
by the official rules (Section 2.5.a) for prize eligibility: weights are
Apache 2.0, but training code is unpublished and training-data
disclosure is only high-level. Per the new foundational constraint
(CLAUDE.md Section 2, decided the same day), license/OSAID compliance is
now checked before any performance evaluation, and no non-compliant
component is allowed in the main pipeline. This ADR selects and adopts a
replacement base model.

## Candidates evaluated

Restricted to models that passed OSI's own OSAID validation phase
(confirmed via web search, same set found in ADR 0012): OLMo (AI2),
Pythia (EleutherAI), Amber / CrystalCoder (LLM360), T5 (Google, encoder-
decoder, not a fit for this decoder-only generation task, excluded).
Models sometimes mentioned as "would probably pass if they changed their
license" (BLOOM, StarCoder2, Falcon) are explicitly **not** validated and
were excluded on that basis alone, consistent with the "verifiably
compliant" wording of the new constraint.

| Model | Params available | Reasoning/code proxy benchmarks | Compliance notes | 8GB VRAM / Unsloth fit |
|---|---|---|---|---|
| OLMo 2 (AI2), base | 1B / 7B / 13B / 32B | 7B: MMLU 63.7, GSM8K 67.5 (from the model's own published eval table) | Apache 2.0 weights; pretraining (OLMo-Mix-1124, 3.9T tokens) and mid-training (Dolmino-Mix-1124, 843B tokens) data both published on Hugging Face under Apache 2.0; training code and eval suite published | Unsloth lists OLMo2 as supported (pre-quantized 4-bit checkpoints exist under the `unsloth/` org); Unsloth's own published figure for 7B QLoRA is ~5GB, fits within 8GB with reduced batch size |
| OLMo 2 (AI2), Instruct | Same sizes | Same base scores plus instruction-following (Tulu 3 SFT + DPO + RLVR) | Apache 2.0 weights, but the model card states the SFT data mix includes "outputs generated from third party models" **subject to the Gemma Terms of Use** - a non-OSI-approved, restricted license, on part of the post-training data | Same as base |
| Pythia | 14M-12B (suite) | No comparably strong published reasoning benchmark; explicitly designed for interpretability research (fixed data order/checkpoints across the whole suite), not competitive performance; predates the 2024-2025 generation of heavily-curated pretraining corpora | Apache 2.0, full data/code/checkpoints, cleanly compliant | 6.9B/12B sizes plausible in 8GB at 4-bit, but no meaningful accuracy upside found |
| Amber / CrystalCoder | 7B | Older (2023) LLM360 release, general benchmarks below contemporaneous 7B models; no standout code/reasoning result found | Apache 2.0, full data/code/checkpoints, cleanly compliant | 7B, similar VRAM profile to OLMo 2 7B |

## Decision

Adopt **`allenai/OLMo-2-1124-7B`, the base (non-instruct) checkpoint**,
as the new TTT base model.

Reasoning:

- It has the strongest documented reasoning/code benchmarks of the fully
  OSAID-validated candidates (MMLU 63.7, GSM8K 67.5 for the 7B base
  checkpoint), clearly ahead of Pythia and Amber/CrystalCoder, both
  older 2023-era releases with no comparable published results.
- The **base** checkpoint is chosen over the Instruct checkpoint
  specifically to avoid the Gemma-Terms-of-Use gray area found on the
  Instruct variant's post-training data mix (Tulu 3 SFT includes
  third-party-model outputs under a non-OSI-approved license). The base
  checkpoint's own training data (OLMo-Mix-1124, Dolmino-Mix-1124) is
  entirely first-party and Apache 2.0. Given the explicit
  "verifiably compliant" bar the project just adopted, the base
  checkpoint is the safer choice even though it costs some
  instruction-following quality.
- This project's solver does not depend on the base model already being
  instruction-tuned: `neural_solver.py` runs per-task LoRA TTT
  (`train_on_task`) before generation on every task, which is itself a
  form of task-specific fine-tuning on top of whatever the starting
  checkpoint is. The existing `prompt_builder.py` prompt format was
  never instruction-tuned-specific to begin with.
- Unsloth explicitly supports OLMo2 (confirmed via a GitHub issue
  referencing "OLMo2 already supported" and pre-existing
  `unsloth/OLMo-2-*-unsloth-bnb-4bit` checkpoints on Hugging Face), and
  publishes ~5GB VRAM for 7B QLoRA, which fits the project's 8GB budget
  with a reduced batch size, the same constraint already in place for
  Qwen3-4B.
- OLMo2's attention/FFN projection modules use the same naming
  (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`,
  `down_proj`) as the existing `lora_target_modules` config, confirmed
  against HuggingFace `transformers`' OLMo2 implementation, so no change
  is needed there.

## Accuracy expectation caveat

No documented ARC-AGI-2 result exists for OLMo 2 (unlike Qwen3-4B, whose
choice in ADR 0003 was anchored to NVARC's 24% private-set result). This
is genuinely unknown territory: OLMo 2 7B has stronger general
reasoning/math benchmarks than Qwen3-4B on paper, but it is also a
**base**, non-instruction-tuned checkpoint being asked to follow a
structured grid-output format cold (before per-task TTT), which
Qwen3-4B (already instruction-tuned) did not have to contend with.
Accuracy after this swap may be better or worse than the 24% reference;
it is not knowable without running the evaluation, which is deliberately
deferred (see Consequences).

## Consequences

- `src/solvers/neural/config.py`'s `NeuralSolverConfig.model_name`
  changes from `"Qwen/Qwen3-4B"` to `"allenai/OLMo-2-1124-7B"`.
  `lora_target_modules` unchanged.
- `CLAUDE.md` Section 3 (decided technical stack) updated to name the
  new base model and reference this ADR instead of ADR 0003 alone.
- `pytest tests/` (pure-logic, no GPU) re-run to confirm the config
  change doesn't break anything structurally; this does not validate
  accuracy or even that the model loads on GPU.
- A real GPU smoke test and the 8-task evaluation re-run are explicitly
  **not** done in this ADR. Per the user's explicit instruction, they
  wait until the ADR 0010 raw-generation-text investigation (still
  in progress, background capture run not yet finished) lands with a
  parsing-fix verdict, so that a new evaluation run doesn't conflate two
  variables (new base model + still-broken parsing) in the same result.

## Alternatives considered

- **`allenai/OLMo-2-1124-7B-Instruct`**: rejected, see the Gemma-Terms-
  of-Use gray area above - the safer, cleanly-compliant base checkpoint
  is preferred given the project's new "verifiably compliant" bar.
- **Pythia (up to 12B)**: rejected, no competitive reasoning/code
  benchmark result found; the suite is explicitly designed for
  interpretability research, not accuracy.
- **Amber / CrystalCoder (LLM360, 7B)**: rejected, older 2023-era
  release, no standout benchmark result over OLMo 2.
- **OLMo 2 13B / 32B**: rejected for now, larger sizes leave less VRAM
  headroom for per-task TTT on top of the base 4-bit load within the
  8GB budget; 7B is already at Unsloth's own stated minimum comfortable
  size for 8GB.
- **Keep Qwen3-4B and dispute the rule's applicability**: rejected per
  the user's explicit instruction to not risk disqualification over the
  model choice.

## References

- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md) (superseded on the model-choice question by this ADR; TTT/LoRA/Unsloth strategy itself unchanged)
- [ADR 0012 - Base model license check](0012-base-model-license-check.md)
- [Open Source AI Definition 1.0](https://opensource.org/ai/open-source-ai-definition)
- [allenai/OLMo-2-1124-7B](https://huggingface.co/allenai/OLMo-2-1124-7B)
- [allenai/OLMo-2-1124-7B-Instruct](https://huggingface.co/allenai/OLMo-2-1124-7B-Instruct) (Gemma Terms of Use note)
