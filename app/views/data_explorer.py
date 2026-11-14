"""Data explorer: FLEX and CFI-G tables, filters, plots, quality flags, CSV download, row provenance (UI_SPEC page 6)."""
import plotly.express as px
import streamlit as st

from common import PLOT_TEMPLATE, cfig, flex, source_note

st.title("Data explorer")
tab1, tab2 = st.tabs(["FLEX droplets (PSI-69)", "CFI-G gaseous flames (PSI-159)"])

with tab1:
    f = flex()
    c1, c2, c3 = st.columns(3)
    fuel = c1.multiselect("Fuel", ["Methanol", "Heptane"], default=["Methanol", "Heptane"])
    dil = c2.multiselect("Diluent", ["N2", "CO2", "He"], default=["N2", "CO2", "He"])
    o2 = c3.slider("O2 mole fraction", 0.10, 0.35, (0.10, 0.35), 0.01)
    v = f[f["fuel"].isin(fuel) & f["diluent"].isin(dil) & f["x_o2"].between(*o2)]
    st.caption(f"{len(v)} of {len(f)} tests; quality flags explained in docs/DATA_QUALITY.md")
    fig = px.scatter(v, x="x_o2", y="K_mm2_s_orig", color="diluent", symbol="fuel", template=PLOT_TEMPLATE,
                     hover_data=["flex_identifier", "p_atm", "d0_mm_orig", "test_end", "quality_flag"],
                     labels={"x_o2": "O2 mole fraction", "K_mm2_s_orig": "burning-rate constant K, mm²/s", "diluent": "diluent"})
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, width="stretch")
    cols = ["flex_identifier", "fuel", "p_atm", "x_o2", "x_n2", "x_co2", "x_he", "d0_mm_orig", "d_ext_mm_orig", "K_mm2_s_orig",
            "burn_time_s", "test_end", "quality_flag", "use_in_model", "source_id", "source_file", "row_id"]
    st.dataframe(v[cols], hide_index=True, width="stretch")
    st.download_button("Download filtered FLEX data (CSV)", v[cols].to_csv(index=False).encode("utf-8"), "flex_filtered.csv", "text/csv")
    source_note("NASA PSI-69 Experimental Table (CC0) + 2 tests from NASA/TP-2015-216046 Table IX; units: p in atm, d in mm, K in mm²/s, "
                "time in s; columns source_id/source_file/row_id point to the raw row")

with tab2:
    c = cfig()
    fig = px.scatter(c, x="p_Pa", y="x_o2_oxidizer", color="end_mode", symbol="table", template=PLOT_TEMPLATE,
                     hover_data=["fuel_label", "test_id", "hot_ignition", "burn_time_s"],
                     labels={"p_Pa": "pressure, Pa", "x_o2_oxidizer": "O2 mole fraction of the oxidizer",
                             "end_mode": "end (SE self-extinguished, FT flow terminated)"})
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, width="stretch")
    ccols = ["table", "test_id", "fuel_label", "p_bar_orig", "x_o2_oxidizer", "tad_K", "z_st", "hot_ignition", "end_mode",
             "burn_time_s", "quality_flag", "source_file", "row_id"]
    st.dataframe(c[ccols], hide_index=True, width="stretch")
    st.download_button("Download CFI-G data (CSV)", c[ccols].to_csv(index=False).encode("utf-8"), "cfig.csv", "text/csv")
    source_note("NASA PSI-159 ACME CFI-G Experimental Tables (CC0); Tad and Zst as computed by the table authors")
