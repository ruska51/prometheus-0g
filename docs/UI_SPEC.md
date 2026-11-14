# UI Specification - Prometheus-0g dashboard

Stage 8 (2026-11-14), approved by Ruslan (ADR-034): structure and order as below, style B, headline "Prometheus-0g - Will it burn on the Moon?". Implemented in app/ (pages in app/views/); screenshots in docs/figures/ui/. Streamlit (ADR-001), multipage (`st.navigation`). The app only calls the `fif` package and reads generated artefacts (`docs/insights.json`, `docs/validation_results.json`, `models/*.joblib`, `data/processed/*.csv`); no physics in page code. Personas: P1 cabin materials engineer, P2 crew-safety specialist / mission planner, P3 combustion researcher (ADR-008).

Evidence badges everywhere: `NASA data` / `model` / `physics theory` / `NASA literature` / `NASA history` / `NASA spinoff`; reliability badges: `in range` / `extrapolation` / `unreliable` (ADR-031).

## Pages (proposed order)

### 1. Overview (home)
- Goal: in 10 seconds the jury knows the problem, what we built and the headline result.
- Users: all; jury first.
- Components: title + tagline; one-paragraph problem statement (microgravity flames, Moon-base atmosphere O2 >= 30 % at <= 10.2 psi); 4 metric tiles; top-3 insight cards with badges; two buttons: "Try the Moon-base scenario", "See how we validated".
- Metric tiles (computed live): PSI combustion investigations catalogued (24); FLEX ISS tests analysed (276, 0 differences vs the NASA report); hybrid model typical error (+-19 % in log space, grouped CV); extrapolation gain on new atmospheres (pure ML 1.2-1.9x worse).
- 10-second message: "NASA's ISS fire data, cleaned and verified, turned into ranked fire-safety insights - and a physics-based model that still works for the Moon-base atmosphere."

### 2. Insights
- Goal: summarize / rank / interpret (challenge objectives).
- Users: P2, P1.
- Components: stage filter (prevention / detection / suppression), ranked cards (title, finding, action, evidence badge, n tests, effect with 95 % CI, confidence, sources), "Lessons from history" (Apollo 1, Apollo 13, Mir - linked to data insights), "Benefits on Earth" (3 spinoffs).
- 10-second message: "Each recommendation shows how strong its evidence is."

### 3. Moon-base scenario (prediction)
- Goal: answer Q5 directly.
- Users: P1, P2.
- Components: presets (ISS air, Moon base, spacesuit, custom); inputs fuel, O2, pressure (atm and psi), diluent fraction (CO2 or He), droplet size; outputs: burning-rate constant from physics (Law & Williams) and hybrid with 95 % band, ratio vs ISS air, P(extinction) trend, reliability badge with reasons, "Earth vs ISS" factor (labelled physics theory, extrapolated); the FLEX tests nearest to the input.
- 10-second message: "A Moon-base atmosphere burns about a third faster than ISS air - and the tool tells you how far it is from tested conditions."
- "See it burn" window (ADR-035): two synchronized canvas panels - left = the selected atmosphere in microgravity, right = a selectable comparison (ISS air, Earth sea-level air at 1 g, Moon base, spacesuit, or the user's settings at 1 g). Real-time playback (1x / 2x / 4x, pause, replay). Shown values come from `fif.insights.flame_sim`: droplet diameter by the d^2-law, burn time, flame-out with unburned fraction (inside tested conditions only), flame temperature, soot colour (blackbody at T_f), theoretical flame size on a common relative scale with the NASA caveat; 1 g flame shape, flicker and sparks are labelled illustrative.

### 4. Risk map
- Goal: visual overview of the O2 x pressure space.
- Components: heatmap of hybrid burning rate relative to ISS air over O2 0.12-0.40 x pressure 0.3-1.1 atm (fuel selector); tested FLEX points overlaid; cabin atmospheres (ISS, Moon base, spacesuit) as labelled markers; region outside tested conditions greyed/hatched.
- 10-second message: "Where real cabin atmospheres sit relative to what NASA has actually tested."

### 5. Investigations (PSI catalog)
- Goal: M1/M2 - find and compare the 24 PSI combustion investigations.
- Users: P3.
- Components: relevance ranking by habitat need and fire-safety stage (rule in ADR-034), filters (stage, fuel type, platform, has data table), table (acronym, title, platform, hardware, dates, tests in table, publications, DOI, PSI link), detail panel (objective, approach, research impacts).
- 10-second message: "All 24 NASA combustion investigations in one searchable, ranked table."

### 6. Data explorer
- Goal: transparency - every number traceable.
- Users: P3.
- Components: FLEX table with filters (fuel, diluent, O2, pressure), scatter plots (K vs O2 by diluent; outcome map), quality flags shown, CSV download, source column (PSI-69 row / NASA TP page), CFI-G map.
- 10-second message: "The raw NASA numbers behind every insight, downloadable."

### 7. Validation
- Goal: Validity criterion.
- Components: repeated grouped-CV table (4 models), extrapolation table and chart, reliability diagram, physicality checks, largest errors with hypotheses; honest statement "hybrid = pure ML inside tested conditions, better for new atmospheres, no model for new fuels".
- 10-second message: "We show where the model fails."

### 8. Method & sources
- Pipeline diagram (data -> physics -> models -> validation -> insights), physics summary (Law & Williams prescription), resources R1-R7 and how each is used, licenses, use of AI, limitations, links to repository docs.

AI assistant: not built (stage 9 optional, CLAUDE.md section 9).

## Visual style options

| Option | Theme | Colours | Font | Character |
|---|---|---|---|---|
| A "Mission control" | dark | background #0B1220, panels #121A2B, primary cyan #22D3EE, flame amber #F59E0B, text #E5E7EB | Inter / system sans | technical, high contrast, looks like a control room |
| B "Clean science" | light | background #FFFFFF, panels #F5F7FA, primary deep blue #1D4ED8, flame orange #EA580C, text #111827 | IBM Plex Sans / system sans | paper-like, best for projectors and phones in daylight |
| C "Flame on navy" | dark | background #111827, primary flame orange #F97316, secondary teal #14B8A6, text #F9FAFB | system sans | warm, dramatic, fire theme |

Colour use: evidence badges with fixed colours (NASA data green, model blue, theory purple, literature grey, history brown, spinoff teal); reliability badges green / amber / red. No NASA logos, flags or mission insignia.

## Responsiveness

Wide layout on desktop; columns collapse on narrow screens (Streamlit stacks columns); charts use `use_container_width`; check at 390 px width.
