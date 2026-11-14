# Data Sources

Format: ID | full reference | URL / DOI | what we took | license / terms | accessed.

## 1. Registered sources

| ID | Reference | URL | What we took | License / terms | Accessed |
|---|---|---|---|---|---|
| R1 | NASA Physical Sciences Informatics (PSI) repository, combustion search | https://psi.nasa.gov/physci/repo/search?q=combustion | Investigation list and records via the public web service used by the page (`/geode-py/ws/repo/search`, `/geode-py/ws/repo/investigations/<id>`); Experimental Table CSVs | CC0-1.0 per investigation record (`licenseIdentifier`); PSI-10 record has no license field (to check) | 2026-11-14 |
| R2 | NASA Office of Safety and Mission Assurance, "Apollo 1" | https://sma.nasa.gov/sma-disciplines/accllp/apollo-1 | Qualitative lessons (NASA history) | NASA web content | 2026-11-14 |
| R3 | NASA Office of Safety and Mission Assurance, "Apollo 13" | https://sma.nasa.gov/sma-disciplines/accllp/apollo-13 | Qualitative lessons (NASA history) | NASA web content | 2026-11-14 |
| R4 | NASA History, "25 Years Ago: Fire Aboard Space Station Mir" | https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/ | Qualitative lessons (NASA history) | NASA web content | 2026-11-14 |
| R5 | NASA Spinoff, "Fireman's Air Tanks" (1976) | https://spinoff.nasa.gov/node/9582 | Impact context (NASA spinoff) | NASA web content | 2026-11-14 |
| R6 | NASA Spinoff, "Fire Detector" (1978) | https://spinoff.nasa.gov/node/9407 | Detection + Impact context (NASA spinoff) | NASA web content | 2026-11-14 |
| R7 | NASA Spinoff, "New Technology for the Fire Attire" (1982) | https://spinoff.nasa.gov/node/9918 | Impact context (NASA spinoff) | NASA web content | 2026-11-14 |
| PSI-meta | 25 PSI ISA-Tab metadata archives (PSI-10 ... PSI-181), downloaded manually by Ruslan | `data/raw/psi_metadata/` | Study descriptions, publication lists | as R1 | 2026-11-14 |
| PSI-rec | 24 PSI Combustion Science investigation records (JSON) + full repository search response | `data/raw/psi_records/` (fetched by `scripts/fetch_psi.py`) | Catalog fields, file lists, licenses | as R1 | 2026-11-14 |
| PSI-tab | 22 PSI Experimental Table CSVs for 20 investigations | `data/raw/psi_tables/` (fetched by `scripts/fetch_psi.py`; sha256 in `MANIFEST.tsv` and `data/catalog.yaml`) | Test conditions and outcomes | as R1 | 2026-11-14 |
| NTRS | NASA Technical Reports Server API | https://ntrs.nasa.gov/api/citations/search | Report search | Public, no login | 2026-11-14 |
| TP-FLEX | Dietrich, D. L.; Ferkul, P. V.; Bryg, V. M.; Nayagam, M. V.; Hicks, M. C.; Williams, F. A.; Dryer, F. L.; Shaw, B. D.; Choi, M. Y.; Avedisian, C. T. "Detailed Results From the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011." NASA/TP-2015-216046, Nov. 2015 | https://ntrs.nasa.gov/citations/20150023456 | Test matrices (Tables I-VIII) and results (Table IX) to cross-check PSI-69 CSV; PDF not in git (42.9 MB), sha256 in catalog (`ntrs_flex_tp`), fetched by `scripts/verify_flex_vs_tp.py` | NASA technical report | 2026-11-14 |
| NIST-SRD69 | NIST Chemistry WebBook, NIST Standard Reference Database 69 (Linstrom & Mallard, eds.): fluid properties (isobaric 1 atm 300-1500 K for O2, N2, CO2, He; saturation tables for methanol, n-heptane, water), species pages (molecular weight, Delta_c H liquid) | https://webbook.nist.gov (files in `data/raw/nist/`, `scripts/fetch_nist.py`) | All property values of the physics layer (PHYSICS.md section 6) | NIST Standard Reference Data, public | 2026-11-14 |
| NTRS-Nayagam | Nayagam, V.; Dietrich, D. L.; Hicks, M. C.; Williams, F. A. "Methanol Droplet Combustion in Oxygen-Inert Environments in Microgravity", 5th US Combustion Meeting paper 070HE-0303 | https://ntrs.nasa.gov/citations/20130014061 | Quasi-steady K and B equations (Eqs. 1-2); water-absorption explanation | NASA technical report | 2026-11-14 |
| RP-1311 | Gordon, S.; McBride, B. J. NASA RP-1311, Part I: Analysis (1994) | https://ntrs.nasa.gov/citations/19950013764 | Mixture viscosity / conductivity rules, Eqs. 5.3-5.6 | NASA technical report | 2026-11-14 |
| LawWilliams1972 | Law, C. K.; Williams, F. A. "Kinetics and convection in the combustion of alkane droplets", Combustion and Flame 19 (1972) 393-405 | https://doi.org/10.1016/0010-2180(72)90009-0 (DOI via Crossref) | Read in full (copy supplied by Ruslan, kept locally in gitignored data/raw/literature/); property prescription, buoyancy correction (ADR-027) | Elsevier (copyrighted, not redistributed) | 2026-11-14 |
| Svehla1962 | Svehla, R. A. "Estimated Viscosities and Thermal Conductivities of Gases at High Temperatures", NASA TR R-132 (1962) | https://ntrs.nasa.gov/citations/19630012982 | Eq. (2); CH3OH Table III p. 56; n-C5H12, n-C6H14 viscosity Table IV p. 119 (transcribed) | NASA technical report | 2026-11-14 |
| TM-4513 | McBride, B. J.; Gordon, S.; Reno, M. A. "Coefficients for Calculating Thermodynamic and Transport Properties of Individual Species", NASA TM-4513 (1993) | https://ntrs.nasa.gov/citations/19940013151 | Thermo data for the equilibrium flame temperature (via Cantera nasa_gas.yaml) | NASA technical report | 2026-11-14 |
| NTRS-WN2020 | Williams, F. A.; Nayagam, V. cool-flame QS theory presentation | https://ntrs.nasa.gov/citations/20205008449 | Statement that QS theory needs an empirical property prescription (L&W) | NASA | 2026-11-14 |
| Cantera | Cantera 3.2.0, open-source chemical kinetics/thermodynamics library | https://cantera.org | HP equilibrium solver | BSD-3-Clause | 2026-11-14 |
| CH-atm | Challenge page "Flame in Freefall" (pasted by Ruslan, docs/challenge/CHALLENGE.md): Moon base O2 "30% or greater" at "10.2 psi or less"; spacesuit "100% oxygen to only 4.3 psi"; sea level 14.7 psi | docs/challenge/CHALLENGE.md | Cabin-atmosphere comparison (INSIGHTS.md) | NASA Space Apps challenge text | 2026-11-14 |
| TP-cabin-air | NASA/TP-2015-216046 Table I: FLEX tests "in cabin air", 0.21 O2, 0.005 CO2, 0.79 N2 at 1.0 atm | https://ntrs.nasa.gov/citations/20150023456 | ISS cabin-air reference atmosphere | NASA technical report | 2026-11-14 |
| TM-BASS-II | "Burning and Suppression of Solids-II (BASS-II) Summary Report", NASA Technical Memorandum (NTRS 20210011385) | https://ntrs.nasa.gov/citations/20210011385 | Candidate source of flame-spread / extinction-velocity tables (stretch) | NASA technical report | 2026-11-14 |

## 2. Candidate datasets (PSI Combustion Science, 24 investigations)

Sources: PSI investigation records and Experimental Table CSVs (2026-11-14). "Tests" = data rows in the Experimental Table (header excluded). Raw data volume = `totalFileSize` in the PSI record (images/telemetry, not downloaded).
Usefulness (U, 1-5) for our product questions Q1/Q2/Q3/Q5/Q8; effort (E, 1-5, 5 = most work) to turn it into model-ready data.

| PSI-id | Acronym | Type | Tests | Inputs (conditions) | Numeric outcomes | Format / access | Theory for physics layer | U | E | Role (ADR-012/013) |
|---|---|---|---|---|---|---|---|---|---|---|
| PSI-69 | FLEX | droplets | 274 | fuel (methanol 157 / heptane 117), pressure (mmHg), O2/N2/CO2/He mole fractions, initial droplet diameter | **yes**: test end (Extinction 186 / Disruption 61 / Completion 27), visible flame extinction diameter (197 values), burning rate (258), burn time (266) | CSV 24.8 KB, CC0, open; raw 923.8 GB | d2-law, quasi-steady burning, radiative / diffusive extinction (FORMULAS.md sections 2-3) | 5 | 2 | **primary model dataset** |
| PSI-159 | ACME CFI-G | gaseous (spherical diffusion flames, normal + inverse) | 179 + 154 | fuel (ethane, propane, butane, diluted), XO2 (normal 0.18-0.40; inverse 0.12-0.85), pressure 0.50-3.31 bar, flow rates | **yes**: hot ignition (yes/no/flash), burn time, self-extinction vs flow termination, peak burner T; cool flame flag (normal) | 2 CSV 22.2 + 39.4 KB, CC0, open; raw 2085.6 GB | Burke-Schumann flame sheet; Tad and Zst already in the table | 4 | 3 | **auxiliary**: ignition / self-extinction map vs O2 and pressure, no separate ML model |
| PSI-25 | BASS-II | solids (51 materials) | 129 | material, flow restrictor, fan/air display, radiometer gain, initial O2, CO2, CO | partial: final O2, CO2, CO (consumption / products); no spread rate | CSV 16.6 KB, CC0, open; raw 274.6 GB | de Ris flame spread (FORMULAS.md section 4) - needs spread rates from TM-BASS-II | 3 | 4 | catalog now; candidate if time remains (Ruslan) |
| PSI-26 | BASS | solids | 122 | date, test #, sample #, material | none | CSV 4.7 KB, CC0, open; raw 163.6 GB | de Ris | 2 | 5 | catalog only |
| PSI-98 | SAFFIRE-I | large-scale solid fire | 4 | material, thickness, length, width, air flow, O2 %, ignition power/time, flow direction | burn time (4 values) | CSV 0.5 KB, CC0, open; raw 12.3 GB | de Ris / concurrent spread | 2 | 2 | catalog only (N too small) |
| PSI-99 | SAFFIRE-II | large-scale solid fire | 15 | as Saffire-I; silicone, PMMA variants | burn time, low-g burn/spread length, 1-g burn length / spread rate (mixed text) | CSV 2.0 KB, CC0, open; raw 16.9 GB | concurrent spread; low-g vs 1-g | 2 | 3 | catalog only |
| PSI-100 | SAFFIRE-III | large-scale solid fire | 2 | material, size, flow 30 cm/s, direction | none | CSV 0.2 KB, CC0, open; raw 35.2 GB | - | 1 | 1 | catalog only |
| PSI-102 | SAME | smoke | 8 | material, air flow, weight-loss rate, aging duration | none (particle sizes not in table) | CSV 0.3 KB, CC0, open; raw 0.7 GB | - | 2 | 4 | catalog only |
| PSI-101 | SAME-R | smoke | 109 | sample type (5 materials), inlet velocity, duration, aging/mixing times | Rt/R0 (meaning to check); no particle sizes | CSV 5.7 KB, CC0, open; raw 6.3 GB | - | 2 | 4 | catalog only |
| PSI-47 | DAFT / DAFT-2 | dust | 2 | session, hardware, sample material, location | none | CSV 0.5 KB, CC0, open | - | 1 | 1 | catalog only |
| PSI-39 | CFI | droplets (cool flames) | 87 | pressure, O2 (0.17-0.21), N2, He, fiber, fuel (dodecane / iso-dodecane blends) | none in table | CSV 7.8 KB, CC0, open; raw 718.9 GB | d2-law; cool-flame chemistry | 2 | 5 | catalog only |
| PSI-68 | FLEX-2 | droplets | 8 (one row per fuel, ranges) | fuel, d0 range, gas mixture, O2 set, pressure set, T, flow | none (ranges only) | CSV 1.0 KB, CC0, open; raw 1224.8 GB | d2-law | 2 | 5 | catalog only |
| PSI-10 | ACME Flame Design | gaseous | 207 + 120 | fuel, Xfuel, flows, XO2, pressure, Zst, Tad | none (conditions + computed Tad/Zst) | 2 CSV 26.9 + 17.3 KB; license field missing in record; raw 2180.4 GB | Burke-Schumann | 2 | 4 | catalog only |
| PSI-20 | ACME BRE | gaseous burner emulating solids | 18 (test days) | burner size, fuel bottle, O2 % (lists), flames ignited count | none | CSV 1.1 KB, CC0, open; raw 2035.6 GB | burning-rate emulation | 2 | 4 | catalog only |
| PSI-21 | ACME CLD Flame | gaseous co-flow | 32 (test days) | fuel bottle, concentration range, flames ignited | none | CSV 2.5 KB, CC0, open | Roper (FORMULAS.md section 5) | 1 | 4 | catalog only |
| PSI-22 | ACME E-FIELD Flames | gaseous + electric field | 32 (test days) | mesh polarity, fuel conc., flames ignited | none | CSV 2.5 KB, CC0, open | - | 1 | 4 | catalog only (partial-g analogue mentioned in CH) |
| PSI-23 | ACME s-Flame | gaseous | 18 (test days) | atmosphere, fuel bottle, flames ignited | none | CSV 2.5 KB, CC0, open | - | 1 | 4 | catalog only |
| PSI-106 | SLICE | gaseous lifted flames | 12 (test days) | test date, fuel type | none | CSV 0.7 KB, CC0, open | - | 1 | 4 | catalog only |
| PSI-107 | SPICE | gaseous co-flow (smoke point) | 469 | fuel, nozzle diameter, fuel rate, air co-flow rate, ignition/off times | none (smoke point not a column) | CSV 31.2 KB, CC0, open; raw 6.9 GB | smoke-point correlations (not in FORMULAS.md) | 2 | 4 | catalog only |
| PSI-142 | (cool-flame transitions, ground) | droplets, analysis | 8 | pointers to figures in publications | none (figure references) | CSV 0.7 KB, CC0, open | - | 1 | 5 | catalog only |
| PSI-60 | (SPICE data analysis, ground) | gaseous, analysis | - | no Experimental Table | - | record only | - | 1 | - | catalog only |
| PSI-62 | (concurrent flame-spread modeling, ground) | solids, modeling | - | no Experimental Table | - | record only | - | 1 | - | catalog only |
| PSI-115 | (SAME data utilization, ground) | smoke, analysis | - | no Experimental Table | - | record only | - | 1 | - | catalog only |
| PSI-117 | (cool flames, thermo-convective perturbation, ground) | droplets, analysis | - | no Experimental Table | - | record only | - | 1 | - | catalog only |

Not in PSI Combustion Science: SoFIE (NTRS presentation 20200000361 only), PSI-108 STDCE-1 (Fluid Physics), PSI-181 solder (Materials Science). Related but other research area: PSI-179 ASE (Aerosol Sampling Experiment, Complex Fluids).

## 3. NTRS reports scanned for tables (2026-11-14)

10 queries from the stage-2 prompt, top 6 results each, PDF text scanned for "Table N" captions. Full log: RESEARCH_LOG.md.

| NTRS id | Report | Tables found | Relevance |
|---|---|---|---|
| 20150023456 | NASA/TP-2015-216046, FLEX detailed results (315 pp.) | Tables I-VIII test matrices (pp. 16-21); **Table IX results by test** (p. 26 on): test, identifier, date, GMT, fuel, pressure mmHg, O2/N2/CO2/He, d0, extinction diameter, burning rate mm2/s, burn time, test end | Stage 3: full cross-check of all 274 CSV rows (pdfplumber word coordinates + rendered pages), 0 value differences; see DATA_QUALITY.md section 3. Table I (test matrix) lists D0 = 1.80 mm for test 001 while Table IX and the CSV give 1.69 mm: Table I is the planned matrix, Table IX the measured value (App. A.1 defines D0 at igniter ON) |
| 20210011385 | BASS-II Summary Report, NASA TM (145 pp.) | Table 2.1 extinction velocity comparison (p. 36); 4.1 rod diameters, 4.2 oxidizer/flow ranges (pp. 55-56); 5.1 twenty BASS-II tests (p. 65); 7.1 SIBAL concurrent-flow test summary (p. 104) | Stretch (BASS-II spread / extinction). Columns not inspected yet |
| 20180005168 | Saffire presentation (33 pp.) | Table 1 summary of samples, test conditions, selected results (pp. 30-31) | Catalog / insights. Not inspected |
| 20170001636 | Saffire objectives, development and status | Tables 1-5 (samples, diagnostics, environment, dates, objectives) | Catalog. Not inspected |
| 20130000422 | SAME-2 particle morphology and size | Table 1 diameter results for baseline runs per material (p. 7) | Stretch S3 (smoke). Not inspected |
| 20210021781 | Recent research on gaseous flames aboard ISS | Tables 1-2 lists of past / recent experiments | Catalog context |
| others | ACME posters, SoFIE presentation, flame-spread papers, workshop proceedings | none relevant / no PDF | - |

## 4. Selected datasets (ADR-012, ADR-013)

| Role | Dataset | Files (`data/raw/psi_tables/`) | Use |
|---|---|---|---|
| Primary | PSI-69 FLEX | `PSI-69_Experimental table_FLEX.csv` | Hybrid model of burning rate K (d2-law + ML residual) and extinction classifier; Q2, Q3, Q5 |
| Auxiliary | PSI-159 ACME CFI-G | `PSI-159_Experimental table_CFI-G_Normal Flames.csv`, `PSI-159_Experimental table_CFI-G_Inverse Flames.csv` | Ignition / self-extinction map vs O2 and pressure (NASA data + Tad/Zst), high-O2 evidence for Q5 |
| If time remains | PSI-25 BASS-II | `PSI-25_Experimental table_BASS-II.csv` (+ TM-BASS-II tables) | O2 consumption and CO/CO2 products |
| Catalog only | all other investigations above | their Experimental Tables + records | M1 catalog: conditions, number of tests, ranking |

## 5. Visualisation references (flame animation, ADR-035)
| Source | Used for | Access |
|---|---|---|
| Wyman C., Sloan P.-P., Shirley P. "Simple Analytic Approximations to the CIE XYZ Color Matching Functions", Journal of Computer Graphics Techniques 2(2), 2013 | colour of a blackbody at T_f (soot glow), `fif.insights.flame_sim.blackbody_srgb` | open access, 2026-11-14 |
| IEC 61966-2-1 sRGB (XYZ -> linear sRGB matrix and transfer curve) | same | standard, 2026-11-14 |
| CODATA / SI 2019 exact constants h, c, k | Planck's law | 2026-11-14 |
| NTRS 20130014061 section 3.2 | flame-size caveat | NTRS, 2026-11-14 |

## 6. Partial gravity (ADR-036)
| Source | Used for | Access |
|---|---|---|
| NTRS 20250004015, "Simulated Lunar Gravity Testing of VIPER Loop Heat Pipe" (NASA) | g_Moon / g_Earth = 1/6 | NTRS API, 2026-11-14 |
| NTRS 20210020516, "Fire on the Moon: Solid Fuel Combustion Experiments" (NASA GRC) | insight P6 quote | NTRS API, 2026-11-14 |
| NTRS 20260000646, Ferkul, Kralik, Liao, "Material Flammability at Lunar and Martian Gravity", LPSC 2026 | insight P6 quote, FM2 | NTRS API, 2026-11-14 |
