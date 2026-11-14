"""Schemas of the processed tables (pandera): types, units (in descriptions) and allowed ranges.

Ranges are physical-plausibility bounds, not the observed ranges; the observed ranges are in
docs/DATA_DICTIONARY.md. Rows excluded from modeling (``use_in_model = False``) are still
validated, so values that are physically impossible must carry a quality flag (checked below).
"""
from __future__ import annotations

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

PROVENANCE = {
    "source_id": Column(str, description="PSI investigation id"),
    "source_file": Column(str, description="raw file name in data/raw"),
    "row_id": Column(int, Check.ge(1), description="1-based data row in the raw file"),
    "quality_flag": Column(str, description="';'-separated flag codes, '' if none (DATA_QUALITY.md)"),
}

FLEX = DataFrameSchema(
    {
        **PROVENANCE,
        "test_no": Column("Int64", Check.in_range(1, 274), nullable=True, description="PSI CSV numbering; NA for TP-supplement rows"),
        "tp_test_no": Column("Int64", nullable=True, description="NASA/TP Table IX number (supplement rows only)"),
        "fuel": Column(str, Check.isin(["Methanol", "Heptane"])),
        "p_Pa": Column(float, Check.in_range(0, 5e5), description="ambient pressure, Pa (0 only with P_NONPOSITIVE)"),
        "x_o2": Column(float, Check.in_range(0, 1)),
        "x_n2": Column(float, Check.in_range(0, 1)),
        "x_co2": Column(float, Check.in_range(0, 1)),
        "x_he": Column(float, Check.in_range(0, 1)),
        "x_sum": Column(float, Check.in_range(0.95, 1.05)),
        "d0_m": Column(float, Check.in_range(0, 0.01), nullable=True, description="initial droplet diameter, m"),
        "d_ext_m": Column(float, Check.in_range(0, 0.01), nullable=True, description="visible-flame extinction diameter, m"),
        "K_m2_s": Column(float, Check.in_range(0, 5e-6), nullable=True, description="burning-rate constant, m^2/s"),
        "burn_time_s": Column(float, Check.in_range(0, 300), nullable=True),
        "test_end": Column(str, Check.isin(["Extinction", "Disruption", "Completion"])),
        "extinct_finite_d": Column("Int8", Check.isin([0, 1]), nullable=True),
        "d_ext_over_d0": Column(float, Check.in_range(0, 1.05), nullable=True),
        "diluent": Column(str, Check.isin(["N2", "CO2", "He"])),
        "p_o2_Pa": Column(float, Check.ge(0)),
        "cv_group": Column(str),
        "use_in_model": Column(bool),
    },
    checks=[
        Check(lambda d: ~((d["p_Pa"] <= 0) & ~d["quality_flag"].str.contains("P_NONPOSITIVE")),
              element_wise=False, error="non-positive pressure without P_NONPOSITIVE flag"),
        Check(lambda d: ~((d["p_Pa"] <= 0) & d["use_in_model"]), element_wise=False,
              error="non-positive pressure must not be used in the model"),
    ],
    strict=False,
    coerce=False,
)

CFIG = DataFrameSchema(
    {
        **PROVENANCE,
        "table": Column(str, Check.isin(["normal", "inverse"])),
        "flame_type": Column(str, Check.isin(["normal", "inverse"])),
        "fuel": Column(str, Check.isin(["ethane", "propane", "butane"])),
        "fuel_bottle_fraction": Column(float, Check.in_range(0, 1)),
        "p_Pa": Column(float, Check.in_range(1e4, 5e5)),
        "x_o2_oxidizer": Column(float, Check.in_range(0, 1)),
        "tad_K": Column(float, Check.in_range(300, 4000), nullable=True),
        "z_st": Column(float, Check.in_range(0, 1), nullable=True),
        "hot_ignition": Column(str, Check.isin(["yes", "no", "flash"])),
        "ignited": Column("Int8", Check.isin([0, 1]), nullable=True),
        "self_extinguished": Column("Int8", Check.isin([0, 1]), nullable=True),
        "burn_time_s": Column(float, Check.in_range(0, 1000), nullable=True),
        "cv_group": Column(str),
    },
    strict=False,
    coerce=False,
)

CATALOG = DataFrameSchema(
    {
        **PROVENANCE,
        "psi_id": Column(str, Check.str_matches(r"^PSI-\d+$"), unique=True),
        "research_area": Column(str, Check.isin(["Combustion Science"])),
        "n_publications": Column(int, Check.ge(0)),
        "n_table_rows": Column(int, Check.ge(0)),
    },
    strict=False,
)
