"""Short EDA of processed FLEX and CFI-G tables -> docs/figures/*.png + coverage tables on stdout.

Reads data/processed (run scripts/build_data.py first). Moon-base box uses the challenge text
(docs/challenge/CHALLENGE.md): O2 "30% or greater" at "10.2 psi or less"; 10.2 psi converted with
1 atm = 14.696 psia (docs/FORMULAS.md section 1).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "docs" / "figures"
MOON_P_ATM = 10.2 / 14.696
MOON_XO2 = 0.30


def pclass(p_atm: float) -> str:
    if p_atm <= 0:
        return "0 (anomaly)"
    if p_atm < 0.8:
        return "~0.7 atm"
    if p_atm < 1.2:
        return "~1 atm"
    if p_atm < 2.5:
        return "~2 atm"
    return "~3 atm"


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    f = pd.read_csv(ROOT / "data" / "processed" / "flex.csv")
    c = pd.read_csv(ROOT / "data" / "processed" / "cfig.csv")
    f["p_class"] = f["p_atm"].map(pclass)

    # 1. condition space
    fig, ax = plt.subplots(figsize=(7, 4.5))
    marks = {"N2": "o", "CO2": "s", "He": "^"}
    colors = {"Methanol": "#1f77b4", "Heptane": "#d62728"}
    for (fuel, dil), g in f[f["use_in_model"]].groupby(["fuel", "diluent"]):
        ax.scatter(g["p_atm"], g["x_o2"], marker=marks[dil], c=colors[fuel], alpha=0.6, s=28,
                   label=f"{fuel}, {dil} (n={len(g)})")
    ax.add_patch(plt.Rectangle((0.5, MOON_XO2), MOON_P_ATM - 0.5, 0.06, fill=True, alpha=0.12, ls="--", ec="k", fc="k"))
    ax.text(0.505, 0.362, "Moon-base atmosphere (challenge):\nO2 >= 0.30 at <= 10.2 psi (0.694 atm)", fontsize=7, va="bottom")
    ax.set_xscale("log"); ax.set_xlim(0.5, 3.6); ax.set_ylim(0.1, 0.40)
    ax.set_xlabel("Ambient pressure, atm (log)"); ax.set_ylabel("Initial O2 mole fraction")
    ax.set_title("FLEX (PSI-69): tested conditions, 273 tests used for modeling")
    ax.legend(fontsize=7, ncol=2, loc="lower right"); fig.tight_layout(); fig.savefig(FIG / "flex_conditions.png", dpi=130)
    plt.close(fig)

    # 2. outcomes
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    lab = f["extinct_finite_d"].map({1: "extinguished at finite d", 0: "no finite-d extinction"}).fillna("unknown (blank)")
    ct = pd.crosstab([f["fuel"], f["diluent"]], lab)
    ct.plot(kind="bar", stacked=True, ax=axes[0], color=["#2ca02c", "#ff7f0e", "#9e9e9e"])
    axes[0].set_title("FLEX outcome by fuel x diluent"); axes[0].set_xlabel(""); axes[0].legend(fontsize=7)
    for fuel, g in f.groupby("fuel"):
        axes[1].hist(g["K_mm2_s_orig"].dropna(), bins=25, alpha=0.6, color=colors[fuel], label=fuel)
    axes[1].set_xlabel("Burning-rate constant K, mm^2/s"); axes[1].set_ylabel("tests"); axes[1].legend()
    axes[1].set_title("FLEX burning-rate constant")
    fig.tight_layout(); fig.savefig(FIG / "flex_outcomes.png", dpi=130); plt.close(fig)

    # 3. coverage matrix
    cov = pd.crosstab([f["fuel"], f["diluent"]], f["p_class"])
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    im = ax.imshow(cov.values, cmap="Blues")
    ax.set_xticks(range(cov.shape[1]), cov.columns, fontsize=8)
    ax.set_yticks(range(cov.shape[0]), [f"{a}, {b}" for a, b in cov.index], fontsize=8)
    for i in range(cov.shape[0]):
        for j in range(cov.shape[1]):
            ax.text(j, i, cov.values[i, j], ha="center", va="center", fontsize=8,
                    color="white" if cov.values[i, j] > cov.values.max() / 2 else "black")
    ax.set_title("FLEX coverage: tests per fuel x diluent x pressure"); fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout(); fig.savefig(FIG / "flex_coverage.png", dpi=130); plt.close(fig)

    # 4. CFI-G map
    def outcome(r):
        if r["hot_ignition"] == "no":
            return "no ignition"
        if r["hot_ignition"] == "flash":
            return "flash"
        return {"SE": "self-extinguished", "FT": "flow terminated"}.get(r["end_mode"], "ignited, end n/a")
    c["outcome"] = c.apply(outcome, axis=1)
    cols = {"no ignition": "#7f7f7f", "flash": "#bcbd22", "self-extinguished": "#ff7f0e",
            "flow terminated": "#2ca02c", "ignited, end n/a": "#17becf"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, (tab, g) in zip(axes, c.groupby("table")):
        for o, gg in g.groupby("outcome"):
            ax.scatter(gg["p_Pa"] / 1e5, gg["x_o2_oxidizer"], c=cols[o], s=22, alpha=0.7, label=f"{o} ({len(gg)})")
        ax.set_title(f"CFI-G {tab} flames (n={len(g)})"); ax.set_xlabel("Pressure, bar"); ax.legend(fontsize=7)
    axes[0].set_ylabel("O2 mole fraction of oxidizer")
    fig.tight_layout(); fig.savefig(FIG / "cfig_map.png", dpi=130); plt.close(fig)

    print("FLEX coverage (fuel x diluent x pressure class):"); print(cov.to_string())
    print("\nFLEX outcome x diluent:"); print(pd.crosstab(f["diluent"], lab).to_string())
    print("\nFLEX K mm2/s by fuel:"); print(f.groupby("fuel")["K_mm2_s_orig"].describe().round(3).to_string())
    print("\nFLEX ranges (use_in_model):")
    m = f[f["use_in_model"]]
    for col in ["p_atm", "x_o2", "x_co2", "x_he", "d0_mm_orig", "d_ext_over_d0", "burn_time_s"]:
        print(f"  {col}: {m[col].min():.3g} .. {m[col].max():.3g} (n={m[col].notna().sum()})")
    near = m[(m["x_o2"] >= MOON_XO2)]
    print(f"\nFLEX tests with O2 >= 0.30: {len(near)}; pressures (atm): {sorted(near['p_atm'].round(3).unique())}")
    print("\nCFI-G outcome by table:"); print(pd.crosstab(c["table"], c["outcome"]).to_string())


if __name__ == "__main__":
    main()
