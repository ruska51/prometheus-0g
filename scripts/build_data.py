"""Rebuild data/interim and data/processed from data/raw with one command.

Usage (repository root): ``.venv/Scripts/python scripts/build_data.py``
Steps: verify raw checksums -> parse -> clean/flag -> validate schema -> write CSV + logs.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fif.data.build import build  # noqa: E402


def main() -> None:
    res = build()
    for name in ("flex", "cfig", "catalog"):
        df = res[name]
        flagged = (df["quality_flag"] != "").sum()
        print(
            f"{name:8} rows={len(df):4} flagged={flagged:3}"
            + (f" use_in_model={int(df['use_in_model'].sum())}" if "use_in_model" in df else "")
        )
    print(f"transform log entries: {len(res['log'])}")


if __name__ == "__main__":
    main()
