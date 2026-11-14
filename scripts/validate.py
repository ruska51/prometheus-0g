"""Stage-6 validation in one command: computes everything, saves docs/validation_results.json,
draws docs/figures/val_*.png and renders docs/VALIDATION.md from the JSON (scripts/render_validation.py).

Usage: ``.venv/Scripts/python scripts/validate.py`` (~3-4 min).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
from fif.models.features import model_table  # noqa: E402
from fif.validation import core, variants  # noqa: E402

FIG = ROOT / "docs" / "figures"
OUT = ROOT / "docs" / "validation_results.json"


def main() -> None:
    flex_path = ROOT / "data" / "processed" / "flex.csv"
    t = model_table(pd.read_csv(flex_path))
    ksub, esub = core.k_and_ext_tables(t)
    var_out, _ = variants.outlier_variants(ksub)
    var_k = variants.k_feature_variants(ksub, core.k_train_mask(ksub))  # mask of the chosen outlier treatment
    var_e = variants.extinction_variants(esub)
    rep = core.repeated_cv(ksub, esub)
    oof_k, oof_e = rep.pop("_oof_K"), rep.pop("_oof_E")
    res = {
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "data_sha256": hashlib.sha256(flex_path.read_bytes()).hexdigest(),
        "n_rows": {
            "K": len(ksub),
            "extinction": len(esub),
            "extinction_positive": int(esub["y_ext"].sum()),
            "groups_K": int(ksub["cv_group"].nunique()),
        },
        "variant_selection": {"outlier": var_out, "k_residual_features": var_k, "extinction_model": var_e},
        "repeated_cv": rep,
        "extrapolation": core.extrapolation(ksub, esub),
        "calibration_seed0": core.calibration(esub, oof_e),
        "residuals_by_group_hybrid_seed0": core.residuals_by_group(ksub, oof_k).to_dict(orient="records"),
        "failures_hybrid_seed0": core.failures(ksub, oof_k).to_dict(orient="records"),
        "physicality": core.physicality(ksub, esub),
        "outlier_sensitivity_C13H201": core.outlier_sensitivity(ksub, oof_k),
    }
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")

    # --- figures
    y = ksub["y_lnK"].to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    mu, sd = oof_k["hybrid"]
    for fuel, m in (("Methanol", ksub.fuel == "Methanol"), ("Heptane", ksub.fuel == "Heptane")):
        axes[0].errorbar(np.exp(mu[m]) * 1e6, np.exp(y[m]) * 1e6, xerr=None, fmt="o", ms=4, alpha=0.6, label=fuel)
    axes[0].plot([0, 1.2], [0, 1.2], "k--", lw=1, label="ideal")
    axes[0].set_xlabel("hybrid prediction, mm$^2$/s (out-of-fold, seed 0)")
    axes[0].set_ylabel("measured K, mm$^2$/s")
    axes[0].legend(fontsize=8)
    axes[0].set_title("Prediction vs measurement")
    g = pd.DataFrame(res["residuals_by_group_hybrid_seed0"])
    lab = [f"{a[:4]} {b} {c}" for a, b, c in zip(g.fuel, g.diluent, g.p_class)]
    axes[1].errorbar(range(len(g)), g.mean_residual_log, yerr=2 * g.se.fillna(0), fmt="o")
    axes[1].axhline(0, c="k", lw=1)
    axes[1].set_xticks(range(len(g)), lab, rotation=70, fontsize=7)
    axes[1].set_ylabel("mean ln(K_meas/K_pred) +- 2 se")
    axes[1].set_title("Hybrid residuals by condition group")
    fig.tight_layout()
    fig.savefig(FIG / "val_K_pred_vs_meas.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.5, 5))
    for k, c in res["calibration_seed0"].items():
        ax.plot(c["mean_predicted"], c["fraction_positive"], "o-", label=f"{k} (Brier {c['Brier']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("predicted P(extinction), quantile bins")
    ax.set_ylabel("observed fraction")
    ax.set_title("Reliability diagram (out-of-fold, seed 0)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "val_reliability.png", dpi=130)
    plt.close(fig)

    ex = res["extrapolation"]
    names = [n for n in ex if ex[n]["K"]]
    fig, ax = plt.subplots(figsize=(9, 4))
    w = 0.2
    for i, mdl in enumerate(("mean", "physics", "pure_ml_gp", "hybrid")):
        ax.bar(np.arange(len(names)) + (i - 1.5) * w, [ex[n]["K"][mdl]["RMSE_log"] for n in names], w, label=mdl)
    ax.set_xticks(range(len(names)), names, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("RMSE ln K on held-out class")
    ax.set_title("Extrapolation: train without a class, predict it")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "val_extrapolation_K.png", dpi=130)
    plt.close(fig)

    ph = res["physicality"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for key, c in ph["cases"].items():
        if "d0 3.5" in key:
            axes[0].plot(ph["O2_grid"], c["K_mm2_s"], label=key)
            axes[1].plot(ph["O2_grid"], c["P_ext_monotonic"], label=key)
    axes[0].set_xlabel("O2 mole fraction")
    axes[0].set_ylabel("hybrid K, mm$^2$/s")
    axes[0].legend(fontsize=6)
    axes[1].set_xlabel("O2 mole fraction")
    axes[1].set_ylabel("P(extinction), monotonic boosting")
    fig.suptitle("Physicality: response to O2 (N2 balance)")
    fig.tight_layout()
    fig.savefig(FIG / "val_physicality_O2.png", dpi=130)
    plt.close(fig)

    subprocess.run([sys.executable, str(ROOT / "scripts" / "render_validation.py")], check=True)
    print("written", OUT)


if __name__ == "__main__":
    main()
