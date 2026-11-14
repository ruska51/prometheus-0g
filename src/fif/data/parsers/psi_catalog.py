"""Parser for PSI investigation records -> interim investigation catalog (basis of MVP item M1).

Inputs: ``data/raw/psi_records/PSI-<n>.json.gz`` (24 Combustion Science records) and the
Experimental Table CSVs in ``data/raw/psi_tables/`` (only to count data rows per table).
Output: one row per investigation with metadata fields as published by PSI (no rewording).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

from .common import read_csv_text


def _table_rows(tables_dir: Path, name: str) -> int:
    _, rows = read_csv_text(tables_dir / name)
    return sum(1 for r in rows[1:] if any(c.strip() for c in r))


def parse(records_dir: Path, tables_dir: Path) -> pd.DataFrame:
    out = []
    for path in sorted(records_dir.glob("PSI-*.json.gz"), key=lambda p: int(p.name.split("-")[1].split(".")[0])):
        rec = json.loads(gzip.decompress(path.read_bytes()))
        tables = [e["file_name"] for e in rec.get("experimentalTable") or []]
        out.append(
            {
                "source_id": rec["accession"],
                "source_file": path.name,
                "row_id": 1,
                "psi_id": rec["accession"],
                "acronym": rec.get("investigationAcronym", ""),
                "title": rec.get("title", ""),
                "research_area": rec.get("researchArea", ""),
                "subresearch_area": rec.get("subResearchArea", ""),
                "project_type": rec.get("projectType", ""),
                "flight_platform": rec.get("flightProgram", ""),
                "hardware": rec.get("experimentHardware", ""),
                "managing_center": rec.get("managingNasaCenter", ""),
                "start_date": rec.get("investigationStartDate", ""),
                "end_date": rec.get("investigationEndDate", ""),
                "doi": rec.get("doi", ""),
                "license": rec.get("licenseIdentifier", "") or "",
                "n_publications": len(rec.get("publications") or []),
                "experimental_tables": "; ".join(tables),
                "n_table_rows": sum(_table_rows(tables_dir, t) for t in tables),
                "raw_data_GB": float(rec.get("totalFileSize") or 0) / 1e9,
                "objective": rec.get("objective", ""),
                "approach": rec.get("approach", ""),
                "hypothesis": rec.get("hypothesis", ""),
                "research_impacts": rec.get("researchImpacts", ""),
                "psi_url": f"https://psi.nasa.gov/physci/repo/data/investigations/{rec['accession']}",
            }
        )
    return pd.DataFrame(out)
