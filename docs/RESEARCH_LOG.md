# Research Log

Format: time (UTC+5) | question | where | query | found | link | conclusion.
Quotes are at most 15 words. Evidence types per CLAUDE.md section 4.

---

## 2026-11-14 11:00 | Environment: is the NTRS API reachable?
- Where: NTRS API
- Query: `GET https://ntrs.nasa.gov/api/citations/search?q=microgravity%20combustion&page.size=3`
- Found: HTTP 200 in ~1.8 s; `stats.total` = 1077; top hits 20150023100 "NASA Microgravity Combustion Program", 19970020547 "Fourth International Microgravity Combustion Workshop", 19990053965 "Fifth International Microgravity Combustion Workshop".
- Conclusion: NTRS API usable without login.

## 2026-11-14 11:15 | R1-R7 availability check

| # | HTTP | Readable by static fetch | Note |
|---|---|---|---|
| R1 | 200 | No | Angular single-page app: the HTML is an empty `<app-root>` shell. Study list supplied by Ruslan instead (see the inventory entry below). |
| R2 | 200 | Yes | |
| R3 | 200 | Yes | |
| R4 | 200 | Yes | |
| R5 | 200 | Yes | |
| R6 | 200 | Yes | |
| R7 | 200 | Yes | |

### R2 - Apollo 1 (NASA history)
URL: https://sma.nasa.gov/sma-disciplines/accllp/apollo-1 (accessed 2026-11-14)
- 27 Jan 1967 pad test, hatches closed, "cabin pressurized with 100% oxygen".
- "a flash fire swept through the spacecraft so quickly, there was no time to open the hatches."
- Cause of death: "asphyxia from carbon monoxide and other toxic gases"; "Their burns were likely survivable."
- Ignition source not determined; "evidence of arcing in several wires" near the environmental control system.
- "Because of the pure oxygen atmosphere, the fire spread quickly" -> pressure vessel rupture.
- Three-piece hatch: 90 s to open in ideal conditions, "impossible to open under increased pressure".
- Response: unified hatch openable "within three seconds"; combustible materials "severely restricted and controlled"; fire-resistant spacesuits.

### R3 - Apollo 13 (NASA history)
URL: https://sma.nasa.gov/sma-disciplines/accllp/apollo-13 (accessed 2026-11-14)
- Oxygen-tank heater voltage raised from 28 to 65 V DC; thermostatic switches "weren't modified to suit this change."
- Heaters reached ~1000 °F during a pad test, "degrading the Teflon insulation"; tank damaged by eight hours of overheating.
- Oxygen tank no. 2 exploded on day 3 and damaged tank no. 1.
- Board recommended redesign of the SM oxygen storage system and review of all cryogenic-oxygen systems.
- Fix: third tank in another bay, upgraded thermostats, stirring fans removed, "sheathing all electrical wiring in stainless steel".
- Apollo 1 lesson reused: added wiring insulation prevented arcing at CM power-up.

### R4 - Mir fire, 24 Feb 1997 (NASA history)
URL: https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/ (accessed 2026-11-14)
- Source: solid-fuel oxygen generator (SFOG, lithium perchlorate canister) in Kvant-1; six crew aboard.
- Canister ignited, "shooting a three-foot flame with sparks and bits of molten metal".
- "The flame blocked the evacuation route to the Soyuz spacecraft".
- Crew used oxygen masks and foam extinguishers; "The flame finally extinguished itself". Flag: the page summary says the crew "extinguished the flames"; wording differs within the page.
- Life support cleared the smoke "over several hours"; panels charred, no structural damage.
- Canisters used "without incident more than 2,500 times"; likely cause: "latex working glove material" (hydrocarbons) in the canister.
- Lessons passed to ISS design and operations; ISS has dissimilar-redundant oxygen generation.

### R5 - Fireman's Air Tanks, 1976 (NASA spinoff)
URL: https://spinoff.nasa.gov/node/9582 (accessed 2026-11-14)
- Developed with NASA Johnson Space Center by Scott Aviation (A-T-O Inc.).
- "20 pounds for 30 minute air supply, 13 pounds less than conventional"; 4,500 psi.
- Aluminum liner wrapped in resin-impregnated glass fibers. Use: Impact section only.

### R6 - Fire Detector, 1978 (NASA spinoff)
URL: https://spinoff.nasa.gov/node/9407 (accessed 2026-11-14)
- Brunswick Incipient Fire Detector, "originally used in space shuttle orbiters".
- Discriminates combustion particles from dust: "less susceptible to false alarms".
- Signals fire "before appearance of flame and smoke". Use: detection stage + Impact.

### R7 - New Technology for the Fire Attire, 1982 (NASA spinoff)
URL: https://spinoff.nasa.gov/node/9918 (accessed 2026-11-14)
- Project FIRES, jointly sponsored by NASA and FEMA's U.S. Fire Administration; managed by Marshall SFC.
- Uses "lightweight, fire-resistant, heat-protective materials" originally developed for space suits.
- Field evaluation with fourteen municipal fire departments. Use: Impact + materials theme.

## 2026-11-14 11:20 | Inventory of `NASA PSI data/` (supplied by Ruslan)
- Where: local folder `NASA PSI data/` (25 zip archives + 1 PDF, 5.5 MB total).
- Found: each zip = ISA-Tab metadata only (`i_Investigation.txt` + a placeholder `s_PSI-xx.txt` whose rows read "Do not use this"). **No measurement tables, no assay files; `Data Source Link` is empty in all 25.**
- Useful content per study: title, acronym, approach, hypothesis, objective, hardware, platform, dates, study DOI (10.60555/...), publication list with DOIs / NTRS links.
- Studies (publications listed; NTRS links among them): PSI-10 ACME/Flame Design (33), PSI-20 ACME BRE (16), PSI-21 ACME CLD Flame (18), PSI-22 ACME E-FIELD (25), PSI-23 ACME s-Flame (44), PSI-25 BASS-II (17; 2 NTRS), PSI-26 BASS (10; 2 NTRS), PSI-39 CFI (7), PSI-47 DAFT/DAFT-2 (2), PSI-60 SPICE data analysis (1), PSI-62 concurrent flame-spread modeling (4), PSI-68 FLEX-2 (48), PSI-69 FLEX (51; 5 NTRS), PSI-98 SAFFIRE-I (6; 2 NTRS), PSI-99 SAFFIRE-II (7; 1 NTRS), PSI-100 SAFFIRE-III (3; 1 NTRS), PSI-102 SAME (16; 2 NTRS), PSI-106 SLICE (5), PSI-107 SPICE (9; 1 NTRS), PSI-108 STDCE-1 (15; 5 NTRS), PSI-115 SAME data utilization (0), PSI-117 cool flames under thermo-convective perturbation (10), PSI-142 cool-flame transitions (10), PSI-159 ACME CFI-G (2), PSI-181 Pb-Sn solder microstructure (0).
- Flags: PSI-108 (surface-tension-driven convection, Space Shuttle) and PSI-181 (solder alloys) are not combustion studies. Publication count = non-empty titles in the ISA file.
- PDF `SAME EIRD Rev 2.00 02-25-05 HIgh Q.pdf` (5.4 MB): not read yet.
- Conclusion: data tables must come from PSI file downloads (Ruslan) or from the linked NTRS reports. Detailed recon = stage 2.

## 2026-11-14 11:29 | Stage 1: is there hope of data for each product question?
- Where: ISA `Comment[Objective]` / `Comment[Approach]` in `data/raw/psi_metadata/`; NTRS API.
- Found in ISA text (test-condition ranges stated by NASA):
  - FLEX (PSI-69): goal is the Limiting Oxygen Index vs ambient pressure and suppressant effect; suppressants CO2, He, SF6 named in the objective.
  - FLEX-2 (PSI-68): pressure 0.5-3.0 atm, O2 mole fraction 0.1-0.4, diluent balance.
  - CFI (PSI-39): chamber 0.25-0.5 atm; droplets on needles or SiC fibers.
  - BASS-II (PSI-25): flow speeds up to 40 cm/s; "Main variables are airflow speed and oxygen".
  - BASS (PSI-26): cotton/fiberglass fabric (75/25 by mass), Nomex, Ultem.
  - Saffire-I (PSI-98): Sibal fabric (75% cotton, 25% fiberglass); Saffire-III (PSI-100): 30 cm/s vs 20 cm/s in Saffire-I, concurrent or opposed flow; Saffire-II (PSI-99): SIBAL, silicone, PMMA variants; goal includes low-g vs normal-g flammability limits.
  - SAME (PSI-102): goal is smoke particle size in low gravity.
  - SPICE (PSI-107): methane, ethylene, propane, propylene; burners 0.41/0.76/1.6 mm; co-flow 5.4-65 cm/s.
  - ACME CFI-G (PSI-159): spherical diffusion flames, multiple fuels, dilutions, flows, pressures.
- NTRS (title search, page.size=4): "FLEX droplet extinction" 1 hit (20130014061, methanol droplet combustion in O2-inert, microgravity); "BASS flame spread microgravity" 8 (e.g. 20160000593 BASS-II results presentation); "Saffire flame spread" 12; "Smoke Aerosol Measurement Experiment" 16 (20130000422 SAME-2 particle morphology and size); "Burning Rate Emulator microgravity" 2.
- Conclusion: catalog-level questions are answerable now from metadata; quantitative questions depend on tables in PSI files or NTRS papers (stage 2 confirms).

## 2026-11-14 ~11:35 | Stage 2: can R1 (PSI) be read without the browser?
- Where: PSI page bundle `https://psi.nasa.gov/physci/repo/main.5216219a85b99359.js`.
- Found: the page calls public JSON endpoints `/geode-py/ws/repo/search`, `/geode-py/ws/repo/filter-options`, `/geode-py/ws/repo/investigations/<id>`, `/geode-py/ws/studies/<id>/download?file=...&redirect=false` (returns a pre-signed S3 URL). No login required; no block circumvented (same calls as the page).
- Query: `GET /geode-py/ws/repo/search?from=0&size=500` -> 133 investigations in the whole repository (`q=combustion` also returns all 133). By Research Area: Materials Science 35, Complex Fluids 34, Fluid Physics 27, **Combustion Science 24**, Biophysics 7, Fundamental Physics 6.
- Combustion Science list: PSI-10, 20, 21, 22, 23, 25, 26, 39, 47, 60, 62, 68, 69, 98, 99, 100, 101, 102, 106, 107, 115, 117, 142, 159. Compared with Ruslan's metadata set: PSI-101 SAME-R missing there; PSI-108 and PSI-181 there are not Combustion Science.
- Conclusion: R1 fully readable via its own web service; catalog source = investigation records.

## 2026-11-14 ~11:40 | Stage 2: do PSI investigations have data tables?
- Where: investigation records, field `experimentalTable`.
- Found: 20 of 24 have Experimental Table CSVs (22 files, 239 B - 39.4 KB); PSI-60, 62, 115, 117 have none. All records `restricted=False`; license CC0-1.0 in 23 records, PSI-10 has an empty license field.
- Downloaded all 22 to scratch via the download endpoint; every size equals `file_size` in the record.
- FLEX (PSI-69): 274 rows; columns FLEX Test #, identifier, date, GMT, fuel, pressure mmHg, O2/N2/CO2/He mole fractions, d0 mm, visible flame extinction diameter mm, burning rate ("mm" in header), burn time s, test end. Fuel: methanol 157, heptane 117. Test end: Extinction 186, Disruption 61, Completion 27. Ranges: O2 0.12-0.34, CO2 0-0.70 (123 tests > 0), He 0-0.45 (50 tests > 0), d0 1.1-4.67 mm (262 values).
- CFI-G (PSI-159): normal 179 rows (XO2 0.18-0.40, p 0.51-3.04 bar; hot ignition Yes 132 / No 47; SE 102, FT 31, "-" 46), inverse 154 rows (XO2 0.12-0.85, p 0.50-3.31 bar; hot ignition Yes 114, yes 17, No 13, flash 8, no 2; SE 81, FT 58, "-" 15).
- BASS-II (PSI-25): 129 rows, 51 distinct material strings; initial O2 13.6-22.2 %, final O2 0.6-40.4 %, CO -3 to 950 ppm.
- Others: see DATA_SOURCES.md section 2.
- Anomaly flags for stage 3 (DATA_QUALITY.md): FLEX pressure minimum 0.0 mmHg and extinction diameter 0.0 mm; FLEX burning-rate header unit "mm" vs "mm2/s" in NASA/TP-2015-216046 Table IX; BASS-II final O2 40.4 % > initial maximum 22.2 % and CO -3 ppm; CFI-G inconsistent case ("Yes"/"yes"); SPICE first two data rows identical.
- Q5 note: FLEX includes tests at O2 0.30 and 0.34 near 540 mmHg (e.g. FLEX-019..027, NASA/TP-2015-216046 Table IX). 539.1 mmHg x 14.696 psia / 760 mmHg = 10.42 psia (conversion per FORMULAS.md section 1). The challenge's Moon-base atmosphere is "30% or greater" O2 at "10.2 psi or less".

## 2026-11-14 ~11:44 | Stage 2: NTRS reports with result tables
- Where: NTRS API, 10 queries from the stage-2 prompt, `page.size=6`; PDFs downloaded to scratch, text via `pdftotext -layout`, captions matched by `^Table|TABLE <n>`.
- Query totals: "Flame Extinguishment Experiment FLEX results" 2; "FLEX-2" 42 (mostly unrelated: "flex" bearings/packaging); "Cool Flames Investigation" 8; "ACME Advanced Combustion via Microgravity Experiments" 5; "BASS-II Burning and Suppression of Solids" 6; "SoFIE Solid Fuel Ignition and Extinction" 1; "Saffire spacecraft fire safety" 26; "SAME smoke aerosol measurement" 13 (half unrelated atmospheric aerosol); "microgravity flame spread" 194; "spacecraft fire safety" 318.
- Reports with relevant tables: 20150023456 (NASA/TP-2015-216046 FLEX, Tables I-IX), 20210011385 (BASS-II Summary TM, Tables 2.1, 4.1, 4.2, 5.1, 7.1), 20180005168 (Saffire, Table 1), 20170001636 (Saffire, Tables 1-5), 20130000422 (SAME-2, Table 1). Detail in DATA_SOURCES.md section 3.
- Conclusion: PSI CSVs are the primary numeric source; NTRS TP-FLEX is the cross-check; NTRS reports for other investigations only for stretch items.

## 2026-11-14 12:19 | Stage 3: correction of the stage-2 Q5 note
- The stage-2 note listed FLEX tests at O2 0.30-0.34 near 540 mmHg. Processed data: all 24 tests with O2 >= 0.30 are N2-diluted at 0.703-0.714 atm (10.33-10.49 psia) or ~1.01 atm. The challenge's Moon-base atmosphere is O2 >= 0.30 at <= 10.2 psi (0.694 atm), so it lies just outside the tested pressure range (by ~1-3 %), not inside. Predictions there are labelled extrapolation.

## 2026-11-14 ~12:17 | Stage 3: FLEX CSV vs NASA/TP-2015-216046 Table IX
- Where: TP PDF (NTRS 20150023456), pages 20-27 rendered and read; pdfplumber word coordinates for all rows.
- Found: 0 value differences in 3288 cells; TP skips FLEX-156, -213, -228 (CSV renumbered); TP-only tests FLEX-216 N03H201 and FLEX-230 H01H103; all CSV blanks are en dashes in the TP. Details in DATA_QUALITY.md section 3.

## 2026-11-14 12:43 | Stage 4: Law & Williams (1972) fragments supplied by Ruslan
- Source: screenshots sent by Ruslan in chat, taken from Law & Williams, Combust. Flame 19 (1972) 393-405 (DOI 10.1016/0010-2180(72)90009-0), per ADR-023 request. Low image quality; transcription below, uncertain parts marked [?].
- Eq. (1): k0 = (8/rho_F) (lambda_1 / C_1) ln(1 + B). Subscript 1 = properties of an inner region (the definitions of lambda_1, C_1 and B are not in the screenshots).
- Eq. (2): Damköhler number D_f = delta^2 rho_f^(l-1) B_f / (D_Of W_O^(m-1) W_F^n) exp(-E / (R0 T_f)) [exponents partly unreadable].
- D_1 = d^2 rho_inf^(l-1) B_inf / (4 D_Oinf W_O^(m-1) W_F^n) (a + b W_F / W_O) [?].
- Convection factors: f_A = A (d^3 p^2)^n [?]; f_B = A_1 (Gr)^n1; forced convection m = m0 (1 + 0.276 Re^(1/2) Sc^(1/3)), f_C = 0.276 Re^(1/2).
- Eq. (8): k = k0 [1 + A_1 Gr^n1][1 - A_2 (d p^n3)^(-n2)], constants fitted.
- Eq. (9): k = k0 [1 + 0.533 Gr^0.52][1 - 3.80e-5 (d p^0.84)^(-1.9)], d in cm, p in atm.
- Eq. (10) (T_inf = 293 K, small pressure dependence of mu and T_f neglected): k = k0 [1 + 13.0 (d^3 p^2)^0.52][1 - 3.80e-5 (d p^0.84)^(-1.9)].
- Activation energy from two extinction points a, b: E = R0 ln[(d_a/d_b)^2 (p_a/p_b)^1.68] / (1/T_fa - 1/T_fb).
- Conclusion: confirms that the burning-rate formula uses inner-region properties (lambda_1, C_1), consistent with hypothesis H1; the recipe values themselves are still missing. Eq. (9) is a fitted 1-g alkane correlation (alternative to the Nu = 2 + 0.6 Gr^1/4 Pr^1/3 estimate). Not implemented yet (Ruslan's decision needed).

## 2026-11-14 12:55 | Stage 4: why the quasi-steady K needs an "effective property" choice
- Where: NTRS search (Nayagam / Dietrich droplet papers), 11 PDFs scanned; NTRS 20205008449 (Williams & Nayagam, cool-flame QS theory, presentation), NTRS 20040000941 (NASA/TM-2003-212553, heptane MSL-1).
- Found: NTRS 20205008449 states that the quasi-steady theory "assumed constant properties and a property-evaluation procedure is needed to compare against experiments (as with hot-flame QS theories)" and that the "property evaluation prescription" is "empirically based on data fitting", citing Law & Williams 1972. NASA/TM-2003-212553 notes helium raises K "because of the high thermal conductivity of helium" but gives no recipe. NASA TR R-132 (Svehla 1962, NTRS 19630012982) is available for Lennard-Jones parameters if a variable-property calculation is needed.
- Conclusion: a single effective lambda and cp is intrinsic to the constant-property theory; NASA used the L&W empirical prescription for FLEX. Decision (Ruslan, 12:58): use the L&W recipe; he will send the full L&W PDF ("honest physics without deviations"). PDF goes to data/raw/literature/ (gitignored, copyrighted).
