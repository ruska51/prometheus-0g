"""Download NASA PSI combustion investigation records and their Experimental Table CSVs.

Stage 2 (ADR-012..014). Uses the public PSI web-service endpoints that the PSI
web page itself calls (no login; files are CC0-1.0):

- ``GET https://psi.nasa.gov/geode-py/ws/repo/search?from=0&size=500``
  -> all investigations; we keep Research Area == "Combustion Science".
- ``GET https://psi.nasa.gov/geode-py/ws/repo/investigations/<PSI-id>``
  -> investigation record (JSON) incl. the list of Experimental Table files.
- ``GET https://psi.nasa.gov/geode-py/ws/studies/<PSI-id>/download?file=<name>&redirect=false``
  -> a pre-signed S3 URL for the file, which is then downloaded.

Outputs (raw, never edited afterwards):
- ``data/raw/psi_records/search_all.json.gz`` (raw response, gzip only)
- ``data/raw/psi_records/<PSI-id>.json.gz`` (raw response, gzip only; records carry a large file change log)
- ``data/raw/psi_tables/<file name as published>.csv``
- ``data/raw/psi_tables/MANIFEST.tsv`` (PSI-id, file, bytes, expected bytes, sha256)

Usage: ``python scripts/fetch_psi.py`` from the repository root.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://psi.nasa.gov/geode-py/ws"
ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "raw" / "psi_records"
TAB_DIR = ROOT / "data" / "raw" / "psi_tables"
HEADERS = {"User-Agent": "prometheus-0g research script (NASA Space Apps 2026)"}


def _get(url: str, timeout: int = 60, retries: int = 4) -> bytes:
    """GET with retries (transient DNS/network errors were seen on 2026-11-14)."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def _write_gz(path: Path, data: bytes) -> None:
    """Store a raw JSON response byte-for-byte, gzip-compressed (mtime=0 for stable hashes)."""
    path.write_bytes(gzip.compress(data, mtime=0))


def main() -> None:
    REC_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)

    search = _get(f"{BASE}/repo/search?from=0&size=500")
    _write_gz(REC_DIR / "search_all.json.gz", search)
    hits = json.loads(search)["hits"]["hits"]
    ids = sorted(
        (h["_source"]["Accession"] for h in hits
         if h["_source"].get("Research Area") == "Combustion Science"),
        key=lambda a: int(a.split("-")[1]),
    )
    print(f"repository total={len(hits)}  combustion={len(ids)}")

    manifest = ["psi_id\tfile\tbytes\texpected_bytes\tsha256"]
    for acc in ids:
        rec_raw = _get(f"{BASE}/repo/investigations/{acc}")
        _write_gz(REC_DIR / f"{acc}.json.gz", rec_raw)
        rec = json.loads(rec_raw)
        for entry in rec.get("experimentalTable") or []:
            name = entry["file_name"]
            query = urllib.parse.urlencode({"file": name, "redirect": "false"},
                                           quote_via=urllib.parse.quote)
            signed = _get(f"{BASE}/studies/{acc}/download?{query}").decode().strip()
            data = _get(signed, timeout=120)
            (TAB_DIR / name).write_bytes(data)
            sha = hashlib.sha256(data).hexdigest()
            manifest.append(f"{acc}\t{name}\t{len(data)}\t{entry.get('file_size')}\t{sha}")
            flag = "OK" if len(data) == entry.get("file_size") else "SIZE MISMATCH"
            print(f"{acc:8} {name} {len(data)} B {flag}")
            time.sleep(0.3)
        time.sleep(0.2)
    (TAB_DIR / "MANIFEST.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
