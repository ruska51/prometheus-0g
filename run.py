"""One-command pipeline for Windows, macOS and Linux (no make needed).

Usage (from the repository root, with any Python 3.12):
    python run.py setup     # create .venv and install pinned requirements + the fif package
    python run.py all       # verify raw data -> build data -> train models -> build insights -> tests
    python run.py app       # start the dashboard at http://localhost:8501
Single steps: verify, data, train, validate (stage-6 validation, ~5 min), insights, test, lint.
"""

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

STEPS = {
    "verify": [["scripts/verify_raw.py"]],
    "data": [["scripts/build_data.py"]],
    "train": [["scripts/train_models.py"]],
    "validate": [["scripts/validate.py"], ["scripts/label_sensitivity.py"], ["scripts/render_validation.py"]],
    "insights": [["scripts/build_insights.py"]],
    "test": [["-m", "pytest", "-q"]],
    "lint": [["-m", "ruff", "check", "."], ["-m", "ruff", "format", "--check", "."]],
    "app": [["-m", "streamlit", "run", "app/main.py"]],
}
ALL = ["verify", "data", "train", "insights", "test"]


def sh(args: list[str]) -> None:
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def setup() -> None:
    if sys.version_info[:2] != (3, 12):
        print(f"warning: tested with Python 3.12, running {sys.version.split()[0]}")
    if not PY.exists():
        venv.create(VENV, with_pip=True)
    sh([str(PY), "-m", "pip", "install", "-r", "requirements.txt"])
    sh([str(PY), "-m", "pip", "install", "-e", "."])


def main(task: str) -> None:
    if task == "setup":
        return setup()
    if not PY.exists():
        sys.exit("no .venv: run `python run.py setup` first")
    for step in ALL if task == "all" else [task]:
        if step not in STEPS:
            sys.exit(f"unknown task {step!r}; tasks: setup, all, " + ", ".join(STEPS))
        for args in STEPS[step]:
            sh([str(PY), *args])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
