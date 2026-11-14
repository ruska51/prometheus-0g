# Physics

Stage 4 (2026-11-14), revised 13:05 after Ruslan's review (ADR-026, ADR-027). Code: `src/fif/physics/` (`properties.py`, `mixing.py`, `flame.py`, `droplet.py`). Comparison with data: `scripts/physics_vs_data.py`. Decisions: ADR-022 (theory level), ADR-023 (property evaluation, superseded by ADR-027), ADR-024 (gravity baseline), ADR-025 (physics features), ADR-026 (inner-region heat capacity), ADR-027 (Law & Williams prescription).

## 1. Scope

| Combustion type (dataset) | What the physics layer does | Status |
|---|---|---|
| Liquid droplets (FLEX, PSI-69) | quasi-steady burning-rate constant with the Law & Williams (1972) property prescription, equilibrium flame temperature, extinction proxies, Earth-gravity correction | implemented |
| Gaseous spherical diffusion flames (CFI-G, PSI-159) | no own model: `Tad`, `Zst` as computed by the PSI table authors | data only (ADR-012, ADR-022) |
| Solids (BASS-II), jet flames, smoke | not in the MVP; FORMULAS.md sections 4, 5, 7 not implemented | - |

## 2. Why a "property prescription" is needed

The quasi-steady droplet theory is derived for **constant** gas properties. Across the gas film the temperature changes from $T_b$ (340-410 K) to $T_f$ (1600-2600 K) and the composition from fuel vapour to ambient gas, so $\lambda$ and $c_p$ change several-fold. A single effective pair has to be chosen to compare the theory with experiments. NASA states this explicitly for the FLEX analyses: the theory "assumed constant properties and a property-evaluation procedure is needed to compare against experiments", and the prescription is "empirically based on data fitting", citing Law & Williams 1972 (NTRS 20205008449). NASA's FLEX burning-rate comparison used the same prescription (NTRS 20130014061). Chemical-engineering textbooks (e.g. "processes and apparatus" texts) solve the same problem with a "defining temperature" and mixing rules; that is what the first stage-4 version did, and it gave the 2x-4x error (section 8).

## 3. Burning-rate constant: Law & Williams (1972) prescription (ADR-027)

Law, C. K.; Williams, F. A. "Kinetics and Convection in the Combustion of Alkane Droplets", Combust. Flame 19 (1972) 393-405 (L&W; copy supplied by Ruslan, kept locally, not in the repository).

$$k_0 = \frac{8}{\rho_F}\frac{\lambda_1}{c_1}\ln(1+B), \qquad B = \frac{Y_{O\infty}\,q/i - c_1(T_b - T_\infty)}{L} \quad \text{(L\&W Eq. 1, p. 394)}$$

| Quantity | L&W prescription (page) | Implementation and data source |
|---|---|---|
| $c_1$ | "the heat capacity of the fuel vapor" (p. 394) | NIST ideal-gas cp: methanol TRC 1997, n-heptane Scott 1974 |
| $\lambda_1$ | $\lambda_1 = x\lambda_{F1} + (1-x)\lambda_{a1}$, $x = 0.4$, "an average fuel mole fraction in region 1", chosen to match a free n-heptane droplet and used "throughout" (pp. 394-395) | $\lambda_{F1}$: methanol from NASA TR R-132 (Svehla 1962) Table III p. 56; n-heptane from Svehla Eq. (2) with viscosity extrapolated in carbon number from n-C5H12 and n-C6H14 (Table IV p. 119), as L&W did for hexadecane (p. 399). $\lambda_{a1}$: actual ambient mixture (A8), NIST + RP-1311 rules |
| $T_1$ | $c_1$, $\lambda_{F1}$, $\lambda_{a1}$ evaluated at $T_1 = (T_b + T_f)/2$ (p. 395) | same |
| $T_f$ | adiabatic flame temperature "of a stoichiometric system in which the initial temperature of fuel is $T_b$ and the initial temperature of air is $T_\infty$", dissociation included (pp. 395, 399) | Cantera HP equilibrium with NASA Glenn thermo data (McBride, Gordon & Reno, NASA TM-4513); fuel vapour at $T_b$; oxidiser = actual ambient mixture (A8) |
| $q$ | heat of combustion per unit mass at $T_\infty$, "obtained from thermochemical tables", not reduced for dissociation (pp. 394-395) | lower heating value from NIST $\Delta_c H$ (section 7), ADR-028 (confirmed by Ruslan). NIST values trace to the same Rossini measurements as L&W ref. [23]. Sensitivity: HHV would raise K by 7.8 % (methanol) / 3.4 % (heptane) |
| $\rho_F$, $L$ | at $T_b$, "rather than room temperature" (p. 395) | NIST saturation tables at $T_b(P)$ |
| $i$ | stoichiometric oxygen-fuel mass ratio (p. 394) | $\nu_s$ from global stoichiometry and NIST molar masses |

Svehla (1962) Eq. (2), p. 3: $\lambda = \frac{R}{M}\left[\frac{15}{4} + 1.32\left(\frac{C_p}{R} - \frac52\right)\right]\eta$ (Eucken-type). Our transcription of the methanol table reproduces its own conductivity column to 0.1 % with this equation (`tests/test_physics.py`).

L&W report agreement "within 15%" for n-alkanes in air (abstract; p. 404).

## 4. Gravity: ISS vs Earth (ADR-024, updated by ADR-027)

Base = microgravity (data are ISS data; $k_0$ has no buoyancy). Earth estimate (evidence type `physics theory`), L&W Eqs. (4), (9), p. 396 and p. 404:

$$k = k_0(1 + f_B), \qquad f_B = 0.533\,Gr^{0.52}, \qquad Gr = \frac{g\,\rho_2^2\,d^3}{\mu_2^2}\,\frac{\Delta T_2}{T_2}, \quad T_2 = \frac{T_f + T_\infty}{2}, \ \Delta T_2 = T_f - T_\infty$$

with $\rho_2$, $\mu_2$ of the ambient gas at $T_2$ and $d = d_0$. **L&W fitted this for Gr <~ 1 (p. 403); FLEX droplets (1-4.7 mm) give Gr = 11.6 median at 1 g, so 256 of 274 rows are outside the fitted range** (`Gr_above_fit_range`): the Earth number is an extrapolation and must be labelled so. The earlier estimate $Nu = 2 + 0.6Gr^{1/4}Pr^{1/3}$ (FORMULAS.md section 6) is no longer used.

**Partial gravity (ADR-036).** $Gr \propto g$, so at $g = \gamma g_0$: $k = k_0[1 + 0.533(\gamma\,Gr_{Earth})^{0.52}]$ (`buoyancy_factor`). On the lunar surface $\gamma = 1/6$ (NTRS 20250004015). We report the lunar rate as a range from $k_0$ (microgravity, data + model) to this value (theory): PSI has no partial-gravity data. For the Moon-base air and a 3 mm droplet $Gr(1/6\,g)$ = 0.69-0.76, inside the fitted range. This concerns droplet burning only; for solid materials NASA reports that flammability limits are widest near lunar gravity (NTRS 20210020516), which this model does not capture.

## 5. Extinction proxies (L3, ADR-022)

- flame-standoff ratio (FORMULAS.md section 2): $r_f/r_s = \ln(1+B)/\ln(1 + Y_{O\infty}/\nu_s)$;
- radiative-loss proxy $\chi_{rad}/\kappa = \sigma P T_f^4 r_{s0}^2 (r_f/r_s)^3 c_1/(3\lambda_1\ln(1+B)q)$ [Pa m] (optically thin, FORMULAS.md section 3; Planck-mean absorption per unit pressure $\kappa$ unknown);
- flow time at the flame $r_f^2/\alpha_g$ [s].

L&W Eq. (2) gives a Damköhler number and p. 401 a way to infer an activation energy from two extinction points; not used yet (needs Ruslan's decision, stage 5/6).

## 6. Mixture rules (NASA RP-1311, Gordon & McBride 1994, CEA Part I, pp. 21-22)

$$\eta_{mix} = \sum_i \frac{x_i\eta_i}{x_i + \sum_{j\ne i} x_j\phi_{ij}}, \quad \lambda_{mix} = \sum_i \frac{x_i\lambda_i}{x_i + \sum_{j\ne i} x_j\psi_{ij}} \quad\text{(5.3, 5.4)}$$

$$\phi_{ij} = \frac14\left[1 + \left(\frac{\eta_i}{\eta_j}\right)^{1/2}\left(\frac{M_j}{M_i}\right)^{1/4}\right]^2\left(\frac{2M_j}{M_i+M_j}\right)^{1/2}, \quad \psi_{ij} = \phi_{ij}\left[1 + \frac{2.41(M_i - M_j)(M_i - 0.142M_j)}{(M_i+M_j)^2}\right] \quad\text{(5.5, 5.6)}$$

Eq. (5.5) equals the Wilke form in FORMULAS.md section 1. Used for the ambient mixture only ($\lambda_{a1}$, $\mu_2$, proxies).

## 7. Property data (every value with source and temperature)

| Quantity | Methanol | n-Heptane | Unit | Source | Condition |
|---|---|---|---|---|---|
| Molar mass M | 32.04 | 100.2 | g/mol | NIST species page | - |
| Boiling point T_b | 337.6 | 371.6 | K | NIST saturation table (ln P interpolation) | 1 atm |
| Heat of vaporisation L | 1101 | 316.7 | kJ/kg | NIST saturation table | at T_b(1 atm) |
| Liquid density rho_F | 748.3 | 613.5 | kg/m3 | NIST saturation table | at T_b(1 atm) |
| -Delta_c H (liquid, H2O liquid) | 725.7 | 4817 | kJ/mol | NIST: methanol Chao & Rossini 1965 (-725.7 ± 0.1); heptane average of 7 (-4817 ± 8) | 298.15 K |
| Higher heating value HHV | 22.65 | 48.07 | MJ/kg | computed from the row above | 298.15 K |
| Lower heating value q (used) | 19.90 | 44.56 | MJ/kg | HHV - n_H2O M_H2O L_water / M; n_H2O = 2 / 8; L_water = 2440.8 kJ/kg (NIST, 298.15 K) | 298.15 K |
| i = nu_s | 1.498 | 3.513 | - | global stoichiometry, NIST molar masses | - |
| Fuel-vapour cp c_1 | 89.54 J/(mol K) = 2794 J/(kg K) | 381.58 J/(mol K) = 3808 J/(kg K) | at 1000 K | NIST gas-phase: TRC 1997 (50-3000 K); Scott 1974 (200-1500 K) | at T_1 |
| Fuel-vapour conductivity lambda_F1 | 0.1245 (Svehla table) | 0.1015 (Svehla Eq. 2, extrapolated viscosity) | W/(m K) at 1000 K | NASA TR R-132 pp. 3, 56, 119 | at T_1 |

Gases (NIST fluid tables, 1 atm, 300-1500 K in 50 K steps; at 300 K and 1200 K):

| Gas | M, g/mol | cp 300 K | cp 1200 K, J/(kg K) | lambda 300 K | lambda 1200 K, W/(m K) | mu 300 K | mu 1200 K, Pa s |
|---|---|---|---|---|---|---|---|
| O2 | 31.9988 | 919.9 | 1115 | 0.02649 | 0.0825 | 2.065e-05 | 5.534e-05 |
| N2 | 28.0134 | 1041 | 1204 | 0.02597 | 0.07468 | 1.789e-05 | 4.677e-05 |
| CO2 | 44.0095 | 852.6 | 1280 | 0.01677 | 0.08402 | 1.5e-05 | 4.684e-05 |
| He | 4.0026 | 5193 | 5193 | 0.156 | 0.4097 | 1.993e-05 | 5.252e-05 |

Thermodynamic data for the equilibrium flame temperature: NASA Glenn polynomials (Cantera `nasa_gas.yaml`, source McBride, Gordon & Reno, NASA TM-4513, 1993). Constants: $\sigma$ = 5.670374419e-8 W/(m² K⁴), $R_u$ = 8.314462618 J/(mol K) (CODATA 2018), $g$ = 9.80665 m/s², 1 cal = 4.184 J.

## 8. Theory vs FLEX data (no calibration; 274 model rows)

Figures: `docs/figures/physics_K_parity.png`, `physics_K_ratio_groups.png`, `physics_extinction_proxies.png`; table: `docs/verification/physics_vs_data.tsv`.

| Version | median $K_{meas}/K_{theory}$ methanol / heptane | share of tests within ±15 % methanol / heptane |
|---|---|---|
| 1. ambient-gas cp, ambient lambda, Burke-Schumann $T_f$ (first stage-4 version) | 0.52 / 0.24 | 0 % / 0 % |
| 2. $c_1$ = fuel vapour, ambient lambda, Burke-Schumann $T_f$ (ADR-026) | 1.36 / 0.89 | 12 % / 46 % |
| **3. Law & Williams prescription (ADR-027, current)** | **0.97 / 0.73** | **74 % / 14 %** |

Current version by group: methanol N2/CO2 0.94-1.05, methanol He 0.81-0.92; heptane 0.68-0.78 (one CO2 3-atm test 0.99). Equilibrium $T_f$ 1630-2630 K (Burke-Schumann without dissociation gave up to 3800 K).

Ratio by initial droplet diameter (current version):

| d0, mm | heptane median (n) | methanol median (n) |
|---|---|---|
| 1-2 | 0.84 (16) | 1.10 (11) |
| 2-2.5 | 0.77 (18) | 1.03 (14) |
| 2.5-3 | 0.71 (25) | 0.99 (45) |
| 3-3.5 | 0.72 (24) | 0.99 (40) |
| 3.5-5 | 0.59 (25) | 0.92 (40) |

corr(ln ratio, d0): heptane -0.42, methanol -0.44; corr(ln ratio, x_He): methanol -0.45.

**Interpretation and hypotheses (for discussion):**
- The L&W prescription removes the constant error for methanol and halves it for heptane: the first version's error came from using air properties where the theory needs fuel-vapour-region properties.
- H3 (size): K falls below theory as droplets get larger, for both fuels. L&W calibrated $x$ = 0.4 on small free heptane droplets; FLEX droplets are 1-4.7 mm. For heptane (sooting) radiative loss grows with flame size (FORMULAS.md section 3); for methanol NASA reports water absorption that raises K of small droplets and lowers it for large ones (NTRS 20130014061 section 3.1). Small heptane droplets (<= 2 mm) are at 0.84, close to the L&W accuracy.
- H4 (He): helium still lowers the ratio (methanol He 0.81-0.92 vs N2 0.94-1.01): $\lambda_{a1}$ carries helium's conductivity at 60 % weight into region 1; non-unity Lewis number of He is not in the formula.
- H6 (heptane conductivity): $\lambda_{F1}$ for heptane is extrapolated (no tabulated value); since $0.4\lambda_{F1}$ is about half of $\lambda_1$ for heptane at $T_1$, a 10 % error in $\lambda_{F1}$ changes K by about 5 %.

What is left (size, He, CO2 trends) is what the per-fuel calibration $c_f$ and the ML residual (stage 5) should take.

## 9. Assumptions

| ID | Assumption | Effect |
|---|---|---|
| A1 | $T_\infty$ = 298.15 K (no temperature in the FLEX CSV; FLEX-2 table lists 25 C) | small |
| A3 | Property tables end at 1500 K (ambient gases, heptane cp): $T_1$ and $T_2$ capped there; 0 model rows capped in the current version | - |
| A4 | Mole fractions renormalised to 1 inside the property calculation only (6 tests sum to 0.98) | negligible |
| A5 | Ambient-gas cp, lambda, mu at 1 atm used at 0.5-3 atm (ideal gas) | small |
| A6 | Droplet surface at $T_b(P)$; no heat-up, no water absorption | K high for large methanol droplets |
| A8 | L&W "air" replaced by the actual FLEX ambient mixture (O2 + N2/CO2/He) in $\lambda_{a1}$, $T_f$, $\rho_2$, $\mu_2$; $x$ = 0.4 kept for all fuels and atmospheres (as L&W did) | He and CO2 atmospheres are outside L&W's calibration |
| A9 | Heptane $\lambda_{F1}$ from viscosity extrapolated linearly in carbon number (C5, C6 -> C7) | H6 |
| A10 | Earth correction applied far outside its fitted range (Gr up to ~10^2 vs fitted Gr <~ 1) | Earth K only as labelled extrapolation |

## 10. What the theory does not describe

- Unsteady effects: droplet heat-up, water absorption (methanol), fuel-vapour accumulation; radiative loss in the burning rate.
- Extinction (only proxies); cool flames (heptane, TP-FLEX notes); disruption; drift convection.
- No textbook worked examples could be used for tests (Turns, Law, Glassman, PAKhT texts not accessible to Claude); tests check NIST and NASA source values, limits and monotonicity.

## 11. References

- Law, C. K.; Williams, F. A. Combustion and Flame 19 (1972) 393-405, DOI 10.1016/0010-2180(72)90009-0 - Eqs. (1), (4), (9); pp. 394-395, 396, 399, 403, 404.
- Nayagam, V.; Dietrich, D. L.; Hicks, M. C.; Williams, F. A. NTRS 20130014061 (5th US Combustion Meeting paper 070HE-0303).
- Williams, F. A.; Nayagam, V. presentation, NTRS 20205008449 (statement on property prescriptions).
- Svehla, R. A. "Estimated Viscosities and Thermal Conductivities of Gases at High Temperatures", NASA TR R-132, 1962, NTRS 19630012982 - Eq. (2) p. 3; Table III p. 56; Table IV p. 119 (transcription `data/raw/nasa_tr_r132/svehla_1962_extract.csv`).
- McBride, B. J.; Gordon, S.; Reno, M. A. NASA TM-4513, 1993 (thermo data used through Cantera `nasa_gas.yaml`).
- Gordon, S.; McBride, B. J. NASA RP-1311, 1994, NTRS 19950013764 - Eqs. (5.3)-(5.6).
- NIST Chemistry WebBook, NIST SRD 69, https://webbook.nist.gov, accessed 2026-11-14.
- Dietrich, D. L. et al. NASA/TP-2015-216046 (FLEX), NTRS 20150023456.
- Cantera 3.2.0 (Goodwin et al.), https://cantera.org - equilibrium solver.
- docs/FORMULAS.md (Ruslan): flame standoff and radiation proxies (sections 2-3).
