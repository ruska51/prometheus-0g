"""Cross-check the PSI-69 FLEX CSV against NASA/TP-2015-216046 Table IX (all rows, all columns).

The TP PDF (42.9 MB) is not committed: it is downloaded from NTRS into ``data/raw/ntrs/`` on
first use and checked against the sha256 registered in data/catalog.yaml (dataset ``ntrs_flex_tp``).
Table IX is read with pdfplumber word coordinates: every TP row has exactly 15 cells
(missing values are printed as an en dash), so a row = all words on the line of "FLEX-NNN".

Rows are matched by FLEX identifier + test date (the CSV renumbers tests: TP has no FLEX-156,
and two TP tests are absent from the CSV). Output: ``docs/verification/flex_vs_tp.tsv`` and a
summary on stdout. Usage: ``.venv/Scripts/python scripts/verify_flex_vs_tp.py``.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import io
import re
import sys
import urllib.request
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "raw" / "ntrs" / "20150023456.pdf"
URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf"
CSV_PATH = ROOT / "data" / "raw" / "psi_tables" / "PSI-69_Experimental table_FLEX.csv"
OUT = ROOT / "docs" / "verification" / "flex_vs_tp.tsv"
COLS = ["tp_test", "ident", "date", "gmt", "fuel", "P", "O2", "N2", "CO2", "He", "d0", "dext", "K", "tb", "end"]
CSV_IDX = {"gmt": 3, "fuel": 4, "P": 5, "O2": 6, "N2": 7, "CO2": 8, "He": 9, "d0": 10, "dext": 11,
           "K": 12, "tb": 13, "end": 14}
DASHES = {"–", "-", "—"}


def expected_sha() -> str:
    sys.path.insert(0, str(ROOT / "src"))
    from fif.data.catalog import load_catalog
    return load_catalog()["ntrs_flex_tp"]["files"][0]["sha256"]


def ensure_pdf() -> None:
    sha = expected_sha()
    if not PDF.exists():
        PDF.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL, headers={"User-Agent": "prometheus-0g research script"})
        PDF.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != sha:
        raise SystemExit("TP PDF checksum mismatch")


def tp_rows() -> list[dict]:
    rows = []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
            for s in (w for w in words if re.fullmatch(r"FLEX.\d{3}", w["text"])):
                yc = (s["top"] + s["bottom"]) / 2
                line = sorted((w for w in words if abs((w["top"] + w["bottom"]) / 2 - yc) < 3.0),
                              key=lambda w: w["x0"])
                toks = [w["text"] for w in line]
                if len(toks) == 15:
                    rows.append(dict(zip(COLS, toks), page=pno))
    return rows


def _num(s: str):
    try:
        return float(s.lstrip("~"))
    except ValueError:
        return None


def _date_key(s: str):
    p = s.split("/")
    return (int(p[0]), int(p[1]), int(p[2]) % 100) if len(p) == 3 and all(x.isdigit() for x in p) else s


def main() -> None:
    ensure_pdf()
    tp = tp_rows()
    raw = list(csv.reader(io.StringIO(CSV_PATH.read_bytes().decode("cp1252"))))
    rows = [[c.strip() for c in r] for r in raw[1:] if any(c.strip() for c in r)]
    by = collections.defaultdict(list)
    for t in tp:
        by[(t["ident"], _date_key(t["date"]))].append(t)
    used, out, n_diff = set(), [], 0
    blank_vs_dash = collections.Counter()
    for r in rows:
        cands = by.get((r[1], _date_key(r[2])), [])
        if len(cands) > 1:  # duplicated identifier+date (193F001): disambiguate by d0
            cands = [c for c in cands if _num(c["d0"]) == _num(r[10])] or cands
        if not cands:
            out.append({"csv_test": r[0], "ident": r[1], "column": "*", "csv": "", "tp": "NOT IN TP", "page": ""})
            continue
        t = cands[0]
        used.add(t["tp_test"])
        for col, i in CSV_IDX.items():
            a, b = r[i], t[col]
            if col in ("end", "fuel"):
                same = a == b
            elif a == "" and b in DASHES:
                blank_vs_dash[col] += 1
                same = True
            elif a in DASHES and b in DASHES:
                same = True
            else:
                same = (_num(a) is not None and _num(a) == _num(b)) or a == b
            status = "match" if same else "DIFF"
            n_diff += not same
            out.append({"csv_test": r[0], "ident": r[1], "column": col, "csv": a, "tp": b,
                        "tp_test": t["tp_test"], "page": t["page"], "status": status})
    missing = [f"{t['tp_test']} {t['ident']} {t['date']}" for t in tp if t["tp_test"] not in used]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["csv_test", "ident", "column", "csv", "tp", "tp_test", "page", "status"],
                           delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"TP rows parsed: {len(tp)}; CSV rows: {len(rows)}; cell comparisons: {len(out)}; differences: {n_diff}")
    print(f"CSV blank where TP prints a dash: {dict(blank_vs_dash)}")
    print(f"TP rows absent from CSV: {missing}")
    for o in out:
        if o.get("status") == "DIFF" or o.get("tp") == "NOT IN TP":
            print("  ", o)


if __name__ == "__main__":
    main()
