# 0005 - AI assistant usage in development

**Status:** Accepted (2026-09-06), not an official ARC Prize Foundation
position (see Context).

## Context

This project is developed with the help of an AI coding assistant
(Claude Code), which is not a registered member of any team and is not
part of the submitted notebook's runtime.

The Kaggle forum thread "Rules clarification: hosted AI coding
assistants" (opened by Evan Moscoso, competition forum) asked whether a
hosted AI assistant may help write/review private code, as long as it
never receives Competition Data (task grids, solutions, task
identifiers). No official response from the ARC Prize Foundation or a
Kaggle moderator appears in that thread. One participant reply, from
CPMP (reported at the time as the 2nd-ranked entry on the competition
leaderboard), states that many competitors already use coding
assistants like Claude Code or Codex, and that the only real limit is
not spending an unreasonable amount of money doing so.

Two rules are unambiguous regardless of how this thread is resolved:

- **No internet access enabled** during notebook evaluation. The
  submitted notebook never calls any LLM API at runtime, this is not
  negotiable and holds independent of this ADR (see Golden Rule 4 in
  CLAUDE.md).
- The competition's data security language (rules Section 2.4.b) is
  about **Competition Data**, meaning the data distributed through the
  Kaggle competition's own Data tab.

## Decision

Claude Code is used normally for development, writing the solver code,
tests, Docker/WSL2 setup, and documentation, with two safeguards to
remove ambiguity rather than depend on the forum thread being the final
word:

1. The submitted notebook never makes an API call to any LLM at
   evaluation time, enforced independently by the "no internet access"
   rule.
2. The task dataset used during development (train/evaluation splits)
   is pulled from the ARC Prize Foundation's public GitHub repository
   (Apache 2.0 license), not from Kaggle's competition-specific Data
   tab. This keeps the assistant from ever handling data under the
   stricter Competition Data definition, since the GitHub copy is
   public and equally accessible to anyone, inside or outside the
   competition.

## Consequences

- No change to how the project is developed day-to-day; this ADR makes
  an already-existing practice explicit and reviewable.
- If the ARC Prize Foundation later publishes an official clarification
  that contradicts this reading, this ADR is revisited immediately.
- Safeguard 2 is also why `data/ARC-AGI-2/` is cloned directly from
  `github.com/arcprize/ARC-AGI-2` (see README.md), not downloaded from
  Kaggle.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| Rely only on the forum thread as justification | Simple | No official response in the thread; a single competitor's comment isn't a rules citation |
| Stop using an AI assistant for development entirely | Removes all ambiguity | Contradicts the project's own working method (Claude Code is used throughout, see CLAUDE.md); no rule found that actually requires this |
| Two explicit safeguards (chosen) | Makes the position defensible independent of the thread's outcome | Requires cloning the dataset from GitHub instead of Kaggle's Data tab, a minor extra setup step |

## References

- Kaggle forum thread "Rules clarification: hosted AI coding
  assistants" (competition forum)
- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
