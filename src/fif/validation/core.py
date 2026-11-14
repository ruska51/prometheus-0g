"""Stage-6 validation: repeated grouped CV, leave-class-out extrapolation, calibration, physicality, failures.

All functions return plain dicts / DataFrames; scripts/validate.py writes them to
docs/validation_results.json and renders docs/VALIDATION.md from that file (no hand-copied numbers).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.model_selection import GroupKFold

from fif.models import classification as C
from fif.models import regression as R
from fif.models.features import FEATURE_SETS, HYBRID_K_FEATURES, conditions_table, k_train_mask
from fif.models.train import N_SPLITS, _aux, _cls_metrics, _reg_metrics, _rows, cv_classification, cv_regression

K_SPECS = {"mean": (R.MeanModel, None, None),
           "physics": (R.PhysicsModel, None, ["ln_K_theory", "fuel"]),
           "pure_ml_gp": (R.GPModel, "K_pure_ml", None),
           "hybrid": (R.HybridKModel, HYBRID_K_FEATURES, ["ln_K_theory", "fuel"])}
E_SPECS = {"prior": (C.PriorModel, None),
           "physics_logistic": (C.logistic, "ext_physics"),
           "pure_ml_boosting": (lambda: C.boosting(FEATURE_SETS["ext_pure_ml"], False), "ext_pure_ml"),
           "hybrid_logistic": (C.logistic, "ext_hybrid"),
           "hybrid_boosting_monotonic": (lambda: C.boosting(FEATURE_SETS["ext_hybrid"], True), "ext_hybrid")}

# Leave-class-out extrapolation tests: name -> row mask on the model table (held-out class).
EXTRAPOLATION = {
    "He diluent": lambda t: t["diluent"] == "He",
    "CO2 diluent": lambda t: t["diluent"] == "CO2",
    "fuel = heptane (train on methanol)": lambda t: t["fuel"] == "Heptane",
    "fuel = methanol (train on heptane)": lambda t: t["fuel"] == "Methanol",
    "p > 1.2 atm": lambda t: t["p_atm"] > 1.2,
    "p ~0.7 atm (< 0.8)": lambda t: t["p_atm"] < 0.8,
    "O2 >= 0.30 (Moon-like O2)": lambda t: t["x_o2"] >= 0.30,
    "O2 <= 0.15": lambda t: t["x_o2"] <= 0.15,
}


def k_and_ext_tables(t: pd.DataFrame):
    ksub, kdrop = _rows(t, "y_lnK", ["K_pure_ml", "K_hybrid_residual"], ["ln_K_theory"])
    esub, edrop = _rows(t, "y_ext", ["ext_pure_ml", "ext_hybrid", "ext_physics"])
    return ksub, esub


def repeated_cv(ksub, esub, seeds=(0, 1, 2, 3, 4)) -> dict:
    """GroupKFold(5, shuffle) with different seeds: spread of metrics over group-to-fold assignments."""
    out = {"seeds": list(seeds), "K": {}, "extinction": {}}
    yk, ye = ksub["y_lnK"].to_numpy(), esub["y_ext"].astype(int).to_numpy()
    for s in seeds:
        sk = list(GroupKFold(N_SPLITS, shuffle=True, random_state=s).split(ksub, yk, ksub["cv_group"]))
        oof = cv_regression(ksub, "y_lnK", K_SPECS, ksub["cv_group"], splits=sk, train_mask=k_train_mask(ksub))
        for k, v in oof.items():
            out["K"].setdefault(k, []).append(_reg_metrics(yk, *v, scale=1e6))
        se = list(GroupKFold(N_SPLITS, shuffle=True, random_state=s).split(esub, ye, esub["cv_group"]))
        eo = cv_classification(esub, E_SPECS, esub["cv_group"], splits=se)
        for k, v in eo.items():
            out["extinction"].setdefault(k, []).append(_cls_metrics(ye, v))
        if s == seeds[0]:
            out["_oof_K"], out["_oof_E"] = oof, eo
    summary = {}
    for target in ("K", "extinction"):
        summary[target] = {}
        for k, runs in out[target].items():
            summary[target][k] = {m: {"mean": float(np.mean([r[m] for r in runs])), "sd": float(np.std([r[m] for r in runs], ddof=1)),
                                      "min": float(np.min([r[m] for r in runs])), "max": float(np.max([r[m] for r in runs]))}
                                  for m in runs[0]}
    out["summary"] = summary
    return out


def extrapolation(ksub, esub) -> dict:
    res = {}
    yk = ksub["y_lnK"].to_numpy()
    ye = esub["y_ext"].astype(int).to_numpy()
    for name, mask_fn in EXTRAPOLATION.items():
        mk = mask_fn(ksub).to_numpy()
        me = mask_fn(esub).to_numpy()
        entry = {"n_test_K": int(mk.sum()), "n_train_K": int((~mk).sum()), "K": {}, "extinction": {}}
        if mk.sum() >= 3 and (~mk).sum() >= 10:
            oof = cv_regression(ksub, "y_lnK", K_SPECS, None, splits=[(np.where(~mk)[0], np.where(mk)[0])],
                                train_mask=k_train_mask(ksub))
            for k, (mu, sd) in oof.items():
                m = _reg_metrics(yk[mk], mu[mk], sd[mk], scale=1e6)
                m["bias_log"] = float(np.mean(yk[mk] - mu[mk]))  # >0: model under-predicts
                entry["K"][k] = m
        entry["n_test_ext"] = int(me.sum()); entry["n_pos_test_ext"] = int(ye[me].sum())
        if me.sum() >= 3 and (~me).sum() >= 10 and len(np.unique(ye[~me])) == 2:
            eo = cv_classification(esub, E_SPECS, None, splits=[(np.where(~me)[0], np.where(me)[0])])
            for k, p in eo.items():
                yt, pt = ye[me], p[me]
                m = {"Brier": float(np.mean((pt - yt) ** 2)), "accuracy": float(np.mean((pt >= 0.5) == yt))}
                if len(np.unique(yt)) == 2:
                    m.update({k2: v for k2, v in _cls_metrics(yt, pt).items() if k2 in ("AUC", "balanced_accuracy")})
                entry["extinction"][k] = m
        res[name] = entry
    return res


def calibration(esub, oof_e: dict, n_bins: int = 5) -> dict:
    ye = esub["y_ext"].astype(int).to_numpy()
    out = {}
    for k, p in oof_e.items():
        frac, mean_pred = calibration_curve(ye, p, n_bins=n_bins, strategy="quantile")
        out[k] = {"mean_predicted": mean_pred.round(4).tolist(), "fraction_positive": frac.round(4).tolist(),
                  "Brier": float(np.mean((p - ye) ** 2))}
    return out


def residuals_by_group(ksub, oof_k: dict, model: str = "hybrid") -> pd.DataFrame:
    r = ksub["y_lnK"].to_numpy() - oof_k[model][0]
    pcls = np.where(ksub["p_atm"] < 0.8, "~0.7 atm", np.where(ksub["p_atm"] < 1.2, "~1 atm", ">1.2 atm"))
    df = pd.DataFrame({"fuel": ksub["fuel"], "diluent": ksub["diluent"], "p_class": pcls, "r": r})
    g = df.groupby(["fuel", "diluent", "p_class"])["r"]
    out = pd.DataFrame({"n": g.size(), "mean_residual_log": g.mean(), "se": g.std(ddof=1) / np.sqrt(g.size())}).reset_index()
    out["significant_2se"] = (out["mean_residual_log"].abs() > 2 * out["se"]) & (out["n"] >= 3)
    return out


def failures(ksub, oof_k: dict, n: int = 10) -> pd.DataFrame:
    mu, sd = oof_k["hybrid"]
    r = ksub["y_lnK"].to_numpy() - mu
    df = ksub.assign(resid_log=r, z=r / sd, K_meas=np.exp(ksub["y_lnK"]) * 1e6, K_pred=np.exp(mu) * 1e6,
                     K_theory_mm2_s=np.exp(ksub["ln_K_theory"]) * 1e6)
    cols = ["flex_identifier", "fuel", "diluent", "p_atm", "x_o2", "x_co2", "x_he", "d0_mm_orig", "K_meas", "K_pred",
            "K_theory_mm2_s", "resid_log", "z", "test_end", "quality_flag"]
    return df.reindex(df["resid_log"].abs().sort_values(ascending=False).index)[cols].head(n)


def physicality(ksub, esub) -> dict:
    """Checks on models fitted to all rows: monotonicity in O2, ranges, uncertainty growth outside data."""
    kfit = ksub[k_train_mask(ksub)]
    hyb = R.HybridKModel().fit(kfit[FEATURE_SETS[HYBRID_K_FEATURES]].to_numpy(), kfit["y_lnK"].to_numpy(), aux=_aux(kfit))
    ye = esub["y_ext"].astype(int).to_numpy()
    Xe = esub[FEATURE_SETS["ext_hybrid"]].to_numpy()
    mono = C.boosting(FEATURE_SETS["ext_hybrid"], True).fit(Xe, ye)
    logi = C.logistic().fit(Xe, ye)
    o2 = np.round(np.arange(0.12, 0.345, 0.01), 3)
    out = {"O2_grid": o2.tolist(), "cases": {}}
    for fuel in ("Methanol", "Heptane"):
        for p in (0.7, 1.0):
            for d0 in (2.0, 3.5):
                c = conditions_table(fuel, p, o2, d0_mm=d0)
                k_mu, k_sd = hyb.predict(c[FEATURE_SETS[HYBRID_K_FEATURES]].to_numpy(), aux=_aux(c))
                pk = np.exp(k_mu) * 1e6
                pm = mono.predict_proba(c[FEATURE_SETS["ext_hybrid"]].to_numpy())[:, 1]
                pl = logi.predict_proba(c[FEATURE_SETS["ext_hybrid"]].to_numpy())[:, 1]
                key = f"{fuel}, {p} atm, N2, d0 {d0} mm"
                out["cases"][key] = {"K_mm2_s": pk.round(4).tolist(), "K_sigma_log": k_sd.round(4).tolist(),
                                     "P_ext_monotonic": pm.round(4).tolist(), "P_ext_logistic": pl.round(4).tolist(),
                                     "K_increases_with_O2": bool(np.all(np.diff(pk) > -1e-9)),
                                     "K_theory_increases_with_O2": bool(np.all(np.diff(np.exp(c["ln_K_theory"])) > 0)),
                                     "P_ext_monotonic_nonincreasing": bool(np.all(np.diff(pm) <= 1e-12)),
                                     "P_ext_logistic_nonincreasing": bool(np.all(np.diff(pl) <= 1e-12))}
    # predictions on all observed rows: physical range
    mu_all, sd_all = hyb.predict(ksub[FEATURE_SETS[HYBRID_K_FEATURES]].to_numpy(), aux=_aux(ksub))
    out["K_pred_range_mm2_s"] = [float(np.exp(mu_all.min()) * 1e6), float(np.exp(mu_all.max()) * 1e6)]
    out["K_sigma_log_on_data"] = {"median": float(np.median(sd_all)), "p95": float(np.percentile(sd_all, 95)),
                                  "max": float(np.max(sd_all))}
    # uncertainty outside the data: Moon-base-like and far extrapolations
    probes = {"in range: methanol 1 atm O2 0.21 d0 3 mm": ("Methanol", 1.0, 0.21, 3.0),
              "edge: methanol 0.70 atm O2 0.34 d0 3 mm": ("Methanol", 0.70, 0.34, 3.0),
              "Moon-like: methanol 0.694 atm O2 0.30 d0 3 mm": ("Methanol", 10.2 / 14.696, 0.30, 3.0),
              "Moon-like: heptane 0.694 atm O2 0.30 d0 3 mm": ("Heptane", 10.2 / 14.696, 0.30, 3.0),
              "far: methanol 0.30 atm O2 0.50 d0 3 mm": ("Methanol", 0.30, 0.50, 3.0),
              "far: heptane 1 atm O2 0.21 d0 8 mm": ("Heptane", 1.0, 0.21, 8.0)}
    out["probes"] = {}
    for name, (f, p, xo, d0) in probes.items():
        c = conditions_table(f, p, xo, d0_mm=d0)
        mu, sd = hyb.predict(c[FEATURE_SETS[HYBRID_K_FEATURES]].to_numpy(), aux=_aux(c))
        out["probes"][name] = {"K_mm2_s": float(np.exp(mu[0]) * 1e6), "sigma_log": float(sd[0]),
                               "K_theory_mm2_s": float(np.exp(c["ln_K_theory"].iloc[0]) * 1e6),
                               "P_ext_monotonic": float(mono.predict_proba(c[FEATURE_SETS["ext_hybrid"]].to_numpy())[0, 1])}
    return out


def outlier_sensitivity(ksub, oof_k: dict, ident: str = "C13H201") -> dict:
    keep = (ksub["flex_identifier"] != ident).to_numpy()
    y = ksub["y_lnK"].to_numpy()
    return {k: {"with": _reg_metrics(y, *v, scale=1e6)["RMSE_log"],
                "without": _reg_metrics(y[keep], v[0][keep], v[1][keep], scale=1e6)["RMSE_log"]} for k, v in oof_k.items()}
