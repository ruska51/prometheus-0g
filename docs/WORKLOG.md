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

## Stage 6 - started 2026-11-14 13:34

2026-11-14 13:39 | 6 | First validation run: hybrid 0.225 +- 0.023 (5 seeds); K non-monotone in O2 (dips 1.4-7 %), boosting P(ext) jump +0.54; C13H201 distorts neighbours | src/fif/validation/core.py, scripts/validate.py | decisions
2026-11-14 ~13:45 | 6 | Ruslan: check all variants / test all; rules fixed; variants run (5.5 min) | src/fif/validation/variants.py | config
2026-11-14 13:54 | 6 | Config applied (C13H201 out of K training, raw residual features, logistic interface model); models retrained | src/fif/models, models/ | full validation
2026-11-14 14:01 | 6 | Final validation: hybrid 0.171 +- 0.002 = pure ML 0.174 in CV; hybrid best on 4/4 atmosphere extrapolations; fuel transfer fails for all; monotonicity passes | docs/validation_results.json | docs
2026-11-14 14:06 | 6 | Reliability rule with O2-pressure combination check; VALIDATION.md generated; MODEL_CARD block; ADR-030..032; correction of the "physics better on new fuel" statement | docs/*, src/fif/validation/reliability.py, tests/test_validation.py | stage 7
- Stage 6 duration: 13:34-14:06 (clock), budget 60 min.

## Stage 7 - started 2026-11-14 14:10

2026-11-14 14:12 | 7 | Insight package (base: Insight, weights, 3 ranking formulas; catalog: 12 live insights + 6 history/spinoff, cabin atmospheres) | src/fif/insights | decisions
2026-11-14 ~14:14 | 7 | ADR-033: keep all, formula A, wording as drafted | docs/DECISIONS.md | docs
2026-11-14 14:16 | 7 | scripts/build_insights.py -> docs/insights.json, INSIGHTS.md; 8 insight tests (91 total green) | docs/INSIGHTS.md, tests/test_insights.py | stage 8
- Stage 7 duration: 14:10-14:16 (clock), budget 60 min.

## Stage 8 - started 2026-11-14 14:17

2026-11-14 ~14:19 | 8 | UI_SPEC.md draft; ADR-034 | docs/UI_SPEC.md | code
2026-11-14 14:22 | 8 | Package logic (investigation ranking M2, scenario M4, risk grid); 8 Streamlit pages + common loaders; smoke tests through st.navigation (9 green) | src/fif/insights/, app/, tests/test_app.py | screenshots
2026-11-14 14:24-14:30 | 8 | Screenshots via Playwright + Edge (desktop 1400 px, phone 390 px), reviewed; fixed truncated metric labels, pressure rounding, map overlay (grey veil instead of markers), clipped phone label, table headers, full-height capture | scripts/screenshots.py, docs/figures/ui/ | stage 9-12
2026-11-14 14:30 | 8 | Docs (UI_SPEC final, ARCHITECTURE app layer, AI_USAGE) | docs/* | -
- Stage 8 duration: 14:17-14:30 (clock), budget 150 min.
2026-11-14 14:39-14:43 | 8+ | Animation inputs in the package: d^2-law series, Earth K x (1 + f_B), extinction diameter (GP, in range only), standoff, blackbody soot colour | src/fif/insights/flame_sim.py | canvas
2026-11-14 14:43-14:52 | 8+ | Canvas animation (two synchronized panels, play/replay/speed), wired into the scenario page with a comparison selector; verified the flame-size caveat in NTRS 20130014061 section 3.2 | app/flame_view.py, app/common.py, app/views/scenario.py | screenshots
2026-11-14 14:43-14:52 | 8+ | Fix: after a server restart the direct URL /scenario ran the page without main.py (file names in the sidebar, centred layout) because Streamlit auto-discovers an `app/pages/` folder; renamed to `app/views/` | app/main.py, app/views/, tests/test_app.py, docs/ARCHITECTURE.md | -
2026-11-14 14:52-14:57 | 8+ | Tests (112 green), screenshots regenerated, docs (ADR-035, UI_SPEC, AI_USAGE, RESEARCH_LOG, DATA_SOURCES) | tests/test_flame_sim.py, docs/* | stage 9-12
2026-11-14 14:57 | post-8 | Inventory of deferred items for Ruslan; decisions ADR-036..038 | docs/DECISIONS.md | item 1
2026-11-14 (after Ruslan's answers, before 15:23)-15:31 | post-8 item 1 | Lunar gravity: source search (fact sheet unreachable; NTRS 20250004015 for 1/6), buoyancy_factor(Gr, g), moon bound in scenario, animation at any g (1/6 g panel, shell-shaped buoyant flame), insights P5/P6, tests (115 green), PHYSICS/RESEARCH_LOG/DATA_SOURCES | src/fif/physics/droplet.py, src/fif/insights/*, app/*, tests/* | item 2 (S5 matrix)
2026-11-14 15:31-15:36 | post-8 item 2 | S5 comparison matrix: variable classes from PSI table headers (regex rules), hardware families, Compare tab with heatmap + computed summary; computed Tad and ambient T excluded from measured outcomes; tests (120 green). Data note: ACME s-Flame 'Atmosphere' has spreadsheet autofill artefacts 'N3'..'N6' for N2 (catalog-only table, not used in models) | src/fif/insights/compare.py, app/views/investigations.py, app/common.py, tests/test_compare.py | item 3
2026-11-14 15:36-15:39 | post-8 item 3 | Extinction label sensitivity (ADR-018 B/C): rule written in src/fif/validation/label_sensitivity.py and announced in chat before the run (15:38); result: directions robust (P falls with O2, S3/S4 hold, no rise along O2), AUC check fails for C (0.882 vs A 0.787, i.e. better); A kept, question to Ruslan | src/fif/validation/label_sensitivity.py, scripts/label_sensitivity.py, docs/verification/extinction_label_sensitivity.*, scripts/render_validation.py, docs/VALIDATION.md | item 5 deploy (needs HF token)
2026-11-14 15:39-15:41 | post-8 item 5 (prep) | HF Spaces deploy prepared: Dockerfile (python 3.12-slim, Streamlit on 8501), scripts/deploy_hf.py (token from env/file outside the repo, staged copy of the app files + Space README header, upload_folder); all 8 pages run from the staged copy; replaced deprecated use_container_width by width='stretch' | Dockerfile, scripts/deploy_hf.py, requirements-dev.txt, app/views/* | waiting for Ruslan's HF account + write token
2026-11-14 15:52-15:53 | post-8 item 5 | HF deploy refused (402: free Docker Spaces need PRO), nothing published, token file deleted; Ruslan chose Streamlit Community Cloud (ADR-040); extinction definition A kept (ADR-039), docs updated | docs/DECISIONS.md, docs/VALIDATION.md, docs/MODEL_CARD.md, docs/DATA_QUALITY.md, scripts/* | Ruslan deploys on share.streamlit.io
2026-11-14 15:53-16:01 | 11 (brought forward) | Ruslan deployed on Streamlit Community Cloud; Claude checked all 8 pages on https://prometheus-0g.streamlit.app/ (0 exceptions, flame window runs, numbers as local); link in README, SUBMISSION, REQUIREMENTS (CH-1, SG-4) | README.md, docs/* | stage 12
2026-11-14 16:04 | 10 | Stage 10 start (tests and quality)
2026-11-14 16:04-16:07 | 10 | Clean install from a fresh clone (venv, pinned pip install, build data, train, insights, tests): 121 passed in 2 min 18 s; rebuilt artefacts differed only by CRLF/LF, timestamps, pickle bytes (predictions identical, max abs diff 0.0) and a stale transform_log count (75 vs 91) | scratchpad clone | fixes
2026-11-14 16:04-16:21 | 10 | Secrets scan of all 32 commits (HF/GitHub/OpenAI/AWS/Google keys, private keys, password/token assignments, secret-like file names, the HF token and the user's e-mail): 0 hits. Raw data: scripts/verify_raw.py (fif.data.catalog.verify) + test, 91 git-tracked files match catalog.yaml. Ruff E/F/W/I/UP/B + format clean (repo formatted; E501/B905 ignored with reasons); type hints on all package functions (ANN001/ANN201 clean in src/fif). Coverage of fif 79 % -> 84 % (end-to-end grouped-CV test); train.py / validation core are covered by the pipeline run. Links: 0 broken relative links; 23 external URLs - all reachable except NTRS HTML pages (timeout from this network; all 7 records confirmed via the NTRS API) and the Streamlit app (auth redirect for curl; opens in a browser). .gitattributes LF for generated tables; run.py cross-platform pipeline, Makefile wrapper, README How to run, requirements-dev pinned | scripts/verify_raw.py, run.py, Makefile, pyproject.toml, .gitattributes, README.md, src/**, tests/** | README run
2026-11-14 16:22-16:24 | 10 | README procedure from a fresh GitHub clone: run.py setup 48 s, run.py all 66 s (raw hashes OK, 123 passed), processed data byte-identical to git, run.py app healthz 200 | - | -
- Stage 10 duration: 16:04-16:24 (clock), budget 30 min.
2026-11-14 16:24-16:40 | post-10 | Related-work check (web + GitHub API, docs/RELATED_WORK.md); EN/RU language switch: app/i18n.py (164 interface keys + dynamic values), Russian fields for insights / reliability reasons / animation notes in the package, all pages and the animation translated, tests/test_i18n.py (136 tests green), screenshots in Russian checked (ADR-041) | app/*, src/fif/insights/*, src/fif/validation/reliability.py, docs/insights.json, tests/test_i18n.py, docs/RELATED_WORK.md | stage 12
2026-11-14 16:41-16:56 | 9 | Stage 9 start; options and decisions (ADR-042: C, Gemini free tier); fixed live crash of the Russian scenario page (cached pre-i18n results, cf33d17, verified on the cloud); NTRS corpus (12 public-use reports, sha256 in catalog.yaml); src/fif/assistant (BM25 retrieval over 49 result blocks + 887 report excerpts, RU->EN glossary, rule-first prompt, citation checks); page 'Ask the data' (EN/RU, 10 questions/session, no-key message); tests 148 green offline; eval script ready | src/fif/assistant/*, app/views/assistant.py, scripts/fetch_ntrs_corpus.py, scripts/assistant_eval.py, data/raw/ntrs_text/*, docs/* | live eval needs Ruslan's Gemini key
2026-11-14 16:56-17:44 | 9 | Live deployment of the assistant: fixed default model name (auto selection from the key's model list), robust fallback over models, key-free technical detail; Streamlit Cloud kept old package modules after deploys (ImportError) -> main.py reloads fif modules when sources change; multi-id citations; Ruslan: answers vague and slow -> 18 numeric data blocks (FLEX statistics, per-atmosphere predictions with burn times), concrete-numbers rule, minimal model thinking (~40 s -> ~14 s); live 10-question evaluation 9/10 twice, reading found a mislabelled number (Q5) and a retrieval regression (Q4) -> mixed retrieval, number-label rule, unsupported-number warning (152 tests) | src/fif/assistant/*, app/*, scripts/assistant_eval_live.py, docs/ASSISTANT_EVAL.md | re-run eval after quota reset
- Stage 9 duration: 16:41-17:44 (clock), budget 30 min (optional stage).
2026-11-14 17:44-17:51 | post-9 | Headline answer block on the Overview (ADR-043): fif.insights.moon, EN/RU, consistency test (numbers = model, P2, S4, d2-law); AppTest workaround for translated radio labels; screenshots desktop/phone reviewed | src/fif/insights/moon.py, app/views/overview.py, app/common.py, app/i18n.py, tests/test_insights.py | stage 12
2026-11-14 19:02 | post-9 | GitHub secret-scanning alert (email 17:11) 'Google API Key' in tests/test_assistant.py (commit bf1b293): a FAKE key-shaped test string written by Claude (AIzaSyA1234567890abc...), replaced in b24e6e6; full history scan: no other key-shaped strings, the real Gemini key was never in the repository (Streamlit secrets only). Alert to be closed as 'used in tests'; rule: test fixtures never use realistic key formats | tests/test_assistant.py | -
2026-11-14 19:06 | 12 | Stage 12 start; decisions (ADR-044); demo recorder script (Playwright video + ffmpeg subtitles), first takes reviewed frame by frame (subtitle size, accurate trimming, scrolling fixed)
2026-11-14 19:07-19:53 | 12 | Flame realism (Ruslan's review, three rounds): 2D bloom -> envelope -> WebGL shader -> reference photo NASA C-1998-485 (laminar spindle at 1 g, soft sphere in microgravity) | app/flame_view.py | -
2026-11-14 19:53-20:07 | 12 | Video re-recorded with the new flame (27.6 s); README rewritten (problem, solution, top-5 Moon insights, Mermaid architecture, physics, data, validation, run, structure, limitations, AI, sources, team); SUBMISSION.md all fields + counts + checklist; DEMO_SCRIPT.md; requirements matrix final; links checked (0 broken relative, all external 200, app 303 auth redirect = normal); screenshots refreshed | README.md, docs/*, docs/demo/*, scripts/make_demo_video.py | Ruslan: YouTube upload, form, Submit
- Stage 12 duration: 19:06-20:07 (clock), budget 90 min.
2026-11-14 20:11-20:16 | 12+ | 7-slide English presentation (Ruslan's request), built from README / app numbers: cover, problem, answer, method, validation, dashboard, impact; published as a private claude.ai Slides artifact (not in the repo); rendered locally and checked for overflow | - (artifact) | Ruslan: review, share link if used
2026-11-14 20:17-20:19 | 12+ | QR code (live app URL) added to the last slide of the presentation; generated with segno in a scratch venv, decoded back with OpenCV = https://prometheus-0g.streamlit.app/ | - (artifact) | -
2026-11-14 20:22-20:30 | post-12 | Assistant fix after Ruslan phone review (ADR-045): Moon headline blocks pinned for Moon questions, numbers-first prompt, superscript citations + numbered source list; 159 tests pass, ruff clean | src/fif/assistant/*, app/views/assistant.py, app/i18n.py, tests/test_assistant.py | live check on the site after redeploy
2026-11-14 20:33-20:35 | 12+ | Presentation vs judging criteria (Ruslan: "do all"): Impact = who uses it + Earth spinoffs on slide 7 (GitHub link moved under the QR); Creativity = "What is new" line on slide 4 from docs/RELATED_WORK.md; Relevance = "summarize, rank, interpret" on slide 6; assistant line updated; re-rendered, no overflow | - (artifact) | -
2026-11-14 20:36-21:02 | post-12 | ADR-046: headline "Fire on the Moon" (app EN/RU, README, SUBMISSION, UI_SPEC, assistant); video + subtitles + make_demo_video.py removed, demo = 7-slide PDF (docs/demo/prometheus-0g_slides.pdf, printed with Playwright/Edge, real fonts and screenshots); deck text rewritten in plain connected English, speaker notes = Russian talk (327 words, ~2-2.5 min); S4 "rarely" -> "less often" (EN/RU), insights rebuilt (ranking unchanged); SUBMISSION summary/description/AI rewritten, counts regenerated; 159 tests pass, ruff clean, raw data 103 files match | README.md, app/*, src/fif/*, docs/* | Ruslan: proofread SUBMISSION, open the PDF link |
2026-11-14 21:10-21:47 | post-12 | Screenshots retaken with the new headline (overview, insights, scenario; others unchanged); ASSISTANT_EVAL notes the ADR-045 change and the pending live re-run; tag submission | docs/figures/ui/*, docs/ASSISTANT_EVAL.md | Ruslan: live assistant check, form, Submit
2026-11-14 21:45-22:03 | post-12 | Load check before the talk (QR on slide 7): Streamlit Community Cloud limits (docs, Feb 2024 figures) 690 MB-2.7 GB RAM, 0.078-2 cores, no viewer limit, sleep after 12 h without traffic. Local test, N browsers opening Overview + Moon-base scenario at once: memory 84 MB idle, 240 MB after 1 visitor, 284 MB at 40 (about 1 MB per visitor); all 40 served, 0 failures; server CPU about 2 s per new visitor, served one after another (10 at once: median 27 s, 40 at once: about 130 s). Page scripts alone take about 0.2 s warm (AppTest), the rest is framework/page delivery. No code change; advice to Ruslan: wake the app before the talk, demo from the laptop | - | -
2026-11-15 09:20-09:25 | post-12 | ADR-047: assistant slow (Ruslan's screenshot). Live measurement before: 6.6 s / 6.0 s per answer, gemini-3.6-flash, answers correct. Change: streamed answer (citations rendered as superscripts while streaming, unfinished bracket held back), 20 s timeout per request with fall-through to the next model, thinking budget 0 for Gemini 2.5, warm-up of model list and search index on page open. Checked with AppTest and a fake Gemini (9 frames, no raw ids, quota error shown); 161 tests pass, ruff clean | src/fif/assistant/llm.py, app/views/assistant.py, tests/test_assistant.py, docs/* | measure the live app after deploy
2026-11-15 09:27-09:30 | post-12 | ADR-047 live check: first words 2.2 s / 1.3 s, finished 3.3 s / 2.2 s (before: 6.6 s / 6.0 s), but answered by gemini-3.5-flash-lite: the best model had failed and the shared generator stayed on the fallback. Fix: best model first on every call, failed model skipped 10 min (quota) / 2 min (other); ?debug=1 shows failure reasons; test added, 162 pass | src/fif/assistant/llm.py, app/views/assistant.py, tests/test_assistant.py | live check with ?debug=1
2026-11-15 09:31-09:36 | post-12 | ADR-047 live check with ?debug=1: 3.8/3.7-flash = 429 (no free quota), 3.6-flash answers, first words 3.7 s, finished 5.8 s. False "numbers not in sources" warning (1.46, 1.44 written "x1.46" in the blocks) fixed in unsupported_numbers; "48 %" was computed by the model -> SYSTEM rule 7 forbids new differences/ratios/percentages, rule 9 plain text (no LaTeX); test added, 163 pass | src/fif/assistant/llm.py, tests/test_assistant.py | live re-check
