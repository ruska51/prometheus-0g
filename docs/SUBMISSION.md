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

Before NASA builds a Moon base, it has to know what a fire would do in the air planned for it: 30 % oxygen at 10.2
psi, richer than the ISS cabin, at one sixth of Earth's gravity. NASA has burned hundreds of fuel droplets on the ISS,
but the results are scattered across 24 investigations in its Physical Sciences Informatics repository. We checked all
276 FLEX droplet tests against NASA's own report (not one difference) and built a model that starts from the physics
of a burning droplet and lets machine learning correct only what theory misses; on atmospheres it never saw, it is
1.2-1.9 times more accurate than machine learning alone. The answer: in Moon-base air a fire burns about a third
faster, runs hotter and goes out on its own less often. Our public dashboard shows the numbers, animates the flame,
lets you sketch a Moon-base module and watch a fire spread at the rates NASA measured at lunar gravity, ranks 20
findings and 24 investigations, and has an AI assistant that answers only from NASA data.

---

## Link to Project Demo

https://github.com/ruska51/prometheus-0g/blob/main/docs/demo/prometheus-0g_slides.pdf

(7 slides including the title, in English; numbers and screenshots from the live app; no AI-generated imagery. GitHub
shows the PDF without login.)

---

## Link to Final Project

https://prometheus-0g.streamlit.app/

Source code, data and documentation: https://github.com/ruska51/prometheus-0g

---

## Detailed Project Description

**What it does.** Prometheus-0g is a public web dashboard that summarizes, ranks and interprets NASA's microgravity
combustion experiments and turns them into fire-safety advice for crewed habitats, above all the planned Moon base.
Its home page opens with the answer: "Fire on the Moon: faster, hotter, and less likely to go out by itself." Take a 3
mm methanol droplet, the size NASA burned in its FLEX experiment. In Moon-base air it burns 32 % faster than in ISS
air (our model; 95 % band -2 % to +77 %, marked as extrapolation), it is gone in 14.1 s instead of 18.5 s, and the
flame is 238 K hotter. Most important, in NASA's own tests at 30 % oxygen or more the flame went out by itself in 46 %
of cases, compared with 86 % at 21 % or less.

**How it works.** We started with the data. The PSI tables of FLEX (droplets), ACME CFI-G (gas flames), BASS-II
(burning solids) and SAME-R (smoke) are parsed and cleaned; anything odd is flagged, never quietly fixed, and every
raw file is registered with a checksum. We checked all 276 FLEX tests against NASA/TP-2015-216046 cell by cell: 3288
cells, no differences, and two tests missing from PSI were recovered from the report. Next comes physics: the classic
quasi-steady theory of a burning droplet with the Law & Williams (1972) property rules, the flame temperature from
chemical equilibrium with dissociation (Cantera with NASA thermodynamic data), and a buoyancy correction for Earth and
for the lunar surface at 1/6 g. The model builds on that theory: a fuel factor and a Gaussian-process correction learn
only what the theory misses, use only what is known before ignition, and report a 95 % band; separate classifiers
estimate the chance of self-extinction. Then we tried to break it. In cross-validation grouped by test regime (78
regimes) the hybrid's typical error is about 19 %. When a whole kind of atmosphere is hidden from training - helium,
CO2, about 0.7 atm, or Moon-like oxygen - physics makes the model 1.2-1.9 times more accurate than machine learning
alone. Where it fails (a fuel it has never seen, high pressure) we say so in the app. Finally, 20 findings are ranked
by the strength of their evidence, the number of tests and the size of the effect, and each is labelled as NASA data,
model, physics theory or NASA literature. Lessons from Apollo 1, Apollo 13 and Mir, and NASA spinoffs that help
firefighters on Earth, complete the picture.

**What users get.** You can build your own Moon-base atmosphere (any oxygen, pressure, diluent and droplet size) and
see the burning rate, how reliable the prediction is and which real NASA tests are closest. You can watch the same
droplet burn side by side in two atmospheres, with the animation driven by the model. The Moon-base fire designer
puts the whole design on one page: you lay out the base from modules (type and size class; areas and air volumes
are computed), see to scale which module a fire would threaten first, then draw a wall of a Moon-base module - fabric stowage bags, acrylic panels, metal racks, the hatch - pick where a fire starts
and watch it spread at the flame-spread rates NASA measured for those materials in microgravity (Saffire), at lunar
gravity (the LUCI sounding rocket) and on Earth, in test air or, scaled with NASA's flame-spread theory, in any cabin
atmosphere; the same fire burns side by side in the three gravities, the page shows when the flame reaches the hatch
in each case, what the fire does to the module air (a well-mixed zone model of the kind fire engineers use: oxygen,
CO2, heat and fire power, from NASA's oxygen and heat-release data; its oxygen-to-CO2 chemistry is checked against 66
BASS-II burns, where the measured CO2 + CO per O2 is 0.833, exactly the 5/6 that PMMA chemistry predicts), and
searches for the 50 cm metal strip that best protects the hatch (from this fire or from a fire starting anywhere; the
ventilation direction counts in microgravity), what NASA has found about solid materials at lunar gravity (quoted from
the reports) and a seven-point fire-safety checklist with the evidence for each point. It is a sketch on measured
rates, not a fire simulation, and says so. There is a risk map of oxygen against pressure, a ranked and searchable
catalog with a comparison matrix of all 24 PSI combustion investigations, and a data explorer where every raw NASA row
can be downloaded. And you can simply ask: "Ask the data" is an AI assistant that answers with numbers from our
results and 12 public NASA reports, shows the source of every statement, and says plainly when the data do not cover a
question. In the designer a Protect step also places detectors and extinguishers on the wall and gives the time until
a CO2 alarm sounds, and a Report step collects the base, the module, fire, air, protection, checklist and sources in
one downloadable report. An AI pilot, a glowing button in the corner of every page, on every page turns a request such as "detectors in the lab module in Moon-base air" into the
right page with its inputs set, from a fixed list the code checks. Pages are grouped into Start here, Moon base and
Evidence, each ends with a link to the next step, a
glossary explains every term, and a scenario or a design can be shared as a link. The
app opens in English and switches to Russian, and its dark style matches the demo slides.

**Benefits and impact.** Habitat and rover designers get measured, sourced reasons to plan for fires that are less
likely to go out on their own: suppress at once, sense CO alongside smoke, and do not rely on Earth-gravity material
tests alone, since NASA researchers expect lunar gravity to be nearly the most flammable condition for solids.
Researchers get a verified, reproducible FLEX dataset and an honest map of where the data stop. Students get an
interactive way to see how flames behave without gravity.

**How it is creative.** Many dashboards summarize NASA's data; ours also predicts beyond it, and measures how well.
The backbone is the classic theory of a burning droplet, and machine learning only learns the correction, so the model
stays sensible in atmospheres nobody has tested yet. We found no paper or public tool that trains a physics-informed
model on NASA's FLEX data and tests it on atmospheres it never saw. We also turned the data into the question a
habitat designer actually asks - what would a fire do on a Moon base? - and answer it with numbers and with a flame
you can watch burning in both atmospheres side by side, driven by the model.

**What we considered.** Scientific honesty first: the model uses only what is known before ignition, repeats of the
same test regime never sit in both the training and the test set, every finding carries its type of evidence and its
number of tests, predictions outside the tested range are marked as extrapolation, and the model's failures are shown
in the app. Trust in the AI part: the assistant may use only our verified results and NASA reports, every statement
links to its source, and numbers that cannot be found in the sources are flagged; if the free AI quota runs out, the
assistant still answers by quoting the most relevant verified facts directly, without AI, instead of showing an error.
Access: a free public web app that works on a phone, in English and Russian, with every raw NASA row downloadable; a
limit of 10 assistant questions per visitor keeps the free API quota shared fairly. Reproducibility and rights: one
command rebuilds everything from the raw NASA files; NASA data are public domain, our code is Apache-2.0, and no NASA
logos or branding are used.

**Tools.** Python 3.12, pandas, NumPy, SciPy, scikit-learn (Gaussian processes, logistic regression, gradient
boosting), Cantera, pdfplumber, Streamlit, Plotly, WebGL (flame animation), Google Gemini API (assistant), Playwright
(screenshots, slide PDF), pytest and ruff (199 tests, lint), GitHub, Streamlit Community Cloud (hosting). Code
Apache-2.0; NASA data CC0 / public domain. One command rebuilds data, models, insights and tests from the raw NASA
files.

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

We used AI in two places. First, to build the project: the code, data analysis, documentation and texts were
written with Claude Code (Anthropic, Claude Opus), directed by the team member, who made every scientific and design
decision - the level of theory, the property data, the model, the validation rules, the ranking formula and the
interface. Each decision is logged in docs/DECISIONS.md and each AI-assisted step in docs/AI_USAGE.md. Every number in
the dashboard comes from deterministic, tested code, not from a language model. Second, inside the product, Google
Gemini runs an AI pilot that opens pages and sets their inputs (it may only choose from a fixed list of pages and
allowed values, which the code checks, and it states no results itself), and the optional "Ask the data" assistant. It sees only excerpts of our verified results and of 12 public
NASA technical reports (found by keyword search), must name a source for every statement and must say when the data
do not cover a question; the app then checks every citation and flags any number it cannot find in the sources. How it
behaves on 10 test questions, including off-topic and prompt-injection attempts, is documented in
docs/ASSISTANT_EVAL.md. No AI-generated images, video or audio are used: the demo slides use screenshots of the app,
and NASA branding is not used or altered.

---

## Checklist before "Submit for Judging" (for Ruslan)

Target: everything submitted by **Sunday 10:00** (team goal; check the official deadline of the Uralsk local event in
the Space Apps Project Submission Guide).

1. Open the demo link (the slide PDF on GitHub) in a private browser window - it must open without login and show
   7 pages.
2. Open https://prometheus-0g.streamlit.app/ in a private window: the overview loads, and "Ask the data" answers one
   question (if it says the free quota is used up, it resets at 11:00 Uralsk time).
3. Paste the fields from this file into the form: Project Name, High-Level Project Summary, Link to Project Demo
   (slide PDF link), Link to Final Project (app link; the GitHub link is in the description), Detailed Project
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
| High-Level Project Summary | 180 | 1016 |
| Link to Project Demo | 24 | 234 |
| Link to Final Project | 7 | 115 |
| Detailed Project Description | 1383 | 8033 |
| NASA Data | 295 | 1891 |
| Space Agency Partner & Other Data | 85 | 627 |
| Use of Artificial Intelligence | 224 | 1356 |
<!-- COUNTS:END -->

## Form link lists (Link Text + Link Url)

The form asks for these two fields as lists of links. All URLs were opened on 2026-11-15 (HTTP 200; PSI pages checked in a browser to show the right investigation).

### NASA Data

| Link Text | Link Url |
|---|---|
| NASA Physical Sciences Informatics (PSI) - Combustion Science investigations (24 used for catalog and ranking) | https://psi.nasa.gov/physci/repo/search?q=combustion |
| PSI-69 FLEX - Flame Extinguishment Experiment, ISS droplet tests (models and insights) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-69 |
| PSI-159 ACME CFI-G - gaseous flame tests (ignition and self-extinction insights) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-159 |
| PSI-25 BASS-II - burning solids tests (CO insight) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-25 |
| PSI-101 SAME-R - smoke tests (detection insight) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-101 |
| NASA/TP-2015-216046 - Detailed Results from FLEX (used to verify every FLEX cell) | https://ntrs.nasa.gov/citations/20150023456 |
| Apollo 1 - NASA Safety & Mission Assurance (lesson) | https://sma.nasa.gov/sma-disciplines/accllp/apollo-1 |
| Apollo 13 - NASA Safety & Mission Assurance (lesson) | https://sma.nasa.gov/sma-disciplines/accllp/apollo-13 |
| Fire aboard Space Station Mir - NASA History (lesson) | https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/ |
| NASA Spinoff - Fireman's Air Tanks (benefits on Earth) | https://spinoff.nasa.gov/node/9582 |
| NASA Spinoff - Fire Detector (benefits on Earth) | https://spinoff.nasa.gov/node/9407 |
| NASA Spinoff - New Technology for the Fire Attire, Project FIRES (benefits on Earth) | https://spinoff.nasa.gov/node/9918 |
| NASA Technical Reports Server (NTRS) - report search for physics checks and the assistant | https://ntrs.nasa.gov |
| NTRS 20130014061 - Methanol Droplet Combustion in Oxygen-Inert Environments in Microgravity | https://ntrs.nasa.gov/citations/20130014061 |
| NTRS 20205008449 - Inert Gas Properties and Cool-Flame Combustion of Alkane Droplets | https://ntrs.nasa.gov/citations/20205008449 |
| NTRS 20210011385 - BASS-II Summary Report | https://ntrs.nasa.gov/citations/20210011385 |
| NTRS 20210021781 - Recent Research on Flames of Gaseous Fuel Aboard the ISS | https://ntrs.nasa.gov/citations/20210021781 |
| NTRS 20130000422 - Smoke Aerosol Measurement Experiment-2 results | https://ntrs.nasa.gov/citations/20130000422 |
| NTRS 20170007283 - Spacecraft Fire Safety Research at NASA Glenn | https://ntrs.nasa.gov/citations/20170007283 |
| NTRS 20170008805 - Results of Large-Scale Spacecraft Flammability Tests (Saffire) | https://ntrs.nasa.gov/citations/20170008805 |
| NTRS 20210020516 - Fire on the Moon: Solid Fuel Combustion Experiments | https://ntrs.nasa.gov/citations/20210020516 |
| NTRS 20260000646 - Material Flammability at Lunar and Martian Gravity | https://ntrs.nasa.gov/citations/20260000646 |
| NTRS 20250010653 - Lunar Combustion Investigation (LUCI) | https://ntrs.nasa.gov/citations/20250010653 |
| NTRS 20240008623 - Flammability of Materials on the Moon | https://ntrs.nasa.gov/citations/20240008623 |
| NTRS 20250004015 - lunar gravity 1/6 g (value used for the lunar-surface case) | https://ntrs.nasa.gov/citations/20250004015 |
| NASA TR R-132 - Svehla 1962, gas viscosities and conductivities | https://ntrs.nasa.gov/citations/19630012982 |
| NASA RP-1311 - Gordon & McBride 1994, mixture property rules | https://ntrs.nasa.gov/citations/19950013764 |
| NASA TM-4513 - McBride, Gordon & Reno 1993, thermodynamic data | https://ntrs.nasa.gov/citations/19940013151 |
| NASA Glenn photo GRC-1998-C-00485 - visual reference for the flame drawing (not embedded) | https://images.nasa.gov/details/GRC-1998-C-00485 |

### Space Agency Partner & Other Data

| Link Text | Link Url |
|---|---|
| No Space Agency Partner data used - NIST Chemistry WebBook (fuel and gas properties) | https://webbook.nist.gov |
| Law & Williams 1972, Combustion and Flame 19 - droplet property rules (cited, not redistributed) | https://doi.org/10.1016/0010-2180(72)90009-0 |
| Wyman, Sloan & Shirley 2013, JCGT - CIE colour approximation (flame colour) | https://jcgt.org/published/0002/02/01/ |
| Cantera - chemical equilibrium (flame temperature) | https://cantera.org |
| Python libraries: NumPy | https://numpy.org |
| pandas | https://pandas.pydata.org |
| SciPy | https://scipy.org |
| scikit-learn (Gaussian processes, classifiers) | https://scikit-learn.org |
| pandera (data schema checks) | https://pandera.readthedocs.io |
| pdfplumber (reading NASA report tables) | https://github.com/jsvine/pdfplumber |
| Matplotlib | https://matplotlib.org |
| Plotly (charts) | https://plotly.com/python/ |
| Streamlit (web app) | https://streamlit.io |
| Streamlit Community Cloud (hosting) | https://streamlit.io/cloud |
| Google Gemini API (Ask-the-data assistant) | https://ai.google.dev/gemini-api/docs |
| Claude Code by Anthropic (AI coding and writing assistant) | https://www.anthropic.com/claude-code |
| Playwright (screenshots, slide PDF) | https://playwright.dev/python/ |
| pytest (tests) | https://docs.pytest.org |
| Ruff (lint) | https://docs.astral.sh/ruff/ |
| segno (QR code on the slides) | https://github.com/heuer/segno |
| OpenCV (QR code check) | https://opencv.org |
| Google Fonts - Space Grotesk (slides) | https://fonts.google.com/specimen/Space+Grotesk |
| Google Fonts - Inter (slides) | https://fonts.google.com/specimen/Inter |
| GitHub (code repository) | https://github.com |
