# Data Dictionary

Processed tables in `data/processed/` (built by `scripts/build_data.py`). Units SI unless the column name says otherwise (`*_orig`, `*_mm`, `*_mmHg` keep the source units). Observed ranges are for rows with `use_in_model = True` (2026-11-14 build); physical bounds enforced by `src/fif/data/schema.py`.

**Timing column** (leakage control, CLAUDE.md section 4): **pre** = known before ignition, may be a model feature; **post** = measured after ignition, target or analysis only; **meta** = provenance / bookkeeping. The code version of this split is `src/fif/data/features.py`.

## Conventions

- Missing numeric value = empty cell (NaN). The original cell text is kept in `<column>__raw` (e.g. `""`, en dash `"–"`, `"~6"`, `"#DIV/0!"`).
- `quality_flag` = `;`-separated codes from DATA_QUALITY.md, empty if none.
- Provenance on every row: `source_id` (PSI id), `source_file` (raw file), `row_id` (1-based data row in that file).

## flex.csv - PSI-69 FLEX droplet tests (274 rows)

Source: `data/raw/psi_tables/PSI-69_Experimental table_FLEX.csv`; definitions from NASA/TP-2015-216046 App. A.1 (TP-FLEX).

| Column | Meaning | Unit | Observed range | Source | Timing |
|---|---|---|---|---|---|
| source_id, source_file, row_id | provenance | - | PSI-69; row 1-274 | parser | meta |
| test_no | FLEX test number as in the PSI CSV (renumbered vs TP: TP skips 156, 213, 228) | - | 1-274 | CSV "FLEX Test #" | meta |
| flex_identifier | CIR engineering test id | - | 273 unique (193F001 twice) | CSV | meta |
| test_date, test_gmt | date, GMT of test | - | 2009-03-05 .. 2011-12-08 | CSV | meta |
| fuel | Methanol / Heptane | - | 157 / 117 | CSV | pre |
| fuel_methanol | 1 if methanol | - | 0/1 | derived | pre |
| p_mmHg_orig | ambient pressure as published | mmHg | 526.3 .. 2319.9 (0 in test 114) | CSV | pre |
| p_Pa | ambient pressure, p_mmHg x 101325/760 | Pa | 7.017e4 .. 3.093e5 | derived | pre |
| p_atm | p_Pa / 101325 | atm | 0.693 .. 3.05 | derived | pre |
| x_o2, x_n2, x_co2, x_he | initial ambient mole fractions | - | O2 0.12-0.34; N2 0.09-0.88; CO2 0-0.70; He 0-0.45 | CSV | pre |
| x_sum | x_o2+x_n2+x_co2+x_he | - | 0.98 .. 1.01 | derived | pre |
| x_inert | 1 - x_o2 | - | 0.66 .. 0.88 | derived | pre |
| p_o2_Pa | O2 partial pressure x_o2 x p_Pa | Pa | - | derived | pre |
| diluent | N2 / CO2 / He (CO2 if x_co2>0, else He if x_he>0, else N2) | - | 101 / 123 / 50 (all rows) | derived | pre |
| d0_mm_orig, d0_m | initial droplet diameter at igniter ON (TP App. A.1) | mm, m | 1.1 .. 4.67 mm (12 missing) | CSV | pre |
| d_ext_mm_orig | visible-flame extinction diameter as published | mm | 0 .. 4.6 | CSV | post |
| d_ext_m | extinction diameter, only where > 0 | m | 0.12e-3 .. 4.6e-3 | derived | post |
| d_ext_over_d0 | d_ext / d0 where d_ext > 0 | - | 0.043 .. 1.0 (188 values) | derived | post |
| K_mm2_s_orig | burning-rate constant from linear fit of d^2 vs t; CSV header says "mm", TP defines mm^2/s (ADR-015) | mm^2/s | heptane 0.05-1.06 (median 0.54); methanol 0.20-0.74 (median 0.46) | CSV | post |
| K_m2_s | K_mm2_s_orig x 1e-6 | m^2/s | - | derived | post |
| burn_time_s | burn time ("~x" parsed as x, flagged) | s | 0.3 .. 39.2 | CSV | post |
| test_end | label as published: Extinction / Disruption / Completion (not defined in TP; display only) | - | 186 / 61 / 27 | CSV | post |
| extinct_finite_d | **target**: 1 = flame extinguished at finite droplet diameter (d_ext > 0); 0 = en dash or 0; NA = blank (ADR-018) | - | 189 / 36 / 49 NA | derived | post |
| cv_group | CV group: fuel x pressure (50 mmHg) x O2/CO2/He (0.01) (ADR-016) | - | 81 groups | derived | meta |
| use_in_model | False only for test 114 (pressure 0) (ADR-015) | - | 273 True | derived | meta |
| quality_flag | see DATA_QUALITY.md | - | 63 rows flagged | derived | meta |

## cfig.csv - PSI-159 ACME CFI-G spherical flames (333 rows: 179 normal + 154 inverse)

Source: `PSI-159_Experimental table_CFI-G_Normal Flames.csv`, `..._Inverse Flames.csv`. Role: data map, no ML model (ADR-012).

| Column | Meaning | Unit | Observed range | Source | Timing |
|---|---|---|---|---|---|
| table, flame_type | normal (fuel from burner into O2/N2 chamber) / inverse (O2/N2 from burner into fuel/N2 chamber) | - | 179 / 154 | file / CSV (lower-cased) | pre |
| day, test_id | test day (YYDDD), test id | - | 23 table-day groups | CSV | meta |
| fuel_label, fuel | label as published; parsed fuel name | - | ethane / propane / butane | CSV / derived | pre |
| fuel_bottle_fraction | fuel fraction of the bottle from the label ("30% butane" -> 0.30; none -> 1.0) | - | 0.30 .. 1.0 | derived | pre |
| x_o2_chamber_before/after | chamber O2 mole fraction (normal flames) | - | 0.18 .. 0.40 | CSV | pre / post |
| x_o2_supply | supplied oxidizer O2 mole fraction (inverse flames) | - | 0.12 .. 0.85 | CSV | pre |
| x_o2_oxidizer | x_o2_chamber_before (normal) or x_o2_supply (inverse) | - | 0.12 .. 0.85 | derived | pre |
| x_fuel_supply / x_fuel_chamber_before/after | fuel mole fraction in supply (normal) / chamber (inverse) | - | - | CSV | pre / post |
| p_bar_orig, p_Pa | approximate pressure | bar, Pa | 0.50 .. 3.31 bar | CSV | pre |
| p_o2_Pa | x_o2_oxidizer x p_Pa | Pa | - | derived | pre |
| m_fuel_mg_s, m_fuel_kg_s | fuel mass flow | mg/s, kg/s | - | CSV | pre |
| m_o2_mg_s, m_o2_kg_s | O2 mass flow (inverse) | mg/s, kg/s | - | CSV | pre |
| tad_K, z_st | adiabatic flame temperature and stoichiometric mixture fraction as computed by the PSI table authors | K, - | 2 + 2 spreadsheet errors -> NaN | CSV | pre (computed) |
| hot_ignition | yes / no / flash (case-normalised) | - | normal 132/47/0; inverse 131/15/8 | CSV | post |
| ignited | **target**: yes -> 1, no -> 0, flash -> NA | - | - | derived | post |
| end_mode | SE (self-extinguished) / FT (flow terminated) / "-" | - | - | CSV | post |
| self_extinguished | **target**: SE -> 1, FT -> 0, "-" -> NA | - | normal 102/31; inverse 81/58 | derived | post |
| burn_time_s | burn time | s | 0 .. 304 | CSV | post |
| peak_burner_T_C, peak_burner_T_K(_from_C) | peak burner temperature | degC, K | - | CSV / derived | post |
| tfp, cool_flame, color, comments | free-text observations as published | - | - | CSV | post |

## psi_investigations.csv - PSI Combustion Science catalog (24 rows)

Source: `data/raw/psi_records/PSI-*.json.gz`. One row per investigation, fields as published by PSI: psi_id, acronym, title, research_area, subresearch_area, project_type, flight_platform, hardware, managing_center, start_date, end_date, doi, license, n_publications, experimental_tables, n_table_rows (data rows over its Experimental Tables), raw_data_GB (PSI `totalFileSize`), objective, approach, hypothesis, research_impacts, psi_url (URL pattern taken from the PSI page code). Timing: meta (catalog, not a model input).
