"""Train, compare (grouped CV) and save the stage-5 models (ADR-029). Called by scripts/train_models.py.

Cross-validation: GroupKFold(5) on ``cv_group`` (regime, ADR-016); metrics on pooled out-of-fold
predictions. Final models are refit on all rows and saved with joblib together with metadata
(data sha256, seed, library versions, features).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.inspection import partial_dependence, permutation_importance
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, r2_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from . import classification as C
from . import regression as R
from .features import EXTINCTION_DIRECTIONS, FEATURE_SETS, check_pre_ignition, model_table

N_SPLITS = 5


def _rows(t: pd.DataFrame, target: str, feature_sets: list[str], extra: list[str] = ()) -> tuple[pd.DataFrame, int]:
    cols = sorted({c for fs in feature_sets for c in FEATURE_SETS[fs]} | set(extra) | {target})
    sub = t.dropna(subset=cols)
    sub = sub[np.isfinite(sub[cols].select_dtypes("number")).all(axis=1)]
    return sub.reset_index(drop=True), len(t) - len(sub)


def _reg_metrics(y_log, mu, sd, scale: float = 1.0):
    """RMSE and R2 in log space; MAE in original units times ``scale`` (K: 1e6 -> mm^2/s)."""
    y, p = np.exp(y_log) * scale, np.exp(mu) * scale
    return {"RMSE_log": float(np.sqrt(np.mean((y_log - mu) ** 2))), "MAE": float(np.mean(np.abs(y - p))),
            "R2_log": float(r2_score(y_log, mu)), "coverage95": float(np.mean(np.abs(y_log - mu) <= 1.96 * sd))}


def _cls_metrics(y, p):
    return {"AUC": float(roc_auc_score(y, p)), "Brier": float(brier_score_loss(y, p)),
            "accuracy": float(accuracy_score(y, p >= 0.5)), "balanced_accuracy": float(balanced_accuracy_score(y, p >= 0.5))}


def cv_regression(sub, target, specs, groups):
    """specs: {name: (factory, feature_set or None, uses_aux)}; returns OOF (mu, sd) per model."""
    y = sub[target].to_numpy()
    oof = {k: (np.full(len(sub), np.nan), np.full(len(sub), np.nan)) for k in specs}
    for tr, te in GroupKFold(N_SPLITS).split(sub, y, groups):
        for name, (factory, fs, aux_cols) in specs.items():
            X = sub[FEATURE_SETS[fs]].to_numpy() if fs else np.zeros((len(sub), 1))
            aux = sub[aux_cols] if aux_cols else None
            mdl = factory().fit(X[tr], y[tr], aux=None if aux is None else _aux(aux.iloc[tr]))
            mu, sd = mdl.predict(X[te], aux=None if aux is None else _aux(aux.iloc[te]))
            oof[name][0][te], oof[name][1][te] = mu, sd
    return oof


def _aux(a: pd.DataFrame) -> dict:
    return {"ln_theory": a["ln_K_theory"].to_numpy() if "ln_K_theory" in a else None, "fuel": a["fuel"].to_numpy()}


def cv_classification(sub, specs, groups):
    y = sub["y_ext"].astype(int).to_numpy()
    oof = {k: np.full(len(sub), np.nan) for k in specs}
    for tr, te in GroupKFold(N_SPLITS).split(sub, y, groups):
        for name, (factory, fs) in specs.items():
            X = sub[FEATURE_SETS[fs]].to_numpy() if fs else np.zeros((len(sub), 1))
            mdl = factory().fit(X[tr], y[tr])
            oof[name][te] = mdl.predict_proba(X[te])[:, 1]
    return oof


def run(repo_root: Path, out_models: Path, out_docs: Path) -> dict:
    flex_path = repo_root / "data" / "processed" / "flex.csv"
    flex = pd.read_csv(flex_path)
    data_sha = hashlib.sha256(flex_path.read_bytes()).hexdigest()
    t = model_table(flex)
    for fs in FEATURE_SETS.values():
        check_pre_ignition(fs)
    report: dict = {"data_sha256": data_sha, "seed": R.SEED, "n_splits": N_SPLITS, "sklearn": sklearn.__version__,
                    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    # ---------------- K
    k_specs = {"mean": (R.MeanModel, None, None),
               "physics": (R.PhysicsModel, None, ["ln_K_theory", "fuel"]),
               "pure_ml_gp": (R.GPModel, "K_pure_ml", None),
               "hybrid": (R.HybridKModel, "K_hybrid_residual", ["ln_K_theory", "fuel"])}
    ksub, kdrop = _rows(t, "y_lnK", ["K_pure_ml", "K_hybrid_residual"], ["ln_K_theory"])
    koof = cv_regression(ksub, "y_lnK", k_specs, ksub["cv_group"])
    report["K"] = {"n_rows": len(ksub), "rows_dropped_missing": kdrop, "n_groups": int(ksub["cv_group"].nunique()),
                   "metrics": {k: _reg_metrics(ksub["y_lnK"].to_numpy(), *v, scale=1e6) for k, v in koof.items()},
                   "metrics_by_fuel": {k: {f: _reg_metrics(ksub["y_lnK"][ksub.fuel == f].to_numpy(), v[0][ksub.fuel == f],
                                                            v[1][ksub.fuel == f], scale=1e6) for f in ksub.fuel.unique()}
                                       for k, v in koof.items()}}
    ksub = ksub.assign(**{f"oof_{k}": v[0] for k, v in koof.items()}, **{f"oofsd_{k}": v[1] for k, v in koof.items()})

    # ---------------- d_ext / d0 (target ln)
    t["y_ln_dext"] = np.log(t["y_dext"])
    d_specs = {"mean": (R.MeanModel, None, None), "pure_ml_gp": (R.GPModel, "dext_pure_ml", None),
               "hybrid_gp": (R.GPModel, "dext_hybrid", None)}
    dsub, ddrop = _rows(t, "y_ln_dext", ["dext_pure_ml", "dext_hybrid"])
    doof = cv_regression(dsub, "y_ln_dext", d_specs, dsub["cv_group"])
    report["d_ext_over_d0"] = {"n_rows": len(dsub), "rows_dropped_missing": ddrop,
                               "note": "no physics baseline: the project has no sourced theory for d_ext (PHYSICS.md section 5)",
                               "metrics": {k: _reg_metrics(dsub["y_ln_dext"].to_numpy(), *v) for k, v in doof.items()}}

    # ---------------- extinction
    e_specs = {"prior": (C.PriorModel, None),
               "physics_logistic": (C.logistic, "ext_physics"),
               "pure_ml_boosting": (lambda: C.boosting(FEATURE_SETS["ext_pure_ml"], False), "ext_pure_ml"),
               "hybrid_logistic": (C.logistic, "ext_hybrid"),
               "hybrid_boosting_free": (lambda: C.boosting(FEATURE_SETS["ext_hybrid"], False), "ext_hybrid"),
               "hybrid_boosting_monotonic": (lambda: C.boosting(FEATURE_SETS["ext_hybrid"], True), "ext_hybrid")}
    esub, edrop = _rows(t, "y_ext", ["ext_pure_ml", "ext_hybrid"])
    eoof = cv_classification(esub, e_specs, esub["cv_group"])
    ye = esub["y_ext"].astype(int).to_numpy()
    report["extinction"] = {"n_rows": len(esub), "rows_dropped_missing": edrop, "n_positive": int(ye.sum()),
                            "metrics": {k: _cls_metrics(ye, v) for k, v in eoof.items()}}

    # ---------------- final fits, interpretation, save
    out_models.mkdir(parents=True, exist_ok=True)
    meta = {k: report[k] for k in ("data_sha256", "seed", "sklearn", "created_utc")}
    Xk = ksub[FEATURE_SETS["K_hybrid_residual"]].to_numpy()
    hyb = R.HybridKModel().fit(Xk, ksub["y_lnK"].to_numpy(), aux=_aux(ksub))
    report["K"]["c_f"] = hyb.c_f
    report["K"]["gp_kernel"] = str(hyb.gp[-1].kernel_)
    r_full = ksub["y_lnK"].to_numpy() - ksub["ln_K_theory"].to_numpy() - np.array([hyb.ln_cf[f] for f in ksub.fuel])
    pi = permutation_importance(hyb.gp, Xk, r_full, n_repeats=20, random_state=R.SEED, scoring="neg_root_mean_squared_error")
    report["K"]["residual_permutation_importance_in_sample"] = dict(zip(FEATURE_SETS["K_hybrid_residual"],
                                                                       np.round(pi.importances_mean, 4).tolist()))
    pdp = {}
    for feat in ("ln_d0_mm", "x_he", "x_co2", "x_o2"):
        j = FEATURE_SETS["K_hybrid_residual"].index(feat)
        res = partial_dependence(hyb.gp, Xk, [j], grid_resolution=15, kind="average")
        pdp[feat] = {"grid": res["grid_values"][0].round(4).tolist(), "residual": res["average"][0].round(4).tolist()}
    report["K"]["partial_dependence_residual"] = pdp
    joblib.dump({"model": hyb, "features": FEATURE_SETS["K_hybrid_residual"], **meta}, out_models / "K_hybrid.joblib")

    Xe = esub[FEATURE_SETS["ext_hybrid"]].to_numpy()
    lg = C.logistic().fit(Xe, ye)
    coefs = dict(zip(FEATURE_SETS["ext_hybrid"], lg[-1].coef_[0].round(3).tolist()))
    signs = {f: {"expected": d, "coef": coefs[f], "agrees": bool(np.sign(coefs[f]) == d)}
             for f, d in EXTINCTION_DIRECTIONS.items() if f in coefs}
    report["extinction"]["hybrid_logistic_standardised_coefs"] = coefs
    report["extinction"]["sign_check"] = signs
    lgp = C.logistic().fit(esub[FEATURE_SETS["ext_physics"]].to_numpy(), ye)
    report["extinction"]["physics_logistic_standardised_coefs"] = dict(zip(FEATURE_SETS["ext_physics"],
                                                                          lgp[-1].coef_[0].round(3).tolist()))
    for name in ("hybrid_logistic", "hybrid_boosting_monotonic", "hybrid_boosting_free"):
        mdl = {"hybrid_logistic": lambda: C.logistic(),
               "hybrid_boosting_monotonic": lambda: C.boosting(FEATURE_SETS["ext_hybrid"], True),
               "hybrid_boosting_free": lambda: C.boosting(FEATURE_SETS["ext_hybrid"], False)}[name]().fit(Xe, ye)
        joblib.dump({"model": mdl, "features": FEATURE_SETS["ext_hybrid"], **meta}, out_models / f"ext_{name}.joblib")

    Xd = dsub[FEATURE_SETS["dext_hybrid"]].to_numpy()
    joblib.dump({"model": R.GPModel().fit(Xd, dsub["y_ln_dext"].to_numpy()), "features": FEATURE_SETS["dext_hybrid"],
                 "target": "ln(d_ext/d0)", **meta}, out_models / "dext_hybrid_gp.joblib")

    out_docs.mkdir(parents=True, exist_ok=True)
    (out_docs / "model_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    ksub[["source_id", "row_id", "flex_identifier", "fuel", "diluent", "cv_group", "y_lnK"]
         + [c for c in ksub.columns if c.startswith("oof")]].to_csv(out_docs / "K_oof_predictions.csv", index=False,
                                                                   lineterminator="\n")
    report["_frames"] = {"K": ksub, "ext": esub.assign(**{f"oof_{k}": v for k, v in eoof.items()})}
    return report
