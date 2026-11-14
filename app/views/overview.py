"""Overview: problem, 4 live metrics, top-3 insights, entry points (UI_SPEC page 1)."""

import math

import pandas as pd
import streamlit as st
from common import ROOT, evidence_badge, flex, insights, investigations, validation
from i18n import t, tr_insight

st.title(t("Prometheus-0g - Will it burn on the Moon?"))
st.markdown(
    "**"
    + t("Physics-first, AI-assisted fire-safety insights from NASA microgravity combustion experiments.")
    + "**  \n"
    + t(
        "NASA's ISS fire experiments, verified and turned into ranked fire-safety insights for spacecraft, stations and Moon bases."
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
