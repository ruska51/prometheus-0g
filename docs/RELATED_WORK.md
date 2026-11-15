# Related work and other teams (checked 2026-11-14)

Ruslan asked whether anyone has built something similar. Searches on 2026-11-14 between 16:24 and 16:40 (UTC+5): web search
(4 queries) and the GitHub repository search API. Only public READMEs were read. **No code was copied or reused**
(CLAUDE.md section 3.2). Full search log: docs/RESEARCH_LOG.md.

## 1. Other Space Apps 2026 "Flame in Freefall" projects

The GitHub search for "flame in freefall" returned **114 public repositories**, created between 2026-09-17 and
2026-11-14 (the challenge is the same for every team). The 10 most relevant READMEs were read. Their recurring
features:

| Feature seen in other teams | How common (of the 10 read) | Prometheus-0g |
|---|---|---|
| Evidence dashboard over the PSI investigations (catalog, ranking, evidence labels) | almost all | yes (24 investigations, ranking formula, evidence badges) |
| LLM / RAG assistant over NTRS reports (Gemini, Claude) | several (at least 4) | no (stage 9 not built by decision) |
| ML models on FLEX (burning rate K, extinction) with grouped CV | 3 (e.g. ignis-lab: Ridge, MAE 0.047 mm²/s, R² 0.72; flex-explorer: random forest) | yes: hybrid MAE 0.045 mm²/s (R² 0.68 on ln K, not comparable with a linear-scale R²); equal to pure ML inside the data |
| Moon / Mars answers as bounds between 0 g and 1 g | 2 | yes (lunar 1/6 g bound, ADR-036) |
| 3D / animated flame visualisation | at least 2 (Three.js combustion chamber, 3D flame lab) | 2D canvas animation driven by computed d²-law, flame size and T_f |
| Audience views, briefing download, kids' version | 1-2 each | no |

## 2. What we did not find elsewhere (in the READMEs read)

- A **first-principles burning-rate model** (Law & Williams 1972 property prescription, fuel-vapour heat capacity,
  equilibrium flame temperature with dissociation) used as the backbone of the ML model, with **leave-a-class-out
  extrapolation tests** that measure the gain from physics on unseen atmospheres (1.2-1.9x lower error for He, CO2,
  ~0.7 atm and O2 >= 30 %). Other teams report CV inside the data only, where we also find no difference between
  physics-informed and pure ML.
- A **cell-by-cell verification of the PSI FLEX table against the NASA technical report** (3288 cells, 0 differences),
  plus two tests recovered from the report that are missing in PSI and a duplicated identifier resolved by evidence.
- **Pre-declared validation rules** (variant selection, extinction-label sensitivity) written before the runs.
- The lunar-gravity bound computed with the same buoyancy correlation and its fit range checked (Gr 0.7-0.8 at 1/6 g).

One other team (ALTAR-NASA) also describes a physics-informed solver (d²-law, de Ris, Burke-Schumann) with a reported
R² of 0.996 against NASA reference curves; its README does not describe held-out validation, so the results are not
comparable.

## 3. Literature

- Physics-informed ML for combustion is an active field (review: arXiv 2509.03347). The closest published droplet work
  we found is data-driven inverse modelling of droplet combustion (Xi, Torero, Jahn, Proc. Combust. Inst. 38, 2021).
  We found no paper that trains a physics-informed model on the FLEX data and tests extrapolation to new atmospheres.
- NASA itself compares FLEX burning rates and flame-standoff ratios with quasi-steady theory (NTRS 20130014061) but does
  not publish a predictive tool.

## 4. Consequence for the submission

Many teams will show dashboards, rankings and AI chat; our distinct claims for the jury are the physics backbone with
measured extrapolation gain, the verified data and the honest failure reporting. These belong in the README and the
demo (stage 12).

Sources: GitHub repository search API (query "flame in freefall"); READMEs of OSAMABASAM/NASA_flame_in_freefall,
Mohammed-Ayman-2023/Flame-in-FreeFall-NASA-Space-Apps, WingManOO7/ignis-lab, mnb60704-netizen/flex-explorer,
hibawaheed/ember-atlas, Faruk042/Nasa, Moaz-Hassanein/Flame-in-Freefall, Team-Efesto/Flame-in-freefall,
z1xO/flame-in-freefall, subhansh-dev/fleur; https://arxiv.org/pdf/2509.03347; https://discovery-pp.ucl.ac.uk/10106831/1/Xi-et-al-Deposited.pdf

## 5. Comparison with nasaprojecthsociety2.netlify.app (checked 2026-11-15 15:47-15:52 UTC+5)

Ruslan asked for a comparison with https://nasaprojecthsociety2.netlify.app/#home ("Flame in Freefall - knowledge base
and FlameAI agent"). Rendered in a headless browser; pages Home, Research catalog, Earth vs microgravity and FlameAI
read; one question asked to the agent. No code was copied.

| Aspect | That site | Prometheus-0g |
|---|---|---|
| Core | Knowledge base: 25 catalog entries (13 experiments, 4 models, 3 facilities, 2 technologies, 2 incidents, 1 program), timeline, 14 topic tags | Analysis of PSI data tables: FLEX, ACME CFI-G, BASS-II, SAME-R; 24 PSI investigations ranked |
| NASA PSI data | The pages read do not mention PSI or its data tables; sources are articles (NASA, ZARM/ESA, publications) | 276 FLEX tests checked cell by cell against NASA/TP-2015-216046 (3288 cells, 0 differences) |
| Model | Simplified thin-fuel flammability model ("calibrated to BASS-II and Ferkul 2026"); sliders for gravity, pressure, O2, ventilation; no validation shown. At "ISS, no flow" it shows "Radiative loss fraction 1.671" - a fraction above 1 | Physics + ML hybrid with grouped CV and leave-a-class-out tests; failures shown |
| Moon atmosphere | 8.2 psia / 34 % O2 ("Exploration Atmosphere") | 30 % O2 at 10.2 psi, as written in the challenge text (docs/challenge/CHALLENGE.md) |
| AI | "Offline" rule-based agent in the browser; a language model needs the user's own key. Asked "How much faster does a methanol droplet burn at 30% O2 and 10.2 psi than in ISS air?", it returned a generic fire-safety audit (requirements, response logic, 5x5 risk register) without a burning-rate number | Gemini assistant limited to our results and 12 NASA reports, with checked citations |
| Strengths over us | Breadth (cool flames, soot, drop towers, Saffire, SoFIE, Exploration Atmosphere); engineering outputs ("shall" requirements, risk register, response logic); interactive Earth vs microgravity view with Moon/Mars presets; polished design | - |
