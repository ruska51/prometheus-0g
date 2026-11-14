"""Validation: honest metrics, extrapolation, calibration, physicality, failures (UI_SPEC page 7)."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import PLOT_TEMPLATE, source_note, validation
from i18n import t

st.title(t("How much can you trust it?"))
v = validation()
s = v["repeated_cv"]["summary"]
atm = ["He diluent", "CO2 diluent", "p ~0.7 atm (< 0.8)", "O2 >= 0.30 (Moon-like O2)"]
gain = [v["extrapolation"][a]["K"]["pure_ml_gp"]["RMSE_log"] / v["extrapolation"][a]["K"]["hybrid"]["RMSE_log"] for a in atm]
st.markdown(
    "**"
    + t(
        "Inside the tested conditions the hybrid ({h:.3f}) and a pure machine-learning model ({m:.3f}) are equally accurate. "
        "When a whole atmosphere is left out of training (helium, CO2, ~0.7 atm, O2 >= 30 %), the physics makes the hybrid "
        "{g0:.1f}-{g1:.1f}x more accurate - the Moon-base case. No model transfers reliably to a fuel it has not seen.",
        h=s["K"]["hybrid"]["RMSE_log"]["mean"],
        m=s["K"]["pure_ml_gp"]["RMSE_log"]["mean"],
        g0=min(gain),
        g1=max(gain),
    )
    + "**"
)

st.subheader(t("Grouped cross-validation (5 folds by test regime, 5 seeds)"))
k = pd.DataFrame(
    [
        {
            t("model"): t(m),
            "RMSE ln K": f"{d['RMSE_log']['mean']:.3f} ± {d['RMSE_log']['sd']:.3f}",
            "MAE, mm²/s": f"{d['MAE']['mean']:.3f}",
            t("95 % coverage"): f"{d['coverage95']['mean']:.2f}",
        }
        for m, d in s["K"].items()
    ]
)
e = pd.DataFrame(
    [
        {
            t("model"): t(m),
            "AUC": "n/a" if m == "prior" else f"{d['AUC']['mean']:.3f} ± {d['AUC']['sd']:.3f}",
            "Brier": f"{d['Brier']['mean']:.3f}",
            t("balanced accuracy"): f"{d['balanced_accuracy']['mean']:.2f}",
        }
        for m, d in s["extinction"].items()
    ]
)
c1, c2 = st.columns(2)
c1.markdown(t("Burning-rate constant K"))
c1.dataframe(k, hide_index=True, width="stretch")
c2.markdown(t("Flame extinction (yes / no)"))
c2.dataframe(e, hide_index=True, width="stretch")

st.subheader(t("Extrapolation: train without a class of conditions, predict it"))
ex = v["extrapolation"]
names = [n for n in ex if ex[n]["K"]]
fig = go.Figure()
for mdl, col in (("physics", "#7C3AED"), ("pure_ml_gp", "#6B7280"), ("hybrid", "#1D4ED8")):
    fig.add_trace(
        go.Bar(
            name=t({"pure_ml_gp": "pure ML"}.get(mdl, mdl)),
            x=[t(n) for n in names],
            y=[ex[n]["K"][mdl]["RMSE_log"] for n in names],
            marker_color=col,
        )
    )
fig.update_layout(
    template=PLOT_TEMPLATE,
    barmode="group",
    height=420,
    yaxis_title=t("error on held-out class (RMSE ln K)"),
    legend=dict(orientation="h", y=1.12),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_tickangle=-25,
)
st.plotly_chart(fig, width="stretch")

st.subheader(t("Physical sanity checks"))
ph = v["physicality"]
yes_no = {True: t("yes"), False: t("no")}
k_up = all(c["K_increases_with_O2"] for c in ph["cases"].values())
p_down = all(c["P_ext_logistic_nonincreasing"] for c in ph["cases"].values())
st.markdown(
    "- "
    + t("Burning rate rises with O2 in every tested case:")
    + f" **{yes_no[k_up]}**\n- "
    + t("Probability of self-extinction never rises with O2 (interface model):")
    + f" **{yes_no[p_down]}**\n- "
    + t(
        "Model uncertainty grows outside the data (sigma ln K: {a:.2f} on data, {b:.2f} far outside)",
        a=ph["K_sigma_log_on_data"]["median"],
        b=max(q["sigma_log"] for q in ph["probes"].values()),
    )
)

st.subheader(t("Where the model fails most (and why we think so)"))
fl = pd.DataFrame(v["failures_hybrid_seed0"])[
    ["flex_identifier", "fuel", "diluent", "p_atm", "x_o2", "d0_mm_orig", "K_meas", "K_pred", "test_end", "quality_flag"]
]
fl = fl.rename(
    columns={
        "flex_identifier": "FLEX id",
        "fuel": t("fuel"),
        "diluent": t("diluent"),
        "x_o2": "O2",
        "p_atm": t("p, atm"),
        "d0_mm_orig": t("d0, mm"),
        "K_meas": t("K measured, mm²/s"),
        "K_pred": t("K predicted, mm²/s"),
        "test_end": t("test end"),
        "quality_flag": t("flags"),
    }
)
st.dataframe(fl.round(3), hide_index=True, width="stretch")
st.caption(
    t(
        "Hypotheses for each case: docs/VALIDATION.md section 8 (small droplets dominated by ignition transients, water "
        "absorption in large methanol droplets, sparse data above 1.2 atm, CO2 radiation)."
    )
)
source_note(t("docs/validation_results.json (generated {ts}); method in docs/VALIDATION.md", ts=v["created_utc"]))
