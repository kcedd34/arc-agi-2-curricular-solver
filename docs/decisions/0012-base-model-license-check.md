# 0012 - Base model license check against the Open Source AI Definition

**Status:** Informative (2026-09-07)

## Context

Official rules Section 2.5.a requires that, to be eligible for any prize,
the winning submission's system, model, and weights/parameters be under a
license meeting the Open Source Initiative's [Open Source AI Definition
(OSAID) 1.0](https://opensource.org/ai/open-source-ai-definition)
checklist, not merely "free for commercial use". This ADR checks whether
the base model currently used for TTT (`Qwen/Qwen3-4B`, decided in
[ADR 0003](0003-base-model-and-finetuning-strategy.md)) meets that bar.
No change is made here; this is a diagnostic finding.

## What OSAID 1.0 actually requires

Confirmed directly from the OSI's own definition page:

- **Four freedoms:** use for any purpose, study, modify, and share the
  system, all without needing separate permission.
- **Data transparency:** "sufficiently detailed information about the
  data used to train the system so that a skilled person can build a
  substantially equivalent system" - a full description of training
  data (provenance, scope, characteristics, how it was obtained/
  selected), labeling/filtering methodology, a listing of publicly
  available training data with sources, and a listing of third-party
  data obtainable for a fee. This information must itself be available
  under OSI-approved terms.
- **Code:** the complete source code used to train and run the system
  (data processing/filtering, training code with arguments/settings,
  validation/testing, supporting libraries, inference code), under
  OSI-approved licenses.
- **Weights/parameters:** must be made available under OSI-approved
  terms (a permissive license, or another legal instrument that secures
  the same freedoms).

The weights license is only one of the four pillars; data transparency
and training-code availability are separate, independently required
pillars.

## Model identified

`Qwen/Qwen3-4B` (dense, 4B-parameter variant), loaded directly from
Hugging Face by `src/solvers/neural/model_loader.py` via Unsloth's
`FastLanguageModel.from_pretrained(model_name="Qwen/Qwen3-4B", ...)`
(`src/solvers/neural/config.py:10`, unchanged since ADR 0003). No local
fork or mirror is used, the model name is passed straight through to
Hugging Face.

## Findings

- **Weights license:** confirmed by fetching
  `https://huggingface.co/Qwen/Qwen3-4B/blob/main/LICENSE` directly -
  standard, unmodified Apache License 2.0 text (opens with the official
  "Apache License, Version 2.0, January 2004" preamble), copyright
  notice "Copyright 2024 Alibaba Cloud", no added field-of-use
  restriction, no competing-product clause, no active-user threshold.
  Apache 2.0 is an OSI-approved license, so the weights pillar is met on
  its own.
- **Training code:** Alibaba's own Qwen3 announcement
  ([qwenlm.github.io/blog/qwen3](https://qwenlm.github.io/blog/qwen3/))
  does not publish the data processing/filtering scripts, the training
  scripts, or the exact hyperparameters used to produce the released
  weights - only inference/deployment examples via existing frameworks
  (transformers, vLLM, etc.) are provided. This pillar is **not met**.
- **Data transparency:** the same announcement states pretraining used
  "nearly twice" Qwen2.5's 18 trillion tokens (about 36 trillion),
  covering 119 languages, collected "not only from the web but also
  from PDF-like documents" processed with Qwen2.5-VL, plus synthetic
  data for math/code. No dataset names, sources, licensing, or a
  public/proprietary split are given, and no OSI-approved-terms
  disclosure exists. This pillar is **not met** - this is the same gap
  publicly documented for essentially every major "open-weight" model
  (confirmed via web search: OSI's own validation phase found only a
  handful of models fully compliant - Pythia (EleutherAI), OLMo (AI2),
  Amber/CrystalCoder (LLM360), T5 (Google) - none of which are Qwen,
  Llama, Mistral, or DeepSeek).

## Assessment

**Does not meet the OSAID checklist.** The weights license (Apache 2.0)
clears the bar on its own, but the data-transparency and training-code
pillars are not met - Qwen3-4B is "open-weight", not "open-source AI" by
OSAID's stricter definition. This is not a Qwen-specific weakness; it is
the standard gap between "open-weight" and full OSAID compliance shared
by nearly every currently competitive LLM (Llama, Mistral, DeepSeek
included). NVARC's 2025 win with the same base model does not resolve
this for 2026: either the OSAID prize-eligibility clause is new this
year, or it was not enforced/checked in 2025 - either way it is a live
risk for this project's prize eligibility if it stands as currently
worded.

## Plausible alternatives (not decided, for a future joint decision)

Models publicly confirmed to have passed OSI's own OSAID validation
(same parameter-count neighborhood where available):

| Model | Org | Params | Notes |
|---|---|---|---|
| OLMo 2 | Allen Institute for AI (AI2) | 1B / 7B / 13B / 32B | Apache 2.0 weights, training code, training data, and eval suite all published; no exact 4B checkpoint, 7B is the nearest size |
| Pythia | EleutherAI | 14M-12B (suite) | Apache 2.0, full data/code/checkpoints, base (non-instruct) architecture, older (GPT-NeoX-based), no documented ARC-AGI-2 result |
| Amber / CrystalCoder | LLM360 | 7B | Apache 2.0, full data/code/checkpoints published |

None of these have a documented ARC-AGI-2 result to anchor an accuracy
expectation the way ADR 0003 anchored Qwen3-4B to NVARC's 24%; switching
would trade a validated accuracy reference for OSAID compliance. That
trade-off, and whether the rule even applies as read, is a decision for
the user, not made here.

## References

- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md)
- [Open Source AI Definition 1.0](https://opensource.org/ai/open-source-ai-definition)
- [Qwen/Qwen3-4B LICENSE](https://huggingface.co/Qwen/Qwen3-4B/blob/main/LICENSE)
- [Qwen3: Think Deeper, Act Faster](https://qwenlm.github.io/blog/qwen3/)
