# Windows 11 Development Workflow

This guide describes a conservative local workflow for developing `wraplorenzmie` on Windows 11 with conda, editable installs, and Git.

## 1. Prerequisites

Install these tools first:

- Miniconda or Anaconda
- Git for Windows
- A Python-aware editor such as VS Code

Use PowerShell or the Anaconda Prompt. The examples below assume the repository is at:

```powershell
E:\ResearchCode\wraplorenzmie
```

## 2. Create a Conda Environment

From a terminal:

```powershell
conda create -n wraplorenzmie python=3.10
conda activate wraplorenzmie
python -m pip install --upgrade pip
```

The package metadata currently targets Python 3.10 or newer. If dependency resolution becomes difficult on Windows, start with Python 3.10 because the pinned scientific stack is older.

## 3. Install the Repository in Editable Mode

Move to the repository root:

```powershell
cd E:\ResearchCode\wraplorenzmie
python -m pip install -e .
```

Editable mode means Python imports the package from this working tree. Changes to `.py` files are available immediately in new Python sessions without reinstalling.

For notebook workflows, install a kernel for the conda environment:

```powershell
python -m pip install ipykernel
python -m ipykernel install --user --name wraplorenzmie --display-name "Python (wraplorenzmie)"
```

Then select `Python (wraplorenzmie)` in Jupyter or VS Code.

## 4. Keep Data Outside the Repository

Raw videos, TIFF sequences, normalized frames, and fit outputs can be large. Store them outside the Git checkout when possible:

```text
E:\ResearchData\lorenzmie\raw
E:\ResearchData\lorenzmie\processed
E:\ResearchData\lorenzmie\results
```

If local data folders are created inside the repository during exploration, `.gitignore` excludes common names such as `data/`, `raw_data/`, `processed_data/`, and `results/`.

## 5. Basic Import Check

After installing, verify the package imports:

```powershell
python -c "import wraplorenzmie; print(wraplorenzmie.__all__)"
```

For fitting-related work, also check the wrapper imports:

```powershell
python -c "from wraplorenzmie.fits.fit import fitting; print(fitting)"
```

## 6. Git Workflow

Check the current branch and pending changes before editing:

```powershell
git status
git branch --show-current
```

Create a focused branch:

```powershell
git switch -c codex/windows-workflow-docs
```

Review changes before committing:

```powershell
git diff
git status
```

Stage and commit only the intended files:

```powershell
git add AGENTS.md .gitignore docs/windows_workflow.md
git commit -m "Add Windows workflow documentation"
```

Push the branch:

```powershell
git push -u origin codex/windows-workflow-docs
```

## 7. Fitting Development Notes

The current high-level fitting wrapper is `wraplorenzmie/fits/fit.py`. Its `fit_video` method expects a video-like object with `get_image`, `get_next_image`, `get_length`, `background`, and `dark_count`.

When adding new input formats such as TIFF image sequences, prefer adding a compatible reader object instead of changing `fit_video`. This preserves existing movie behavior while allowing new workflows to pass a different frame source.

## 8. Common Windows Notes

- Prefer `python -m pip` over bare `pip` to ensure packages install into the active conda environment.
- If PowerShell script execution blocks activation, use Anaconda Prompt or initialize conda for PowerShell.
- Avoid spaces and non-ASCII characters in experiment data paths when troubleshooting older scientific packages.
- Keep paths configurable in notebooks rather than hard-coding machine-specific locations.

