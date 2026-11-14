# Physics

Stage 4 (2026-11-14). Code: `src/fif/physics/` (`properties.py`, `mixing.py`, `droplet.py`). Comparison with data: `scripts/physics_vs_data.py`. Decisions: ADR-022 (theory level), ADR-023 (property evaluation), ADR-024 (gravity baseline), ADR-025 (physics features for ML).

## 1. Scope

| Combustion type (dataset) | What the physics layer does | Status |
|---|---|---|
| Liquid droplets (FLEX, PSI-69) | quasi-steady burning-rate constant, flame temperature, transfer number, extinction proxies, Earth-gravity estimate | implemented (L2 + L3 proxies) |
| Gaseous spherical diffusion flames (CFI-G, PSI-159) | no own model: adiabatic flame temperature `Tad` and stoichiometric mixture fraction `Zst` as computed by the PSI table authors are used as physics features of the data map | data only (ADR-012, ADR-022) |
| Solids (BASS-II), jet flames, smoke | not in scope of the MVP (ADR-007, ADR-012); formulas in docs/FORMULAS.md sections 4, 5, 7 not implemented | - |

## 2. Theory levels for droplets

**L1 - classical quasi-steady theory**, as used by NASA to compare FLEX data (Nayagam, Dietrich, Hicks, Williams, NTRS 20130014061, Eqs. 1-2):

$$K = \frac{8\,\lambda_g}{\rho_l\,c_{p,g}}\,\ln(1+B), \qquad B = \frac{q_f\,Y_{O,\infty}\,\nu_f + c_{p,g}\,(T_\infty - T_b)}{L}$$

with $\nu_f$ the stoichiometric fuel-to-oxygen mass ratio ($\nu_f = 1/\nu_s$ below). The NASA paper evaluates properties "according to the semi-empirical recipe proposed by Law and Williams" (Combust. Flame 19 (1972) 393-405, DOI 10.1016/0010-2180(72)90009-0), which was not accessible to Claude (ADR-023).

Law & Williams (1972), Eq. (1) and the paragraph after it (supplied by Ruslan, 2026-11-14): $k_0 = \frac{8}{\rho_F}\frac{\lambda_1}{C_1}\ln(1+B)$, $B = [Y_{O\infty}\,q/i - c_1(T_b - T_\infty)]/L$; $q$ = heat of combustion per unit mass of fuel at $T_\infty$, $i$ = stoichiometric oxygen-fuel mass ratio, $L$ = latent heat at the boiling point, $\rho_F$ = liquid density at $T_b$; subscripts 1 and 2 = gas regions inside and outside the flame; elementary assumptions: Lewis numbers of unity, $\lambda_1 = \lambda_2$ = const, $c_1 = c_2$ = const.

**L2 - implemented (ADR-022, corrected by ADR-026):** L1 plus
- $T_b(P)$ from the NIST saturation curve (interpolated in $\ln P$), so pressure enters through $T_b$, $L(T_b)$, $\rho_l(T_b)$;
- **$C_1$ in K and B = ideal-gas cp of the fuel vapour** (NIST gas-phase tables: methanol TRC 1997, n-heptane Scott 1974) at $\bar T = (T_b + T_f)/2$ (capped at the table end: 3000 K methanol, 1500 K heptane; 21 model rows capped). This is the inner-region heat capacity of L&W Eq. (1). The first stage-4 version used the cp of the ambient gas and over-predicted K by 2x (methanol) and 4x (heptane); it is kept as column `K_theory_ambient_cp` for comparison;
- $\lambda_1$ = conductivity of the ambient mixture (O2 + N2/CO2/He, NASA RP-1311 mixing rules, section 4) at $\bar T$, using the L&W assumption $\lambda_1 = \lambda_2$ (NIST has no fuel-vapour conductivity at flame temperatures);
- $q = Q$ = **lower** heating value (water leaves the flame as vapour); the higher heating value from the same NIST data is 22.65 MJ/kg (methanol) and 48.07 MJ/kg (heptane), section 6;
- flame temperature with the outer-region cp $c_2$ = cp of the ambient mixture;
- flame temperature from the Burke-Schumann flame sheet (docs/FORMULAS.md section 2):

$$Z_{st} = \frac{Y_{O,\infty}}{Y_{O,\infty} + \nu_s}, \qquad T_f = T_\infty + Z_{st}\left[(T_s - T_\infty) + \frac{Q - L}{c_{p,g}}\right], \quad T_s = T_b$$

solved by fixed-point iteration because $c_{p,g}$ depends on $\bar T$ (30 iterations).

**L3 - proxies for extinction (ADR-022), pre-ignition inputs only, constants unknown (not calibrated in stage 4):**
- flame-standoff ratio (FORMULAS.md section 2): $r_f/r_s = \ln(1+B)/\ln(1 + Y_{O,\infty}/\nu_s)$;
- radiative-loss fraction proxy at ignition: $\chi_{rad}/\kappa = \sigma\,P\,T_f^4\,r_{s0}^2\,(r_f/r_s)^3\,c_{p,g}/(3\,\lambda_g\,\ln(1+B)\,Q)$ [Pa m], from $\dot Q_{rad} = 4\sigma a_P T_f^4 V_f$ (optically thin, FORMULAS.md section 3) with $a_P = \kappa P$ and $\dot m_F = 4\pi\lambda_g r_s\ln(1+B)/c_{p,g}$; the Planck-mean absorption per unit pressure $\kappa$ is not sourced and is left out (one unknown constant);
- flow (residence) time at the flame $\tau = r_f^2/\alpha_g$ [s]; the chemical time needs $A$, $E_a$ (FORMULAS.md section 3) which are not sourced, so no Damköhler number is formed.

Cool flames (heptane, after radiative extinction of the hot flame) are documented in NASA/TP-2015-216046 test notes (e.g. "cool flame burning and extinction") but are outside the quasi-steady theory; they enter only as NASA literature in the insights.

## 3. Gravity: ISS vs Earth (ADR-024)

Base = microgravity: the data are ISS data and the quasi-steady theory assumes pure diffusion (Nu = 2). Earth estimate (evidence type `physics theory`, never shown as data), docs/FORMULAS.md section 6:

$$Nu = 2 + 0.6\,Gr^{1/4}\,Pr^{1/3}, \qquad \frac{K_{1g}}{K_{0g}} \approx \frac{Nu}{2}, \qquad Gr = \frac{g\,(T_f - T_\infty)\,d^3}{T_\infty\,\nu^2}$$

with $\nu = \mu_{mix}/\rho_g$ at $\bar T$, $d = d_0$, $g = 9.80665$ m/s². The correlation source (Ranz & Marshall 1952, cited in FORMULAS.md) was not accessible to Claude; it is used as given by Ruslan. For FLEX conditions Nu_earth = 2.5-6.0 (median 3.4), i.e. the same droplet would burn ~1.7x faster on Earth by this estimate.

## 4. Mixture rules (NASA RP-1311, Gordon & McBride 1994, CEA Part I, pp. 21-22; read from the rendered pages)

$$\eta_{mix} = \sum_i \frac{x_i\eta_i}{x_i + \sum_{j\ne i} x_j\phi_{ij}}, \quad \lambda_{mix} = \sum_i \frac{x_i\lambda_i}{x_i + \sum_{j\ne i} x_j\psi_{ij}} \quad\text{(5.3, 5.4)}$$

$$\phi_{ij} = \frac14\left[1 + \left(\frac{\eta_i}{\eta_j}\right)^{1/2}\left(\frac{M_j}{M_i}\right)^{1/4}\right]^2\left(\frac{2M_j}{M_i+M_j}\right)^{1/2}, \quad \psi_{ij} = \phi_{ij}\left[1 + \frac{2.41(M_i - M_j)(M_i - 0.142M_j)}{(M_i+M_j)^2}\right] \quad\text{(5.5, 5.6)}$$

Eq. (5.5) is algebraically identical to the Wilke form in FORMULAS.md section 1 (checked in `tests/test_physics.py`). $c_{p,mix} = \sum_i Y_i c_{p,i}(T)$. Fuel vapour and combustion products are not part of the mixture (assumption A2).

## 5. Assumptions

| ID | Assumption | Effect / where it matters |
|---|---|---|
| A1 | $T_\infty$ = 298.15 K for all FLEX tests (FLEX CSV has no temperature; the FLEX-2 PSI-68 table lists 25 C) | small; enters B and $T_f$ |
| A2 | $C_1$ = pure fuel-vapour cp (no products, no inert in the inner region); $\lambda_1$ = ambient-mixture conductivity ($\lambda_1 = \lambda_2$, L&W); $c_2$ for $T_f$ = ambient-mixture cp (ADR-023, ADR-026) | $C_1$ of pure vapour is an upper bound of the real inner-region cp -> K slightly low (methanol ratio 1.36) |
| A3 | $\bar T = (T_b + T_f)/2$ ("1/2 rule", ADR-023), capped at 1500 K (end of the NIST tables): 38 of 274 model rows capped (`T_bar_capped`) | high-O2 / high-$T_f$ rows |
| A4 | Mole fractions renormalised to sum 1 inside the property calculation only (6 tests sum to 0.98, ADR-015 keeps the data unchanged) | negligible |
| A5 | cp, $\lambda$, $\mu$ of gases taken at 1 atm and used at 0.5-3 atm (ideal gas); density from the ideal-gas law | small for these gases |
| A6 | Droplet surface at the boiling point; $\rho_l$, $L$ at $T_b(P)$; no droplet heat-up, no liquid-phase mixing | K slightly high early in burning |
| A7 | Constant-cp flame sheet, no dissociation, no radiation in $T_f$ | $T_f$ up to 3800 K at O2 = 0.34: unphysically high |

## 6. Property data (every value with source and temperature)

Generated from the raw NIST files by the code (2026-11-14). NIST Chemistry WebBook, NIST Standard Reference Database 69, https://webbook.nist.gov, files in `data/raw/nist/` (sha256 in `data/catalog.yaml`).

| Quantity | Methanol | n-Heptane | Unit | Source (NIST SRD 69, accessed 2026-11-14) | Condition |
|---|---|---|---|---|---|
| Molar mass M | 32.04 | 100.2 | g/mol | species page, Molecular weight | - |
| Boiling point T_b | 337.6 | 371.6 | K | saturation table (interpolated in ln P) | 1 atm |
| Heat of vaporisation L = h_v - h_l | 1101 | 316.7 | kJ/kg | saturation table | at T_b(1 atm) |
| Liquid density rho_l | 748.3 | 613.5 | kg/m3 | saturation table | at T_b(1 atm) |
| Liquid cp | 2.826 | 2.558 | kJ/(kg K) | saturation table (not used in L2) | at T_b(1 atm) |
| -Delta_c H (liquid, H2O liquid) | 725.7 | 4817 | kJ/mol | species page: methanol Chao & Rossini 1965 (-725.7 ± 0.1); heptane NIST average of 7 (-4817 ± 8) | 298.15 K |
| Higher heating value HHV = -Delta_c H / M | 22.65 | 48.07 | MJ/kg | computed from the row above (water liquid in products) | 298.15 K |
| Lower heating value Q (used in B and T_f) | 19.90 | 44.56 | MJ/kg | computed: HHV - n_H2O M_H2O L_water / M_fuel; n_H2O = 2 (methanol), 8 (heptane); L_water = 2440.8 kJ/kg at 298.15 K (NIST water saturation table) | 298.15 K |
| Fuel-vapour ideal-gas cp (C_1) | 89.54 J/(mol K) = 2794 J/(kg K) | 381.58 J/(mol K) = 3808 J/(kg K) | at 1000 K | gas-phase page: methanol TRC 1997 (50-3000 K); heptane Scott 1974 (200-1500 K) | used at T_bar |
| Stoichiometric O2/fuel mass ratio nu_s | 1.498 | 3.513 | - | computed from global stoichiometry and NIST molar masses | - |

Gases (NIST fluid tables at 1 atm, 300-1500 K in 50 K steps; values at 300 K and 1200 K shown):

| Gas | M, g/mol | cp 300 K | cp 1200 K, J/(kg K) | lambda 300 K | lambda 1200 K, W/(m K) | mu 300 K | mu 1200 K, Pa s |
|---|---|---|---|---|---|---|---|
| O2 | 31.9988 | 919.9 | 1115 | 0.02649 | 0.0825 | 2.065e-05 | 5.534e-05 |
| N2 | 28.0134 | 1041 | 1204 | 0.02597 | 0.07468 | 1.789e-05 | 4.677e-05 |
| CO2 | 44.0095 | 852.6 | 1280 | 0.01677 | 0.08402 | 1.5e-05 | 4.684e-05 |
| He | 4.0026 | 5193 | 5193 | 0.156 | 0.4097 | 1.993e-05 | 5.252e-05 |

Physical constants: $\sigma$ = 5.670374419e-8 W/(m² K⁴), $R_u$ = 8.314462618 J/(mol K) (CODATA 2018); $g$ = 9.80665 m/s² (standard gravity).

## 7. Raw theory vs FLEX data (no calibration; 274 model rows)

Figures: `docs/figures/physics_K_parity.png`, `physics_K_ratio_groups.png`, `physics_extinction_proxies.png`; table: `docs/verification/physics_vs_data.tsv`.

| Finding | First version (ambient-gas cp, stage 4 12:40) | Corrected (C_1 = fuel-vapour cp, ADR-026, 12:51) |
|---|---|---|
| median $K_{meas}/K_{theory}$ | methanol 0.52, heptane 0.24 | **methanol 1.36, heptane 0.89** |
| spread of ln(ratio) within a fuel | methanol 0.15, heptane 0.28 | methanol 0.18, heptane 0.30 |
| corr(ln ratio, d0): larger droplets burn slower than theory | -0.37 / -0.42 | -0.24 / -0.34 |
| helium effect over-predicted | corr(ln ratio, x_He) methanol -0.56 | methanol -0.78 (ratio He 0.85-1.05 vs N2/CO2 1.34-1.41); heptane -0.28 (He 0.67-0.78 vs N2/CO2 0.85-0.97) |
| CO2 | methanol +0.36 | methanol +0.24, heptane -0.22 |
| $T_f$ at O2 0.30-0.34 | up to 3800 K (A7) | unchanged (T_f uses the outer-region cp) |
| extinction: "no finite-diameter extinction" at high $T_f$ | qualitative | unchanged |

Cause of the first version's error: $K \propto \lambda/C$; the cp of the fuel vapour at flame-zone temperatures is 2.4x (methanol) and 3.3x (heptane) the cp of air at 1000 K (NIST), almost exactly the 2x / 4x over-prediction. Using the ambient-gas cp was a modelling error against the L&W Eq. (1) definition, not an arithmetic one; the heating value was not the cause (Q = LHV 19.90 MJ/kg is correct for vapour-phase products; using the HHV 22.65 MJ/kg would raise K further).

**Hypotheses for the remaining errors (for discussion):**
- H1' (methanol 1.36): pure-vapour $C_1$ is an upper bound; the real inner region also holds products and N2 with lower cp. In addition the NASA paper reports water absorption by methanol droplets, which raises the measured K of small droplets (NTRS 20130014061 section 3.1).
- H2: $T_f$ without dissociation or radiation (A7) inflates $\bar T$ and $\lambda_1$, most at high O2.
- H3 (d0 trend): radiative heat loss grows with flame size (FORMULAS.md section 3); water absorption (methanol).
- H4 (He): $\lambda_1 = \lambda_2$ puts helium's conductivity into the inner region, where there is little helium; non-unity Lewis number of He is not in the formula.
- H5 (CO2): radiation and chemistry of CO2 not in L2.

The per-fuel constant left (methanol 1.36, heptane 0.89) is what the calibration $c_f$ (FORMULAS.md section 8, stage 5) absorbs; the trends (H3-H5) are what the ML residual should learn.

## 8. What the theory does not describe; limits of applicability

- Unsteady effects: droplet heat-up, water absorption/condensation (methanol), fuel-vapour accumulation.
- Radiative and diffusive extinction are only proxies (unknown constants $\kappa$, $A$, $E_a$).
- Cool flames, disruption (heptane) and convection from droplet drift.
- Pressures 0.5-3 atm and O2 0.12-0.34 (FLEX range); outside, the NIST property cap (1500 K) and A7 dominate.
- No textbook worked examples could be used for tests (Turns, Law, Glassman not accessible to Claude); tests check NIST data, the NASA source equations, limits and monotonicity instead.

## 8a. Law & Williams (1972) fragments received 2026-11-14 12:43 (Eq. 1 and its definitions used since ADR-026; Eqs. 8-10 and the E relation not yet used)

Screenshots from Ruslan (transcription in RESEARCH_LOG.md, 12:43). Eq. (1) $k_0 = \frac{8}{\rho_F}\frac{\lambda_1}{C_1}\ln(1+B)$ uses properties of an inner region (index 1), supporting H1; the definitions of $\lambda_1$, $C_1$ are not in the screenshots. Eq. (9), a 1-g correlation for alkanes, $k = k_0[1 + 0.533\,Gr^{0.52}][1 - 3.80\times10^{-5}(d\,p^{0.84})^{-1.9}]$ ($d$ in cm, $p$ in atm), could replace the FORMULAS.md section 6 estimate for the Earth comparison; the extinction relation $E = R^0\ln[(d_a/d_b)^2(p_a/p_b)^{1.68}]/(1/T_{fa} - 1/T_{fb})$ could give an activation energy from FLEX extinction pairs (needed for a real Damköhler number). Both await Ruslan's decision.

## 9. References

- Nayagam, V.; Dietrich, D. L.; Hicks, M. C.; Williams, F. A. "Methanol Droplet Combustion in Oxygen-Inert Environments in Microgravity", 5th US Combustion Meeting, paper 070HE-0303 (as printed in the paper footer), NTRS 20130014061, https://ntrs.nasa.gov/citations/20130014061 - Eqs. (1), (2), section 3.1.
- Gordon, S.; McBride, B. J. "Computer Program for Calculation of Complex Chemical Equilibrium Compositions and Applications, Part I: Analysis", NASA RP-1311, 1994, NTRS 19950013764 - Eqs. (5.3)-(5.6), pp. 21-22.
- NIST Chemistry WebBook, NIST Standard Reference Database 69 (Linstrom & Mallard, eds.), https://webbook.nist.gov, accessed 2026-11-14.
- Dietrich, D. L. et al. NASA/TP-2015-216046 (FLEX detailed results), NTRS 20150023456.
- Law, C. K.; Williams, F. A. Combustion and Flame 19 (1972) 393-405, DOI 10.1016/0010-2180(72)90009-0 - cited by Nayagam et al. for property evaluation; not read (paywalled).
- docs/FORMULAS.md (Ruslan): Burke-Schumann $T_f$ and $Z_{st}$ (section 2), radiation (section 3), gravity correlation (section 6); textbook sources named there were not accessible to Claude.
