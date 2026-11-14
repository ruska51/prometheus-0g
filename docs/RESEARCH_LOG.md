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
