"""Moon-base scenario: conditions in, physics + hybrid prediction with band, reliability, ISS/Earth comparison (UI_SPEC page 3)."""
import streamlit as st

from common import evidence_badge, flame_sim, scenario, source_note, status_badge
from flame_view import render as render_flame

from fif.insights.flame_sim import ATMOSPHERES
from fif.physics.droplet import G_MOON_RATIO
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
    m7, m8 = st.columns([1, 2])
    m7.metric("On the lunar surface (1/6 g)", f"×1.0–{r['moon_factor']:.2f}",
              help=f"Partial-gravity bound: lower = microgravity rate, upper = Law & Williams buoyancy correction at 1/6 g "
                   f"(Gr = {r['moon_Gr']:.2f}; fitted for Gr <= 1). No partial-gravity data in PSI - physics theory.")
    m8.markdown(evidence_badge("NASA literature") + " &nbsp;**Solids may be worse on the Moon.** NASA Glenn: for solid materials "
                "\"Lunar gravity is nearly the most flammable condition\" (NTRS 20210020516); a partial-g habitat fire is expected "
                "to be \"substantially worse than in 0-g and potentially worse than even 1-g\" (NTRS 20260000646). "
                "Droplet burning rate (this page) and solid flammability limits are different questions.", unsafe_allow_html=True)

st.markdown("**See it burn: the same droplet in two atmospheres**")
same_1g, same_moon = "Your settings at 1 g (Earth)", "Your settings on the lunar surface (1/6 g)"
cmp_opts = [a for a in ATMOSPHERES if not (preset == "ISS cabin air" and a.startswith("ISS"))] + [same_moon, same_1g]
default_cmp = "Moon base on the lunar surface (1/6 g)" if preset.startswith("Moon") else "Earth sea-level air (1 g)"
cmp = st.columns([1, 2])[0].selectbox("Compare with (right panel; left panel = the atmosphere above)", cmp_opts,
                                     index=cmp_opts.index(default_cmp))
left_label = preset if preset in PRESETS else "Your settings"
left = flame_sim(fuel, round(p_atm, 4), x_o2, x_co2, x_he, d0, 0, left_label + " (microgravity)")
if cmp in (same_1g, same_moon):
    g = 1.0 if cmp == same_1g else G_MOON_RATIO
    right = flame_sim(fuel, round(p_atm, 4), x_o2, x_co2, x_he, d0, g, left_label + (" at 1 g" if g == 1 else " at 1/6 g"))
else:
    a = ATMOSPHERES[cmp]
    right = flame_sim(fuel, round(a["p_atm"], 4), a["x_o2"], 0.0, 0.0, d0, a["g"], cmp)
render_flame([left, right])
st.caption("Computed: droplet shrinking by the d²-law with K from the model (×(1 + f_B) with gravity: physics theory; on the Moon the "
           "upper bound of the range), "
           "burn time, extinction diameter (GP model, only inside tested conditions), flame temperature and soot colour "
           "(blackbody at T_f, an upper bound). Flame size: quasi-steady theory on a common relative scale - known to "
           "overestimate the measured flame several-fold (NASA NTRS 20130014061). Buoyant flame shape, flicker and sparks are illustrative.")
for n in dict.fromkeys(left["notes"] + right["notes"]):
    st.caption("- " + n)
st.markdown("**Nearest NASA FLEX tests (measured K, mm²/s)**")
st.caption("K = burning-rate constant, the slope of droplet diameter squared vs time (d²-law); higher K = faster burning.")
st.dataframe(r["nearest_tests"].round({"p_atm": 3, "x_o2": 2, "x_co2": 2, "x_he": 2}).rename(columns={"flex_identifier": "FLEX id", "x_o2": "O2", "x_co2": "CO2", "x_he": "He",
                                                 "p_atm": "p, atm", "d0_mm_orig": "d0, mm", "K_mm2_s_orig": "K measured, mm²/s",
                                                 "test_end": "test end", "source_id": "source", "row_id": "row"}),
             hide_index=True, width="stretch")
source_note("NASA PSI-69 FLEX + NASA/TP-2015-216046; models: docs/MODEL_CARD.md; reliability rule: ADR-031")
