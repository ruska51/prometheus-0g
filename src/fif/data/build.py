"""Raw -> interim -> processed pipeline for the data layer (called by scripts/build_data.py).

Inputs: files registered in data/catalog.yaml (checksums verified first).
Outputs (in ``out_root``; default = repository ``data/``):
- interim/flex.csv, interim/cfig.csv, interim/psi_investigations.csv
- processed/flex.csv, processed/cfig.csv, processed/psi_investigations.csv
- processed/transform_log.tsv, processed/quality_flags.tsv
Tests pass a temporary ``out_root`` so live files are never touched.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import catalog, clean, schema
from .parsers import cfig, flex, psi_catalog


def build(repo_root: Path = catalog.REPO_ROOT, out_root: Path | None = None) -> dict[str, pd.DataFrame]:
    out_root = out_root or (repo_root / "data")
    n_checked = catalog.verify(repo_root)
    (out_root / "interim").mkdir(parents=True, exist_ok=True)
    (out_root / "processed").mkdir(parents=True, exist_ok=True)
    log = clean.TransformLog()
    log.add("all", "verify", n_checked, "sha256 of all registered raw files match data/catalog.yaml")

    tables = repo_root / "data" / "raw" / "psi_tables"
    flex_i = flex.parse(catalog.raw_path("psi_tables", "PSI-69_", repo_root))
    cfig_i = cfig.parse(catalog.raw_path("psi_tables", "CFI-G_Normal", repo_root),
                        catalog.raw_path("psi_tables", "CFI-G_Inverse", repo_root))
    cat_i = psi_catalog.parse(repo_root / "data" / "raw" / "psi_records", tables)
    log.add("flex", "parse", len(flex_i), "raw CSV -> interim (no corrections)")
    log.add("cfig", "parse", len(cfig_i), "raw CSVs (normal + inverse) -> interim (no corrections)")
    log.add("catalog", "parse", len(cat_i), "PSI records -> interim catalog")

    flex_p = schema.FLEX.validate(clean.clean_flex(flex_i, log))
    cfig_p = schema.CFIG.validate(clean.clean_cfig(cfig_i, log))
    cat_p = schema.CATALOG.validate(clean.clean_catalog(cat_i, log))

    for name, interim, processed in [("flex", flex_i, flex_p), ("cfig", cfig_i, cfig_p),
                                     ("psi_investigations", cat_i, cat_p)]:
        interim.to_csv(out_root / "interim" / f"{name}.csv", index=False, lineterminator="\n")
        processed.to_csv(out_root / "processed" / f"{name}.csv", index=False, lineterminator="\n")
    log.frame().to_csv(out_root / "processed" / "transform_log.tsv", sep="\t", index=False, lineterminator="\n")

    flags = []
    for name, df in [("flex", flex_p), ("cfig", cfig_p), ("psi_investigations", cat_p)]:
        for _, r in df[df["quality_flag"] != ""].iterrows():
            flags.append({"dataset": name, "source_id": r["source_id"], "row_id": r["row_id"],
                          "test": r.get("test_no", r.get("test_id", r.get("psi_id", ""))),
                          "quality_flag": r["quality_flag"],
                          "use_in_model": r.get("use_in_model", "")})
    pd.DataFrame(flags).to_csv(out_root / "processed" / "quality_flags.tsv", sep="\t", index=False, lineterminator="\n")
    return {"flex": flex_p, "cfig": cfig_p, "catalog": cat_p, "log": log.frame()}
