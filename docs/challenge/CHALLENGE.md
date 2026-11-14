# Challenge: Flame in Freefall - AI-Powered Fire Safety Insights from Microgravity Combustion Data

> NASA International Space Apps Challenge 2026. Background / Objectives / Potential Considerations pasted verbatim by Ruslan from spaceappschallenge.org on 2026-11-14 (the site blocks automated access).

## Background

Fire hazards are extremely dangerous in space exploration! In describing a smoke alarm that went off during the recent Artemis II mission, the commander commented, "[If] you want to get somebody's attention really quick, make the fire alarm go off in your spacecraft when you're still about 80,000 miles from home." Decades earlier, the Apollo 13 crew endured the life-threatening results of an oxygen tank explosion on their way to the Moon. Similarly, a multinational crew survived a fire aboard the Mir space station caused by an oxygen generator failure. In 1967, the Apollo 1 crew died in a pre-launch test when fire erupted in their oxygen-filled spacecraft.

Compared to Earth, flames in free fall (i.e., in microgravity) are often dramatically different because of the absence of buoyancy and thus rising hot gases. Instead of a flickering teardrop, a candle flame becomes a ghostly blue sphere reliant on diffusion for its oxygen.

NASA's spacecraft fire safety work is focused on prevention, detection, and suppression. Prevention is achieved by controlling ignition sources and through material selection, which depends on understanding flammability limits. To facilitate spacesuit use, an atmosphere with increased oxygen and reduced pressure compared to Earth's is expected within the planned Moon Base and pressurized rovers. Flammability is highly dependent on oxygen concentration, and air flow is also important in microgravity. Flammability studies focus on solid materials such as fabrics and plastics, as studied in the Burning and Suppression of Solids (BASS and BASS-II) and Spacecraft Fire Safety Demonstration (Saffire-I, -II, and -III) investigations.

Fire detection was tested in microgravity through the Smoke and Aerosol Measurement Experiment studies (SAME and SAME-R). Suppression was studied in the Flame Extinguishment Experiment (FLEX) through dilution of the chamber atmosphere with carbon dioxide and helium, both of which suppress fire.

## Objectives

Results from low-gravity combustion experiments, conducted for example on the International Space Station (ISS), are being made publicly available through NASA's Physical Science Informatics (PSI) database, but the amount of data can be overwhelming. It can be hard to find, harder to compare, and harder yet to interpret.

Your challenge is to build an SI-powered, web-based dashboard that summarizes, ranks, and interprets combustion science investigations to deliver critical foundational insights for fire safety. You may consider enabling users to:

- Identify investigations most relevant to the fire safety needs of habitable crew environments, including spacecraft, space stations, bases on the lunar and Martian surfaces, and pressurized rovers.*
- Extract data that supports predictive modeling of flammability and fire scenarios in space exploration.
- Highlight research that informs the development of next-generation fire safety controls and equipment.

In this challenge, you'll help turn complex data into clear answers and make the next giant leap a safer one.

Your dashboard could also address potential applications of the PSI data to fire safety on Earth. Fine-water-mist extinguishers developed for use on the ISS have practical applications here on Earth, and NASA technology has similarly led to improvements in terrestrial smoke detection and firefighter gear, including protective clothing and air tanks.

*Fire safety involving rockets and propellants is generally beyond the scope of the research available in the PSI database. The high velocities within rocket engines render the combustion effectively independent of gravity — although a rocket's launch is of course strongly dependent on gravity.

## Potential Considerations

You may (but are not required to) consider the following:

- Your target audience can include professors, graduate students, undergraduate students, aerospace researchers, and aerospace engineers.
- Consider how you might summarize and display attributes such as:
  - Experimental objectives
  - Fuels, including shape and size of the samples or burners
  - Other test conditions, such as oxygen concentration and airflow speed
  - Variables: how did tests from the same investigation differ and how were they the same?
  - Sensors or types of measurements
- Consider how to summarize and display similarities and differences between different investigations.

**Other investigations in PSI**
- One of the instruments used for smoke detection in the SAME and SAME-R studies was instead used to detect dust in the Dust and Aerosol Measurement Feasibility Test (DAFT and DAFT-2) studies.
- While it burned gaseous fuels, the Burning Rate Emulator (BRE) experiment of the Advanced Combustion via Microgravity Experiments (ACME) project was a study of materials flammability in still atmospheres as a function of material properties.
- Other combustion investigations within the PSI database (but not explicitly referenced above) are still relevant to fire safety, just not as strongly or directly.

**Hardware**
- The six experiments in the ACME project featured flames of gaseous fuels and were all conducted with the same modular set of ACME hardware in the Combustion Integrated Rack (CIR).
- FLEX, FLEX-2, and the Cool Flames Investigation (CFI) each featured burning droplets of liquid fuel and were conducted with the Multi-user Droplet Combustion Apparatus (MDCA) in the CIR.
- BASS, BASS-II, the Smoke Point In Co-flow Experiment (SPICE), and the Structure & Liftoff In Combustion Experiment (SLICE) collectively featured both solid and gaseous fuels. Each of these investigations was conducted within the Microgravity Science Glovebox (MSG) using the modular fan-driven flow duct built for SPICE.

**Spacesuits and oxygen concentration**
- To enable flexibility, spacesuits are filled with 100% oxygen to only 4.3 psi (pounds per square inch), where the Earth's pressure at sea level is 14.7 psi.
- To avoid the bends (decompression sickness), the astronauts pre-breathe 100% oxygen to expel absorbed nitrogen.
- To reduce the pre-breathing duration and thus facilitate lunar excursions, it is expected that the Moon Base and pressurized rover(s) will be at a pressure and oxygen concentration between those in a spacesuit and the Earth's atmosphere.
- The intermediate oxygen concentration used on the Moon will likely be 30% or greater, with a corresponding pressure of 10.2 psi or less. Compared to Earth's atmosphere, that's more than a 40% increase in the oxygen concentration making materials much more flammable.
- Microgravity tests with the highest oxygen concentrations were conducted as part of the ACME's Cool Flames Investigation with Gases (CFI-G). In those tests, the combustion chamber was filled with a mixture of nitrogen and a flammable gas (e.g., propane), while an oxygen-nitrogen mixture of up to 85% oxygen flowed from the spherical burner creating an inside-out flame.

**Partial-gravity data**
- Although NASA is heavily focused on the return of astronauts to the Moon's surface and the establishment of a Moon Base in preparation for the future human exploration of Mars, there is currently no partial-gravity combustion data available in PSI. We expect such data will be added in the future, for example from the Lunar-g Combustion Investigation (LUCI) and the Flammability of Materials on the Moon (FM2) experiment.
- Partial gravity was mimicked in ACME's Electric-Field Effects on Laminar Diffusion Flames (E-FIELD Flames) experiment through the effect of the electric field on the ions that naturally occur in flames.
- Microgravity and normal-gravity results could bound what occurs at intermediate gravity levels.

For data and resources related to this challenge, refer to the Resources tab at the top of the page. More resources may be added before the hackathon begins.

## Resources (NASA)

| # | Resource | What it is |
|---|---|---|
| R1 | [NASA Physical Sciences Informatics - combustion search](https://psi.nasa.gov/physci/repo/search?q=combustion) | NASA PSI repository of ISS / drop-tower combustion investigations; the only official source of quantitative data. |
| R2 | [NASA SMA - Apollo 1](https://sma.nasa.gov/sma-disciplines/accllp/apollo-1) | NASA Safety & Mission Assurance case page on the Apollo 1 cabin fire (27 Jan 1967). |
| R3 | [NASA SMA - Apollo 13](https://sma.nasa.gov/sma-disciplines/accllp/apollo-13) | NASA SMA case page on the Apollo 13 oxygen tank explosion (1970). |
| R4 | [25 Years Ago: Fire Aboard Space Station Mir](https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/) | NASA History article on the 24 Feb 1997 oxygen-generator fire aboard Mir. |
| R5 | [NASA Spinoff - Fireman's Air Tanks (1976)](https://spinoff.nasa.gov/node/9582) | Lightweight firefighter air tanks developed with NASA Johnson Space Center. |
| R6 | [NASA Spinoff - Fire Detector (1978)](https://spinoff.nasa.gov/node/9407) | Incipient fire detector derived from Space Shuttle orbiter equipment. |
| R7 | [NASA Spinoff - New Technology for the Fire Attire (1982)](https://spinoff.nasa.gov/node/9918) | Project FIRES: Apollo-derived fire-resistant materials for firefighter gear. |

## Resources (Space Agency Partners)

_Not provided in the pasted text (the Resources tab was not included). Ruslan to paste if the tab lists partner resources._

## Notes

- "SI-powered" in Objectives is reproduced verbatim from the page; the challenge title says "AI-Powered".
- The pasted text names two investigations not in `NASA PSI data/`: SAME-R and the fine-water-mist work (no PSI-id given). It also names LUCI and FM2 as future partial-gravity sources (no data in PSI yet).
- R1 is a JavaScript single-page app; a static fetch returns an empty shell (checked 2026-11-14). Study metadata was downloaded by Ruslan into `NASA PSI data/`.
- R2-R7 are context only (evidence types `NASA history` / `NASA spinoff`), never model data (CLAUDE.md section 3.0).
