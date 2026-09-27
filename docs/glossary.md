# Glossary

| Term | Definition |
|---|---|
| **Task** | A single ARC-AGI-2 evaluation unit: 2-4 input→output training pairs + 1+ test inputs with hidden output. |
| **Grid** | A rectangular matrix of integers 0-9 (each integer represents a color). Size varies per task, up to 30x30. |
| **DSL (Domain-Specific Language)** | A restricted language of primitives (rotate, flip, fill, count objects, map color, etc.) used to compose candidate programs that explain a task's transformation. |
| **Program synthesis** | An approach that searches, within a program space (usually defined by a DSL), for a program that correctly reproduces all training pairs of a task. |
| **Test-time training (TTT)** | Quickly adapting a model's parameters at inference time, using only the task's own training pairs (without retraining from scratch). |
| **Fine-tuning (LoRA)** | Adapting a pretrained model using low-rank adapters (Low-Rank Adaptation), much cheaper in memory/compute than retraining all weights. |
| **Semi-private eval set** | The subset of tasks used for the public leaderboard during the competition; not the final judging set. |
| **Private eval set** | The set of tasks never publicly exposed, used for the official final score (the "85% on private" competition goal). |
| **Exact match / exact scoring** | Scoring criterion: the predicted grid must be identical (dimensions and every cell) to the expected grid, no partial credit for partial matches. |
| **2 predictions per task** | Submission rule: for each test input, the solver must provide up to 2 candidate grids; the task scores if at least one matches exactly. |
| **ADR (Architecture Decision Record)** | A short document recording an architecture decision: context, decision, consequences, alternatives. See `docs/decisions/`. |
