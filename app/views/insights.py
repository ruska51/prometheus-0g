"""Ranked insights with stage filter, evidence badges, history and Earth blocks (UI_SPEC page 2)."""

import streamlit as st
from common import STAGE_LABEL, evidence_badge, insights
from i18n import t, tr_insight

st.title(t("Fire-safety insights"))
st.markdown(
    t(
        "Ranked by evidence strength x number of tests x effect size (formula in Method & sources). "
        "Every number is computed live from NASA data or our models."
    )
)
data = insights()
stages = st.multiselect(t("Stage"), list(STAGE_LABEL), default=list(STAGE_LABEL), format_func=lambda s: t(STAGE_LABEL[s]))

for rank, i in enumerate([x for x in data["ranked"] if x["stage"] in stages], 1):
    with st.container(border=True):
        st.markdown(f"#### {rank}. {tr_insight(i, 'title')}")
        tags = (
            evidence_badge(i["evidence_type"])
            + f" &nbsp; **{t(STAGE_LABEL[i['stage']])}** &nbsp; n = {i['n_tests']} &nbsp; "
            + t("confidence:")
            + f" **{t(i['confidence'])}**"
            + (" &nbsp; :orange[" + t("extrapolation") + "]" if i["extrapolation"] else "")
        )
        st.markdown(tags, unsafe_allow_html=True)
        st.write(tr_insight(i, "finding"))
        st.markdown(f"**{t('What to do:')}** {tr_insight(i, 'action')}")
        st.caption(
            t("Sources:")
            + " "
            + "; ".join(i["sources"])
            + (f" | {t('Linked:')} {', '.join(i['related'])}" if i["related"] else "")
        )

st.header(t("Lessons from history"))
for i in [x for x in data["history_and_earth"] if x["stage"] == "history"]:
    with st.container(border=True):
        st.markdown(f"**{tr_insight(i, 'title')}** &nbsp; " + evidence_badge(i["evidence_type"]), unsafe_allow_html=True)
        st.write(tr_insight(i, "finding"))
        st.caption(tr_insight(i, "action") + " " + t("Source:") + " " + i["sources"][0])

st.header(t("Benefits on Earth"))
cols = st.columns(3)
for col, i in zip(cols, [x for x in data["history_and_earth"] if x["stage"] == "earth"], strict=False):
    with col.container(border=True):
        st.markdown(f"**{tr_insight(i, 'title')}**  \n" + evidence_badge(i["evidence_type"]), unsafe_allow_html=True)
        st.write(tr_insight(i, "finding"))
        st.caption(tr_insight(i, "action") + " " + t("Source:") + " " + i["sources"][0])
