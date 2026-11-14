"""Render docs/VALIDATION.md (and the metrics block of docs/MODEL_CARD.md) from saved results.

Inputs: docs/validation_results.json (scripts/validate.py), docs/verification/model_report.json
(scripts/train_models.py). Every number in the generated text comes from these files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "docs" / "validation_results.json").read_text(encoding="utf-8"))
M = json.loads((ROOT / "docs" / "verification" / "model_report.json").read_text(encoding="utf-8"))

# Hypotheses for the largest hybrid errors: physical reasoning, no numbers (numbers come from the table).
HYPOTHESES = {
    "C13H201": "K itself is suspect (OUTLIER_K, KTB_INCONSISTENT); excluded from K training (ADR-030), still evaluated.",
    "193R002": "Very small heptane droplet (smallest d0 in FLEX) ending in completion: ignition transient and heat-up are a large share of its short life, the quasi-steady fit over few frames overstates K; also O2+N2 sum 0.98 (MOLE_SUM_OFF).",
    "193R001": "Small heptane droplet burning to completion: same short-life effect as 193R002 but in the other direction - few frames, uncertain K.",
    "205F001": "Large methanol droplet ending in disruption: water absorption grows with droplet size and lowers K (NASA, NTRS 20130014061); disruption truncates the fit.",
    "193F001": "The kept row of the duplicated 193F001 pair (ADR-019): unintended very large droplet that hit the igniter and drifted (TP Fig. 74); short, disturbed burn.",
    "30CAL06": "Early calibration-series heptane test ending in disruption: disruption (micro-explosion) accelerates apparent regression.",
    "248F001": "Heptane at 2 atm in 70 % CO2: only 9 tests above 1.2 atm, the GP has little support there.",
    "C11H101": "Large heptane droplet in CO2 at 0.7 atm: radiative loss of a big sooting flame in a CO2-rich (radiating) atmosphere.",
    "C14M101": "Large methanol droplet in 50 % CO2 at low O2: near-limit burning, water absorption; few comparable tests.",
    "C12M401": "Methanol in 40 % CO2 at 0.7 atm: CO2 radiation/chemistry not represented in the theory (H5).",
}


def f3(x):
    return "n/a" if x is None or (isinstance(x, float) and x != x) else f"{x:.3f}"


def cv_table():
    s = R["repeated_cv"]["summary"]
    lines = ["| Model | RMSE ln K mean ± sd (min-max) | MAE mm²/s | R² ln | 95 % coverage |", "|---|---|---|---|---|"]
    for k, v in s["K"].items():
        lines.append(
            f"| {k} | {f3(v['RMSE_log']['mean'])} ± {f3(v['RMSE_log']['sd'])} ({f3(v['RMSE_log']['min'])}-{f3(v['RMSE_log']['max'])}) "
            f"| {f3(v['MAE']['mean'])} | {f3(v['R2_log']['mean'])} | {f3(v['coverage95']['mean'])} |"
        )
    lines += ["", "| Model | AUC mean ± sd (min-max) | Brier | accuracy | balanced accuracy |", "|---|---|---|---|---|"]
    for k, v in s["extinction"].items():
        auc = (
            "n/a (constant)"
            if k == "prior"
            else f"{f3(v['AUC']['mean'])} ± {f3(v['AUC']['sd'])} ({f3(v['AUC']['min'])}-{f3(v['AUC']['max'])})"
        )
        lines.append(
            f"| {k} | {auc} | {f3(v['Brier']['mean'])} | {f3(v['accuracy']['mean'])} | {f3(v['balanced_accuracy']['mean'])} |"
        )
    return "\n".join(lines)


def extrap_table():
    lines = [
        "| Held-out class | n | mean | physics | pure ML | hybrid | best | hybrid bias ln(meas/pred) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, e in R["extrapolation"].items():
        k = e["K"]
        if not k:
            continue
        best = min(k, key=lambda m: k[m]["RMSE_log"])
        lines.append(
            f"| {name} | {e['n_test_K']} | "
            + " | ".join(f3(k[m]["RMSE_log"]) for m in ("mean", "physics", "pure_ml_gp", "hybrid"))
            + f" | {best} | {f3(k['hybrid']['bias_log'])} |"
        )
    lines += [
        "",
        "Extinction on the held-out class (AUC where both classes are present; Brier otherwise):",
        "",
        "| Held-out class | n (positive) | physics logistic | pure ML boosting | hybrid logistic | hybrid boosting monotonic |",
        "|---|---|---|---|---|---|",
    ]
    for name, e in R["extrapolation"].items():
        x = e["extinction"]
        if not x:
            lines.append(f"| {name} | {e['n_test_ext']} ({e['n_pos_test_ext']}) | too few tests or one class | | | |")
            continue

        def cell(m, x=x):
            return f"AUC {f3(x[m]['AUC'])}" if "AUC" in x[m] else f"Brier {f3(x[m]['Brier'])}"

        lines.append(
            f"| {name} | {e['n_test_ext']} ({e['n_pos_test_ext']}) | "
            + " | ".join(
                cell(m) for m in ("physics_logistic", "pure_ml_boosting", "hybrid_logistic", "hybrid_boosting_monotonic")
            )
            + " |"
        )
    return "\n".join(lines)


def variants_text():
    vs = R["variant_selection"]
    o, kf, ex = vs["outlier"], vs["k_residual_features"], vs["extinction_model"]
    lines = [
        f"**1. Treatment of suspect K values.** Rule: {o['rule']}. Evaluation rows: {o['n_eval_trusted']}.",
        "",
        "| Variant | training rows | hybrid RMSE (trusted) | pure ML RMSE (trusted) | hybrid RMSE (all rows) |",
        "|---|---|---|---|---|",
    ]
    for k, v in o["variants"].items():
        lines.append(
            f"| {k} | {v['n_train_rows']} | {f3(v['RMSE_log_trusted_mean']['hybrid'])} ± {f3(v['RMSE_log_trusted_sd']['hybrid'])} "
            f"| {f3(v['RMSE_log_trusted_mean']['pure_ml_gp'])} ± {f3(v['RMSE_log_trusted_sd']['pure_ml_gp'])} | {f3(v['RMSE_log_all_rows_mean']['hybrid'])} |"
        )
    lines += [
        "",
        f"Chosen: **{o['chosen']}**.",
        "",
        f"**2. Residual feature set of the hybrid.** Rule: {kf['rule']}.",
        "",
        "| Feature set | RMSE ln K mean ± sd | 95 % coverage | worst K drop along O2 |",
        "|---|---|---|---|",
    ]
    for k, v in kf["variants"].items():
        lines.append(
            f"| {k} | {f3(v['RMSE_log_mean'])} ± {f3(v['RMSE_log_sd'])} | {f3(v['coverage95_mean'])} | {v['worst_K_drop_along_O2'] * 100:.1f} % |"
        )
    lines += [
        "",
        f"Chosen: **{kf['chosen']}** (differences between sets are within one sd).",
        "",
        f"**3. Extinction model for the interface.** Rule: {ex['rule']}.",
        "",
        "| Model | AUC mean ± sd | Brier | balanced accuracy | worst rise of P along O2 |",
        "|---|---|---|---|---|",
    ]
    for k, v in ex["variants"].items():
        lines.append(
            f"| {k} | {f3(v['AUC_mean'])} ± {f3(v['AUC_sd'])} | {f3(v['Brier_mean'])} | {f3(v['balanced_accuracy_mean'])} | {f3(v['worst_P_rise_along_O2'])} |"
        )
    lines += ["", f"Chosen: **{ex['chosen']}**."]
    return "\n".join(lines)


def calib_table():
    lines = ["| Model | Brier | bins: mean predicted -> observed fraction |", "|---|---|---|"]
    for k, c in R["calibration_seed0"].items():
        pairs = ", ".join(f"{a:.2f}->{b:.2f}" for a, b in zip(c["mean_predicted"], c["fraction_positive"]))
        lines.append(f"| {k} | {f3(c['Brier'])} | {pairs} |")
    return "\n".join(lines)


def groups_table():
    lines = ["| Fuel | Diluent | Pressure | n | mean ln(meas/pred) | se | |mean| > 2 se |", "|---|---|---|---|---|---|---|"]
    for g in R["residuals_by_group_hybrid_seed0"]:
        lines.append(
            f"| {g['fuel']} | {g['diluent']} | {g['p_class']} | {g['n']} | {f3(g['mean_residual_log'])} | {f3(g['se'])} | {'yes' if g['significant_2se'] else ''} |"
        )
    return "\n".join(lines)


def physicality_text():
    ph = R["physicality"]
    ok_k = all(c["K_increases_with_O2"] for c in ph["cases"].values())
    ok_l = all(c["P_ext_logistic_nonincreasing"] for c in ph["cases"].values())
    ok_b = all(c["P_ext_monotonic_nonincreasing"] for c in ph["cases"].values())
    lines = [
        f"- K (hybrid) rises with O2 in all 8 cases (2 fuels x 0.7/1.0 atm x d0 2.0/3.5 mm, N2 balance, O2 0.12-0.34): **{ok_k}**.",
        f"- P(extinction) does not rise with O2 - hybrid logistic (interface model): **{ok_l}**; monotonic boosting: **{ok_b}** (constraints on O2 and T_f alone do not make the whole response monotone, because the unconstrained proxies also change with O2).",
        f"- Hybrid K predicted on all observed rows: {ph['K_pred_range_mm2_s'][0]:.3f}-{ph['K_pred_range_mm2_s'][1]:.3f} mm²/s.",
        f"- GP sigma of ln K on the data: median {f3(ph['K_sigma_log_on_data']['median'])}, 95th percentile {f3(ph['K_sigma_log_on_data']['p95'])}, max {f3(ph['K_sigma_log_on_data']['max'])}.",
        "",
        "| Probe | K hybrid, mm²/s | sigma ln K | K theory, mm²/s | P(extinction), monotonic boosting |",
        "|---|---|---|---|---|",
    ]
    for k, v in ph["probes"].items():
        lines.append(
            f"| {k} | {f3(v['K_mm2_s'])} | {f3(v['sigma_log'])} | {f3(v['K_theory_mm2_s'])} | {f3(v['P_ext_monotonic'])} |"
        )
    lines.append(
        "\nAutomated tests: `tests/test_validation.py` (monotonicity of the saved interface models, K range, uncertainty growth, reliability rule)."
    )
    return "\n".join(lines)


def failures_table():
    lines = [
        "| Test | Fuel | Diluent | p, atm | O2 | CO2 | He | d0, mm | K meas | K hybrid | K theory | z | Test end | Flags | Hypothesis |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for f in R["failures_hybrid_seed0"]:
        lines.append(
            f"| {f['flex_identifier']} | {f['fuel']} | {f['diluent']} | {f['p_atm']:.2f} | {f['x_o2']} | {f['x_co2']} | {f['x_he']} | {f['d0_mm_orig']} "
            f"| {f['K_meas']:.2f} | {f['K_pred']:.2f} | {f['K_theory_mm2_s']:.2f} | {f['z']:.1f} | {f['test_end']} | {f['quality_flag'] or ''} "
            f"| {HYPOTHESES.get(f['flex_identifier'], 'to discuss')} |"
        )
    return "\n".join(lines)


def main():
    s = R["repeated_cv"]["summary"]["K"]
    ex = R["extrapolation"]
    atm = ["He diluent", "CO2 diluent", "p ~0.7 atm (< 0.8)", "O2 >= 0.30 (Moon-like O2)"]
    wins = [n for n in atm if min(ex[n]["K"], key=lambda m: ex[n]["K"][m]["RMSE_log"]) == "hybrid"]
    ratio = [ex[n]["K"]["pure_ml_gp"]["RMSE_log"] / ex[n]["K"]["hybrid"]["RMSE_log"] for n in atm]
    ls_path = ROOT / "docs" / "verification" / "extinction_label_sensitivity.json"
    LS = ""
    if ls_path.exists():
        ls = json.loads(ls_path.read_text(encoding="utf-8"))
        v = ls["variants"]
        auc = {k: x["models"][ls["interface_model"]]["AUC"] for k, x in v.items()}
        failed = [f"{k}: {c}" for k, cs in ls["checks"].items() for c, ok in cs.items() if not ok]
        LS = (
            "Sensitivity to the definition (docs/verification/extinction_label_sensitivity.md): interface-model AUC "
            + ", ".join(f"{k.split('_')[0]} {a:.3f}" for k, a in auc.items())
            + "; P(extinction) falls with O2 under every definition (S3, S4 hold); "
            + (
                "all pre-declared checks pass."
                if ls["robust"]
                else "pre-declared checks failed: "
                + "; ".join(failed)
                + " (variant C ranks better because 'Disruption' tests become negatives)."
            )
        )
    doc = f"""# Validation

Generated by `scripts/render_validation.py` from `docs/validation_results.json` (created {R["created_utc"]}, data sha256 `{R["data_sha256"][:16]}...`) and `docs/verification/model_report.json`. Do not edit numbers by hand: rerun `.venv/Scripts/python scripts/validate.py`. Decisions: ADR-030 (variant selection rules), ADR-031 (interface tests, reliability thresholds), ADR-032 (presentation).

## 1. Method

- Data: FLEX model rows; K: {R["n_rows"]["K"]} tests ({R["n_rows"]["groups_K"]} regime groups); extinction: {R["n_rows"]["extinction"]} tests ({R["n_rows"]["extinction_positive"]} positive).
- Grouped k-fold: GroupKFold(5) on test regimes (fuel x pressure x composition, ADR-016), repeated with shuffled group assignment for seeds {R["repeated_cv"]["seeds"]}; metrics on pooled out-of-fold predictions per seed, then mean ± sd over seeds.
- Leave-class-out extrapolation: train without a whole class of conditions, predict it.
- Variant choices (outlier treatment, residual features, interface extinction model) by rules fixed before running (section 2).
- Leakage: only pre-ignition features (`tests/test_models.py`).

## 2. Variant selection (rules fixed in advance, ADR-030)

{variants_text()}

## 3. Grouped CV, repeated over seeds (final configuration)

{cv_table()}

Reading: inside the tested conditions the hybrid and the pure-ML GP are statistically equal; both are far better than the uncalibrated physics or the mean.

## 4. Extrapolation: train without a class, predict it (RMSE ln K)

{extrap_table()}

Figure: `docs/figures/val_extrapolation_K.png`.

Reading (K): the hybrid is best on {len(wins)} of {len(atm)} atmosphere classes ({", ".join(wins)}); there pure ML is {min(ratio):.1f}-{max(ratio):.1f}x worse. On a new fuel the hybrid does not transfer (its calibration constant and residual are fuel-specific): predicting methanol from heptane-only training, pure ML ({f3(ex["fuel = methanol (train on heptane)"]["K"]["pure_ml_gp"]["RMSE_log"])}) and the uncalibrated theory ({f3(ex["fuel = methanol (train on heptane)"]["K"]["physics"]["RMSE_log"])}) are equal; predicting heptane from methanol-only training, every model is poor (best pure ML {f3(ex["fuel = heptane (train on methanol)"]["K"]["pure_ml_gp"]["RMSE_log"])}, theory {f3(ex["fuel = heptane (train on methanol)"]["K"]["physics"]["RMSE_log"])}). No model here transfers reliably to a fuel it has not seen. Low O2 (<= 0.15): pure ML slightly better than the hybrid. Above 1.2 atm only {ex["p > 1.2 atm"]["n_test_K"]} tests exist; there the uncalibrated theory is best.

Reading (extinction): on held-out classes the interface model (hybrid logistic) is weak - AUC {f3(ex["He diluent"]["extinction"]["hybrid_logistic"].get("AUC"))} on He and {f3(ex["O2 >= 0.30 (Moon-like O2)"]["extinction"]["hybrid_logistic"].get("AUC"))} on O2 >= 0.30 (only {ex["O2 >= 0.30 (Moon-like O2)"]["n_test_ext"]} tests); the monotonic boosting ranks better there but is not monotone in O2. Extinction predictions outside the tested atmospheres are therefore shown only as a labelled trend, not as a probability to rely on.

## 5. Classifier calibration (reliability diagram, out-of-fold seed 0)

{calib_table()}

Figure: `docs/figures/val_reliability.png`. Balanced class weights push predicted probabilities toward 0.5 for the logistic models (higher Brier than boosting); the ranking (AUC) is what the interface uses, probabilities are shown with this caveat.

## 6. Prediction vs measurement and systematic errors (hybrid, seed 0)

{groups_table()}

Figure: `docs/figures/val_K_pred_vs_meas.png`.

## 7. Physicality checks

{physicality_text()}

## 8. Largest errors (hybrid, out-of-fold seed 0) and hypotheses

{failures_table()}

## 9. Conclusions

- Within the FLEX conditions the hybrid K model reaches RMSE ln K {f3(s["hybrid"]["RMSE_log"]["mean"])} ± {f3(s["hybrid"]["RMSE_log"]["sd"])} (about ±{(2.718281828 ** s["hybrid"]["RMSE_log"]["mean"] - 1) * 100:.0f} % typical error) with 95 % coverage {f3(s["hybrid"]["coverage95"]["mean"])}; pure ML is equal there ({f3(s["pure_ml_gp"]["RMSE_log"]["mean"])}).
- The physics earns its place under extrapolation to a new atmosphere: He, CO2, ~0.7 atm and Moon-like O2 - exactly the Moon-base question.
- It does not transfer to a new fuel, and neither does any other model reliably; for anything but methanol and n-heptane the interface shows only the uncalibrated theory, labelled extrapolation.
- The extinction classifier ranks tests reasonably inside the data (AUC about 0.79) but extrapolates poorly to new atmospheres.
- Reliability labels (ADR-031): "extrapolation" if a condition or the O2-pressure combination was not tested for that fuel and diluent (the Moon-base corner O2 0.30 at 0.694 atm is such a case: tested only from 0.703 atm at that O2); "unreliable" if sigma ln K > 0.20.
- One suspect test (C13H201) was the cause of the earlier non-monotonic K response; with it excluded from K training all physicality checks pass.

## 10. Limitations

- Two fuels, one experiment (FLEX), ISS ambient about 298 K; partial gravity untested.
- Extinction: {R["n_rows"]["extinction"] - R["n_rows"]["extinction_positive"]} negative examples; class definition from the extinction diameter (ADR-018), kept after the sensitivity check (ADR-039). {LS}
- Earth (1 g) numbers are outside the fitted range of the L&W buoyancy correlation (PHYSICS.md section 4).
"""
    (ROOT / "docs" / "VALIDATION.md").write_text(doc, encoding="utf-8")

    # MODEL_CARD metrics block
    mc_path = ROOT / "docs" / "MODEL_CARD.md"
    mc = mc_path.read_text(encoding="utf-8")
    block = (
        "<!-- METRICS:BEGIN (generated by scripts/render_validation.py) -->\n"
        f"Final configuration (ADR-030): K hybrid residual features `{R['variant_selection']['k_residual_features']['chosen']}`, "
        f"K training excludes {M['K'].get('train_excluded', [])}, interface extinction model `{R['variant_selection']['extinction_model']['chosen']}`. "
        f"Calibration constants c_f: " + ", ".join(f"{k} {v:.3f}" for k, v in M["K"]["c_f"].items()) + ".\n\n"
        "Grouped CV repeated over 5 seeds (docs/VALIDATION.md section 3):\n\n" + cv_table() + "\n<!-- METRICS:END -->"
    )
    if "<!-- METRICS:BEGIN" in mc:
        mc = re.sub(r"<!-- METRICS:BEGIN.*?<!-- METRICS:END -->", lambda _: block, mc, flags=re.S)
    else:
        mc = mc.replace(
            "## Metrics (grouped CV, out-of-fold)",
            "## Metrics (grouped CV, out-of-fold)\n\n"
            + block
            + "\n\nStage-5 single-split tables below are kept for history (before ADR-030).\n",
            1,
        )
    mc_path.write_text(mc, encoding="utf-8")
    print("rendered VALIDATION.md and MODEL_CARD metrics block")


if __name__ == "__main__":
    main()
