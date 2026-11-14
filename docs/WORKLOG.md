# Work Log

Format: `YYYY-MM-DD HH:MM | stage | what was done | files | next`. Times UTC+5 (Uralsk), taken from the system clock and git commit times.

## Stage 0 - started 2026-11-14 10:57

2026-11-14 10:57 | 0 | Environment check (below) | - | decisions
- Python: 3.14.3 (default) and 3.12.10 installed (`py -0`). The project uses **3.12** (Claude's technical choice: wider wheel availability for scientific packages and hosting images than 3.14).
- git 2.53.0; pip 26.2.1; uv: not installed; conda: not installed; gh CLI: not installed.
- Internet: NTRS API `microgravity combustion` -> HTTP 200, 1077 hits (see RESEARCH_LOG.md).
- Disk: C: 47 GB free of 477 GB (91% used), enough for this project.
- Repository: existing git repo `prometheus-0g` with initial commit 8619e3c (Apache-2.0 LICENSE, .gitattributes) by ruska51; no remote at that time; folder `NASA PSI data/` present (untracked). Not re-initialised.

2026-11-14 ~11:05 | 0 | Decisions ADR-001..005 recorded (Streamlit + HF Spaces, public repo now, Apache-2.0, venv+pip, use `NASA PSI data/`) | docs/DECISIONS.md | -

2026-11-14 ~11:10 | 0 | Inventory of `NASA PSI data/` (metadata only, no data tables); R1-R7 checked and summarised | docs/RESEARCH_LOG.md, docs/DATA_SOURCES.md | stage 2 recon

2026-11-14 11:18 | 0 | Repository skeleton per CLAUDE.md section 5 (repo root `prometheus-0g` plays the role of `flame-in-freefall/`); module stubs with docstrings; requirements.txt, pyproject.toml, Makefile, .gitignore; doc templates; CHALLENGE.md with R1-R7. Commit 521f993 | all | challenge text -> 01_REQUIREMENTS.md

2026-11-14 11:18 | 0 | Ruslan's FORMULAS.md (sections 1-9) moved to docs/FORMULAS.md as the file itself instructs. Note: it entered commit 521f993 before Claude had read it. Not yet verified against primary sources. Commit bc0001f | docs/FORMULAS.md | stage 4: verify each formula -> PHYSICS.md

2026-11-14 ~11:20 | 0 | Ruslan published the repository: https://github.com/ruska51/prometheus-0g (origin/main = bc0001f) | - | -

2026-11-14 11:25 | 0 | Correction: earlier entries of this log carried invented times (11:25/11:35/11:45, written before checking the clock) and a claimed stage duration of ~55 min. Replaced with clock/git times; actual stage-0 work 10:57-11:18 (~21 min) | docs/WORKLOG.md | -

2026-11-14 11:24 | 0 | Challenge text pasted by Ruslan into CHALLENGE.md (verbatim); requirements matrix written | docs/challenge/CHALLENGE.md, docs/01_REQUIREMENTS.md | tag stage-0

Open items:
- (closed in stage 1, ADR-006)

## Stage 1 - started 2026-11-14 11:27

2026-11-14 11:27 | 1 | `NASA PSI data/` -> `data/raw/psi_metadata/` (ADR-006); sha256 per file in data/catalog.yaml; live docs repointed | data/raw/psi_metadata/, data/catalog.yaml, docs/* | stage 1 analysis

2026-11-14 11:29 | 1 | Data-outlook research: ISA objectives/approaches of key studies + 5 NTRS queries | docs/RESEARCH_LOG.md | options for Ruslan

2026-11-14 11:32 | 1 | Ruslan's decisions: scope C, personas P1-P3, questions Q1/Q2/Q3/Q5/Q8, MVP M1-M6 (S5 first stretch), name Prometheus-0g | docs/DECISIONS.md (ADR-007..011) | brief

2026-11-14 11:33 | 1 | 00_PROJECT_BRIEF.md filled; 01_REQUIREMENTS.md traceability mapped to M/S/Q; README name + tagline; CH-12 no longer carries "21% O2" (not in the challenge text, was from memory) | docs/00_PROJECT_BRIEF.md, docs/01_REQUIREMENTS.md, README.md | stage 2: data recon
- Stage 1 duration: 11:27-11:33 (clock).

## Stage 2 - started 2026-11-14 11:34

2026-11-14 ~11:40 | 2 | PSI read through its public web service: 133 investigations, 24 Combustion Science; 20 have Experimental Table CSVs (22 files, CC0) | docs/RESEARCH_LOG.md | assess candidates

2026-11-14 ~11:44 | 2 | NTRS: 10 queries, PDFs scanned for tables; NASA/TP-2015-216046 (FLEX) Table IX = cross-check for PSI-69 | docs/RESEARCH_LOG.md, docs/DATA_SOURCES.md | -

2026-11-14 11:48 | 2 | Decisions ADR-012 (FLEX primary, CFI-G auxiliary, BASS-II if time), ADR-013 (no-outcome datasets = catalog only), ADR-014 (Claude downloads open PSI files via API) | docs/DECISIONS.md | fetch

2026-11-14 12:02 | 2 | scripts/fetch_psi.py: 25 raw JSON responses (gzip) + 22 CSVs + MANIFEST.tsv; all sizes match PSI records; byte-identical to the first scratch download; first run failed on a DNS error -> retries added, records stored gzip (raw PSI-23 record alone was 8.1 MB due to a file change log) | scripts/fetch_psi.py, data/raw/psi_records/, data/raw/psi_tables/, data/catalog.yaml | stage 3: parse FLEX + CFI-G

2026-11-14 12:02 | 2 | DATA_SOURCES.md rewritten (registered sources, 24 candidates rated, NTRS tables, selection); stage closed | docs/DATA_SOURCES.md | -
- Stage 2 duration: 11:34-12:02 (clock), budget 60 min.

## Stage 3 - started 2026-11-14 12:03

2026-11-14 12:10 | 3 | venv (Python 3.12) with pinned packages; anomaly scan of FLEX and CFI-G; decisions ADR-015..018 | requirements.txt, docs/DECISIONS.md | parsers
2026-11-14 ~12:13 | 3 | data layer: catalog, parsers (flex, cfig, psi_catalog), clean, schema (pandera), features, build; scripts/build_data.py | src/fif/data/, scripts/build_data.py, data/interim, data/processed | verification
2026-11-14 ~12:17 | 3 | FLEX CSV vs NASA/TP-2015-216046 Table IX: pdftotext showed false diffs (text layer shifted) -> rendered pages checked by eye + pdfplumber word-coordinate parser; 3288 cells, 0 differences; numbering offset, 2 TP-only tests, blank-vs-dash finding | scripts/verify_flex_vs_tp.py, docs/verification/flex_vs_tp.tsv, docs/DATA_QUALITY.md | tests
2026-11-14 ~12:19 | 3 | tests (13, built into tmp dirs; live processed mtime unchanged), EDA + 4 figures | tests/test_data_flex.py, scripts/eda.py, docs/figures/ | docs
2026-11-14 12:22 | 3 | DATA_DICTIONARY, DATA_QUALITY, ARCHITECTURE (data layer + Mermaid), DATA_SOURCES; correction: Moon-base atmosphere is just outside the FLEX tested pressure range (0.694 vs >= 0.703 atm), not inside as said in stage 2 | docs/* | stage 4
- Stage 3 duration: 12:03-12:22 (clock), budget 90 min.

## Stage 4 - started 2026-11-14 12:25

2026-11-14 12:27 | 4 | Stage-3 follow-up: 70/73 examined (TP Table IV, Figs. 74/77, K-burn-time consistency) -> row 73 excluded; FLEX-216/230 added from TP; commit 64dde02 | src/fif/data, data/raw/ntrs/flex_tp_supplement.csv | physics
2026-11-14 ~12:30 | 4 | Theory sources: NTRS 20130014061 (K, B equations), NASA RP-1311 (mixing rules, read from rendered pages), Law & Williams DOI via Crossref | docs/PHYSICS.md | decisions
2026-11-14 ~12:35 | 4 | Decisions ADR-022..025 (L2 + L3 proxies, 1/2 rule ambient mixture, microgravity base, compact features) | docs/DECISIONS.md | code
2026-11-14 ~12:37 | 4 | NIST SRD 69 data fetched (scripts/fetch_nist.py, 13 files, catalog) | data/raw/nist | code
2026-11-14 ~12:40 | 4 | physics package (properties, mixing, droplet); theory vs data: K_meas/K_theory 0.52 (methanol), 0.24 (heptane); trends with d0, He, CO2 | src/fif/physics, scripts/physics_vs_data.py, docs/figures/physics_*.png | tests, docs
2026-11-14 12:43 | 4 | 18 physics tests (32 total green); PHYSICS.md, ARCHITECTURE (physics), DATA_SOURCES, features list | tests/test_physics.py, docs/* | stage 5
- Stage 4 duration: 12:25-12:43 (clock), budget 90 min.
2026-11-14 12:49 | 4 | Rework after Ruslan's review: Q checked (19.90 = LHV, HHV 22.65 MJ/kg - both from NIST); cause of the 2x/4x error = ambient-gas cp instead of the inner-region C_1 of L&W Eq. (1) | - | fix
2026-11-14 12:51 | 4 | C_1 = NIST fuel-vapour cp (TRC 1997 / Scott 1974); K_meas/K_theory methanol 1.36, heptane 0.89; 34 tests green; PHYSICS.md sections 2, 5, 6, 7 updated; ADR-026; tag stage-4.1 | src/fif/physics, data/raw/nist/thermo_gas_*, docs/PHYSICS.md | stage 5
- Stage 4 rework: 12:49-12:52 (clock).
2026-11-14 12:53 | 4 | Ruslan: "why is it so crude, find something proper"; NASA statement found (NTRS 20205008449): QS theory needs an empirical property prescription (L&W) | docs/RESEARCH_LOG.md | decision
2026-11-14 ~12:58 | 4 | Full L&W paper received; prescription extracted (pp. 394-395, 399, 404) | - | implement
2026-11-14 ~13:02 | 4 | NASA TR R-132 (Svehla) transcribed (CH3OH table, C5/C6 viscosity), Eq. (2) self-check 0.1 %; Cantera 3.2.0 + NASA Glenn thermo for equilibrium T_f | data/raw/nasa_tr_r132, src/fif/physics/flame.py | droplet rewrite
2026-11-14 13:07 | 4 | droplet.py rewritten to the L&W prescription; K_meas/K_theory methanol 0.97 (74 % within 15 %), heptane 0.73; size trend confirmed; 39 tests green; PHYSICS.md rewritten; ADR-027; tag stage-4.2 | src/fif/physics, tests/test_physics.py, docs/PHYSICS.md | stage 5
2026-11-14 13:11 | 4 | ADR-028: q = LHV confirmed by Ruslan; HHV sensitivity +7.8 % / +3.4 % in K | docs/DECISIONS.md, docs/PHYSICS.md | stage 5

## Stage 5 - started 2026-11-14 13:14

2026-11-14 ~13:16 | 5 | Architecture proposed; decisions ADR-029 (3 targets, GP residual, logistic vs boosting, constraints both ways, full metrics) | docs/DECISIONS.md | code
2026-11-14 13:21 | 5 | models package (features + leakage guard, regression, classification, train); scripts/train_models.py one command (~45 s) | src/fif/models, scripts/train_models.py | metrics
2026-11-14 13:23 | 5 | K: hybrid RMSE_log 0.214 vs physics 0.302 / mean 0.304 / pure ML 0.288; c_f methanol 0.964, heptane 0.714; extinction AUC 0.805 (monotonic boosting), physics-only logistic balanced acc 0.733; d_ext/d0 pure ML best (0.406); 62 tests green | docs/verification/model_*, models/*.joblib, docs/figures/model_*.png | docs
2026-11-14 13:24 | 5 | MODEL_CARD.md, ARCHITECTURE (models), Makefile data/train targets | docs/* | stage 6
- Stage 5 duration: 13:14-13:24 (clock), budget 90 min.
