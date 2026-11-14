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
