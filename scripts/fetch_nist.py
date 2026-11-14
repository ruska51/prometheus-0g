"""Download property data from the NIST Chemistry WebBook (SRD 69) into data/raw/nist/.

Stage 4 (ADR-022..025). Raw responses are stored unchanged; sha256 go to data/catalog.yaml.

- Isobaric gas properties at 1 atm, 300-1500 K step 50 K (cp, viscosity, thermal conductivity,
  density) for O2, N2, CO2, He: ``gas_<ID>.tsv`` (NIST fluid.cgi, Type=IsoBar).
- Saturation tables (liquid and vapor) for methanol, n-heptane, water: ``sat_<ID>.tsv`` (Type=SatT).
- Species pages with molecular weight and condensed-phase thermochemistry (Delta_c H liquid):
  ``thermo_<ID>.html`` (cbook.cgi, Mask=2).

NIST IDs: O2 C7782447, N2 C7727379, CO2 C124389, He C7440597, methanol C67561,
n-heptane C142825, water C7732185.
Usage: ``.venv/Scripts/python scripts/fetch_nist.py``
"""
from __future__ import annotations

import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "nist"
BASE = "https://webbook.nist.gov/cgi"
UNITS = ("&RefState=DEF&TUnit=K&PUnit=atm&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs"
         "&VisUnit=Pa*s&STUnit=N%2Fm")
GASES = {"O2": "C7782447", "N2": "C7727379", "CO2": "C124389", "He": "C7440597"}
LIQUIDS = {"methanol": "C67561", "heptane": "C142825", "water": "C7732185"}
SAT_RANGE = {"C67561": (300, 500, 1), "C142825": (300, 560, 1), "C7732185": (280, 400, 1)}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except OSError:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, nid in GASES.items():
        url = (f"{BASE}/fluid.cgi?Action=Data&Wide=on&ID={nid}&Type=IsoBar&Digits=6&P=1"
               f"&THigh=1500&TLow=300&TInc=50{UNITS}")
        (OUT / f"gas_{nid}.tsv").write_bytes(_get(url))
        print("gas", name, nid)
        time.sleep(1)
    for name, nid in LIQUIDS.items():
        lo, hi, inc = SAT_RANGE[nid]
        url = (f"{BASE}/fluid.cgi?Action=Data&Wide=on&ID={nid}&Type=SatT&Digits=6"
               f"&THigh={hi}&TLow={lo}&TInc={inc}{UNITS}")
        (OUT / f"sat_{nid}.tsv").write_bytes(_get(url))
        (OUT / f"thermo_{nid}.html").write_bytes(_get(f"{BASE}/cbook.cgi?ID={nid}&Units=SI&Mask=2"))
        print("liquid", name, nid)
        time.sleep(1)
    for name, nid in GASES.items():
        (OUT / f"thermo_{nid}.html").write_bytes(_get(f"{BASE}/cbook.cgi?ID={nid}&Units=SI&Mask=1"))
        time.sleep(1)


if __name__ == "__main__":
    main()
