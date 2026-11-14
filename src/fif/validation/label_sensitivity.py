"""Sensitivity of the extinction results to the class definition (ADR-018 variants B and C; ADR-021 open question).

Variants of the FLEX label "flame extinguished":
- A (used): from the extinction diameter - 1 = d_ext > 0, 0 = en dash or 0, missing = blank cell (ADR-018);
- B: from "Test end" - 1 = Extinction, 0 = Completion, Disruption rows excluded;
- C: from "Test end" - 1 = Extinction, 0 = Completion or Disruption.

Rule fixed BEFORE running (2026-11-14, docs/WORKLOG.md): the extinction conclusions are robust if, for both B and C,
(1) the mean grouped-CV AUC of the interface model (hybrid logistic) differs from A by <= 0.05,
(2) the refitted interface model's P(extinction) does not rise with O2 on the 8-case grid (as in stage 6), and
(3) the directions behind insights S3 / S4 hold: P(extinction) at O2 0.30 is below P at O2 0.15
    (methanol and heptane, 1 atm, 3 mm).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fif.models.features import EXTINCTION_UI_MODEL, FEATURE_SETS, conditions_table
from fif.models.train import _cls_metrics, cv_classification
from fif.validation.core import E_SPECS
from fif.validation.variants import CASES, O2_GRID, SEEDS, _splits

AUC_TOL = 0.05
UI_SPEC = {"hybrid_logistic": "hybrid_logistic", "hybrid_boosting_monotonic": "hybrid_boosting_monotonic"}[EXTINCTION_UI_MODEL]


def labels(t: pd.DataFrame) -> dict[str, pd.Series]:
    te = t["test_end"]
    return {
        "A_diameter": t["extinct_finite_d"].astype("Float64"),
        "B_test_end_no_disruption": te.map({"Extinction": 1.0, "Completion": 0.0}).astype("Float64"),
        "C_test_end_disruption_0": te.map({"Extinction": 1.0, "Completion": 0.0, "Disruption": 0.0}).astype("Float64"),
    }


def _rows(t: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    cols = sorted({c for fs in ("ext_pure_ml", "ext_hybrid", "ext_physics") for c in FEATURE_SETS[fs]})
    sub = t.assign(y_ext=y).dropna(subset=cols + ["y_ext"])
    sub = sub[np.isfinite(sub[cols].astype(float)).all(axis=1)].reset_index(drop=True)
    sub["y_ext"] = sub["y_ext"].astype(int)
    return sub


def run(t: pd.DataFrame) -> dict:
    rule = " ".join(__doc__.split("Rule fixed BEFORE running")[1].split()).removeprefix("(2026-11-14, docs/WORKLOG.md): ")
    out = {"rule": rule, "interface_model": UI_SPEC, "variants": {}}
    labs = labels(t)
    a = labs["A_diameter"]
    for name, y in labs.items():
        sub = _rows(t, y)
        ye = sub["y_ext"].to_numpy()
        per_model = {}
        for m, spec in E_SPECS.items():
            runs = [_cls_metrics(ye, cv_classification(sub, {m: spec}, None, splits=_splits(sub, ye, s))[m]) for s in SEEDS]
            per_model[m] = {k: float(np.mean([r[k] for r in runs])) for k in ("AUC", "Brier", "balanced_accuracy")}
        factory, fsn = E_SPECS[UI_SPEC]
        mdl = factory().fit(sub[FEATURE_SETS[fsn]].to_numpy(), ye)
        worst = 0.0
        for f, p, d in CASES:
            c = conditions_table(f, p, O2_GRID, d0_mm=d)
            worst = max(worst, float(np.max(np.diff(mdl.predict_proba(c[FEATURE_SETS[fsn]].to_numpy())[:, 1]))))
        p_lo_hi = {}
        for fuel in ("Methanol", "Heptane"):
            c = conditions_table(fuel, 1.0, np.array([0.15, 0.30]), d0_mm=3.0)
            pr = mdl.predict_proba(c[FEATURE_SETS[fsn]].to_numpy())[:, 1]
            p_lo_hi[fuel] = {"P_O2_0.15": float(pr[0]), "P_O2_0.30": float(pr[1])}
        both = a.notna() & y.notna()
        out["variants"][name] = {
            "n": int(len(sub)), "n_positive": int(ye.sum()), "n_negative": int(len(ye) - ye.sum()),
            "agreement_with_A": float((a[both] == y[both]).mean()) if name != "A_diameter" else 1.0,
            "n_compared_with_A": int(both.sum()),
            "models": per_model, "interface_worst_P_rise_along_O2": worst, "interface_P_at_O2": p_lo_hi,
        }
    base = out["variants"]["A_diameter"]["models"][UI_SPEC]["AUC"]
    checks = {}
    for name, v in out["variants"].items():
        if name == "A_diameter":
            continue
        checks[name] = {
            "auc_within_tol": abs(v["models"][UI_SPEC]["AUC"] - base) <= AUC_TOL,
            "no_P_rise_with_O2": v["interface_worst_P_rise_along_O2"] <= 1e-9,
            "S3_S4_direction_holds": all(d["P_O2_0.30"] < d["P_O2_0.15"] for d in v["interface_P_at_O2"].values()),
        }
    out["checks"] = checks
    out["robust"] = all(all(c.values()) for c in checks.values())
    return out
