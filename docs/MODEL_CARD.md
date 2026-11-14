# Model Card - Prometheus-0g FLEX models

Stage 5, 2026-11-14. Decisions: ADR-029 (targets, model types, constraints, metrics); physics: ADR-027. Train everything with one command: `.venv/Scripts/python scripts/train_models.py` (~45 s). Numbers below are from `docs/verification/model_report.json` and `model_comparison.tsv` of that run (data sha256 in the report).

## Intended use

Explain and predict droplet burning and flame extinction for the conditions tested in NASA's FLEX experiment on the ISS (methanol and n-heptane, O2 0.12-0.34, 0.69-3.05 atm, N2/CO2/He diluents, droplets 1.1-4.7 mm), to support fire-safety insights (product questions Q2, Q3, Q5). Not a design tool: every prediction comes with an uncertainty and an in-range / extrapolation label.

## Data

`data/processed/flex.csv` (PSI-69 FLEX + 2 tests from NASA/TP-2015-216046), rows with `use_in_model = True` (274), each target only where measured and all features are present:

| Target | Rows | Notes |
|---|---|---|
| burning-rate constant K (ln K) | 258 | 16 rows lack K or d0 |
| extinction at finite diameter (1/0) | 223 | 188 positive / 35 negative; definition ADR-018 (open question ADR-021) |
| d_ext/d0 (ln) | 188 | |

Cross-validation: GroupKFold, 5 folds, groups = test regime (fuel x pressure x composition, ADR-016; 80 groups in the K set). Metrics on pooled out-of-fold predictions. Seed 20261114.

## Features (pre-ignition only)

Raw: fuel (methanol flag), ln p, x_O2, x_CO2, x_He, ln d0. Physics (computed from the raw conditions only, PHYSICS.md): ln K_theory, B, T_f (equilibrium), Y_O2, ln alpha of the ambient gas; for extinction also ln chi_rad proxy, ln flow-time proxy, flame-standoff ratio. Allow-list and leakage guard: `src/fif/models/features.py`; `tests/test_models.py` fails if any post-ignition quantity (K, d_ext, burn time, test end, extinction label) enters a feature list.

## Architecture

**Burning-rate constant K (hybrid):**

$$\ln K = \underbrace{\ln K_{theory}}_{\text{level 1: Law \& Williams}} + \underbrace{\ln c_f}_{\text{level 2: one constant per fuel}} + \underbrace{GP(\mathbf{x})}_{\text{level 3: residual}}$$

- $c_f = \exp(\overline{\ln(K_{meas}/K_{theory})})$ per fuel on the training data (FORMULAS.md section 8). Fitted on all data: **methanol 0.964, heptane 0.714**. Physical meaning: the correction to the L&W effective-property prescription (x = 0.4 was tuned on ~1 mm heptane droplets in air) for each fuel under FLEX conditions; for heptane it absorbs mostly the larger, more radiating FLEX droplets (PHYSICS.md section 8).
- GP: StandardScaler, constant x RBF with one length scale per feature + white noise, normalize_y. 95 % interval = mean ± 1.96 sigma in ln K; sigma grows away from the training data (tested).

**Extinction:** logistic regression (L2, balanced class weights) and gradient boosting (HistGradientBoosting, balanced), boosting with and without monotonic constraints (P(extinction) decreasing in x_O2 and T_f, increasing in x_CO2; free in d0, p, He).

**d_ext/d0:** GP on ln(d_ext/d0) (no physics baseline exists in this project).

Saved models (`models/*.joblib`, each with data sha256, seed, sklearn version, features): `K_hybrid`, `ext_hybrid_logistic`, `ext_hybrid_boosting_monotonic`, `ext_hybrid_boosting_free`, `dext_hybrid_gp`.

## Metrics (grouped CV, out-of-fold)

**K (258 tests):**

| Model | RMSE ln K | MAE, mm²/s | R² (ln) | 95 % coverage |
|---|---|---|---|---|
| mean | 0.304 | 0.108 | -0.02 | 0.95 |
| physics (L&W, uncalibrated) | 0.302 | 0.113 | 0.00 | 0.90 |
| pure ML (GP on raw conditions) | 0.288 | 0.061 | 0.09 | 0.91 |
| **hybrid** | **0.214** | **0.053** | **0.49** | **0.93** |

By fuel (RMSE ln K): methanol - physics 0.133, hybrid 0.152, pure ML 0.307; heptane - physics 0.439, hybrid 0.278, pure ML 0.258. For methanol the uncalibrated theory alone is already the best model; the hybrid gains come from heptane. Hybrid 95 % coverage: methanol 0.96, heptane 0.89.

**Extinction at finite diameter (223 tests, 188 positive):**

| Model | AUC | Brier | accuracy | balanced accuracy |
|---|---|---|---|---|
| prior (constant) | n/a* | 0.134 | 0.843 | 0.500 |
| physics-only logistic (T_f, chi_rad, flow time, standoff) | 0.770 | 0.192 | 0.727 | **0.733** |
| pure ML boosting (raw conditions) | 0.689 | 0.150 | 0.803 | 0.616 |
| hybrid logistic | 0.776 | 0.177 | 0.718 | 0.670 |
| hybrid boosting, free | 0.785 | 0.119 | 0.816 | 0.647 |
| **hybrid boosting, monotonic** | **0.805** | 0.121 | 0.812 | 0.656 |

*The constant prior has no ranking ability; its computed 0.39 only reflects prevalence differences between folds.

**d_ext/d0 (188 tests):** mean RMSE_log 0.509; pure ML GP 0.406 (R² 0.36); hybrid GP 0.440 (R² 0.25). Adding the physics proxies did not help here.

## Interpretation and physics sign checks

- **K residual (GP, partial dependence over the data range):** ln d0 from 1.7 to 4.0 mm moves the residual from +0.13 to -0.14 (large droplets burn slower than theory, hypothesis H3); x_He from 0 to 0.45: +0.02 to -0.07 (theory over-predicts the helium effect, H4); x_CO2 and x_O2 flat. Permutation importance (in-sample): ln d0 0.147, B 0.142, x_CO2 0.063, x_He 0.024, the rest 0.
- **Physics-only extinction logistic (standardised coefficients):** T_f -1.24 (hotter flame, less extinction), ln chi_rad +0.65 (more radiative loss, more extinction), ln flow time -1.29 (longer residence time, less extinction, the Damköhler argument), flame standoff +0.45. All signs agree with FORMULAS.md section 3.
- **Hybrid extinction logistic:** x_O2 -0.44 and T_f -0.76 agree with the expected direction; **x_CO2 -0.09 disagrees** (expected +, CO2 as suppressant), small and collinear with T_f (CO2 lowers T_f), so the effect of CO2 is carried by T_f; x_He +1.56 (helium raises extinction probability; plausible through higher diffusivity and shorter residence time, not imposed). For discussion with Ruslan.
- **Monotonic vs free boosting:** constraints raised AUC from 0.785 to 0.805 at the same Brier score; they are kept for the interface model.

## Limitations - where not to trust the models

- Only methanol and n-heptane, only FLEX ranges (O2 <= 0.34, p 0.69-3.05 atm, d0 1.1-4.7 mm, T_inf about 298 K). The Moon-base atmosphere (O2 >= 0.30 at <= 10.2 psi) is just outside the tested pressure range: label as extrapolation.
- Above 1.2 atm only 9 CO2-diluted tests; no He or N2 data there.
- Heptane K: wider errors (RMSE ln 0.28, coverage 0.89 < 0.95).
- Extinction: only 35 negative examples; the class definition has an open question (ADR-021); balanced accuracy is 0.65-0.73.
- One test (C13H201, K = 0.05 mm²/s, flagged OUTLIER_K) dominates the largest errors of every model.
- Earth (1 g) numbers come from the L&W buoyancy correlation far outside its fitted range (PHYSICS.md section 4): not a model output to trust.
- CFI-G is not modelled (data map only, ADR-012).
