"""Ranked insights with stage filter, evidence badges, history and Earth blocks (UI_SPEC page 2)."""

import streamlit as st
from common import STAGE_LABEL, evidence_badge, insights

st.title("Fire-safety insights")
st.markdown(
    "Ranked by evidence strength x number of tests x effect size (formula in Method & sources). "
    "Every number is computed live from NASA data or our models."
)
data = insights()
stages = st.multiselect("Stage", list(STAGE_LABEL), default=list(STAGE_LABEL), format_func=lambda s: STAGE_LABEL[s])

for rank, i in enumerate([x for x in data["ranked"] if x["stage"] in stages], 1):
    with st.container(border=True):
        st.markdown(f"#### {rank}. {i['title']}")
        tags = (
            evidence_badge(i["evidence_type"]) + f" &nbsp; **{STAGE_LABEL[i['stage']]}** &nbsp; n = {i['n_tests']} &nbsp; "
            f"confidence: **{i['confidence']}**" + (" &nbsp; :orange[extrapolation]" if i["extrapolation"] else "")
        )
        st.markdown(tags, unsafe_allow_html=True)
        st.write(i["finding"])
        st.markdown(f"**What to do:** {i['action']}")
        st.caption("Sources: " + "; ".join(i["sources"]) + (f" | Linked: {', '.join(i['related'])}" if i["related"] else ""))

st.header("Lessons from history")
for i in [x for x in data["history_and_earth"] if x["stage"] == "history"]:
    with st.container(border=True):
        st.markdown(f"**{i['title']}** &nbsp; " + evidence_badge(i["evidence_type"]), unsafe_allow_html=True)
        st.write(i["finding"])
        st.caption(i["action"] + " Source: " + i["sources"][0])

st.header("Benefits on Earth")
cols = st.columns(3)
for col, i in zip(cols, [x for x in data["history_and_earth"] if x["stage"] == "earth"]):
    with col.container(border=True):
        st.markdown(f"**{i['title']}**  \n" + evidence_badge(i["evidence_type"]), unsafe_allow_html=True)
        st.write(i["finding"])
        st.caption(i["action"] + " Source: " + i["sources"][0])
