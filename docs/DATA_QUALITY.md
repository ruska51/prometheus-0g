# Data Quality Report

Build of 2026-11-14 (stage 3). Machine-readable lists: `data/processed/quality_flags.tsv` (every flagged row) and `data/processed/transform_log.tsv` (every transformation with row counts). Nothing is deleted or silently corrected; handling follows ADR-015 (Ruslan: "default package").

## Summary

| Dataset | Rows | Flagged rows | Excluded from model | Notes |
|---|---|---|---|---|
| FLEX (PSI-69) | 274 | 63 | 1 (test 114) | all 274 rows agree with NASA/TP-2015-216046 Table IX (section 3) |
| CFI-G (PSI-159) | 333 | 23 | 0 (no ML model) | spreadsheet errors + case variants |
| PSI catalog | 24 | 5 | - | 1 missing license field, 4 without Experimental Table |

## 1. Checks performed

Missing values; non-numeric codes; duplicates (identifier, full row); sum of mole fractions = 1 (tolerance 0.011); physically impossible values (pressure <= 0, negative sizes/times, O2 fraction outside 0-1); extinction diameter vs initial diameter; outliers (burning-rate robust z > 3.5 within fuel, MAD-based); label consistency (`Test end` vs extinction-diameter code); schema bounds (pandera, `src/fif/data/schema.py`).

## 2. Flags

### FLEX (PSI-69)

| Code | Rows | Tests (CSV numbering) | Handling (ADR-015) |
|---|---|---|---|
| P_NONPOSITIVE | 1 | 114 (C11M201): 0 mmHg; also printed 0 in TP Table IX p. 23 | `use_in_model = False`; kept in catalog |
| MOLE_SUM_OFF | 6 | 69, 75, 76, 79, 80, 81: sum 0.98 (e.g. O2 .13 + N2 .85); same in TP | kept, not renormalised |
| D_EXT_ZERO | 8 | 39, 43, 51, 52, 63, 69, 93, 135: extinction diameter 0; same in TP | d_ext target = missing; counted as "no finite-diameter extinction" (ADR-018) |
| D_EXT_GT_D0 | 1 | 129 (C13H102): d_ext 3.34 > d0 3.33; same in TP | kept |
| APPROX_BURN_TIME | 2 | 223, 224: "~6", "~9" s; same in TP | value used, flagged |
| DUP_IDENTIFIER | 2 | 70 and 73: both 193F001, same date and GMT 7:25:43, same conditions, different d0 4.67/4.64, d_ext 4.6/4.58, K .41/.56, burn time 1.6/1.5 s; same in TP p. 22 | kept both; same CV group, so no train/test leakage. **Possibly one physical test entered twice - Ruslan to decide** |
| D0_MISSING | 12 | initial diameter blank or en dash | kept; models that need d0 skip these rows |
| OUTLIER_K | 1 | see quality_flags.tsv | kept |
| TEST_END_CONFLICT | 35 | 10 "Completion" + 20 "Disruption" with measured d_ext > 0; 5 "Extinction" with en dash | `test_end` kept for display only; target uses the diameter (ADR-018) |

### CFI-G (PSI-159)

| Code | Rows | Handling |
|---|---|---|
| EXCEL_ERROR_TAD_K, EXCEL_ERROR_Z_ST | 2 each (normal table) | `#DIV/0!` -> NaN |
| EXCEL_ERROR_PEAK_BURNER_T_K | 2 (inverse) | `#VALUE!` -> NaN |
| CASE_NORMALISED | 19 | "yes"/"no" variants of Yes/No lower-cased; original in `hot_ignition_orig` |

`flash` ignition (8 inverse tests) is kept as its own category; target `ignited` = NA for them.

### PSI catalog

PSI-10 record has an empty license field (other 23: CC0-1.0) -> LICENSE_MISSING. PSI-60, 62, 115, 117 have no Experimental Table -> NO_EXPERIMENTAL_TABLE.

## 3. Verification of FLEX against the PDF report (NASA/TP-2015-216046, Table IX)

**Automated, all rows** (`scripts/verify_flex_vs_tp.py`, pdfplumber word coordinates; output `docs/verification/flex_vs_tp.tsv`): 276 TP rows parsed (every row has exactly 15 cells); 274 CSV rows matched by FLEX identifier + date; 3288 cell comparisons (12 columns); **0 value differences**.

Findings from the comparison:
- **Numbering.** The CSV renumbers tests 1-274 continuously; the TP skips FLEX-156, -213 and -228 and runs to FLEX-280. Rows must be matched by identifier, never by test number.
- **Two TP tests are not in the PSI CSV:** FLEX-216 N03H201 (9/1/11, heptane, 766.2 mmHg, 0.15/0.85, d0 1.77, d_ext 0.33, K 0.47, 6.7 s, Completion) and FLEX-230 H01H103 (9/13/11, heptane, 756.5 mmHg, 0.2/0.75/0/0.05, d0 2.3, d_ext "–", K 0.58, 9.8 s, Disruption) (TP p. 26). **Ruslan to decide** whether to add them from the TP.
- **Blank vs dash.** Every blank cell in the CSV is printed as an en dash in the TP: d_ext 49, d0 6, K 16, burn time 6, GMT 1. The TP uses the dash both for "flame extinction did not occur" and for values "not listed" (droplet left the field of view) (TP App. A.1). So the CSV's split of d_ext into blank (49) vs dash (28) has no counterpart in the TP. **This affects ADR-018** (class 0 vs NA) - Ruslan to decide (see section 5).

**Manual check against rendered pages** (images of TP pp. 20-27 viewed one by one):

| Check | Tests (CSV no. -> identifier, TP page) | Result |
|---|---|---|
| 10 random rows (seed 20261114) | 13 256R002 (p20), 33 177R002 (p21), 67 189F002 (p22), 122 C12M201 (p23), 124 C12M401 (p23), 221 N06M202 (p26), 225 H02M101 (p26), 248 H08M101 (p27), 255 H12M101 (p27), 259 H12H201 (p27) | all 12 compared fields agree |
| Pressure min / max | 526.3 C12M101 (p23) / 2319.9 264F003 (p20) | agree |
| O2 min / max | 0.12 304F002 (p22) / 0.34 196F001 (p20) | agree |
| CO2 min>0 / max | 0.05 C01M101 (p24) / 0.70 256F002 (p20) | agree |
| He min>0 / max | 0.05 H01M102 (p26) / 0.45 H15H101 (p27) | agree |
| d0 min / max | 1.1 193R002 / 4.67 193F001 (p22) | agree |
| d_ext min>0 / max | 0.12 H11H101 (p27) / 4.6 193F001 (p22) | agree |
| K min / max | 0.05 C13H201 (p23) / 1.06 H15H201 | min agrees visually; max checked by the automated comparison only (page not viewed) |
| Burn time min / max | 0.3 H08M101 (p27) / 39.2 C01M301 (p24) | agree |
| Anomalies | 114 (P = 0, p23), 129 (d_ext > d0, p23), 32 and 136 (see note) | printed so in the TP |

Note: a first plain-text extraction (`pdftotext`) showed false differences for tests 32 and 136 (O2 0.2 vs 0.3; 0.15/0.35/0.5 vs 0.24/0.56/0.2). The rendered pages show the CSV values; the text layer of the first rows on each page is shifted. This is why the automated check uses word coordinates.

## 4. Coverage (EDA, `scripts/eda.py`, figures in `docs/figures/`)

FLEX tests per fuel x diluent x pressure class (all 274 rows):

| fuel, diluent | ~0.7 atm | ~1 atm | ~2 atm | ~3 atm | 0 (anomaly) |
|---|---|---|---|---|---|
| Heptane, CO2 | 19 | 27 | 1 | 1 | 0 |
| Heptane, He | 10 | 12 | 0 | 0 | 0 |
| Heptane, N2 | 10 | 37 | 0 | 0 | 0 |
| Methanol, CO2 | 38 | 29 | 1 | 6 | 1 |
| Methanol, He | 14 | 14 | 0 | 0 | 0 |
| Methanol, N2 | 12 | 42 | 0 | 0 | 0 |

Gaps: no He or N2 tests above ~1 atm; above ~1.2 atm only CO2-diluted tests with O2 0.21 (9 tests). O2 >= 0.30 occurs in 24 tests, all at 0.703-0.714 atm or 1.009-1.015 atm, all N2-diluted. **The challenge's Moon-base atmosphere (O2 >= 0.30 at <= 10.2 psi = 0.694 atm) lies just outside the tested pressure range** (closest tests 0.703 atm = 10.33 psia): predictions there are extrapolation by ~1-3 % in pressure (correction of the stage-2 note "inside the tested range").

FLEX outcome by diluent: CO2 95 extinguished / 21 not / 7 unknown; He 38 / 0 / 12; N2 56 / 15 / 30.

CFI-G outcomes: normal 102 self-extinguished, 30 flow-terminated, 47 no ignition; inverse 73 self-extinguished, 58 flow-terminated, 15 no ignition, 8 flash (outcome assignment in `scripts/eda.py`).

Figures: `flex_conditions.png` (O2 vs pressure, Moon-base box), `flex_outcomes.png`, `flex_coverage.png`, `cfig_map.png`.

## 5. Open questions for Ruslan

1. Tests 70/73 (193F001, identical timestamp): keep both, or keep one?
2. Add the two TP-only tests (FLEX-216, FLEX-230) from the TP?
3. ADR-018 class "no finite-diameter extinction" currently = en dash (28) + zero (8); blanks (49) = unknown. The TP prints all 77 as dashes with a double meaning. Keep, or treat all 77 as unknown (class 0 would then be the 8 zeros only)?
