"""Risk map: hybrid burning rate relative to ISS air over O2 x pressure, tested points, cabin atmospheres (UI_SPEC page 4)."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from common import PLOT_TEMPLATE, flex, next_step, risk_grid, source_note
from i18n import t

from fif.insights.scenario import PRESETS

SHORT = {"ISS cabin air": "ISS air", "Moon base / rover (planned)": "Moon base"}

st.title(t("Risk map: oxygen x pressure"))
st.markdown(
    t(
        "Colour = predicted burning rate relative to ISS cabin air (hybrid model, 3 mm droplet, N2 balance). "
        "Dimmed cells are outside the conditions NASA tested for that fuel (O2 within ±0.02 at that pressure); light dots "
        "are the FLEX tests, stars are real or planned cabin atmospheres."
    )
)
with st.expander(t("How to read this map"), expanded=True):
    st.markdown(
        "\n".join(
            "- " + t(x)
            for x in (
                "Right = more oxygen, up = higher cabin pressure.",
                "Darker red = the droplet burns faster than in ISS air (1 = same as the ISS); pale yellow = slower.",
                "Bright cells are backed by NASA tests nearby; dimmed cells are model extrapolation - trust them less.",
                "Compare the two stars: the planned Moon-base air sits in a redder cell than ISS air.",
            )
        )
    )
fuel = st.radio(t("Fuel"), ["Methanol", "Heptane"], horizontal=True, format_func=t)
g = risk_grid(fuel, 3.0)
o2 = np.sort(g["x_o2"].unique())
p = np.sort(g["p_atm"].unique())
z = g.pivot(index="p_atm", columns="x_o2", values="ratio_vs_iss").loc[p, o2].to_numpy()
st_ = g.pivot(index="p_atm", columns="x_o2", values="status").loc[p, o2].to_numpy()
fig = go.Figure(
    go.Heatmap(
        x=o2,
        y=p * 14.696,
        z=z,
        colorscale="YlOrRd",
        zmin=0.4,
        zmax=1.6,
        colorbar=dict(title="K / K(ISS air)"),
        hovertemplate="O2 %{x:.2f}<br>p %{y:.1f} psi<br>K / K_ISS %{z:.2f}<extra></extra>",
    )
)
# grey veil over cells outside the tested conditions (instead of markers on every cell)
veil = np.where(st_ != "in range", 1.0, np.nan)
fig.add_trace(
    go.Heatmap(
        x=o2,
        y=p * 14.696,
        z=veil,
        colorscale=[[0, "rgba(21,29,51,0.72)"], [1, "rgba(21,29,51,0.72)"]],
        showscale=False,
        hoverinfo="skip",
        name=t("outside tested conditions"),
    )
)
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(size=12, color="rgba(90,100,125,0.9)", symbol="square"),
        name=t("outside tested conditions (dimmed)"),
    )
)
f = flex()
f = f[(f["fuel"] == fuel) & f["use_in_model"] & (f["diluent"] == "N2")]
fig.add_trace(
    go.Scatter(
        x=f["x_o2"],
        y=f["p_atm"] * 14.696,
        mode="markers",
        marker=dict(size=7, color="#EDE9E1", line=dict(width=1, color="#0D1322")),
        name=t("NASA FLEX tests (N2)"),
        hovertemplate="FLEX %{text}<extra></extra>",
        text=f["flex_identifier"],
    )
)
for name, a in PRESETS.items():
    if a["x_o2"] <= 0.41:
        fig.add_trace(
            go.Scatter(
                x=[a["x_o2"]],
                y=[a["p_atm"] * 14.696],
                mode="markers+text",
                text=[f"<b>{t(SHORT.get(name, name))}</b>"],
                textposition="top center",
                textfont=dict(size=14, color="#EDE9E1"),
                marker=dict(size=18, symbol="star", color="#7FA6FF", line=dict(width=2, color="#0D1322")),
                name=t(name),
            )
        )
fig.update_layout(
    template=PLOT_TEMPLATE,
    height=700,
    xaxis_title=t("Oxygen mole fraction"),
    yaxis_title=t("Cabin pressure, psi"),
    legend=dict(orientation="h", y=-0.18),
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig, width="stretch")
st.caption(
    t(
        "Spacesuit (100 % O2, {p:.1f} psi) lies far outside this map and all tested data.",
        p=PRESETS["Spacesuit"]["p_atm"] * 14.696,
    )
)
source_note(
    t(
        "hybrid model (docs/MODEL_CARD.md); FLEX tests: NASA PSI-69; cabin atmospheres: NASA/TP-2015-216046 Table I and "
        "the challenge page"
    )
)

next_step("views/risk_map.py")
