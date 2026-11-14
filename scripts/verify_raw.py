"""Check that raw data are unchanged: every file registered in data/catalog.yaml matches its sha256
(fif.data.catalog.verify; on-demand files such as the FLEX TP PDF are checked only when present).
Usage: ``python scripts/verify_raw.py`` - exit code 1 on any mismatch or missing git-tracked file.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fif.data.catalog import verify


def main() -> int:
    try:
        n = verify()
    except (ValueError, FileNotFoundError) as e:
        print("RAW DATA CHECK FAILED:", e)
        return 1
    print(f"raw data unchanged: {n} git-tracked files match data/catalog.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
