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
