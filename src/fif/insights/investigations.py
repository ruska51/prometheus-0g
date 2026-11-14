"""Relevance ranking of the 24 PSI combustion investigations (MVP M2, ADR-034).

Relevance = 0.5 * fire_safety + 0.3 * data + 0.2 * size
- fire_safety: 1.0 if the challenge page names the investigation for a fire-safety stage, 0.6 if PSI files it under the
  sub-research area "Spacecraft Fire Safety" / "Fire Safety", 0.3 for other combustion investigations;
- data: 1.0 if its Experimental Table has numeric outcomes usable for modeling (docs/DATA_SOURCES.md section 2),
  0.5 if the table holds conditions only, 0 if there is no table;
- size: ln(1 + rows in its Experimental Tables) / ln(1 + max rows).
Stage tags from the challenge text (docs/challenge/CHALLENGE.md): prevention - BASS, BASS-II, Saffire-I/II/III
("Flammability studies focus on solid materials"), ACME BRE ("materials flammability"); detection - SAME, SAME-R
("Fire detection was tested"), DAFT ("used to detect dust"); suppression - FLEX ("Suppression was studied in FLEX"),
FLEX-2 and CFI (same MDCA hardware, listed with FLEX under Hardware).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from fif.data.catalog import REPO_ROOT

STAGE_BY_ACRONYM = {
    "BASS": "prevention",
    "BASS-II": "prevention",
    "SAFFIRE-I": "prevention",
    "SAFFIRE-II": "prevention",
    "SAFFIRE-III": "prevention",
    "ACME BRE": "prevention",
    "SAME": "detection",
    "SAME-R": "detection",
    "DAFT / DAFT-2": "detection",
    "FLEX": "suppression",
    "FLEX-2": "suppression",
    "CFI": "suppression",
}
NAMED_IN_CHALLENGE = {
    "BASS",
    "BASS-II",
    "SAFFIRE-I",
    "SAFFIRE-II",
    "SAFFIRE-III",
    "SAME",
    "SAME-R",
    "FLEX",
    "DAFT / DAFT-2",
    "ACME BRE",
    "FLEX-2",
    "CFI",
}
# Experimental tables with numeric outcomes (DATA_SOURCES.md section 2): FLEX, CFI-G; BASS-II partial outcomes (CO, O2)
OUTCOMES = {"PSI-69": 1.0, "PSI-159": 1.0, "PSI-25": 1.0}
FUEL_TYPE = {
    "FLEX": "droplet",
    "FLEX-2": "droplet",
    "CFI": "droplet",
    "BASS": "solid",
    "BASS-II": "solid",
    "SAFFIRE-I": "solid",
    "SAFFIRE-II": "solid",
    "SAFFIRE-III": "solid",
    "SAME": "smoke",
    "SAME-R": "smoke",
    "DAFT / DAFT-2": "dust",
    "SLICE": "gas jet",
    "SPICE": "gas jet",
}


def ranked_investigations() -> pd.DataFrame:
    c = pd.read_csv(REPO_ROOT / "data" / "processed" / "psi_investigations.csv")
    c["acronym"] = c["acronym"].fillna("").astype(str)
    sub = c["subresearch_area"].fillna("").astype(str).str.lower()
    fs = np.where(c["acronym"].isin(NAMED_IN_CHALLENGE), 1.0, np.where(sub.str.contains("fire safety"), 0.6, 0.3))
    has_table = c["experimental_tables"].fillna("").astype(str).str.len() > 0
    data = np.where(c["psi_id"].map(OUTCOMES).fillna(0) > 0, 1.0, np.where(has_table, 0.5, 0.0))
    size = np.log1p(c["n_table_rows"]) / np.log1p(c["n_table_rows"].max())
    c["fire_safety_score"], c["data_score"], c["size_score"] = fs, data, size
    c["relevance"] = (0.5 * fs + 0.3 * data + 0.2 * size).round(3)
    c["stage"] = c["acronym"].map(STAGE_BY_ACRONYM).fillna("other")
    c["fuel_type"] = c["acronym"].map(FUEL_TYPE)
    c.loc[c["acronym"].str.startswith("ACME") & c["fuel_type"].isna(), "fuel_type"] = "gas flame"
    c["fuel_type"] = c["fuel_type"].fillna("analysis / other")
    return c.sort_values("relevance", ascending=False).reset_index(drop=True)
