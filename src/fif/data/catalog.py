"""Read the dataset registry ``data/catalog.yaml`` and verify raw-file checksums.

Inputs: ``data/catalog.yaml`` (dataset id -> files with sha256).
Outputs: Python dicts; :func:`verify` raises if any raw file changed.
Units: none. See docs/ARCHITECTURE.md (Data layer).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = REPO_ROOT / "data" / "catalog.yaml"


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, dict]:
    """Return ``{dataset_id: entry}`` from the YAML registry."""
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return {d["id"]: d for d in doc["datasets"]}


def raw_path(dataset_id: str, name_contains: str, root: Path = REPO_ROOT) -> Path:
    """Absolute path of the single registered file of ``dataset_id`` whose path contains ``name_contains``."""
    entry = load_catalog(root / "data" / "catalog.yaml")[dataset_id]
    hits = [f["path"] for f in entry["files"] if name_contains in f["path"]]
    if len(hits) != 1:
        raise KeyError(f"{dataset_id}: expected 1 file matching {name_contains!r}, got {hits}")
    return root / hits[0]


def verify(root: Path = REPO_ROOT) -> int:
    """Check sha256 of every registered file; return the number checked. Raises ValueError on mismatch."""
    checked = 0
    for entry in load_catalog(root / "data" / "catalog.yaml").values():
        for f in entry["files"]:
            path = root / f["path"]
            if entry.get("in_git") is False and not path.exists():
                continue  # large reference file fetched on demand (e.g. the FLEX TP PDF)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != f["sha256"]:
                raise ValueError(f"checksum mismatch: {f['path']}")
            checked += 1
    return checked
