"""Compare raw L2 theory with FLEX data (stage 4): K_meas / K_theory by condition group, figures.

Outputs: docs/figures/physics_K_parity.png, docs/figures/physics_K_ratio_groups.png,
docs/figures/physics_extinction_proxies.png, docs/verification/physics_vs_data.tsv, stdout summary.
Only rows with use_in_model = True. No fitting here (calibration is stage 5).
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
from fif.physics.droplet import evaluate_flex  # noqa: E402

FIG = ROOT / "docs" / "figures"


def pclass(p_atm: float) -> str:
    return "~0.7 atm" if p_atm < 0.8 else "~1 atm" if p_atm < 1.2 else ">1.2 atm"


def main() -> None:
    f = pd.read_csv(ROOT / "data" / "processed" / "flex.csv")
    f = pd.concat([f, evaluate_flex(f)], axis=1)
    m = f[f["use_in_model"]].copy()
    m["K_theory_mm2_s"] = m["K_theory"] * 1e6
    m["ratio"] = m["K_mm2_s_orig"] / m["K_theory_mm2_s"]
    m["p_class"] = m["p_atm"].map(pclass)

    # summary table by group
    rows = []
    for keys, g in m.dropna(subset=["ratio"]).groupby(["fuel", "diluent", "p_class"]):
        r = g["ratio"]
        rows.append({"fuel": keys[0], "diluent": keys[1], "p_class": keys[2], "n": len(r),
                     "ratio_median": r.median(), "ratio_iqr_lo": r.quantile(0.25), "ratio_iqr_hi": r.quantile(0.75),
                     "K_meas_median": g["K_mm2_s_orig"].median(), "K_theory_median": g["K_theory_mm2_s"].median(),
                     "T_f_median": g["T_f"].median(), "B_median": g["B"].median()})
    tab = pd.DataFrame(rows)
    out = ROOT / "docs" / "verification" / "physics_vs_data.tsv"
    tab.to_csv(out, sep="\t", index=False, float_format="%.4g", lineterminator="\n")
    pd.set_option("display.width", 200)
    print(tab.round(3).to_string(index=False))
    print("\nOverall ratio median by fuel:", m.groupby("fuel")["ratio"].median().round(3).to_dict())
    lr = np.log(m["ratio"].dropna())
    print("log-ratio std by fuel:", m.assign(lr=np.log(m["ratio"])).groupby("fuel")["lr"].std().round(3).to_dict())
    # correlation of ratio with conditions (does theory miss a trend?)
    for fuel, g in m.dropna(subset=["ratio"]).groupby("fuel"):
        c = {k: round(float(np.corrcoef(g[k], np.log(g["ratio"]))[0, 1]), 2)
             for k in ["x_o2", "p_atm", "d0_mm_orig", "T_f", "x_he", "x_co2"] if g[k].notna().all() and g[k].std() > 0}
        print(f"corr(log ratio, X) {fuel}:", c)
    print("T_1 capped:", int(m["T_1_capped"].sum()), "rows; Gr > 1 (outside L&W buoyancy fit):", int(m["Gr_above_fit_range"].sum()))
    for col in ["K_theory_ambient_cp", "K_theory_c1_only", "K_theory"]:
        r = m["K_mm2_s_orig"] / (m[col] * 1e6)
        print(f"variant {col:22} median by fuel {r.groupby(m['fuel']).median().round(3).to_dict()}"
              f"  share within +-15% {((r > 0.85) & (r < 1.15)).groupby(m['fuel']).mean().round(2).to_dict()}")

    colors = {"N2": "#1f77b4", "CO2": "#d62728", "He": "#2ca02c"}
    marks = {"Methanol": "o", "Heptane": "^"}
    fig, ax = plt.subplots(figsize=(6, 5.5))
    for (fuel, dil), g in m.groupby(["fuel", "diluent"]):
        ax.scatter(g["K_theory_mm2_s"], g["K_mm2_s_orig"], c=colors[dil], marker=marks[fuel], s=22, alpha=0.65,
                   label=f"{fuel}, {dil}")
    lim = [0, max(m["K_theory_mm2_s"].max(), 1.1)]
    ax.plot(lim, lim, "k--", lw=1, label="1:1")
    ax.set_xlabel("K theory (quasi-steady, Law & Williams 1972 prescription), mm$^2$/s"); ax.set_ylabel("K measured (FLEX), mm$^2$/s")
    ax.set_title("FLEX burning-rate constant: raw theory vs ISS data"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "physics_K_parity.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    groups = [(k, g["ratio"].dropna()) for k, g in m.groupby(["fuel", "diluent", "p_class"])]
    groups = [(k, v) for k, v in groups if len(v) >= 3]
    ax.boxplot([v for _, v in groups], tick_labels=[f"{a[:4]}\n{b}\n{c}" for (a, b, c), _ in groups])
    ax.axhline(1, ls="--", c="k", lw=1)
    ax.set_ylabel("K measured / K theory"); ax.set_title("Where the raw theory errs (groups with n >= 3)")
    ax.tick_params(axis="x", labelsize=7)
    fig.tight_layout(); fig.savefig(FIG / "physics_K_ratio_groups.png", dpi=130); plt.close(fig)

    e = m.dropna(subset=["extinct_finite_d"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, (fuel, g) in zip(axes, e.groupby("fuel")):
        for cls, gg in g.groupby("extinct_finite_d"):
            ax.scatter(gg["chi_rad_proxy"], gg["T_f"], s=20, alpha=0.6,
                       label={1: "extinguished at finite d", 0: "no finite-d extinction"}[int(cls)])
        ax.set_xscale("log"); ax.set_xlabel("radiative-loss proxy chi/kappa, Pa m (log)"); ax.set_ylabel("T_f (equilibrium, with dissociation), K")
        ax.set_title(f"{fuel}: extinction vs physics proxies"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "physics_extinction_proxies.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
