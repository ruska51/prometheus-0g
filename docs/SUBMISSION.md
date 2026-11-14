# Submission Texts - NASA Space Apps Challenge 2026

Ready-to-paste texts for every field of the Space Apps project form (CLAUDE.md section 7). All in English. Every number
comes from the project's generated artefacts (docs/insights.json, docs/validation_results.json, fif.insights.moon) -
see README.md. Word and character counts are listed at the end; if the form shows a shorter limit, cut from the end of
a field - the first paragraph of each field stands alone.

---

## Project Name

Prometheus-0g

---

## High-Level Project Summary

Prometheus-0g answers a question NASA must settle before building a Moon base: will a fire in its planned
oxygen-rich, low-pressure air (30 % O2, 10.2 psi) burn faster and go out less easily than on the ISS? We turned NASA's
microgravity combustion data from the Physical Sciences Informatics repository into a public, bilingual dashboard.
All 276 ISS droplet-fire tests (FLEX) were verified against NASA's technical report (0 differences). A physics-first
hybrid model - Law & Williams droplet-burning theory plus machine learning - predicts the burning rate with an
uncertainty band and is 1.2-1.9x more accurate than pure machine learning on atmospheres it never saw. The answer:
yes - about 32 % faster, hotter, and flames rarely put themselves out. The dashboard ranks 20 evidence-labelled
fire-safety insights and all 24 NASA combustion investigations, animates the burning flame, and includes an AI
assistant that answers only from NASA data, with sources.

---

## Link to Project Demo

`<YouTube link - Ruslan uploads docs/demo/prometheus-0g_demo.mp4 as "Unlisted" or "Public" and pastes the link here>`

(30-second screen recording of the live app with burned-in English subtitles; no AI-generated imagery.)

---

## Link to Final Project

https://prometheus-0g.streamlit.app/

Source code, data and documentation: https://github.com/ruska51/prometheus-0g

---

## Detailed Project Description

**What it does.** Prometheus-0g is a web dashboard that summarizes, ranks and interprets NASA's microgravity
combustion investigations and turns them into fire-safety insights for crewed habitats, with a focus on the planned
Moon base. Its home page answers the headline question directly: "Will it burn on the Moon? Yes - faster, hotter, and
less likely to go out by itself." For a 3 mm fuel droplet in Moon-base air the burning rate is 32 % higher than in ISS
air (model, 95 % band -2 % to +77 %, labelled extrapolation), the droplet burns out in 14.1 s instead of 18.5 s, the
flame is 238 K hotter, and in NASA's FLEX tests at 30 % oxygen or more the flame went out by itself in 46 % of tests,
versus 86 % at 21 % or less.

**How it works.** (1) Data: the PSI Experimental Tables of FLEX (droplets), ACME CFI-G (gas flames), BASS-II (solids)
and SAME-R (smoke) are parsed, cleaned and flagged - anomalies are flagged, never silently fixed - and every raw file is
registered with a checksum. The 276 FLEX tests were cross-checked cell by cell against NASA/TP-2015-216046 (3288 cells,
0 differences; two tests missing from PSI were recovered from the report). (2) Physics: quasi-steady droplet
combustion with the Law & Williams (1972) property prescription, equilibrium flame temperature with dissociation
(Cantera with NASA thermodynamic data), and a buoyancy correction for Earth and for the lunar surface (1/6 g).
(3) Models: a hybrid model (theory + fuel factor + Gaussian-process correction) that uses only conditions known before
ignition and reports a 95 % band; extinction classifiers. (4) Validation: grouped cross-validation over 78 test regimes
(typical hybrid error about 19 %), and leave-a-class-out tests showing that the physics makes the model 1.2-1.9x more
accurate for helium, CO2, ~0.7 atm and Moon-like oxygen; failures (new fuels, high pressure) are reported openly.
(5) Insights: 20 findings, each with its type of evidence (NASA data, model, physics theory, NASA literature), number
of tests and a confidence label, ranked by evidence strength, sample size and effect size; lessons from Apollo 1,
Apollo 13 and Mir; benefits on Earth.

**What users get.** A Moon-base scenario tool (any O2, pressure, diluent, droplet size) with a reliability label and the
nearest real NASA tests; an animation of the same droplet burning in two atmospheres, driven by the model; a risk map of
oxygen x pressure; a ranked, searchable catalog and a comparison matrix of all 24 PSI combustion investigations; a data
explorer with every raw NASA row downloadable; and "Ask the data", an AI assistant restricted to our results and 12
public NASA technical reports that cites a source after every statement and says when the data do not cover a
question. English by default, Russian on request.

**Benefits and impact.** Habitat and rover designers get quantified, sourced reasons to plan for faster fires that do
not self-extinguish: immediate suppression, CO sensing alongside smoke detectors, and material screening that does not
rely on 1-g tests alone (NASA reports that lunar gravity may be the most flammable condition for solids). Researchers
get a verified, reproducible FLEX dataset and an honest map of where the data stop. Students get an interactive view
of how flames behave without gravity.

**Tools.** Python 3.12, pandas, NumPy, SciPy, scikit-learn (Gaussian processes, logistic regression, gradient
boosting), Cantera, pdfplumber, Streamlit, Plotly, WebGL (flame animation), Google Gemini API (assistant), Playwright
and ffmpeg (screenshots, demo video), pytest and ruff (153 tests, lint), GitHub, Streamlit Community Cloud (hosting).
Code Apache-2.0; NASA data CC0 / public domain. One command reproduces data, models, insights and tests from the raw
NASA files.

---

## NASA Data

- **R1 - NASA Physical Sciences Informatics (psi.nasa.gov):** the source of all quantitative data - the Experimental
  Tables of FLEX (276 ISS droplet tests; models and insights), ACME CFI-G (333 gas-flame tests), BASS-II (129 solid
  tests; CO) and SAME-R (109 smoke tests), plus the records of all 24 Combustion Science investigations for the
  catalog, ranking and comparison matrix.
- **R2 - Apollo 1 (NASA SMA):** quoted as the lesson that a pure-oxygen atmosphere spreads fire quickly and that CO and
  toxic gases killed the crew, linked to our oxygen and CO insights.
- **R3 - Apollo 13 (NASA SMA):** quoted as the lesson that oxygen hardware plus electrical heat is an ignition source,
  linked to our insight that gaseous fuels ignite almost every time in oxygen-rich streams.
- **R4 - Fire aboard Mir (NASA History):** quoted as a real microgravity fire that blocked the escape route and left
  smoke for hours, linked to our detection and suppression insights.
- **R5 - Fireman's Air Tanks (NASA Spinoff):** shown under "Benefits on Earth" as a life-support spinoff for
  firefighters.
- **R6 - Fire Detector (NASA Spinoff):** shown under "Benefits on Earth" and linked to the smoke-detection insight
  from the SAME/SAME-R data.
- **R7 - Fire Attire / Project FIRES (NASA Spinoff):** shown under "Benefits on Earth" as fire-resistant materials
  from the space program.
- **Other NASA sources:** NASA/TP-2015-216046 (FLEX detailed results; used to verify every FLEX cell and to recover two
  tests), NASA NTRS reports on FLEX, BASS-II, ACME, SAME, Saffire and lunar flammability (physics checks and the
  assistant's report search; only documents marked for public use), NASA TR R-132, RP-1311 and TM-4513 (gas properties
  and thermodynamic data), NTRS 20250004015 (lunar gravity 1/6 g), and NASA Glenn photo C-1998-485 (visual reference
  for the flame drawing; not embedded).

---

## Space Agency Partner & Other Data

No data from partner space agencies were used. Other data and resources: NIST Chemistry WebBook (fuel and gas
properties); Law & Williams, "Kinetics and Convection in the Combustion of Alkane Droplets", Combustion and Flame 19
(1972) 393-405 (property prescription; not redistributed); Cantera (chemical equilibrium); the CIE colour-matching
approximation of Wyman, Sloan and Shirley (2013) for the soot colour; and the open-source libraries and services listed
under Tools (Streamlit, Plotly, scikit-learn, Google Gemini API, Streamlit Community Cloud, GitHub). Full list with
licenses: docs/DATA_SOURCES.md in the repository.

---

## Use of Artificial Intelligence

AI was used in two places. (1) Development: the code, data analysis, documentation and texts were produced with Claude
Code (Anthropic, Claude Opus) working under the direction of the team member, who made every scientific and design
decision (theory level, property data, model choice, validation rules, ranking formula, interface); every decision is
logged in docs/DECISIONS.md and every AI-assisted step in docs/AI_USAGE.md. All numbers in the dashboard come from
deterministic, tested code, not from a language model. (2) In the product: the optional "Ask the data" assistant uses
Google Gemini. It receives only excerpts of our verified results and of 12 public NASA technical reports (retrieved by
keyword search), must cite a source after every statement and say when the data do not cover a question; the app
checks every citation and flags numbers not found in the sources. Its behaviour on 10 test questions, including
off-topic and prompt-injection questions, is documented in docs/ASSISTANT_EVAL.md. No AI-generated images, video or
audio are used: the demo is a screen recording of the app, and NASA branding is not used or altered.

---

## Checklist before "Submit for Judging" (for Ruslan)

Target: everything submitted by **Sunday 10:00** (team goal; check the official deadline of the Uralsk local event in
the Space Apps Project Submission Guide).

1. Upload `docs/demo/prometheus-0g_demo.mp4` to YouTube (visibility "Unlisted" or "Public"; title "Prometheus-0g -
   Will it burn on the Moon? (NASA Space Apps 2026)"). Open the link in a private browser window - it must play
   without login.
2. Open https://prometheus-0g.streamlit.app/ in a private window: the overview loads, and "Ask the data" answers one
   question (if it says the free quota is used up, it resets at 11:00 Uralsk time).
3. Paste the fields from this file into the form: Project Name, High-Level Project Summary, Link to Project Demo
   (YouTube link), Link to Final Project (app link; the GitHub link is in the description), Detailed Project
   Description, NASA Data, Space Agency Partner & Other Data, Use of Artificial Intelligence.
4. Team: The Catalyst; member Ruslan Sharafutdinov; local event Uralsk; challenge "Flame in Freefall".
5. Tick the Terms and Conditions and the originality confirmation yourself (the work is ours; AI use is declared).
6. Read the preview once, then press **Submit for Judging** - the submission is final.
7. Close the GitHub secret-scanning alert as "Used in tests" (docs/WORKLOG.md, 19:02) so the public repository shows
   no open alert.

## Field lengths

<!-- COUNTS:BEGIN (generated) -->
| Field | Words | Characters |
|---|---|---|
| Project Name | 1 | 13 |
| High-Level Project Summary | 149 | 963 |
| Link to Project Demo | 29 | 222 |
| Link to Final Project | 7 | 115 |
| Detailed Project Description | 603 | 3785 |
| NASA Data | 295 | 1891 |
| Space Agency Partner & Other Data | 85 | 627 |
| Use of Artificial Intelligence | 178 | 1145 |
<!-- COUNTS:END -->
