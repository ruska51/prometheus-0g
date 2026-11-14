"""Stage-6 variant selection with rules fixed BEFORE running (ADR-030).

1. Outlier treatment of suspect K values (train-time only): keep all / drop C13H201 / drop all rows flagged
   KTB_INCONSISTENT or OUTLIER_K. Rule: lowest mean RMSE_log of the hybrid on the SAME trusted evaluation rows
   (no KTB_INCONSISTENT / OUTLIER_K flag), 3 seeds of GroupKFold(5, shuffle).
2. Residual feature set of the hybrid K model: full / raw + ln K_theory / raw only. Rule: lowest mean RMSE_log
   among sets whose worst K drop along O2 (0.01 steps, 8 cases) is <= 2 %; if none passes, lowest RMSE_log.
3. Extinction model for the interface: hybrid logistic / physics logistic / monotonic boosting / monotonic
   boosting with proxy constraints. Rule: highest mean AUC among models with no increase of P(extinction) along O2.
"""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import GroupKFold

from fif.models import classification as C
from fif.models import regression as R
from fif.models.features import EXTINCTION_DIRECTIONS_PROXIES, FEATURE_SETS, conditions_table
from fif.models.train import N_SPLITS, _aux, _cls_metrics, _reg_metrics, cv_classification, cv_regression

SUSPECT_FLAGS = ("KTB_INCONSISTENT", "OUTLIER_K")
SEEDS = (0, 1, 2)
O2_GRID = np.round(np.arange(0.12, 0.345, 0.01), 3)
CASES = [(f, p, d) for f in ("Methanol", "Heptane") for p in (0.7, 1.0) for d in (2.0, 3.5)]


def trusted_mask(sub) -> np.ndarray:
    q = sub["quality_flag"].fillna("").astype(str)
    return ~q.str.contains("|".join(SUSPECT_FLAGS)).to_numpy()


def _splits(sub, y, seed):
    return list(GroupKFold(N_SPLITS, shuffle=True, random_state=seed).split(sub, y, sub["cv_group"]))


def outlier_variants(ksub) -> dict:
    variants = {"keep_all": np.ones(len(ksub), bool),
                "drop_C13H201": (ksub["flex_identifier"] != "C13H201").to_numpy(),
                "drop_all_flagged_KTB_or_OUTLIER": trusted_mask(ksub)}
    ev = trusted_mask(ksub)
    y = ksub["y_lnK"].to_numpy()
    specs = {"pure_ml_gp": (R.GPModel, "K_pure_ml", None),
             "hybrid": (R.HybridKModel, "K_hybrid_residual", ["ln_K_theory", "fuel"])}
    out = {"n_eval_trusted": int(ev.sum()), "variants": {}}
    for name, tm in variants.items():
        tr, al = {k: [] for k in specs}, {k: [] for k in specs}
        for s in SEEDS:
            oof = cv_regression(ksub, "y_lnK", specs, None, splits=_splits(ksub, y, s), train_mask=tm)
            for k, (mu, sd) in oof.items():
                tr[k].append(_reg_metrics(y[ev], mu[ev], sd[ev], scale=1e6)["RMSE_log"])
                al[k].append(_reg_metrics(y, mu, sd, scale=1e6)["RMSE_log"])
        out["variants"][name] = {"n_train_rows": int(tm.sum()),
                                 "RMSE_log_trusted_mean": {k: float(np.mean(v)) for k, v in tr.items()},
                                 "RMSE_log_trusted_sd": {k: float(np.std(v, ddof=1)) for k, v in tr.items()},
                                 "RMSE_log_all_rows_mean": {k: float(np.mean(v)) for k, v in al.items()}}
    out["rule"] = ("lowest mean RMSE_log of the hybrid on the same trusted rows (no KTB_INCONSISTENT / OUTLIER_K), "
                   "3 seeds of GroupKFold(5, shuffle)")
    out["chosen"] = min(out["variants"], key=lambda v: out["variants"][v]["RMSE_log_trusted_mean"]["hybrid"])
    return out, variants[out["chosen"]]


def k_feature_variants(ksub, train_mask) -> dict:
    y = ksub["y_lnK"].to_numpy()
    out = {"variants": {}}
    fit = ksub[train_mask]
    for fs in ("K_hybrid_residual", "K_resid_raw_lnK", "K_resid_raw"):
        spec = {"hybrid": (R.HybridKModel, fs, ["ln_K_theory", "fuel"])}
        rm = [_reg_metrics(y, *cv_regression(ksub, "y_lnK", spec, None, splits=_splits(ksub, y, s),
                                             train_mask=train_mask)["hybrid"], scale=1e6) for s in SEEDS]
        hyb = R.HybridKModel().fit(fit[FEATURE_SETS[fs]].to_numpy(), fit["y_lnK"].to_numpy(), aux=_aux(fit))
        worst = 0.0
        for f, p, d in CASES:
            c = conditions_table(f, p, O2_GRID, d0_mm=d)
            k = np.exp(hyb.predict(c[FEATURE_SETS[fs]].to_numpy(), aux=_aux(c))[0])
            worst = min(worst, float(np.min(np.diff(k) / k[:-1])))
        out["variants"][fs] = {"RMSE_log_mean": float(np.mean([m["RMSE_log"] for m in rm])),
                               "RMSE_log_sd": float(np.std([m["RMSE_log"] for m in rm], ddof=1)),
                               "coverage95_mean": float(np.mean([m["coverage95"] for m in rm])),
                               "worst_K_drop_along_O2": worst}
    ok = {k: v for k, v in out["variants"].items() if v["worst_K_drop_along_O2"] >= -0.02}
    pool = ok or out["variants"]
    out["rule"] = "lowest mean RMSE_log among residual feature sets with worst K drop along O2 <= 2 % per 0.01 step"
    out["any_passed_monotonic_rule"] = bool(ok)
    out["chosen"] = min(pool, key=lambda k: pool[k]["RMSE_log_mean"])
    return out


def extinction_variants(esub) -> dict:
    ye = esub["y_ext"].astype(int).to_numpy()
    fs = FEATURE_SETS["ext_hybrid"]
    cands = {"hybrid_logistic": (C.logistic, "ext_hybrid"),
             "physics_logistic": (C.logistic, "ext_physics"),
             "hybrid_boosting_monotonic": (lambda: C.boosting(fs, True), "ext_hybrid"),
             "hybrid_boosting_monotonic_proxies": (lambda: C.boosting(fs, True, directions=EXTINCTION_DIRECTIONS_PROXIES),
                                                   "ext_hybrid")}
    out = {"variants": {}}
    for name, (factory, fsn) in cands.items():
        runs = [_cls_metrics(ye, cv_classification(esub, {name: (factory, fsn)}, None,
                                                   splits=_splits(esub, ye, s))[name]) for s in SEEDS]
        mdl = factory().fit(esub[FEATURE_SETS[fsn]].to_numpy(), ye)
        worst = 0.0
        for f, p, d in CASES:
            c = conditions_table(f, p, O2_GRID, d0_mm=d)
            pr = mdl.predict_proba(c[FEATURE_SETS[fsn]].to_numpy())[:, 1]
            worst = max(worst, float(np.max(np.diff(pr))))
        out["variants"][name] = {"AUC_mean": float(np.mean([r["AUC"] for r in runs])),
                                 "AUC_sd": float(np.std([r["AUC"] for r in runs], ddof=1)),
                                 "Brier_mean": float(np.mean([r["Brier"] for r in runs])),
                                 "balanced_accuracy_mean": float(np.mean([r["balanced_accuracy"] for r in runs])),
                                 "worst_P_rise_along_O2": worst}
    ok = {k: v for k, v in out["variants"].items() if v["worst_P_rise_along_O2"] <= 1e-9}
    pool = ok or out["variants"]
    out["rule"] = "highest mean AUC among models with no increase of P(extinction) along O2 on the 8-case grid"
    out["chosen"] = max(pool, key=lambda k: pool[k]["AUC_mean"])
    return out
