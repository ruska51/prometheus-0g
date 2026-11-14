"""Method & sources (UI_SPEC page 8)."""
import streamlit as st

st.title("Method & sources")
st.markdown("""
**Pipeline.** NASA data -> verified tables -> physics -> calibration + machine learning -> validation -> ranked insights.

1. **Data.** NASA PSI repository: all 24 combustion investigations; FLEX (ISS droplet tests) checked cell by cell against
   NASA/TP-2015-216046 (0 differences); anomalies flagged, never silently fixed.
2. **Physics.** Quasi-steady droplet combustion with the Law & Williams (1972) property prescription: burning-rate constant
   `K = 8 lambda_1 / (rho_F c_1) ln(1 + B)`; fuel-vapour heat capacity, mixed conductivity (0.4 fuel vapour + 0.6 ambient gas),
   equilibrium flame temperature with dissociation. Property data from NIST and NASA reports.
3. **Hybrid model.** `ln K = ln K_theory + ln c_fuel + Gaussian-process correction` on conditions known before ignition only;
   95 % uncertainty band; labels "in range" / "extrapolation" / "unreliable".
4. **Validation.** Cross-validation grouped by test regime, leave-a-class-out extrapolation, physical sanity tests.
5. **Insights.** Ranked by `S = w_evidence x ln(1 + n_tests) x (0.3 + 0.7 e)`; evidence weights: NASA data 1.0, model 0.7,
   NASA literature 0.6, physics theory 0.5, NASA history 0.5, NASA spinoff 0.3. Investigations ranked by
   0.5 x fire-safety role + 0.3 x usable data + 0.2 x data size.

**Official challenge resources and how they are used**

| # | Resource | Use |
|---|---|---|
| R1 | NASA Physical Sciences Informatics (psi.nasa.gov) | all quantitative data: 24 investigations, FLEX, CFI-G, BASS-II, SAME-R tables |
| R2 | NASA SMA - Apollo 1 | lesson: pure O2 spreads fire, CO kills (linked to O2 and CO insights) |
| R3 | NASA SMA - Apollo 13 | lesson: oxygen systems + electrical heat as ignition source |
| R4 | NASA History - Mir fire 1997 | lesson: a real microgravity fire, smoke for hours, escape route blocked |
| R5-R7 | NASA Spinoff - air tanks, fire detector, fire attire | benefits on Earth |

**Other sources.** NASA NTRS reports (FLEX technical publication, Svehla 1962, RP-1311, TM-4513), NIST Chemistry WebBook,
Law & Williams (1972, Combustion and Flame), Cantera (equilibrium). Full list with licenses: `docs/DATA_SOURCES.md`.

**Use of AI.** Code, analysis and texts were produced with Claude Code (Anthropic) under the direction of the team member,
who made every scientific and design decision (`docs/DECISIONS.md`, `docs/AI_USAGE.md`). No AI-generated images.

**Limitations.** Two fuels from one experiment; ISS ambient about 298 K; no partial-gravity data exist in PSI; extinction
classifier weak outside tested atmospheres; the Earth (1 g) factor is an extrapolated physics estimate.

Repository: https://github.com/ruska51/prometheus-0g - code Apache-2.0; NASA data CC0 / public domain. No NASA endorsement implied.
""")
