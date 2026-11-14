# Decision Log (ADR)

All decisions are made by Ruslan Sharafutdinov (CLAUDE.md section 2.1). Claude records them.

## Template

```
## ADR-NNN: <title>
- Date/time:
- Stage:
- Context: <why the question came up>
- Options: A) ... B) ... C) ...
- Claude's recommendation: <option + why>
- Decision (Ruslan): <choice + his words, if any>
- Consequences: <what changes in code/data/UI>
- Sources: <links>
```

---

## ADR-001: Dashboard stack and hosting
- Date/time: 2026-11-14 11:00 (UTC+5)
- Stage: 0
- Context: Single team member who is not a programmer; ~2.5 h budget for the UI; a free public demo link is required.
- Options: A) Streamlit B) Dash (Plotly) C) React + FastAPI. Hosting: 1) Hugging Face Spaces 2) Streamlit Community Cloud.
- Claude's recommendation: A + 1. Streamlit is the fastest Python-only path; HF Spaces can be deployed from the command line, so Claude can deploy and redeploy without browser steps.
- Decision (Ruslan): "the hosting that starts quickly, looks more or less fine, and that you can launch yourself" -> Streamlit; hosting: Hugging Face Spaces.
- Consequences: `app/` is a Streamlit app. Stage 11 needs a Hugging Face account and a write token from Ruslan (one-time, ~3 min). Token never committed (.gitignore).
- Sources: -

## ADR-002: Repository visibility
- Date/time: 2026-11-14 11:00 (UTC+5)
- Stage: 0
- Context: The "Link to Final Project" must be public. No remote is configured yet.
- Options: A) public GitHub now B) private, open at the end C) local only until stage 11.
- Claude's recommendation: A - deploy and public link can be checked early.
- Decision (Ruslan): A, public from the start.
- Consequences: Ruslan published the repository at https://github.com/ruska51/prometheus-0g on 2026-11-14. Commits are pushed after each step.
- Sources: -

## ADR-003: Code license
- Date/time: 2026-11-14 11:00 (UTC+5)
- Stage: 0
- Context: The repository's initial commit (8619e3c) already contains an Apache-2.0 LICENSE.
- Options: A) keep Apache-2.0 B) MIT C) other.
- Claude's recommendation: A - already in place, permissive, explicit patent grant.
- Decision (Ruslan): A, keep Apache-2.0.
- Consequences: `pyproject.toml` declares Apache-2.0. Third-party licenses go to DATA_SOURCES.md.
- Sources: LICENSE

## ADR-004: Environment manager
- Date/time: 2026-11-14 11:00 (UTC+5)
- Stage: 0
- Context: Python 3.14 and 3.12 installed; pip present; uv and conda absent.
- Options: A) venv + pip B) uv C) conda.
- Claude's recommendation: A - nothing to install; requirements.txt is read directly by the hosting.
- Decision (Ruslan): A, venv + pip.
- Consequences: `requirements.txt` + `.venv`. Python 3.12 chosen by Claude (technical, see WORKLOG).
- Sources: -

## ADR-005: Prior material
- Date/time: 2026-11-14 11:10 (UTC+5)
- Stage: 0
- Context: Whether Ruslan has drafts that may be used as reference.
- Options: A) start from scratch B) use Ruslan's material.
- Claude's recommendation: none (Ruslan's call).
- Decision (Ruslan): B - read the training files, most important in the folder `NASA PSI data`; Ruslan will also send the formulas he thinks should be used.
- Consequences: `NASA PSI data/` (25 PSI ISA-Tab metadata archives + SAME EIRD PDF) is the starting inventory for stage 2. Formulas from Ruslan go to PHYSICS.md with sources checked.
- Sources: NASA PSI data/ (see RESEARCH_LOG.md, 2026-11-14)

## ADR-006: Commit the PSI metadata to git
- Date/time: 2026-11-14 11:27 (UTC+5)
- Stage: 1 (start)
- Context: `NASA PSI data/` (25 ISA-Tab zips + SAME EIRD PDF, 5.5 MB, public NASA material) was untracked; CLAUDE.md leaves committing raw data to Ruslan.
- Options: A) move to `data/raw/psi_metadata/` and commit B) keep out of git.
- Claude's recommendation: A - small, public, makes the pipeline reproducible from the repo.
- Decision (Ruslan): "Yes, move the folder and commit; the data is open anyway."
- Consequences: Folder renamed to `data/raw/psi_metadata/` (older log entries keep the old name as history); sha256 of every file in `data/catalog.yaml`.
- Sources: data/catalog.yaml

## ADR-007: Project scope
- Date/time: 2026-11-14 11:31 (UTC+5)
- Stage: 1
- Context: ~15 h total budget; the challenge asks to summarize, rank and interpret investigations; quantitative data availability is unconfirmed until stage 2.
- Options: A) droplets only, maximum depth B) droplets + solids, two models C) catalog of all PSI combustion investigations + one deep model.
- Claude's recommendation: C - summarize/rank/compare is the literal objective, metadata is already parsed, depth stays on one dataset.
- Decision (Ruslan): C.
- Consequences: Two tracks: catalog/ranking from ISA metadata (all studies) and one hybrid model (default FLEX droplets, final pick after stage 2).
- Sources: docs/00_PROJECT_BRIEF.md; docs/RESEARCH_LOG.md 2026-11-14 11:29

## ADR-008: Personas
- Date/time: 2026-11-14 11:31 (UTC+5)
- Stage: 1
- Context: Who the dashboard serves determines pages and insight wording.
- Options: P1 cabin materials engineer; P2 crew-safety specialist / mission planner; P3 combustion researcher / graduate student; subsets.
- Claude's recommendation: all three - P3 is the audience named by the challenge, P1/P2 carry the Moon-base scenario and Impact.
- Decision (Ruslan): all three.
- Consequences: UI_SPEC pages map to P1-P3 tasks (stage 8).
- Sources: docs/00_PROJECT_BRIEF.md

## ADR-009: Product questions
- Date/time: 2026-11-14 11:31 (UTC+5)
- Stage: 1
- Context: Eight candidate questions (Q1-Q8) with different data outlooks.
- Options: A) Q1, Q2, Q3, Q5, Q8 B) Q1, Q4, Q5, Q8 (solids) C) all eight.
- Claude's recommendation: A - fits scope C with a droplet model; Q4/Q6/Q7 go to stretch.
- Decision (Ruslan): A.
- Consequences: Model targets serve Q2/Q3 (extinction / suppression); Q5 needs a tested-range envelope; Q4, Q6, Q7 deferred (stretch S1-S3).
- Sources: docs/00_PROJECT_BRIEF.md

## ADR-010: MVP definition
- Date/time: 2026-11-14 11:32 (UTC+5)
- Stage: 1
- Context: What must work by Sat 22:30 (end of stage 8).
- Options: A) M1-M6 B) without M4 (Moon-base scenario) C) M1-M6 + S5 comparison matrix.
- Claude's recommendation: A.
- Decision (Ruslan): A; "if time remains, we do the extended one" -> S5 is the first stretch item.
- Consequences: MVP = catalog, ranking, one hybrid model, Moon-base scenario, insights page, one-command local run. Stretch order: S5 first, then Claude's proposed order S1, S2, S3, S6, S4.
- Sources: docs/00_PROJECT_BRIEF.md

## ADR-011: Project name and tagline
- Date/time: 2026-11-14 11:31 (UTC+5)
- Stage: 1
- Context: Name for the submission form and UI.
- Options: A) Prometheus-0g B) Flame in Freefall Explorer C) ZeroG FireAtlas D) FlameScope μg.
- Claude's recommendation: A - matches the repository name, memorable.
- Decision (Ruslan): A.
- Consequences: Name "Prometheus-0g"; tagline "Physics-first, AI-assisted fire-safety insights from NASA microgravity combustion experiments." Used in README, app title, SUBMISSION.md.
- Sources: -

## ADR-012: Model datasets
- Date/time: 2026-11-14 11:48 (UTC+5)
- Stage: 2
- Context: Of 24 PSI Combustion Science investigations, only FLEX (274 tests) and CFI-G (333 tests) have Experimental Tables with numeric outcomes and enough tests; BASS-II has partial outcomes (O2/CO/CO2 changes) and no spread rates.
- Options: A) FLEX primary + CFI-G auxiliary B) FLEX only C) FLEX + CFI-G + BASS-II.
- Claude's recommendation: A - FLEX answers Q2/Q3/Q5 with outcomes and d2-law theory; CFI-G adds tested O2 up to 0.85 for Q5 as an ignition/self-extinction map without a separate ML model.
- Decision (Ruslan): "For now FLEX + CFI-G; if time remains we add BASS-II."
- Consequences: Stage 3 parses PSI-69 and PSI-159 to model-ready tables; BASS-II becomes a stretch item after S5. Model = FLEX; CFI-G = data map with Tad/Zst from the table.
- Sources: docs/DATA_SOURCES.md sections 2 and 4; docs/RESEARCH_LOG.md 2026-11-14 stage 2

## ADR-013: Datasets without numeric outcomes
- Date/time: 2026-11-14 11:48 (UTC+5)
- Stage: 2
- Context: SPICE, ACME Flame Design, CFI, FLEX-2, SAME/SAME-R, Saffire I-III, SLICE, DAFT and others hold test conditions but no usable outcomes.
- Options: A) catalog/overview only B) drop.
- Claude's recommendation: A - the challenge asks to display fuels, O2, airflow and within-investigation variables (CH-10).
- Decision (Ruslan): A.
- Consequences: Their Experimental Tables feed the M1 catalog (condition ranges, number of tests); never model inputs.
- Sources: docs/DATA_SOURCES.md section 2

## ADR-014: Who downloads PSI files
- Date/time: 2026-11-14 11:48 (UTC+5)
- Stage: 2
- Context: CLAUDE.md section 3.1 assumed Ruslan downloads PSI files manually. The files turned out to be open (CC0-1.0, no login) through the public web service the PSI page uses.
- Options: A) Claude downloads via the API with a reproducible script B) Ruslan downloads manually.
- Claude's recommendation: A - reproducible, checksummed, no manual work.
- Decision (Ruslan): A.
- Consequences: `scripts/fetch_psi.py` writes `data/raw/psi_records/*.json.gz` (raw responses, gzip only) and `data/raw/psi_tables/*.csv` + `MANIFEST.tsv`; sha256 in `data/catalog.yaml`. Changes the CLAUDE.md 3.1 assumption for open PSI files only; login-protected files would still go through Ruslan.
- Sources: scripts/fetch_psi.py

## ADR-015: Handling of data anomalies (FLEX, CFI-G)
- Date/time: 2026-11-14 12:10 (UTC+5)
- Stage: 3
- Context: FLEX anomalies all appear identically in NASA/TP-2015-216046 Table IX, so no second source can correct them: test 114 pressure 0; 6 tests mole-fraction sum 0.98; 8 tests extinction diameter 0; test 129 d_ext 3.34 > d0 3.33; burn times "~6", "~9"; identifier 193F001 used twice; burning-rate header unit "mm" (TP: mm^2/s). CFI-G: #DIV/0! / #VALUE! in 4 cells (Tad, Zst, peak T), "Yes"/"yes" case variants.
- Options: A) default package B) exclude every flagged row from modeling C) keep everything incl. P = 0.
- Claude's recommendation: A.
- Decision (Ruslan): A, "default package".
- Consequences: test 114 `use_in_model = False` (kept in catalog); other anomalies kept with flags, no renormalisation; d_ext = 0 -> d_ext target missing; K unit mm^2/s per TP App. A.1; spreadsheet errors -> NaN; case normalised, originals kept. Implemented in `src/fif/data/clean.py`; list in DATA_QUALITY.md.
- Sources: NASA/TP-2015-216046 Table IX and App. A.1; data/processed/quality_flags.tsv

## ADR-016: Cross-validation groups (FLEX)
- Date/time: 2026-11-14 12:10 (UTC+5)
- Stage: 3
- Context: repeats of one test regime must never be split between train and test.
- Options: A) regime = fuel x pressure (50 mmHg) x O2/CO2/He (0.01), 81 groups B) test day, 80 groups C) union of regime and day.
- Claude's recommendation: A - tests prediction for a new atmosphere, which is what Q5 needs.
- Decision (Ruslan): A.
- Consequences: column `cv_group` (81 groups, 11 singletons, max 17 tests); used by GroupKFold in stage 6.
- Sources: src/fif/data/clean.py `regime_group`

## ADR-017: Targets
- Date/time: 2026-11-14 12:10 (UTC+5)
- Stage: 3
- Context: which measured outcomes the models predict / the dashboard maps.
- Options (multi): FLEX burning-rate constant K; FLEX extinction yes/no; FLEX d_ext/d0; CFI-G ignition and self-extinction.
- Claude's recommendation: K, extinction yes/no, CFI-G ignition/self-extinction; d_ext/d0 optional.
- Decision (Ruslan): all four ("FLEX: K, extinction yes/no, d_ext/d0, CFI-G ignition and SE, all").
- Consequences: targets `K_m2_s`, `extinct_finite_d`, `d_ext_over_d0` (FLEX) and `ignited`, `self_extinguished` (CFI-G, data map only per ADR-012). Post-ignition columns listed in `src/fif/data/features.py` and never used as features.
- Sources: docs/DATA_DICTIONARY.md

## ADR-018: Definition of the FLEX extinction class
- Date/time: 2026-11-14 12:10 (UTC+5)
- Stage: 3
- Context: `Test end` disagrees with the extinction diameter in 35 tests and is not defined in the TP; the TP defines the en dash in the diameter column as "flame extinction did not occur" (burned to completion or ended by disruption).
- Options: A) from the diameter: 1 = d_ext > 0, 0 = en dash or 0, NA = blank B) from Test end, Disruption excluded C) from Test end, Disruption = no extinction.
- Claude's recommendation: A.
- Decision (Ruslan): A first; "if time remains, all the others" (B and C as sensitivity checks in validation).
- Consequences: `extinct_finite_d` = 189 / 36 / 49 NA. Caveat found after the decision (DATA_QUALITY.md section 3): all 49 CSV blanks are printed as en dashes in the TP, where the dash also covers "not listed"; open question to Ruslan.
- Sources: NASA/TP-2015-216046 App. A.1; docs/DATA_QUALITY.md

## ADR-019: Duplicate identifier 193F001 and K-burn-time consistency
- Date/time: 2026-11-14 12:27 (UTC+5)
- Stage: 4 (data follow-up)
- Context: CSV tests 70 and 73 carry the same identifier, date and GMT. TP Table IV (test matrix) and Figs. 74 and 77 show two different tests on 3/23/10, both with an unintended very large droplet that hit the igniter and left the field of view; the shared timestamp is likely a table copy error.
- Options: A) keep both B) keep one, chosen by evidence C) drop both.
- Claude's recommendation: B. Check of the d2-law record: K x t_burn / (d0^2 - d_ext^2) has median 1.05 and 90 % of 188 tests within 0.95-1.25; test 70 gives 1.01, test 73 gives 1.52 (above the 97th percentile).
- Decision (Ruslan): "check the results, interpret them and choose the most truthful" (delegated).
- Consequences: test 73 `use_in_model = False` (flag DUP_ID_LESS_CONSISTENT); test 70 kept. New general flag KTB_INCONSISTENT for ratio outside 0.8-1.5 (11 rows, kept, no exclusion).
- Sources: NASA/TP-2015-216046 Table IV, Table IX p. 22, Figs. 74 and 77 (pp. 97, 100)

## ADR-020: Add the two TP-only FLEX tests
- Date/time: 2026-11-14 12:27 (UTC+5)
- Stage: 4 (data follow-up)
- Context: FLEX-216 (N03H201) and FLEX-230 (H01H103) are in TP Table IX but not in the PSI CSV.
- Options: A) add from the TP B) leave out.
- Claude's recommendation: A, with a flag.
- Decision (Ruslan): "Yes".
- Consequences: `data/raw/ntrs/flex_tp_supplement.csv` (transcribed from TP p. 26, verified cell by cell against the pdfplumber parse), source_id NTRS-20150023456, flag FROM_TP_SUPPLEMENT, `test_no` empty, `tp_test_no` 216 / 230. FLEX now 276 rows, 274 used for modeling.
- Sources: NASA/TP-2015-216046 Table IX p. 26

## ADR-021: Extinction class kept as in ADR-018 for now
- Date/time: 2026-11-14 12:27 (UTC+5)
- Stage: 4
- Context: open question 3 of DATA_QUALITY.md (blank vs dash).
- Decision (Ruslan): "Keep it for now, we will see later."
- Consequences: no change; revisit in validation (stage 6) with the ADR-018 sensitivity variants.
- Sources: docs/DATA_QUALITY.md section 5

## ADR-022: Theory level for droplets (FLEX) and CFI-G
- Date/time: 2026-11-14 ~12:35 (UTC+5; answer received between the 12:27 and 12:36 clock readings)
- Stage: 4
- Context: three levels proposed: L1 classical quasi-steady (NASA's comparison, NTRS 20130014061 Eqs. 1-2); L2 = L1 + T_b(P) + diluent-specific mixture properties + Burke-Schumann T_f; L3 = L2 + extinction proxies.
- Options: A) L2 + simple L3 B) L1 only C) L1 + L2 without L3.
- Claude's recommendation: A.
- Decision (Ruslan): A; "maybe add L1 later if it is needed and time remains". CFI-G: no own flame model, Tad/Zst from the NASA table.
- Consequences: `fif.physics.droplet.evaluate` implements L2 + proxies (flame standoff, chi_rad/kappa, r_f^2/alpha); no Damköhler number (A, E_a not sourced).
- Sources: NTRS 20130014061; docs/FORMULAS.md sections 2-3

## ADR-023: Gas-property evaluation
- Date/time: 2026-11-14 ~12:35 (UTC+5; answer received between the 12:27 and 12:36 clock readings)
- Stage: 4
- Context: NASA used the Law & Williams (1972) recipe, not accessible to Claude. NIST data exist for O2/N2/CO2/He at 300-1500 K, not for fuel vapour at flame temperatures.
- Options: A) ambient-mixture properties at T_bar = (T_b+T_f)/2, capped 1500 K, NASA RP-1311 mixing rules B) same with the 1/3 rule C) obtain the Law & Williams paper.
- Claude's recommendation: A.
- Decision (Ruslan): A, and "give me the DOI and say what exactly you need, I will try to find it".
- Consequences: implemented A (assumptions A2-A5 in PHYSICS.md). Request to Ruslan: Law & Williams, Combustion and Flame 19 (1972) 393-405, DOI 10.1016/0010-2180(72)90009-0 - the part where the property values (lambda, cp, reference temperature, which species) for the burning-rate calculation are defined. If obtained, the recipe can replace A (hypothesis H1).
- Sources: NASA RP-1311 Eqs. 5.3-5.6; NIST SRD 69

## ADR-024: Gravity baseline
- Date/time: 2026-11-14 ~12:35 (UTC+5; answer received between the 12:27 and 12:36 clock readings)
- Stage: 4
- Decision (Ruslan): base = microgravity (recommended). Earth = theory x Nu/2 (FORMULAS.md section 6), shown as `physics theory`, never as data.
- Consequences: columns Gr, Pr, Nu_earth, K_earth_theory.
- Sources: docs/FORMULAS.md section 6

## ADR-025: Physics features for ML
- Date/time: 2026-11-14 ~12:35 (UTC+5; answer received between the 12:27 and 12:36 clock readings)
- Stage: 4
- Options: A) compact set B) everything computed C) ln K_theory only.
- Decision (Ruslan): A (recommended).
- Consequences: features ln K_theory, B, T_f, Y_O2 (mass), alpha_g = lambda/(rho cp); for extinction also d0 and chi_rad proxy; plus the raw pre-ignition conditions. Listed in `fif.data.features` / stage 5.
- Sources: docs/PHYSICS.md

## ADR-026: Inner-region heat capacity C_1 in the burning-rate formula (correction of stage 4)
- Date/time: 2026-11-14 12:52 (UTC+5)
- Stage: 4 (rework requested by Ruslan before stage 5)
- Context: the first stage-4 version used the cp of the ambient gas in K and B and over-predicted FLEX K by 2x (methanol) and 4x (heptane). Ruslan supplied the paragraph after L&W (1972) Eq. (1): K uses lambda_1 / C_1 of the gas region inside the flame; elementary assumptions lambda_1 = lambda_2, c_1 = c_2; q = heat of combustion per unit mass at T_inf. Ruslan also pointed to HHV vs LHV.
- Options: A) C_1 = fuel-vapour cp (NIST ideal-gas tables) at T_bar, lambda_1 = ambient-mixture lambda B) keep ambient cp C) C_1 from a full inner-region mixture (needs product composition and fuel-vapour conductivity, not in NIST).
- Claude's recommendation: A - follows the L&W definition with sourced data; C would need data we do not have.
- Decision (Ruslan): "fix it and make everything correct before stage 5" - implemented A; Q stays the LHV (19.90 / 44.56 MJ/kg), HHV 22.65 / 48.07 MJ/kg shown in PHYSICS.md section 6 - Ruslan to confirm LHV vs HHV.
- Consequences: median K_meas/K_theory 0.52 -> 1.36 (methanol), 0.24 -> 0.89 (heptane). Old version kept as K_theory_ambient_cp. New raw files data/raw/nist/thermo_gas_C67561.html, thermo_gas_C142825.html. Tag stage-4.1 (stage-4 left unchanged).
- Sources: Law & Williams, Combust. Flame 19 (1972) 393-405, Eq. (1) and following paragraph; NIST SRD 69 gas-phase cp (TRC 1997; Scott 1974)

## ADR-027: Law & Williams (1972) property prescription for the burning-rate constant
- Date/time: 2026-11-14 13:07 (UTC+5)
- Stage: 4 (rework requested by Ruslan: "find out why it is computed so crudely and find something proper but applicable"; "honest physics without deviations")
- Context: ADR-026 (c_1 = fuel vapour, lambda = ambient) left methanol at 1.36 and heptane at 0.89 with a strong He effect. Ruslan supplied the full L&W paper. NASA (NTRS 20205008449) states that the constant-property QS theory needs an empirical property prescription and that it follows L&W.
- Options: A) L&W prescription as written (c_1 fuel vapour; lambda_1 = 0.4 lambda_F1 + 0.6 lambda_air; at T_1 = (T_b+T_f)/2; T_f equilibrium with dissociation) B) variable-property integration with Chapman-Enskog properties (no fitted constant, ~1.5 h, not done) C) keep ADR-026 + calibration.
- Claude's recommendation: A.
- Decision (Ruslan): A ("in general the recommendation ... I am for honest physics without deviations").
- Consequences: new physics/flame.py (Cantera HP equilibrium, NASA Glenn thermo); lambda_F1 from NASA TR R-132 (methanol table; heptane via Svehla Eq. 2 with C5/C6 -> C7 viscosity extrapolation, as L&W did for hexadecane); L&W buoyancy correction f_B = 0.533 Gr^0.52 replaces the Nu-based estimate (outside its fitted range for 256 of 274 FLEX rows, flagged). Result: median K_meas/K_theory 0.97 (methanol, 74 % within 15 %), 0.73 (heptane); residual trend with d0 for both fuels. Deviations from L&W stated as assumptions A8 (actual ambient mixture instead of air), A9 (heptane lambda_F1), A10 (Earth correction range). q = LHV still to be confirmed by Ruslan. Tag stage-4.2.
- Sources: L&W 1972 pp. 394-396, 399, 403-404; NASA TR R-132; NASA TM-4513; NTRS 20205008449; NIST SRD 69

## ADR-028: Heat of combustion q in B = lower heating value
- Date/time: 2026-11-14 13:11 (UTC+5)
- Stage: 4
- Context: L&W (p. 395) take q "from thermochemical tables" without saying higher or lower heating value; their ref. [23] is Rossini et al., NBS Circular C461 (1947). Our NIST values come from the same Rossini measurements (heptane page cites Prosen and Rossini 1945; methanol value is Chao and Rossini 1965).
- Options: A) LHV (water vapour in the flame) B) HHV.
- Sensitivity (FLEX, 274 rows): HHV raises K_theory by 7.8 % (methanol) and 3.4 % (heptane); median K_meas/K_theory methanol 0.974 -> 0.905, heptane 0.733 -> 0.710; share within 15 % methanol 74 % -> 69 %.
- Claude's recommendation: A.
- Decision (Ruslan): "In general yes, but taking the higher one would also be fine" -> A (LHV) kept; HHV variant documented as a sensitivity check.
- Consequences: no code change; PHYSICS.md section 3 updated.
- Sources: L&W 1972 p. 395 and ref. 23; NIST SRD 69 species pages

## ADR-029: Final targets and model choices (stage 5)
- Date/time: 2026-11-14 ~13:16 (UTC+5)
- Stage: 5
- Context: architecture proposed: level 1 physics (L&W K, ADR-027), level 2 calibration c_f per fuel = exp(mean ln(K_meas/K_theory)), level 3 ML residual r = ln(K_meas/(c_f K_theory)); classification of finite-diameter extinction on physics features.
- Decisions (Ruslan):
  - Targets: all three - K (hybrid), extinction yes/no (classifier), d_ext/d0 (regression; no physics baseline exists for it).
  - Residual model: Gaussian process (recommended).
  - Classifier: "both, compare" - logistic regression and gradient boosting on the same grouped CV.
  - Monotonic constraints: "not sure which is better... try both and see" - boosting is run with and without constraints (proposed directions: P(extinction) decreasing in O2 and T_f, increasing in CO2 fraction; none for d0, pressure, He); logistic coefficient signs are checked against the same directions.
  - Metrics: full set (recommended) - K and d_ext/d0: RMSE in log space (primary), MAE in original units, R^2, 95 % interval coverage; extinction: AUC (primary), Brier, accuracy, balanced accuracy.
- Consequences: src/fif/models/, scripts/train_models.py, MODEL_CARD.md.
- Sources: docs/FORMULAS.md section 8 (calibration and residual formulas)

## ADR-030: Stage-6 variant selection by pre-declared rules
- Date/time: 2026-11-14 ~13:45 (UTC+5; rules written into src/fif/validation/variants.py before the run)
- Stage: 6
- Context: Ruslan asked to "check everything and choose the best result" for (1) the suspect test C13H201 (K = 0.05 mm2/s, OUTLIER_K + KTB_INCONSISTENT), and to "test everything" for (2) the non-monotonic O2 response.
- Rules: (1) lowest mean RMSE_log of the hybrid on the same trusted rows (no KTB_INCONSISTENT / OUTLIER_K), 3 seeds; (2) residual feature set: lowest RMSE_log among sets with worst K drop along O2 <= 2 % per 0.01 step; (3) interface extinction model: highest AUC among models with no rise of P(extinction) along O2.
- Result: (1) drop C13H201 from K training only (hybrid 0.128 vs 0.158 keep-all on trusted rows); with it excluded, K became monotone in O2 in all cases - the outlier caused the dips. (2) residual GP on raw conditions (`K_resid_raw`), differences between sets within one sd. (3) hybrid logistic (AUC 0.787; boosting variants rise up to +0.54 / +0.39 along O2).
- Decision (Ruslan): delegated ("check everything and choose the best", "test everything"); choices made by the rules above.
- Consequences: fif.models.features: HYBRID_K_FEATURES, K_TRAIN_EXCLUDE, EXTINCTION_UI_MODEL, k_train_mask; models retrained; numbers in docs/VALIDATION.md (generated).
- Sources: docs/validation_results.json

## ADR-031: Extrapolation tests in the interface and reliability thresholds
- Date/time: 2026-11-14 ~13:44 (UTC+5)
- Stage: 6
- Decisions (Ruslan): show all extrapolation tests (atmosphere He / CO2 / O2 >= 0.30, ~0.7 atm, fuel transfer as an honest failure, low O2 and p > 1.2 atm); label "extrapolation" when a condition is outside the tested range, "unreliable" when sigma ln K > 0.20 (recommended option).
- Implementation note (Claude): a per-variable range check misses the Moon-base corner (0.694 atm is tested, but not at O2 0.30). The rule therefore also checks the O2-pressure combination for the same fuel and diluent (O2 window +-0.02) against the data. Reported here for Ruslan's review.
- Consequences: src/fif/validation/reliability.py; tests/test_validation.py.

## ADR-032: Presentation when the hybrid equals pure ML in ordinary CV
- Date/time: 2026-11-14 ~14:01 (UTC+5)
- Stage: 6
- Context: with C13H201 excluded, grouped CV gives hybrid 0.171 +- 0.002 vs pure ML 0.174 +- 0.003 (RMSE ln K); on held-out atmospheres the hybrid is 1.2-1.9x better (He, CO2, ~0.7 atm, O2 >= 0.30); on a held-out fuel no model transfers reliably.
- Options: A) honest, with the extrapolation argument B) numbers only.
- Decision (Ruslan): A.
- Correction: Claude's question stated "on a new fuel pure physics is better"; the final table shows physics and pure ML equal for methanol and all models poor for heptane. VALIDATION.md states the corrected version.
- Consequences: README / interface text: "equal inside tested conditions; physics makes the model hold for new atmospheres (the Moon-base case); not for new fuels".
