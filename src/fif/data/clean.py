"""Interim -> processed: SI units, quality flags, targets, derived pre-ignition features, CV groups.

Every transformation is explicit and appended to a log (``TransformLog``) that build_data.py
writes to ``data/processed/transform_log.tsv``. Nothing is dropped: rows excluded from modeling
keep ``use_in_model = False`` and a reason in ``quality_flag``.

Decisions implemented here (docs/DECISIONS.md):
- ADR-015 anomaly handling (default package), ADR-016 CV groups = regime,
- ADR-017 targets (FLEX K, extinction yes/no, d_ext/d0; CFI-G ignition + self-extinction),
- ADR-018 extinction class defined from the visible-flame extinction diameter.

Units: SI internally (Pa, m, m^2/s, s, kg/s, K). Original values are kept in ``*_orig`` columns.
Conversions: 1 atm = 760 mmHg = 101325 Pa (docs/FORMULAS.md section 1) -> 1 mmHg = 101325/760 Pa;
1 bar = 1e5 Pa; 1 mm = 1e-3 m; 1 mm^2/s = 1e-6 m^2/s; 1 mg/s = 1e-6 kg/s; T[K] = T[degC] + 273.15.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

PA_PER_MMHG = 101325.0 / 760.0
PA_PER_BAR = 1.0e5
PA_PER_ATM = 101325.0


@dataclass
class TransformLog:
    rows: list[dict] = field(default_factory=list)

    def add(self, dataset: str, step: str, n_rows: int, detail: str) -> None:
        self.rows.append({"dataset": dataset, "step": step, "n_rows": int(n_rows), "detail": detail})

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=["dataset", "step", "n_rows", "detail"])


def _flag(df: pd.DataFrame, mask: pd.Series, code: str) -> None:
    mask = pd.Series(mask, index=df.index).fillna(False).astype(bool)
    df.loc[mask, "quality_flag"] = df.loc[mask, "quality_flag"].map(lambda s: code if not s else f"{s};{code}")


# --------------------------------------------------------------------------- FLEX (PSI-69)

def regime_group(fuel: pd.Series, p_mmHg: pd.Series, x_o2, x_co2, x_he, p_bin_mmHg: float = 50.0) -> pd.Series:
    """CV group (ADR-016): fuel x pressure rounded to 50 mmHg x O2/CO2/He rounded to 0.01."""
    pb = (p_mmHg / p_bin_mmHg).round() * p_bin_mmHg
    return (fuel.str.lower() + "|P" + pb.map(lambda v: "nan" if math.isnan(v) else f"{v:.0f}")
            + "|O2=" + x_o2.round(2).map("{:.2f}".format) + "|CO2=" + x_co2.round(2).map("{:.2f}".format)
            + "|He=" + x_he.round(2).map("{:.2f}".format))


def clean_flex(interim: pd.DataFrame, log: TransformLog) -> pd.DataFrame:
    df = interim.copy()
    n = len(df)
    df["quality_flag"] = ""
    df["use_in_model"] = True

    # keep originals, convert to SI
    df["p_mmHg_orig"] = df["p_mmHg"]
    df["d0_mm_orig"] = df["d0_mm"]
    df["d_ext_mm_orig"] = df["d_ext_mm"]
    df["K_mm2_s_orig"] = df["burning_rate_raw_value"]
    df["p_Pa"] = df["p_mmHg"] * PA_PER_MMHG
    df["d0_m"] = df["d0_mm"] * 1e-3
    df["K_m2_s"] = df["burning_rate_raw_value"] * 1e-6
    log.add("flex", "unit", n, "p_Pa = p_mmHg * 101325/760; d0_m = d0_mm*1e-3; K_m2_s = burning rate * 1e-6 "
            "(CSV header unit 'mm' read as mm^2/s per NASA/TP-2015-216046 App. A.1, ADR-015)")

    # --- quality checks (flags; nothing removed)
    m = df["p_mmHg"] <= 0
    _flag(df, m, "P_NONPOSITIVE"); df.loc[m, "use_in_model"] = False
    log.add("flex", "flag+exclude", m.sum(), "pressure <= 0 (test 114, same in TP Table IX) -> use_in_model=False (ADR-015)")

    xsum = df[["x_o2", "x_n2", "x_co2", "x_he"]].sum(axis=1)
    df["x_sum"] = xsum
    m = (xsum - 1).abs() > 0.011
    _flag(df, m, "MOLE_SUM_OFF")
    log.add("flex", "flag", m.sum(), "|sum of O2+N2+CO2+He - 1| > 0.011; kept, not renormalised (ADR-015)")

    m = df["d_ext_mm"] == 0
    _flag(df, m, "D_EXT_ZERO")
    log.add("flex", "flag", m.sum(), "extinction diameter = 0 -> d_ext target set missing; counted as 'no finite-diameter extinction' (ADR-015, ADR-018)")

    m = df["d_ext_mm"] > df["d0_mm"]
    _flag(df, m, "D_EXT_GT_D0")
    log.add("flex", "flag", m.sum(), "extinction diameter > initial diameter; kept (ADR-015)")

    m = df["burn_time_s__raw"].str.startswith("~")
    _flag(df, m, "APPROX_BURN_TIME")
    df["burn_time_s"] = df["burn_time_s"].where(~m, df["burn_time_s__raw"].str.lstrip("~").map(
        lambda s: float(s) if s.replace(".", "", 1).isdigit() else np.nan))
    log.add("flex", "parse+flag", m.sum(), "burn time '~x' -> x with APPROX_BURN_TIME flag (ADR-015)")

    dup = df["flex_identifier"].duplicated(keep=False)
    _flag(df, dup, "DUP_IDENTIFIER")
    log.add("flex", "flag", dup.sum(), "FLEX identifier used by more than one test; kept (ADR-015)")

    # internal consistency of the d^2 law record: K * t_burn should be close to d0^2 - d_ext^2
    # (stage-4 check, ADR-019): median ratio 1.05, 90 % of tests within 0.95-1.25
    dd2 = df["d0_mm"] ** 2 - df["d_ext_mm"].where(df["d_ext_mm"] > 0) ** 2
    df["ktb_ratio"] = df["burning_rate_raw_value"] * df["burn_time_s"] / dd2
    m = (df["ktb_ratio"] < 0.8) | (df["ktb_ratio"] > 1.5)
    _flag(df, m, "KTB_INCONSISTENT")
    log.add("flex", "flag", m.sum(), "K*t_burn / (d0^2 - d_ext^2) outside 0.8-1.5; kept (ADR-019)")

    # duplicated identifier 193F001: two real tests (TP Figs. 74, 77) with the same timestamp in Table IX;
    # the row of CSV test 73 is internally inconsistent (ratio 1.52) -> excluded (ADR-019, delegated by Ruslan)
    m = (df["flex_identifier"] == "193F001") & (df["test_no"] == 73)
    _flag(df, m, "DUP_ID_LESS_CONSISTENT"); df.loc[m.fillna(False), "use_in_model"] = False
    log.add("flex", "flag+exclude", int(m.fillna(False).sum()), "193F001 second row (CSV test 73) excluded; test 70 row kept (ADR-019)")

    m = df["source_id"] != "PSI-69"
    _flag(df, m, "FROM_TP_SUPPLEMENT")
    log.add("flex", "flag", m.sum(), "rows added from NASA/TP-2015-216046 Table IX, absent from the PSI CSV (ADR-020)")

    m = df["d0_mm"].isna()
    _flag(df, m, "D0_MISSING")
    log.add("flex", "flag", m.sum(), "initial diameter missing ('' or en dash)")

    full_dup = df.drop(columns=["row_id", "test_no"]).duplicated(keep=False)
    _flag(df, full_dup, "DUP_ROW")
    log.add("flex", "flag", full_dup.sum(), "rows identical except row/test number")

    # outliers: robust z of K within fuel (|z| > 3.5, MAD based)
    for fuel, g in df.groupby("fuel"):
        k = g["K_mm2_s_orig"]
        med = k.median(); mad = (k - med).abs().median()
        if mad > 0:
            z = 0.6745 * (k - med) / mad
            idx = z.index[z.abs() > 3.5]
            _flag(df, df.index.isin(idx), "OUTLIER_K")
    log.add("flex", "flag", df["quality_flag"].str.contains("OUTLIER_K").sum(), "burning rate robust |z| > 3.5 within fuel; kept")

    # --- targets (post-ignition quantities: targets only, never features)
    d_ext_code = df["d_ext_mm__raw"]
    finite = df["d_ext_mm"] > 0
    no_ext = d_ext_code.isin(["–", "-"]) | (df["d_ext_mm"] == 0)
    df["extinct_finite_d"] = pd.array([pd.NA] * n, dtype="Int8")
    df.loc[finite, "extinct_finite_d"] = 1
    df.loc[no_ext, "extinct_finite_d"] = 0
    log.add("flex", "target", n, f"extinct_finite_d: 1 if d_ext>0 ({finite.sum()}), 0 if en dash or 0 ({no_ext.sum()}), "
            f"NA if blank ({(~finite & ~no_ext).sum()}) (ADR-018)")
    df["d_ext_m"] = (df["d_ext_mm"] * 1e-3).where(finite)
    df["d_ext_over_d0"] = (df["d_ext_mm"] / df["d0_mm"]).where(finite)
    m = ((df["test_end"].isin(["Completion", "Disruption"])) & finite) | ((df["test_end"] == "Extinction") & no_ext)
    _flag(df, m, "TEST_END_CONFLICT")
    log.add("flex", "flag", m.sum(), "'Test end' label disagrees with extinction-diameter code (kept for display only)")

    # --- derived pre-ignition features (no physical model)
    df["diluent"] = np.select([df["x_co2"] > 0, df["x_he"] > 0], ["CO2", "He"], "N2")
    df["p_atm"] = df["p_Pa"] / PA_PER_ATM
    df["p_o2_Pa"] = df["x_o2"] * df["p_Pa"]
    df["x_inert"] = 1 - df["x_o2"]
    df["fuel_methanol"] = (df["fuel"] == "Methanol").astype(int)
    log.add("flex", "derive", n, "diluent class, p_atm, p_o2_Pa = x_o2*p_Pa, x_inert = 1-x_o2, fuel_methanol")

    df["cv_group"] = regime_group(df["fuel"], df["p_mmHg"], df["x_o2"], df["x_co2"], df["x_he"])
    log.add("flex", "group", df["cv_group"].nunique(), "cv_group = fuel x P(50 mmHg) x O2/CO2/He(0.01) (ADR-016)")
    return df


# --------------------------------------------------------------------------- CFI-G (PSI-159)

def clean_cfig(interim: pd.DataFrame, log: TransformLog) -> pd.DataFrame:
    df = interim.copy()
    n = len(df)
    df["quality_flag"] = ""
    df["use_in_model"] = True  # CFI-G is a data map, no ML model (ADR-012)

    # spreadsheet error codes -> missing, flagged
    for col in [c for c in df.columns if c.endswith("__raw")]:
        m = df[col].str.startswith("#")
        if m.any():
            _flag(df, m, f"EXCEL_ERROR_{col[:-5].upper()}")
            log.add("cfig", "flag", m.sum(), f"{col[:-5]}: spreadsheet error code -> NaN (ADR-015)")

    # normalise categorical case (raw kept)
    df["flame_type_orig"] = df["flame_type"]; df["flame_type"] = df["flame_type"].str.lower()
    df["hot_ignition_orig"] = df["hot_ignition"]
    hi = df["hot_ignition"].str.lower()
    changed = df["hot_ignition"].isin(["yes", "no"])  # lower-case variants of Yes/No in the raw table
    df["hot_ignition"] = hi
    _flag(df, changed, "CASE_NORMALISED")
    log.add("cfig", "normalise", changed.sum(), "hot_ignition lower-cased ('Yes'/'yes' -> 'yes'); original in hot_ignition_orig")
    df["ignited"] = df["hot_ignition"].map({"yes": 1, "no": 0}).astype("Int8")
    log.add("cfig", "target", n, "ignited: yes->1, no->0, 'flash' -> NA (category kept in hot_ignition) (ADR-017)")
    df["self_extinguished"] = df["end_mode"].map({"SE": 1, "FT": 0}).astype("Int8")
    log.add("cfig", "target", n, "self_extinguished: SE->1, FT (flow terminated)->0, '-' -> NA (ADR-017)")

    df["fuel"] = df["fuel_label"].str.extract(r"(ethane|propane|butane)", expand=False)
    pct = df["fuel_label"].str.extract(r"(\d+)\s*%", expand=False).astype(float) / 100
    df["fuel_bottle_fraction"] = pct.fillna(1.0)
    log.add("cfig", "derive", n, "fuel name and bottle fraction parsed from fuel label ('30% butane' -> butane, 0.30; no % -> 1.0)")

    df["p_bar_orig"] = df["p_bar"]; df["p_Pa"] = df["p_bar"] * PA_PER_BAR
    df["m_fuel_kg_s"] = df["m_fuel_mg_s"] * 1e-6
    df["m_o2_kg_s"] = df["m_o2_mg_s"] * 1e-6 if "m_o2_mg_s" in df else np.nan
    df["peak_burner_T_K_from_C"] = df["peak_burner_T_C"] + 273.15
    log.add("cfig", "unit", n, "p_Pa = p_bar*1e5; mg/s*1e-6 -> kg/s; peak burner T degC + 273.15")

    df["x_o2_oxidizer"] = np.where(df["table"] == "normal", df["x_o2_chamber_before"], df["x_o2_supply"])
    df["p_o2_Pa"] = df["x_o2_oxidizer"] * df["p_Pa"]
    log.add("cfig", "derive", n, "x_o2_oxidizer = chamber XO2 before test (normal) or supplied XO2 (inverse); p_o2_Pa = x_o2_oxidizer*p_Pa")

    m = df["p_Pa"] <= 0
    _flag(df, m, "P_NONPOSITIVE")
    m = (df["x_o2_oxidizer"] <= 0) | (df["x_o2_oxidizer"] > 1)
    _flag(df, m, "XO2_OUT_OF_RANGE")
    m = df["burn_time_s"] < 0
    _flag(df, m, "NEGATIVE_BURN_TIME")
    df["cv_group"] = df["table"] + "|day" + df["day"].map(lambda v: f"{v:.0f}")
    log.add("cfig", "group", df["cv_group"].nunique(), "cv_group = table x test day (no ML on CFI-G; for completeness)")
    return df


def clean_catalog(interim: pd.DataFrame, log: TransformLog) -> pd.DataFrame:
    df = interim.copy()
    df["quality_flag"] = ""
    _flag(df, df["license"] == "", "LICENSE_MISSING")
    _flag(df, df["experimental_tables"] == "", "NO_EXPERIMENTAL_TABLE")
    log.add("catalog", "flag", (df["quality_flag"] != "").sum(), "missing license / no experimental table")
    return df
