# AGENTS.md

Development guidance for agents and contributors working in this repository.

## Scope

This repository wraps a vendored copy of `pylorenzmie` for Lorenz-Mie holography particle tracking. Treat the wrapper code, vendored theory/fitting code, notebooks, and experimental data paths as separate concerns.

## Core Rules

- Do not modify core fitting behavior unless the task explicitly asks for it.
- Keep changes narrowly scoped to the requested files and behavior.
- Prefer additive adapters over changing existing APIs, especially `fitting.fit_video`.
- Preserve existing notebook workflows unless a migration is requested.
- Do not commit raw videos, TIFF image sequences, processed data, generated fit outputs, or local caches.
- Use Windows-compatible paths in documentation examples where possible.
- Avoid hard-coded absolute paths in source code and notebooks.
- Keep vendored `wraplorenzmie/pylorenzmie` changes separate from wrapper changes.

## Repository Layout

- `wraplorenzmie/fits/fit.py`: high-level fitting wrapper and current `fit_video` implementation.
- `wraplorenzmie/utilities/utilities.py`: video reader, image normalization, cropping, and localization helpers.
- `wraplorenzmie/pylorenzmie/`: vendored Lorenz-Mie analysis, fitting, and theory implementation.
- `tuto/`, `test/`, `test_lorenzmie/`: notebooks and sample exploratory material.
- `webapp/`: Streamlit single-image fitting app.
- `docs/`: project workflow and contributor documentation.

## Development Environment

- Use a conda environment on Windows 11.
- Install the package in editable mode with `python -m pip install -e .`.
- Run commands from the repository root unless noted otherwise.
- Keep generated data outside the repository when practical, for example in `E:\ResearchData\...`.

## Testing and Verification

- For code changes, run the smallest relevant test or import check first.
- For fitting changes, verify both a single-frame path and any video/sequence path touched by the change.
- For documentation-only changes, inspect the rendered Markdown mentally for command correctness and Windows path clarity.

## Git Hygiene

- Check status before and after edits.
- Do not revert unrelated user changes.
- Keep commits focused: docs, ignore rules, fitting changes, and notebook updates should be separate when possible.
- Use descriptive branch names, for example `codex/windows-workflow-docs` or `codex/tiff-sequence-reader`.

## Data and Outputs

The repository should not track:

- raw videos or image sequences,
- background frames generated from experiments,
- normalized or processed images,
- fit result arrays, tables, plots, or exports,
- local conda or virtual environments,
- notebook checkpoints and transient caches.

