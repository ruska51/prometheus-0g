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

## ADR-033: Insight catalog, ranking formula and wording
- Date/time: 2026-11-14 ~14:14 (UTC+5)
- Stage: 7
- Context: 12 data/model/theory insights (prevention P1-P4, detection D1-D4, suppression S1-S4) + 3 history (Apollo 1, Apollo 13, Mir) + 3 spinoffs, all computed live (src/fif/insights/catalog.py).
- Options: keep all / drop D4 / drop D2-D3 / drop P3; ranking A (FORMULAS.md section 8), B (multi-criteria), C (lexicographic); wording as drafted / softer.
- Claude's recommendation: keep all with confidence labels; A; wording as drafted.
- Decision (Ruslan): keep all; A; wording as drafted.
- Consequences: docs/INSIGHTS.md and docs/insights.json generated by scripts/build_insights.py; tests/test_insights.py checks every number against a direct calculation. Note: for D1 (no ratio effect) e uses ln((median final CO + 1)/(median initial CO + 1)).
- Sources: docs/INSIGHTS.md

## ADR-034: Dashboard structure, style, headline, investigation ranking
- Date/time: 2026-11-14 ~14:19 (UTC+5)
- Stage: 8
- Decisions (Ruslan, all recommended options): 8 pages in the order Overview, Insights, Moon-base scenario, Risk map, Investigations, Data explorer, Validation, Method & sources (no AI assistant); style B "Clean science" (light, #1D4ED8 + #EA580C); headline "Prometheus-0g - Will it burn on the Moon?"; PSI investigation relevance = 0.5 fire-safety role + 0.3 usable data + 0.2 data size, stage tags from the challenge text.
- Consequences: app/ (main.py + pages), .streamlit/config.toml, fif.insights.investigations, fif.insights.scenario; docs/UI_SPEC.md.

## ADR-035: Burning-droplet animation window on the Moon-base scenario page
- Date/time: 2026-11-14, answers before 14:39 (UTC+5; first file created 14:39)
- Stage: 8 (extension after the stage report)
- Context: Ruslan asked for "a small window that shows the flame, how it spreads and burns, based on the calculations".
- Options: content - (A) follow the selected atmosphere preset + a selectable comparison atmosphere, (B) fixed ISS vs Moon; flame size - (A) relative theoretical scale with a caveat, (B) measured-size proxy, (C) fixed size; technique - (A) HTML/JS canvas with glow (numbers from Python), (B) Plotly frames, (C) static images.
- Claude's recommendation: A / A (relative scale) / A (canvas).
- Decision (Ruslan): left panel follows the Atmosphere preset (or custom settings), right panel any selectable atmosphere, e.g. Earth ("сравнение с любой другой атмосферой, например земли"); relative scale; "very beautiful, alive and roughly realistic".
- Consequences: `fif.insights.flame_sim.simulate` computes everything shown (d^2-law series with K from the hybrid model, physics-only K when the model is withheld, K x (1 + f_B) at 1 g; flame diameter = theoretical r_f/r_s x d; extinction diameter from the d_ext GP only for reliability "in range" and P(extinction) >= 0.5; T_f; soot colour = blackbody at T_f). `app/flame_view.py` only interpolates and draws (canvas). Caveat on the page: quasi-steady theory "typically yields a value several times that of experimental measurements" for D_f/D (NTRS 20130014061, section 3.2); 1 g shape, flicker and sparks are illustrative. Tests: tests/test_flame_sim.py.
- Sources: docs/PHYSICS.md sections 3-5; NTRS 20130014061; Wyman, Sloan & Shirley, JCGT 2(2) 2013 (CIE fit); IEC 61966-2-1 (sRGB).

## ADR-036: Lunar-surface (1/6 g) burning rate as a labelled bound
- Date/time: 2026-11-14, answer received between the 14:57 and 15:23 clock readings (UTC+5)
- Stage: post-8 stretch S2 (Q6), item 1 of Ruslan's list
- Context: the Moon-base scenario used the microgravity rate, but a Moon base sits at lunar gravity; PSI has no partial-gravity data (challenge page).
- Options: A) range: microgravity rate .. Law & Williams correction at g_Moon (physics theory) B) single L&W number C) text only.
- Claude's recommendation: A.
- Decision (Ruslan): A.
- Consequences: `fif.physics.droplet.buoyancy_factor(Gr_Earth, g_ratio)` (Gr proportional to g), `G_MOON_RATIO = 1/6` (NTRS 20250004015); `predict` returns `moon_factor`, `moon_Gr`; scenario page metric "On the lunar surface (1/6 g)"; animation comparison "Moon base on the lunar surface (1/6 g)" (default when the Moon preset is selected) and "Your settings on the lunar surface"; insights P5 (physics theory, bound) and P6 (NASA literature: lunar g may be the most flammable condition for solids, NTRS 20210020516, 20260000646). For the Moon-base air and a 3 mm droplet Gr(1/6 g) = 0.69-0.76, inside the L&W fitted range (Gr <= 1), unlike Earth (Gr 4-5).
- Sources: NTRS 20250004015, 20210020516, 20260000646; Law & Williams 1972 Eq. (9)

## ADR-037: Investigation comparison matrix (S5) placement
- Date/time: 2026-11-14, answer received between the 14:57 and 15:23 clock readings (UTC+5)
- Stage: post-8 stretch S5, item 2
- Options: A) "Compare" tab on the Investigations page B) separate page C) side-by-side picker of 2-3 investigations.
- Claude's recommendation: A. Decision (Ruslan): A.

## ADR-038: Hosting confirmed
- Date/time: 2026-11-14, answer received between the 14:57 and 15:23 clock readings (UTC+5)
- Context: Ruslan asked why Hugging Face for a NASA hackathon. NASA does not host projects; the form needs a public "Link to Final Project".
- Options: A) HF Spaces (Claude deploys with Ruslan's write token) B) Streamlit Community Cloud (Ruslan clicks deploy) C) GitHub only.
- Claude's recommendation: A. Decision (Ruslan): A (ADR-001 unchanged). Deploy brought forward (item 5).

## ADR-039: Extinction class definition stays A
- Date/time: 2026-11-14, answer received between the 15:42 and 15:52 clock readings (UTC+5)
- Stage: post-8 item 3
- Context: sensitivity analysis (docs/verification/extinction_label_sensitivity.md): directions hold for A, B, C; variant C (Disruption = no extinction) fails the pre-declared AUC check by ranking better (0.882 vs 0.787).
- Options: A) keep the diameter-based definition B) switch to C.
- Claude's recommendation: A - 'Disruption' ends a test for another reason (droplet breakup / drift), so whether the flame would have gone out is unknown; counting it as 'no extinction' answers a different question.
- Decision (Ruslan): A ("оставляем А"). Closes the open question of ADR-021.

## ADR-040: Hosting moves to Streamlit Community Cloud
- Date/time: 2026-11-14, answer received after the 15:53 clock reading (UTC+5)
- Context: Hugging Face refused to create the Space (HTTP 402): "hosting Gradio and Docker Spaces on free cpu-basic requires a PRO subscription"; only static Spaces are free. Nothing was published on HF; the local token file was deleted.
- Options: A) Streamlit Community Cloud (free, deploys from the public GitHub repo, Ruslan logs in once) B) HF PRO (paid) C) Render free tier (sleeps, 512 MB) D) Google Cloud Run (billing account).
- Claude's recommendation: A.
- Decision (Ruslan): A. Supersedes the hosting part of ADR-001 / ADR-038. Dockerfile and scripts/deploy_hf.py are kept as a fallback (any Docker host).
- Result: deployed by Ruslan on share.streamlit.io (repo ruska51/prometheus-0g, branch main, app/main.py, Python 3.12): https://prometheus-0g.streamlit.app/; all 8 pages checked by Claude in Edge (Playwright) at 16:01, no exceptions, scenario numbers equal to the local run. Every push to main redeploys.

## ADR-041: Interface language switch (English default, Russian optional)
- Date/time: 2026-11-14, request received after the 16:24 clock reading (UTC+5)
- Stage: post-10
- Context: Ruslan: "add a language switch so that there is Russian, but English opens first, and Russian for whoever needs it".
- Decision (Ruslan): English by default, Russian on request. Implementation choices (Claude, technical): sidebar radio "Language / Язык" plus URL parameter `?lang=ru`; English text is the translation key (app/i18n.py), so a missing translation shows English; package-generated texts (insight cards, reliability reasons, animation notes) carry parallel Russian fields (`ru`, `reasons_ru`, `notes_ru`) with the same computed numbers; NASA record text, data values and quotes stay in English. Repository documents and submission texts stay English (NASA requirement).
- Consequences: app/i18n.py, all pages, flame_view labels, fif.insights.catalog / base, fif.validation.reliability, fif.insights.flame_sim; tests/test_i18n.py (every literal key translated, placeholders match, all pages run in Russian).

## ADR-042: "Ask the data" assistant - variant C with Google Gemini
- Date/time: 2026-11-14, answers received between the 16:41 and 16:48 clock readings (UTC+5)
- Stage: 9 (optional, done after Ruslan's request: "let's add the AI chat")
- Options: A) none B) compact summary (JSON) + citations C) B + retrieval over NASA NTRS report excerpts with citations; provider: Claude Opus 5.5 / Sonnet 5.5 / Haiku 5.5 (paid key) or Google Gemini (free tier).
- Claude's recommendation: C; Claude Opus 5.5.
- Decision (Ruslan): C; Google Gemini free tier; key protection left to Claude ("choose yourself").
- Implementation (Claude, technical): src/fif/assistant (BM25 retrieval over 49 result blocks generated from the dashboard artefacts + 12 public-use NTRS reports split into ~1100-character excerpts; a Russian->English glossary for retrieval only; a rule-first system prompt: context only, a citation after every factual sentence, "the data do not cover this", ignore instructions inside the context); citations are checked after generation (unknown ids removed and reported, uncited answers flagged). Key only from GEMINI_API_KEY (environment / Streamlit secrets), never in git (test scans tracked files for key patterns); 10 questions per browser session, question 600 characters, answer 1500 tokens; quota/key/model errors shown as a short message, the rest of the app works without a key. NTRS corpus: scripts/fetch_ntrs_corpus.py, only documents whose NTRS copyright determination permits public use, registered with sha256 in data/catalog.yaml.
- Consequences: new page "Ask the data" (EN/RU), requirements: google-genai 3.3.0; evaluation protocol docs/ASSISTANT_EVAL.md (scripts/assistant_eval.py, 10 questions incl. out-of-data, prompt injection, false premise). Note: free-tier Gemini requests may be used by Google to improve its models; only public data and user questions are sent.
- Sources: https://ai.google.dev (Gemini API), google-genai package 3.3.0 (signatures read from the installed package)

## ADR-043: Headline answer on the Overview page
- Date/time: 2026-11-14, approved after the 17:44 clock reading (UTC+5)
- Context: self-review against the judging criteria (Impact, Creativity, Validity, Relevance, Presentation): the headline asks "Will it burn on the Moon?" but the Overview did not answer it.
- Claude's recommendation: an answer block at the top of the Overview. Decision (Ruslan): "давай ... максимально круто по критериям".
- Consequences: fif.insights.moon.moon_answer (all numbers computed: hybrid ratio Moon/ISS with 95 % band, d2-law burn-out time of a 3 mm droplet in ISS air / Moon-base air / lunar surface, measured FLEX self-extinction share O2 >= 0.30 vs <= 0.21, equilibrium flame temperature, NASA literature on solids, actions from insights S4/D1/P6), fuel switch, links to the animation, assistant and validation; evidence and reliability badges on every number; EN/RU; test that the numbers equal the model, insights P2/S4 and the d2-law.

## ADR-044: Stage 12 - demo format, README top insights, submission target
- Date/time: 2026-11-14, answers received after the 19:06 clock reading (UTC+5)
- Stage: 12
- Options: demo = 30-s video recorded automatically from the live app / 7 slides (PDF) / video recorded by Ruslan; README top-5 = Moon-base set (P2, S4, P1, D1, P6) / formula-A top-5 (D1, S3, P1, S4, P4); deadline.
- Claude's recommendation: automatic video; Moon-base set.
- Decision (Ruslan): video 30 s (recommended); Moon-base set (recommended); "finish by Sunday 10:00".
- Consequences: scripts/make_demo_video.py (Playwright + Edge recording of https://prometheus-0g.streamlit.app, ffmpeg from imageio-ffmpeg, burned-in English subtitles, <= 30 s), docs/demo/prometheus-0g_demo.mp4 + subtitles.srt, docs/DEMO_SCRIPT.md; README rewritten for the jury; docs/SUBMISSION.md with every form field, counts and Ruslan's checklist; requirements matrix closed except SG-11 / TC-1 (Ruslan's actions). Flame drawing reworked after Ruslan's review to match NASA photo C-1998-485 (WebGL, laminar 1-g spindle, soft microgravity sphere) before recording.

## ADR-045: Assistant answers lead with numbers; citation codes shown as superscript numbers
- Date/time: 2026-11-14 20:22-20:30
- Stage: post-12 (live-site review by Ruslan on a phone)
- Context: a Russian question about burning on the Moon got a qualitative answer full of raw block ids
  ([R:20240008623#5], [D:insight-P6]). Cause: the knowledge base had no block with the Overview headline comparison,
  and BM25 ranked PSI records and report excerpts above the scenario rows, so the model had no Moon numbers to give.
- Options: A) numbered citations + numbers first; B) keep the codes, smaller; C) other.
- Claude's recommendation: A.
- Decision (Ruslan): "I want it to give concrete information quickly instead of these codes - numbers and values."
- Consequences: new blocks D:moon-answer-methanol / -heptane built from fif.insights.moon (same numbers as the
  Overview), pinned first for any Moon/lunar question; prompt rule 8 "lead with the answer and its key numbers", limit
  120 words; the page replaces citation brackets by superscript numbers with a numbered source list under the answer
  (block ids stay in the excerpts expander; citation and number checks unchanged). Tests: 4 new.
- Sources: src/fif/assistant/knowledge.py, src/fif/assistant/llm.py, app/views/assistant.py

## ADR-046: Headline "Fire on the Moon"; demo = 7 slides (video dropped); S4 wording; plainer texts
- Date/time: 2026-11-14 20:36-21:02
- Stage: post-12 (Ruslan's review before the local-event talk)
- Context: Ruslan found "Will it burn on the Moon?" / "Загорится ли на Луне?" awkward in both languages and asked for a
  catchier headline; then decided the 30-second video is not needed; asked for more connected, human texts; the talk at
  the Uralsk event is in Russian (2-3 min), the deck in English. While renaming, Claude found that insight S4 and the
  summary said flames "rarely" put themselves out, although FLEX shows 46 % (n 13) at O2 >= 30 % vs 86 % (n 58).
- Options: headline A) "Fire on the Moon" B) "One-sixth gravity. Full-size fire." C) "How would a fire behave on a Moon
  base?" D) "Moonfire"; S4: "less often" / "half as often" / unchanged.
- Claude's recommendation: A (note: also the title of a NASA GRC presentation we cite, NTRS 20210020516); "less often".
- Decision (Ruslan): A, everywhere; "the video is not needed, delete it"; S4 "less often"; rewrite the submission texts.
- Consequences: app title and headline block (EN "Fire on the Moon" + "Faster, hotter, and less likely to go out by
  itself."; RU "Пожар на Луне" + "Быстрее, жарче и реже гаснет сам."), README, SUBMISSION, UI_SPEC, assistant Moon
  block. Video, subtitles and scripts/make_demo_video.py removed (in git history); the demo is
  docs/demo/prometheus-0g_slides.pdf (7 slides, linked on GitHub, no login); ADR-044's video choice is superseded.
  S4 title EN "At 30 % O2 droplet flames put themselves out less often", RU "При 30 % O2 пламя капли реже гаснет само"
  (ranking unchanged). Summary, detailed description and AI field rewritten in plainer prose, same numbers.
- Sources: docs/insights.json (S4), fif.insights.moon, docs/DEMO_SCRIPT.md

## ADR-047: Assistant answers stream; per-request timeout; warm-up
- Date/time: 2026-11-15 09:20-09:30
- Stage: post-12 (talk day)
- Context: Ruslan saw the assistant spinner for a long time and asked that it answer fast and correctly, as requested
  the day before (ADR-045). Measured on the live app before the change: 6.6 s and 6.0 s per answer (gemini-3.6-flash,
  correct numbers), the whole answer appearing only at the end. google-genai 3.3.0 has no request timeout and no
  retries by default, so a stalled request could hang without limit; a Gemini 2.5 model rejects the thinking level and
  then ran with unlimited internal thinking; the first question after a restart also built the search index (about 2 s)
  and listed the models.
- Options: A) stream the answer + 20 s timeout per model + warm-up on page open B) switch to a "lite" model (faster,
  weaker answers) C) leave as is.
- Claude's recommendation: A - the words start to appear after the first chunk instead of after the whole answer;
  answer quality and sources unchanged.
- Decision (Ruslan): "answer fast and correctly" - Claude chose A as the technical means; to be confirmed by Ruslan.
- Consequences: the page shows the question and the growing answer at once; citation brackets are rendered as
  superscript numbers while streaming and an unfinished bracket is held back, so raw block ids never appear. Each
  request has a 20 s timeout, then the next candidate model is tried. Thinking: level MINIMAL (Gemini 3), else budget 0
  (Gemini 2.5), else a plain request. The model list and search index are prepared when the page opens.
  After the first deploy the live app answered with gemini-3.5-flash-lite: the best model had failed once and the
  generator (shared by all visitors) kept the last working model for good. Now every call starts from the best-ranked
  model; a failed model is skipped for 10 min after a quota error, 2 min after other errors. ?debug=1 on the page shows
  the last call's key-free failure reasons.
  Live check with ?debug=1: gemini-3.8-flash and 3.7-flash return 429 (no free quota), 3.6-flash answers. Its Moon answer
  showed a false warning: the number check did not read factors written "x1.46" (fixed; test added), and the model had
  computed "48 %" itself (prompt now forbids new differences/ratios/percentages and LaTeX markup).
  Second live check: the free quota of all full Flash models on this key was used up for the day (429; resets at
  midnight Pacific time = 13:00 Uralsk), gemini-2.5-flash is withdrawn for new users (404, now paused for a day), so
  gemini-3.5-flash-lite answered: fast (first words 1.2-1.4 s) but it wrote "methane" for methanol, called our model
  "NASA's" and answered an off-topic Russian question in English. Prompt rules added for substance names, model
  ownership and answer language. Claude stopped live testing to save the quota for the talk.
- Sources: src/fif/assistant/llm.py, app/views/assistant.py, tests/test_assistant.py

## ADR-048: Live-app link at the top of README; keep-awake check
- Date/time: 2026-11-15 11:24-11:38
- Stage: post-12
- Context: Streamlit Community Cloud keeps apps deployed with no stated time limit, but "All apps without traffic for
  12 hours go to sleep"; any visitor can wake one with "Yes, get this app back up!" (docs.streamlit.io, manage your
  app). Judges may open the app days or weeks later. Ruslan also asked to remove the video link from the README.
- Options: A) scheduled visit by a headless browser (GitHub Actions, free for public repositories) + prominent link and
  wake-up hint in README B) README hint only C) nothing.
- Claude's recommendation: A.
- Decision (Ruslan): "put the link right at the start [of the GitHub README], and add the auto-ping"; "remove the video
  link from README".
- Consequences: README starts with "Live app" and the wake-up hint; the phrase "No AI-generated images or video" became
  "No AI-generated images" (the video link itself was already removed by ADR-046; it remains only in the old tag
  stage-12). scripts/keep_awake.py opens the Overview page, clicks the wake-up button if shown and checks the headline
  (never the assistant page, so no Gemini quota); tested on the live app (up in 26 s) and on a local sleeping-page mock
  (button clicked, up in 10 s). .github/workflows/keep-awake.yml runs it at minute 17 every 4 hours and on demand.
  Limits (GitHub docs): scheduled runs can be delayed or dropped at high load; in a public repository they are
  disabled after 60 days without repository activity (re-enable in the Actions tab). No automatic commits are made to
  keep it alive, so the repository stays as submitted.
- Sources: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app ;
  https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows ;
  https://docs.github.com/en/billing/concepts/product-billing/github-actions

## ADR-049: Improvements for global judging until the deadline; assistant answers without AI when Gemini fails
- Date/time: 2026-11-15 18:04
- Stage: post-12
- Context: Ruslan: "improve the project for the global stage". Project Submission Guide: submission closes Sunday,
  November 15, 11:59 p.m. local event time; "Only your last saved submission will be reviewed by the judges". The free
  Gemini quota ran out during the day (ADR-047), so a judge could see only an error on "Ask the data".
- Options (time): until 23:59 then freeze / continue after the deadline; features: assistant without quota, Moon-base
  checklist, solids at lunar gravity, nothing new.
- Claude's recommendation: until 23:59 then freeze; assistant without quota first.
- Decision (Ruslan): until 23:59, then freeze; all three features, plus "module design and fire spread in it, if
  applicable".
- Consequences (step 1): when Gemini fails or no key is set, the assistant quotes the most relevant sentences of our
  result blocks and NASA report excerpts (deterministic, numbered sources, sentences with numbers preferred) with a
  note that no AI was used; off-topic questions get the coverage note. The page works without a key.
  Steps 2-4 (one page, "Module fire"): module-wall editor and fire-spread sketch on measured NASA rates (Saffire,
  LUCI; PHYSICS.md section 10b), five verbatim NASA findings on solids at lunar gravity, 7-item checklist with the
  evidence for each item. Applicable as a sketch only: rates exist for thin fabric and acrylic in air, not for 30 % O2.
- Sources: https://www.spaceappschallenge.org/resources/project-submission-guide/ (read 2026-11-15)
