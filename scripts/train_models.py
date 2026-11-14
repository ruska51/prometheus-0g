"""Train and compare all stage-5 models with one command; save models and the comparison.

Usage (repository root): ``.venv/Scripts/python scripts/train_models.py``
Outputs: models/*.joblib, docs/verification/model_report.json, docs/verification/K_oof_predictions.csv,
docs/verification/model_comparison.tsv, docs/figures/model_*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fif.models.train import run  # noqa: E402

FIG = ROOT / "docs" / "figures"
VER = ROOT / "docs" / "verification"


def main() -> None:
    rep = run(ROOT, ROOT / "models", VER)
    rows = []
    for target in ("K", "d_ext_over_d0", "extinction"):
        for model, m in rep[target]["metrics"].items():
            rows.append({"target": target, "model": model, "n_rows": rep[target]["n_rows"], **{k: round(v, 4) for k, v in m.items()}})
    tab = pd.DataFrame(rows)
    tab.to_csv(VER / "model_comparison.tsv", sep="\t", index=False, lineterminator="\n")
    pd.set_option("display.width", 200)
    print(tab.to_string(index=False))
    print("\nK by fuel (RMSE_log):", {m: {f: round(v["RMSE_log"], 3) for f, v in d.items()}
                                     for m, d in rep["K"]["metrics_by_fuel"].items()})
    print("c_f:", {k: round(v, 3) for k, v in rep["K"]["c_f"].items()})
    print("GP kernel:", rep["K"]["gp_kernel"])
    print("residual permutation importance (in-sample):", rep["K"]["residual_permutation_importance_in_sample"])
    for f, d in rep["K"]["partial_dependence_residual"].items():
        print(f"PDP {f}: {d['grid'][0]}..{d['grid'][-1]} -> residual {d['residual'][0]:+.3f}..{d['residual'][-1]:+.3f}")
    print("extinction hybrid logistic coefs:", rep["extinction"]["hybrid_logistic_standardised_coefs"])
    print("sign check:", rep["extinction"]["sign_check"])
    print("physics logistic coefs:", rep["extinction"]["physics_logistic_standardised_coefs"])
    print("rows: K", rep["K"]["n_rows"], "dropped", rep["K"]["rows_dropped_missing"], "| ext", rep["extinction"]["n_rows"],
          "pos", rep["extinction"]["n_positive"], "| dext", rep["d_ext_over_d0"]["n_rows"])

    k = rep["_frames"]["K"]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4), sharex=True, sharey=True)
    for ax, name in zip(axes, ("mean", "physics", "pure_ml_gp", "hybrid")):
        for fuel, g in k.groupby("fuel"):
            ax.scatter(np.exp(g[f"oof_{name}"]) * 1e6, np.exp(g["y_lnK"]) * 1e6, s=14, alpha=0.6, label=fuel)
        ax.plot([0, 1.2], [0, 1.2], "k--", lw=1)
        m = rep["K"]["metrics"][name]
        ax.set_title(f"{name}\nRMSE_log {m['RMSE_log']:.3f}, cov95 {m['coverage95']:.2f}", fontsize=9)
        ax.set_xlabel("predicted K, mm$^2$/s (out-of-fold)")
    axes[0].set_ylabel("measured K, mm$^2$/s"); axes[0].legend(fontsize=7)
    fig.suptitle("FLEX burning-rate constant: 4 models, grouped CV by regime (5 folds)")
    fig.tight_layout(); fig.savefig(FIG / "model_K_oof.png", dpi=130); plt.close(fig)

    fig, axes = plt.subplots(1, 4, figsize=(15, 3.4))
    for ax, (f, d) in zip(axes, rep["K"]["partial_dependence_residual"].items()):
        ax.plot(d["grid"], d["residual"], "o-")
        ax.axhline(0, c="k", lw=0.8); ax.set_xlabel(f); ax.set_ylabel("GP residual ln(K/(c_f K_theory))")
    fig.suptitle("Hybrid model: partial dependence of the ML residual")
    fig.tight_layout(); fig.savefig(FIG / "model_K_pdp.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
