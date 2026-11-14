"""Moon-base scenario: conditions in, physics + hybrid prediction with band, reliability, ISS/Earth comparison (UI_SPEC page 3)."""
import streamlit as st

from common import scenario, source_note, status_badge

from fif.insights.scenario import PRESETS

st.title("Moon-base scenario")
st.markdown("How fast would a fuel droplet burn in a given cabin atmosphere, compared with ISS air? "
            "Physics (Law & Williams 1972) + per-fuel calibration + machine-learned correction, trained on NASA's FLEX tests.")

c_in, c_out = st.columns([1, 2])
with c_in:
    preset = st.selectbox("Atmosphere preset", list(PRESETS) + ["Custom"], index=1)
    base = PRESETS.get(preset, PRESETS["Moon base / rover (planned)"])
    if preset in PRESETS:
        st.caption("Preset source: " + base["src"])
    fuel = st.radio("Fuel", ["Methanol", "Heptane"], horizontal=True)
    x_o2 = st.slider("Oxygen mole fraction", 0.10, 1.00, float(base["x_o2"]), 0.01, disabled=preset in PRESETS)
    p_psi = st.slider("Pressure, psi", 3.0, 45.0, float(round(base["p_atm"] * 14.696, 1)), 0.1, disabled=preset in PRESETS)
    dil = st.radio("Extra diluent (replaces N2)", ["none", "CO2", "He"], horizontal=True)
    x_dil = st.slider("Diluent mole fraction", 0.0, 0.7, 0.0, 0.05, disabled=dil == "none")
    d0 = st.slider("Initial droplet diameter, mm", 1.0, 5.0, 3.0, 0.1)
    p_atm = p_psi / 14.696
    x_co2 = x_dil if dil == "CO2" else 0.0
    x_he = x_dil if dil == "He" else 0.0
    if x_o2 + x_co2 + x_he > 1.0:
        st.error("O2 + diluent exceed 1; reduce the diluent.")
        st.stop()

r = scenario(fuel, round(p_atm, 4), x_o2, x_co2, x_he, d0)
rel = r["reliability"]
with c_out:
    st.markdown("Status: " + status_badge(rel["status"]), unsafe_allow_html=True)
    for reason in rel["reasons"]:
        st.caption("- " + reason)
    m1, m2, m3 = st.columns(3)
    if r["K_hybrid_mm2_s"] is not None:
        m1.metric("K, hybrid model", f"{r['K_hybrid_mm2_s']:.2f} mm²/s",
                  help=f"95 % band {r['K_band_mm2_s'][0]:.2f}-{r['K_band_mm2_s'][1]:.2f} mm²/s")
        m1.caption(f"95 % band {r['K_band_mm2_s'][0]:.2f}-{r['K_band_mm2_s'][1]:.2f} mm²/s")
    else:
        m1.metric("K, hybrid model", "withheld")
        m1.caption("Model uncertainty too large: physics only")
    m2.metric("K, physics only", f"{r['K_theory_mm2_s']:.2f} mm²/s")
    m3.metric("vs ISS cabin air", f"{(r['ratio_vs_iss'] - 1) * 100:+.0f} %", help=f"Basis: {r['ratio_basis']}")
    m4, m5, m6 = st.columns(3)
    m4.metric("Flame temperature", f"{r['T_f_K']:.0f} K")
    m5.metric("P(self-extinction)", f"{r['P_extinction'] * 100:.0f} %",
              help="Logistic model on physics features; trend only outside tested atmospheres (Validation)")
    m6.metric("On Earth (1 g)", f"×{r['earth_factor']:.1f} faster",
              help=f"Law & Williams buoyancy correction, Gr = {r['earth_Gr']:.1f}; fitted only for Gr <= 1 - physics theory, extrapolated")
    st.markdown("**Nearest NASA FLEX tests (measured K, mm²/s)**")
    st.caption("K = burning-rate constant, the slope of droplet diameter squared vs time (d²-law); higher K = faster burning.")
    st.dataframe(r["nearest_tests"].round({"p_atm": 3, "x_o2": 2, "x_co2": 2, "x_he": 2}).rename(columns={"flex_identifier": "FLEX id", "x_o2": "O2", "x_co2": "CO2", "x_he": "He",
                                                     "p_atm": "p, atm", "d0_mm_orig": "d0, mm", "K_mm2_s_orig": "K measured, mm²/s",
                                                     "test_end": "test end", "source_id": "source", "row_id": "row"}),
                 hide_index=True, use_container_width=True)
    source_note("NASA PSI-69 FLEX + NASA/TP-2015-216046; models: docs/MODEL_CARD.md; reliability rule: ADR-031")
