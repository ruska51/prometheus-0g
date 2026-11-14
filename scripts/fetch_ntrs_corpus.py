"""Download the NASA NTRS full texts used by the assistant's report search (stage 9, ADR-042).

Only documents whose NTRS copyright determination permits public use are fetched (checked from the NTRS record at
download time; documents marked "may include copyright material" are excluded). Files are written unchanged to
data/raw/ntrs_text/<id>.txt, a manifest with title, type, copyright status, URL and sha256 to MANIFEST.tsv, and the
files are registered in data/catalog.yaml (dataset ``ntrs_text``) so scripts/verify_raw.py checks them.
Usage: ``python scripts/fetch_ntrs_corpus.py``
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "ntrs_text"
API = "https://ntrs.nasa.gov/api/citations/"
ALLOWED = {"PUBLIC_USE_PERMITTED", "GOV_PUBLIC_USE_PERMITTED", "GOV_PERMITTED"}
# id -> why it is in the corpus (which investigation / question it serves)
CORPUS = {
    "20150023456": "FLEX detailed results (PSI-69), NASA/TP-2015-216046",
    "20130014061": "FLEX methanol droplets: burning rate, flame standoff, extinction",
    "20205008449": "FLEX cool flames, inert-gas effects",
    "20210011385": "BASS-II summary report (PSI-25)",
    "20210021781": "ACME gaseous flames incl. CFI-G (PSI-159)",
    "20130000422": "SAME smoke particle results (PSI-102 / PSI-101)",
    "20170007283": "Spacecraft fire safety research at NASA Glenn (overview)",
    "20170008805": "Large-scale spacecraft flammability tests (Saffire)",
    "20210020516": "Fire on the Moon: solid fuel combustion (lunar gravity)",
    "20260000646": "Material flammability at lunar and Martian gravity (FM2)",
    "20250010653": "LUCI: flammability in simulated lunar gravity",
    "20240008623": "FM2 poster: flammability of materials on the Moon",
}


def get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "prometheus-0g corpus fetch"})
    with urlopen(req, timeout=120) as r:
        return r.read()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, files = [], []
    for nid, why in CORPUS.items():
        meta = json.loads(get(API + nid))
        cr = (meta.get("copyright") or {}).get("determinationType")
        if cr not in ALLOWED:
            print("skip (copyright)", nid, cr)
            continue
        txt = [d["links"]["fulltext"] for d in meta.get("downloads", []) if d.get("links", {}).get("fulltext")]
        if not txt:
            print("skip (no full text)", nid)
            continue
        path = txt[0]
        url = "https://ntrs.nasa.gov" + quote(path, safe="/%")
        data = get(url)
        p = OUT / f"{nid}.txt"
        p.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        rows.append([nid, meta.get("title", "").replace("\t", " "), meta.get("stiType", ""), cr, url, why, sha])
        files.append({"path": f"data/raw/ntrs_text/{nid}.txt", "sha256": sha})
        print(f"{nid} {len(data) // 1024} KB {cr}")
        time.sleep(1)
    with open(OUT / "MANIFEST.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("ntrs_id\ttitle\ttype\tcopyright\turl\tpurpose\tsha256\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    cat_path = ROOT / "data" / "catalog.yaml"
    cat = yaml.safe_load(cat_path.read_text(encoding="utf-8"))
    cat["datasets"] = [d for d in cat["datasets"] if d["id"] != "ntrs_text"]
    cat_text = cat_path.read_text(encoding="utf-8").rstrip("\n")
    block = {
        "id": "ntrs_text",
        "title": "NASA NTRS full texts for the assistant's report search (public-use documents only)",
        "source": "https://ntrs.nasa.gov (API full-text downloads, fetched by scripts/fetch_ntrs_corpus.py)",
        "license": "NTRS copyright determination PUBLIC_USE_PERMITTED / GOV_PUBLIC_USE_PERMITTED / GOV_PERMITTED (per file in MANIFEST.tsv)",
        "accessed": str(date.today()),
        "notes": "raw NTRS text layer, unchanged; ADR-042",
        "files": files,
    }
    if "id: ntrs_text" in cat_text:
        cat_text = cat_text[: cat_text.index("  - id: ntrs_text")].rstrip("\n")
    dump = yaml.safe_dump([block], sort_keys=False, allow_unicode=True, width=200)
    dump = "\n".join("  " + line if line else line for line in dump.splitlines())  # item of the datasets list
    cat_path.write_text(cat_text + "\n\n" + dump + "\n", encoding="utf-8")
    assert any(d["id"] == "ntrs_text" for d in yaml.safe_load(cat_path.read_text(encoding="utf-8"))["datasets"])
    print("registered", len(files), "files in data/catalog.yaml")


if __name__ == "__main__":
    main()
