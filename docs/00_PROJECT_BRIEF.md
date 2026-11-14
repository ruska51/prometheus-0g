# Project Brief - Prometheus-0g

**Tagline:** Physics-first, AI-assisted fire-safety insights from NASA microgravity combustion experiments.

Decisions: ADR-007 (scope), ADR-008 (personas), ADR-009 (product questions), ADR-010 (MVP), ADR-011 (name). Stage 1, 2026-11-14.

## Problem

NASA publishes results of low-gravity combustion experiments (mostly ISS) through the Physical Sciences Informatics (PSI) database, but "the amount of data can be overwhelming. It can be hard to find, harder to compare, and harder yet to interpret" (challenge Objectives). Fire behaves differently without buoyancy, and planned Moon Base and pressurized-rover atmospheres are expected at "30% or greater" oxygen and "10.2 psi or less" (challenge Considerations), which makes materials more flammable than in Earth air. Past fires (Apollo 1, Apollo 13, Mir; resources R2-R4) show what is at stake.

## Challenge analysis

**Explicit requirements** (Objectives): an AI-powered, web-based dashboard that summarizes, ranks and interprets combustion science investigations to deliver foundational fire-safety insights. Optional: identify investigations most relevant to habitable crew environments; extract data that supports predictive modeling of flammability; highlight research for next-generation fire-safety controls and equipment; Earth applications.

**Implicit jury expectations** (our reading, to be checked against judging):
- Built on PSI itself, not generic fire-safety text.
- Framed by NASA's prevention / detection / suppression triad (Background).
- Addresses the Moon Base / rover atmosphere, which the page spells out in numbers.
- Compares investigations (similarities, differences, shared hardware: ACME in CIR; FLEX/FLEX-2/CFI on MDCA in CIR; BASS/BASS-II/SPICE/SLICE in MSG).
- Honest about gaps: no partial-gravity data in PSI; rockets/propellants out of scope.
- Technical audience: professors, students, aerospace researchers and engineers.

**Keywords:** summarize, rank, interpret, foundational insights, fire safety, habitable crew environments, flammability limits, oxygen concentration, air flow, prevention / detection / suppression, Moon Base, pressurized rovers, partial gravity, Earth applications.

## Users

| ID | Persona | Task | Question the dashboard answers | Valuable insight |
|---|---|---|---|---|
| P1 | Cabin materials engineer (Moon Base / pressurized rover) | Select materials and set atmosphere limits | Which tested conditions burn or self-extinguish at elevated O2 and given airflow, and where does NASA have no data? | Flammability boundary vs O2 / pressure with evidence level and an extrapolation flag |
| P2 | Crew-safety specialist / mission planner | Choose cabin atmosphere and fire-response measures | How much riskier is a Moon-base atmosphere than ISS air, and which measures matter most? | Ranked prevention / detection / suppression insights, each with its evidence |
| P3 | Combustion researcher / graduate student | Find and compare investigations; get data for modeling | Which PSI investigations cover my conditions, what was measured, where are the files and papers? | Searchable, comparable catalog + extracted data + where theory fails (model residuals) |

## Key product questions

| ID | Question | Data needed | Data outlook (stage 1) |
|---|---|---|---|
| Q1 | Which investigations are most relevant to a given habitat (spacecraft, station, lunar base, rover) and fire-safety stage? | PSI metadata: objectives, hardware, conditions, publications | High: metadata of 25 studies in `data/raw/psi_metadata/` |
| Q2 | Under what atmosphere (O2, pressure, diluent) does a droplet flame self-extinguish or fail to ignite? | FLEX / FLEX-2 test tables | Medium: FLEX targets LOI vs pressure (ISA Approach); tables to be located in stage 2 |
| Q3 | Which diluent suppresses combustion better, CO2 or He? | FLEX tests with CO2 / He dilution | Medium: suppressants named in the FLEX objective; tables in stage 2 |
| Q5 | How much more flammable is a Moon-base atmosphere than ISS / Earth air, and is it inside the tested range? | Q2/Q3 data + calibrated model + tested-range envelope | Medium: answer outside tested range is labelled extrapolation |
| Q8 | Which research informs next-generation fire-safety equipment, and what are the Earth applications? | ISA "Research Impacts" fields + R5-R7 spinoffs | High (qualitative) |

Deferred to stretch: Q4 (solid-material flame spread, BASS/Saffire), Q6 (microgravity vs 1g, partial-gravity bounds), Q7 (smoke for detectors, SAME).

## Value

- One place to find, compare and rank NASA combustion investigations for a habitat and a fire-safety stage.
- Quantitative answers from a physics model calibrated on NASA data, with ML learning only what theory misses and showing its uncertainty.
- Every statement carries its evidence type (`NASA data` / `model` / `physics theory` / `NASA literature` / `NASA history` / `NASA spinoff`) and the number of tests behind it.

## Scope

**Option C (ADR-007):** catalog + ranking of all PSI combustion investigations from metadata, plus one deep physics-informed model on one dataset (default: FLEX-family droplets; final choice after stage 2).

## MVP (due Sat 2026-11-14 22:30, end of stage 8)

| ID | Item | Answers |
|---|---|---|
| M1 | Catalog of all combustion investigations in `data/raw/psi_metadata/` (PSI-108 and PSI-181 flagged as non-combustion): objective, fuel and geometry, hardware, platform, conditions (or "not stated"), measurements, publications, fire-safety stage tags | Q1, Q8 |
| M2 | Relevance ranking by habitat and fire-safety stage (formula approved by Ruslan) | Q1 |
| M3 | One hybrid model: calibrated physics + ML residual + uncertainty; grouped CV against 4 baselines (mean / physics only / ML only / hybrid); at least one extrapolation test | Q2, Q3 |
| M4 | Moon-base scenario: O2 / pressure input, in-range vs extrapolation flag, comparison with ISS and Earth air | Q5 |
| M5 | Ranked, evidence-tagged insights page | Q8 + model insights |
| M6 | Runs locally with one command (public deploy in stage 11) | - |

## Stretch (in order)

1. S5 - comparison matrix of investigations (similarities / differences). First pick if time remains (Ruslan).
2. S1 - solids flame spread (Q4).
3. S2 - microgravity vs 1g and partial-gravity bounds (Q6).
4. S3 - smoke for detectors, SAME (Q7).
5. S6 - Earth-applications page.
6. S4 - LLM assistant (off by default, CLAUDE.md section 9).

Order of S1-S4 and S6 is Claude's proposal; only S5 first was set by Ruslan.

## Not doing

- Rocket and propellant fire safety (out of PSI scope per the challenge footnote).
- Partial-gravity predictions presented as data (PSI has none); at most labelled bounds.
- CFD or detailed chemical-kinetics simulation.
- Data from outside NASA / partner sources as model input.
- NASA logos, flags or mission insignia in our materials.

## Success criteria

- All MVP items M1-M6 working by Sat 22:30.
- Every number in the UI and README traceable to a source.
- Validation reported honestly, including failures (VALIDATION.md).
- Submission complete by Sun 18:00.
