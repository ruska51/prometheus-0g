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

2026-11-14 ~11:30 | 0 | Challenge text pasted by Ruslan into CHALLENGE.md (verbatim); requirements matrix written | docs/challenge/CHALLENGE.md, docs/01_REQUIREMENTS.md | tag stage-0

Open items:
- `NASA PSI data/` not committed: whether raw files go into git (and moving them to `data/raw/psi_metadata/`) is Ruslan's decision.

## Stage 1 - started 2026-11-14 11:27

2026-11-14 11:27 | 1 | `NASA PSI data/` -> `data/raw/psi_metadata/` (ADR-006); sha256 per file in data/catalog.yaml; live docs repointed | data/raw/psi_metadata/, data/catalog.yaml, docs/* | stage 1 analysis
