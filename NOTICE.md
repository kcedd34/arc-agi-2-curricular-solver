# Licensing notice

This repository uses two licenses.

- **Code and documentation** (everything under `src/`, `tests/`, `docs/`, `notebooks/`, and
  this repository's own text) are licensed **CC BY 4.0** (see [LICENSE](LICENSE)), per the
  ARC Prize 2026 open-source requirement.
- **Data derived from the ARC-AGI-2 dataset** is licensed **Apache 2.0**, matching the
  dataset's own license (ARC Prize Foundation, `https://github.com/arcprize/ARC-AGI-2`),
  because it is a derivative of that data rather than original code or prose. This applies
  to:
  - `outputs/curriculum/kaggle_run_v1/submission.json`: the frozen output grids the
    submitted kernel produced for the official ARC-AGI-2 evaluation tasks.
  - Any other versioned file whose content is predicted or reproduced task grids rather
    than analysis, code, or task identifiers.

The ARC-AGI-2 dataset itself is not redistributed in this repository (see `data/` in
[.gitignore](.gitignore)); reproducing the results requires cloning it separately from its
own Apache-2.0-licensed source, as described in [README.md](README.md).

Task identifiers (e.g. `17b866bd`) and references to them in prose, code, or catalogues are
not, by themselves, treated as dataset data for licensing purposes.
