# Requirements Traceability

Origins: **CH** = challenge page (docs/challenge/CHALLENGE.md, pasted 2026-11-14); **SG** = Space Apps Project Submission Guide 2026; **TC** = Space Apps Terms and Conditions. SG and TC items are taken from CLAUDE.md section 7; the Guide and Terms pages themselves were not read by Claude (spaceappschallenge.org blocks automated access). Ruslan verifies them against the live pages before submitting.

Status: `open` / `partial` / `done`. Priority: **M** = must (core objective or submission rule), **S** = should (named in the challenge as an option), **C** = could (Potential Considerations).

## A. Challenge (what the dashboard must do)

| ID | Requirement | Origin | Pri | How we close it | Status |
|---|---|---|---|---|---|
| CH-1 | Web-based dashboard, AI-powered | CH Objectives | M | Streamlit app on HF Spaces (ADR-001); physics-informed ML layer (stages 5-6) | open |
| CH-2 | Summarize combustion science investigations | CH Objectives | M | Investigation catalog from PSI ISA metadata (25 studies in `data/raw/psi_metadata/`) + extracted test conditions; summary page | open |
| CH-3 | Rank investigations | CH Objectives | M | Relevance ranking to fire-safety needs; formula is Ruslan's decision (FORMULAS.md section 8 is a draft) | open |
| CH-4 | Interpret investigations -> foundational fire-safety insights | CH Objectives | M | Insight engine (stage 7), each insight tagged with evidence type and N tests | open |
| CH-5 | Identify investigations most relevant to habitable crew environments (spacecraft, stations, lunar/Martian bases, pressurized rovers) | CH Objectives | S | Relevance filter by environment; rockets/propellants out of scope (CH footnote) | open |
| CH-6 | Extract data that supports predictive modeling of flammability and fire scenarios | CH Objectives | S | data layer (stage 3) + calibrated hybrid model (stages 4-5); downloadable tables | open |
| CH-7 | Highlight research informing next-generation fire-safety controls/equipment | CH Objectives | S | Insights grouped by prevention / detection / suppression | open |
| CH-8 | (Optional) Applications of PSI data to fire safety on Earth | CH Objectives | C | Impact section: R5-R7 spinoffs; water mist mentioned on the page (source to find) | open |
| CH-9 | Audience: professors, students, aerospace researchers and engineers | CH Considerations | C | Technical language, units shown, links to sources | open |
| CH-10 | Display objectives, fuels (shape/size of samples or burners), O2 concentration, airflow speed, within-investigation variables, sensors/measurement types | CH Considerations | C | Per-investigation card with these fields; DATA_DICTIONARY.md | open |
| CH-11 | Show similarities and differences between investigations | CH Considerations | C | Comparison view (shared hardware: ACME/CIR, MDCA/CIR, MSG/SPICE duct) | open |
| CH-12 | Moon Base / rover atmosphere: >=30% O2 at <=10.2 psi vs 21% at 14.7 psi; spacesuit 100% O2 at 4.3 psi | CH Considerations | C | Scenario input on the dashboard; any prediction outside tested ranges is flagged as extrapolation (CLAUDE.md section 4) | open |
| CH-13 | No partial-gravity data in PSI; micro- and normal-gravity results may bound intermediate gravity | CH Considerations | C | State explicitly; any partial-g output is a labelled bound, not data | open |

## B. Submission (what must be handed in)

| ID | Requirement | Origin | Pri | How we close it | Status |
|---|---|---|---|---|---|
| SG-1 | Project Name | SG | M | SUBMISSION.md; name is Ruslan's decision | open |
| SG-2 | High-Level Project Summary | SG | M | SUBMISSION.md, stage 12 | open |
| SG-3 | Link to Project Demo | SG | M | Video or slides (SG-9), stage 12 | open |
| SG-4 | Link to Final Project, publicly accessible | SG | M | https://github.com/ruska51/prometheus-0g (public, ADR-002) + HF Spaces app | partial |
| SG-5 | Detailed Project Description | SG | M | SUBMISSION.md + README.md | open |
| SG-6 | NASA Data: what was used and how; all of R1-R7 explained | SG + CLAUDE.md 3.0 | M | README table + SUBMISSION.md, every R explained | partial (R1-R7 listed, usage TBD) |
| SG-7 | Space Agency Partner & Other Data: all data, resources and tools | SG | M | DATA_SOURCES.md -> SUBMISSION.md; libraries and their licenses | partial |
| SG-8 | Use of Artificial Intelligence stated | SG | M | AI_USAGE.md (logged from stage 0) -> SUBMISSION.md | partial |
| SG-9 | Demo: video <=30 s with English subtitles OR <=7 slides incl. title; external hosting, no password or registration. Exceeding limits = no global judging | SG | M | DEMO_SCRIPT.md, stage 12; check length/count before upload | open |
| SG-10 | All submission content in English | SG | M | Repo, UI, docs in English (CLAUDE.md 2.2) | partial |
| SG-11 | "Submit for Judging" before the deadline; submission is final. Deadline per Guide (~23:59 Sun 15 Nov, local event time; our target Sun 18:00) | SG | M | Ruslan verifies exact time in the Guide; submit early | open |
| SG-12 | Judging criteria: Impact, Creativity, Validity, Relevance, Presentation | SG | M | Map each to README sections; Validity via VALIDATION.md | open |

## C. Terms and rules

| ID | Requirement | Origin | Pri | How we close it | Status |
|---|---|---|---|---|---|
| TC-1 | Confirm Terms and Conditions and originality of work | TC | M | Ruslan ticks in the form; no code from other 2026 teams (CLAUDE.md 3.2) | open |
| TC-2 | AI allowed but disclosed: where and how | TC / SG | M | AI_USAGE.md | partial |
| TC-3 | AI-generated images/video carry a visible label | TC / SG | M | Label on every AI image/frame; checklist in SUBMISSION.md | open |
| TC-4 | AI content must not contain or alter NASA branding; no NASA logos, flags, mission insignia in own materials | TC / SG + CLAUDE.md 3.2 | M | No logos in app/slides/video; check at stage 12 | open |
| TC-5 | Third-party data and library licenses respected | TC + CLAUDE.md 3.2 | M | DATA_SOURCES.md license column | partial |
