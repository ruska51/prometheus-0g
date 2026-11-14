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
