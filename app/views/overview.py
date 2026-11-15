"""Overview: problem, 4 live metrics, top-3 insights, entry points (UI_SPEC page 1)."""

import math

import pandas as pd
import streamlit as st
from common import (
    ORANGE,
    ROOT,
    evidence_badge,
    flame_sim,
    flex,
    insights,
    investigations,
    moon,
    next_step,
    status_badge,
    validation,
)
from flame_view import render as render_flame
from i18n import flame_labels, t, tr_insight
from theme import kicker

from fif.insights.flame_sim import ATMOSPHERES

kicker(t("NASA Space Apps 2026 · Flame in Freefall · Team The Catalyst"))
st.title(t("Prometheus-0g - Fire on the Moon"))
st.markdown(
    "**"
    + t("Physics-first, AI-assisted fire-safety insights from NASA microgravity combustion experiments.")
    + "**  \n"
    + t(
        "NASA's ISS fire experiments, verified and turned into ranked fire-safety insights for spacecraft, stations and Moon bases."
    )
)


# ---- the headline answer (ADR-043): every number from fif.insights.moon
with st.container(border=True):
    head, pick = st.columns([3, 1])
    head.markdown(
        f"<div style='font-size:1.05rem;color:#6B7280;margin-bottom:-0.4rem'>{t('A fire on a Moon base, compared with the ISS')}</div>"
        f"<div style='font-size:2.0rem;font-weight:800;color:{ORANGE};line-height:1.25'>"
        f"{t('Faster, hotter, and less likely to go out by itself.')}</div>",
        unsafe_allow_html=True,
    )
    fuels = {t("Heptane"): "Heptane", t("Methanol"): "Methanol"}  # heptane first (Ruslan, 2026-11-15); translated labels
    fuel = fuels[pick.radio(t("Fuel"), list(fuels), horizontal=True)]
    a = moon(fuel)
    st.caption(
        t(
            "Planned Moon-base / rover air (30 % O2, 10.2 psi) compared with ISS cabin air (21 % O2, 14.7 psi), a 3 mm {fuel} "
            "droplet as in NASA's FLEX experiment.",
            fuel=t(fuel).lower(),
        )
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Burning rate vs ISS air"), f"{(a['k_ratio'] - 1) * 100:+.0f} %")
    c1.markdown(
        evidence_badge("model")
        + " "
        + status_badge(a["status"])
        + "<br><span style='font-size:0.8rem;color:#6B7280'>"
        + t("95 % band {lo:+.0f} to {hi:+.0f} %", lo=(a["k_ratio_band"][0] - 1) * 100, hi=(a["k_ratio_band"][1] - 1) * 100)
        + "</span>",
        unsafe_allow_html=True,
    )
    c2.metric(
        t("Droplet burns out in"),
        f"{a['burn_time_moon_s']:.1f} " + t("s"),
        delta=f"{a['burn_time_moon_s'] - a['burn_time_iss_s']:+.1f} " + t("s vs ISS"),
        delta_color="normal",
    )
    c2.markdown(
        evidence_badge("model")
        + " "
        + evidence_badge("physics theory")
        + "<br><span style='font-size:0.8rem;color:#6B7280'>"
        + t("on the lunar surface down to {t:.1f} s (1/6 g upper bound)", t=a["burn_time_lunar_surface_s"])
        + "</span>",
        unsafe_allow_html=True,
    )
    c3.metric(
        t("Flames that put themselves out"),
        f"{a['self_ext_high_o2'] * 100:.0f} %",
        delta=t("{d:+.0f} points vs O2 <= 21 %", d=(a["self_ext_high_o2"] - a["self_ext_low_o2"]) * 100),
        delta_color="normal",
    )
    c3.markdown(
        evidence_badge("NASA data")
        + "<br><span style='font-size:0.8rem;color:#6B7280'>"
        + t(
            "FLEX tests at O2 >= 30 %: n = {n1}; at O2 <= 21 %: {p0:.0f} % of {n0}",
            n1=a["n_high_o2"],
            p0=a["self_ext_low_o2"] * 100,
            n0=a["n_low_o2"],
        )
        + "</span>",
        unsafe_allow_html=True,
    )
    c4.metric(
        t("Flame temperature"),
        f"{a['flame_temperature_moon_K']:.0f} K",
        delta=f"{a['flame_temperature_moon_K'] - a['flame_temperature_iss_K']:+.0f} K " + t("vs ISS"),
        delta_color="inverse",
    )
    c4.markdown(
        evidence_badge("physics theory")
        + "<br><span style='font-size:0.8rem;color:#6B7280'>"
        + t("equilibrium flame temperature with dissociation")
        + "</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        evidence_badge("NASA literature")
        + " &nbsp;"
        + t(
            "For solid materials NASA expects lunar gravity to be nearly the most flammable condition - possibly worse than "
            "on Earth (NTRS 20210020516, 20260000646)."
        ),
        unsafe_allow_html=True,
    )
    by_id = {i["id"]: i for i in insights()["ranked"]}
    st.markdown(
        "**"
        + t("What a Moon base should do")
        + "**\n"
        + "\n".join(f"- {tr_insight(by_id[k], 'action')}" for k in ("S4", "D1", "P6") if k in by_id)
    )
    l1, l2, l3, l4 = st.columns([1.55, 1.25, 0.9, 1.1])
    l1.page_link("views/scenario.py", label=t("See it burn: Moon vs ISS animation"), icon=":material/local_fire_department:")
    l2.page_link("views/module.py", label=t("Fire in a Moon-base module"), icon=":material/home_work:")
    l3.page_link("views/assistant.py", label=t("Ask the data"), icon=":material/forum:")
    l4.page_link("views/validation.py", label=t("How sure are we?"), icon=":material/fact_check:")

# ---- see it burn, right on the home page: the same droplet in ISS air and in Moon-base air (both microgravity)
_iss, _mb, _earth = (
    ATMOSPHERES["ISS cabin air (microgravity)"],
    ATMOSPHERES["Moon base / rover (planned)"],
    ATMOSPHERES["Earth sea-level air (1 g)"],
)
render_flame(
    [
        flame_sim(fuel, round(_iss["p_atm"], 4), _iss["x_o2"], 0.0, 0.0, 3.0, 0, t("ISS cabin air (microgravity)")),
        flame_sim(fuel, round(_mb["p_atm"], 4), _mb["x_o2"], 0.0, 0.0, 3.0, 0, t("Moon base / rover (planned)")),
        flame_sim(fuel, round(_earth["p_atm"], 4), _earth["x_o2"], 0.0, 0.0, 3.0, _earth["g"], t("Earth sea-level air (1 g)")),
    ],
    flame_labels(),
    height=470,
)
st.caption(
    t(
        "The same 3 mm droplet burning in real time: ISS cabin air and Moon-base air (both weightless), and ordinary "
        "air on Earth at 1 g for comparison. The animation is driven by the model; the flame shape is illustrative and "
        "the 1 g burning rate is a physics extrapolation."
    )
)

st.markdown(
    t(
        "Without gravity a flame has no buoyant plume: it becomes a slow, spherical, diffusion-fed flame. NASA has run hundreds "
        "of such experiments on the ISS and published them in the Physical Sciences Informatics (PSI) database, but the results "
        "are hard to find, compare and interpret. Planned Moon bases and pressurized rovers will use **30 % or more oxygen at "
        "10.2 psi or less** - more flammable than ISS air. This dashboard turns the PSI combustion data into verified numbers, "
        "a physics-based model and ranked recommendations."
    )
)

v = validation()
inv = investigations()
fx = flex()
diff = pd.read_csv(ROOT / "docs" / "verification" / "flex_vs_tp.tsv", sep="\t")
hyb = v["repeated_cv"]["summary"]["K"]["hybrid"]["RMSE_log"]["mean"]
atm = ["He diluent", "CO2 diluent", "p ~0.7 atm (< 0.8)", "O2 >= 0.30 (Moon-like O2)"]
gain = [v["extrapolation"][a]["K"]["pure_ml_gp"]["RMSE_log"] / v["extrapolation"][a]["K"]["hybrid"]["RMSE_log"] for a in atm]

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("PSI investigations"), f"{len(inv)}", help=t("NASA PSI repository, Combustion Science"))
c2.metric(
    t("ISS tests analysed"),
    f"{len(fx)}",
    help=t("Checked cell by cell against NASA/TP-2015-216046: {n} differences", n=int((diff["status"] == "DIFF").sum())),
)
c3.metric(
    t("Typical model error"),
    f"±{(math.exp(hyb) - 1) * 100:.0f} %",
    help=t("Hybrid physics + ML model, grouped cross-validation over test regimes (Validation page)"),
)
c4.metric(
    t("Physics gain, new air"),
    f"{min(gain):.1f}-{max(gain):.1f}x",
    help=t("Pure-ML error divided by hybrid error when a whole atmosphere class is held out (He, CO2, ~0.7 atm, O2 >= 30 %)"),
)

st.subheader(t("Top insights"))
top = insights()["ranked"][:3]
cols = st.columns(3)
for col, i in zip(cols, top, strict=False):
    with col.container(border=True):
        st.markdown(f"**{tr_insight(i, 'title')}**")
        st.markdown(evidence_badge(i["evidence_type"]) + " &nbsp; " + t("n = {n} tests", n=i["n_tests"]), unsafe_allow_html=True)
        st.write(tr_insight(i, "finding"))
        st.caption(t("Action:") + " " + tr_insight(i, "action"))

b1, b2 = st.columns(2)
b1.page_link("views/scenario.py", label=t("Try the Moon-base scenario"), icon=":material/science:")
b2.page_link("views/validation.py", label=t("See how we validated"), icon=":material/fact_check:")
st.caption(
    t(
        "Team The Catalyst - NASA Space Apps Challenge 2026, challenge 'Flame in Freefall'. Data: NASA PSI (CC0), NASA NTRS, "
        "NIST. No NASA endorsement implied."
    )
)

next_step("views/overview.py")
