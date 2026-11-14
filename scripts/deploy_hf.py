"""Deploy the dashboard to a public Hugging Face Space (Docker SDK) - stage 11, ADR-001 / ADR-038.

The token is read from the environment variable HF_TOKEN or from a file given by HF_TOKEN_FILE (default
~/.hf_token_prometheus); it is never written into the repository. The Space gets a copy of the files the app needs
(code, models, processed data, PSI tables, generated docs) plus a Space README with the YAML header; the GitHub
README stays the jury document.
Usage: ``.venv/Scripts/python scripts/deploy_hf.py [space_name]``
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ["app", "src", "models", ".streamlit", "data/processed", "data/catalog.yaml", "data/raw/psi_tables",
           "data/raw/nist", "data/raw/nasa_tr_r132", "docs", "Dockerfile", "requirements.txt", "LICENSE"]
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache"}
GITHUB = "https://github.com/ruska51/prometheus-0g"

SPACE_README = f"""---
title: Prometheus-0g
emoji: 🔥
colorFrom: blue
colorTo: red
sdk: docker
app_port: 8501
pinned: false
license: apache-2.0
short_description: Fire-safety insights from NASA microgravity combustion data
---

# Prometheus-0g - Will it burn on the Moon?

Physics-first, AI-assisted fire-safety insights from NASA microgravity combustion experiments
(NASA Space Apps Challenge 2026, "Flame in Freefall"). Source code, data provenance and documentation: {GITHUB}
"""


def token() -> str:
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"].strip()
    f = Path(os.environ.get("HF_TOKEN_FILE", Path.home() / ".hf_token_prometheus"))
    return f.read_text(encoding="utf-8").strip()


def stage(dst: Path) -> None:
    for item in INCLUDE:
        src = ROOT / item
        if src.is_dir():
            shutil.copytree(src, dst / item, ignore=shutil.ignore_patterns(*EXCLUDE_DIRS))
        else:
            (dst / item).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / item)
    (dst / "README.md").write_text(SPACE_README, encoding="utf-8")


def main(space: str = "prometheus-0g") -> None:
    api = HfApi(token=token())
    user = api.whoami()["name"]
    repo_id = f"{user}/{space}"
    api.create_repo(repo_id, repo_type="space", space_sdk="docker", private=False, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage(Path(tmp))
        api.upload_folder(folder_path=tmp, repo_id=repo_id, repo_type="space",
                          commit_message="Deploy Prometheus-0g dashboard from GitHub " + GITHUB)
    print(f"https://huggingface.co/spaces/{repo_id}")


if __name__ == "__main__":
    main(*sys.argv[1:])
