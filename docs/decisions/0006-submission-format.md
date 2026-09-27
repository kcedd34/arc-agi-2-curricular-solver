# 0006 - Submission format

**Status:** Accepted (2026-09-06)

## Context

The final Kaggle submission is a single `submission.json` file. Its
exact structure must be followed precisely or the notebook submission
is rejected/scored as zero, so this is documented as its own ADR rather
than left implicit in code.

## Decision

`submission.json` is a JSON object (dictionary):

- Each key is a `task_id` (string), matching a key in the competition's
  `arc-agi_test_challenges.json` input file.
- Each value is a list of entry objects, one per expected test output
  for that task, **in the same order as the task's test inputs**.
- Each entry object has exactly two keys: `attempt_1` and `attempt_2`,
  each holding a predicted grid (a list of lists of integers 0-9).
- **Every** `task_id` present in the input challenges file must appear
  in `submission.json`, even if the solver produced no real prediction
  for it (use a placeholder grid rather than omitting the key).
- Both `attempt_1` and `attempt_2` are required even when the solver
  only produced one real candidate grid (reuse that same grid for both
  keys in that case).

Example (two tasks, the second with two test inputs):

```json
{"00576224": [{"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]}],
 "12997ef3": [{"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]},
              {"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]}]}
```

Implementation: [src/evaluation/submission_format.py](../../src/evaluation/submission_format.py)
(`build_submission`, `validate_submission`, `write_submission`), covered
by [tests/test_submission_format.py](../../tests/test_submission_format.py).
`validate_submission` is run against every local evaluation before it is
treated as a trustworthy result, so a format bug is caught long before
the real Kaggle submission.

## Consequences

- The evaluation harness (`src/evaluation/harness.py`) stays focused on
  scoring against locally-known outputs (public dataset); the
  submission-format concern (what the file looks like, independent of
  whether we know the right answer) is a separate module, one
  responsibility per file per project convention.
- The final Kaggle notebook must call `build_submission` +
  `validate_submission` + `write_submission` in that order before
  finishing, using whatever solver is current at submission time.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| Validate only informally / by eye before submitting | No extra code | Exactly the kind of mistake (missing task_id, wrong key name) that silently zeroes a submission |
| Encode format rules only as a docstring, no automated validation | Less code | Nothing catches a regression; contradicts Golden Rule 3 (every test run logged/verified) |
| Dedicated `submission_format.py` + unit tests (chosen) | Format bugs caught locally, before submission; documented once, checked automatically | One more small file to maintain |

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0005 - AI assistant usage in development](0005-ai-assistant-usage-in-development.md)
