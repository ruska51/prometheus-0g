# Work Log

Format: `YYYY-MM-DD HH:MM | stage | what was done | files | next`. Times UTC+5 (Uralsk).

## Stage 0 - started 2026-11-14 10:55

2026-11-14 11:00 | 0 | Environment check (below) | - | decisions
- Python: 3.14.3 (default) and 3.12.10 installed (`py -0`). The project uses **3.12** (Claude's technical choice: wider wheel availability for scientific packages and hosting images than 3.14).
- git 2.53.0; pip 26.2.1; uv: not installed; conda: not installed; gh CLI: not installed.
- Internet: NTRS API `microgravity combustion` -> HTTP 200, 1077 hits (see RESEARCH_LOG.md).
- Disk: C: 47 GB free of 477 GB (91% used), enough for this project.
- Repository: existing git repo `prometheus-0g` with initial commit 8619e3c (Apache-2.0 LICENSE, .gitattributes) by ruska51; no remote configured; folder `NASA PSI data/` present (untracked). Not re-initialised.

2026-11-14 11:10 | 0 | Decisions ADR-001..005 recorded (Streamlit + HF Spaces, public repo now, Apache-2.0, venv+pip, use `NASA PSI data/`) | docs/DECISIONS.md | -

2026-11-14 11:25 | 0 | Inventory of `NASA PSI data/` (metadata only, no data tables); R1-R7 checked and summarised | docs/RESEARCH_LOG.md, docs/DATA_SOURCES.md | stage 2 recon

2026-11-14 11:35 | 0 | Repository skeleton per CLAUDE.md section 5 (repo root `prometheus-0g` plays the role of `flame-in-freefall/`); module stubs with docstrings; requirements.txt, pyproject.toml, Makefile, .gitignore; doc templates; CHALLENGE.md with R1-R7 | all | wait for challenge text -> 01_REQUIREMENTS.md, tag stage-0

2026-11-14 11:45 | 0 | Ruslan's FORMULAS.md (sections 1-9: gas mixture, d2-law, extinction, solid flame spread, jet flames, gravity correction, cabin fire, hybrid model/metrics/ranking, constants table) moved to docs/FORMULAS.md as the file itself instructs. Note: it entered commit 521f993 before Claude had read it. Not yet verified against primary sources | docs/FORMULAS.md | stage 4: verify each formula -> PHYSICS.md

Open items:
- `NASA PSI data/` not committed yet: whether raw files go into git (and moving them to `data/raw/psi_metadata/`) is Ruslan's decision.
- GitHub publication pending (no gh CLI, no remote).
- Stage 0 time budget (15 min) exceeded.
