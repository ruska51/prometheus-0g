"""PSI combustion investigations: relevance-ranked catalog with filters and details (UI_SPEC page 5, MVP M1/M2)."""

import plotly.graph_objects as go
import streamlit as st
from common import BLUE, ORANGE, PLOT_TEMPLATE, comparison, investigations, source_note

from fif.insights.compare import VARIABLES

st.title("NASA combustion investigations (PSI)")
st.markdown(
    "All 24 Combustion Science investigations in NASA's Physical Sciences Informatics repository, ranked by relevance "
    "to crew fire safety: 0.5 x fire-safety role + 0.3 x usable data + 0.2 x size of the data table (formula in Method & sources)."
)
tab_rank, tab_cmp = st.tabs(["Ranked catalog", "Compare investigations"])
with tab_rank:
    c = investigations()
    f1, f2, f3 = st.columns(3)
    stage = f1.multiselect("Fire-safety stage", ["prevention", "detection", "suppression", "other"], default=[])
    ftype = f2.multiselect("Fuel / subject", sorted(c["fuel_type"].unique()), default=[])
    only_data = f3.toggle("Only investigations with a data table", value=False)
    v = c.copy()
    if stage:
        v = v[v["stage"].isin(stage)]
    if ftype:
        v = v[v["fuel_type"].isin(ftype)]
    if only_data:
        v = v[v["n_table_rows"] > 0]
    show = v[
        [
            "relevance",
            "psi_id",
            "acronym",
            "title",
            "stage",
            "fuel_type",
            "flight_platform",
            "start_date",
            "end_date",
            "n_table_rows",
            "n_publications",
            "doi",
            "psi_url",
        ]
    ].rename(
        columns={
            "relevance": "relevance",
            "psi_id": "PSI id",
            "acronym": "acronym",
            "title": "title",
            "stage": "stage",
            "fuel_type": "subject",
            "flight_platform": "platform",
            "start_date": "start",
            "end_date": "end",
            "n_table_rows": "tests in table",
            "n_publications": "publications",
            "doi": "DOI",
            "psi_url": "PSI page",
        }
    )
    st.dataframe(
        show,
        hide_index=True,
        width="stretch",
        column_config={
            "PSI page": st.column_config.LinkColumn(display_text="open"),
            "relevance": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
        },
    )
    st.download_button(
        "Download this table (CSV)", show.to_csv(index=False).encode("utf-8"), "psi_investigations.csv", "text/csv"
    )

    pick = st.selectbox("Details", v["psi_id"] + " - " + v["acronym"].replace("", "(no acronym)") + " " + v["title"].str[:60])
    if pick:
        r = v[v["psi_id"] == pick.split(" - ")[0]].iloc[0]
        st.markdown(f"**{r['title']}** ({r['psi_id']}, {r['flight_platform'] or 'ground'}; hardware: {r['hardware'] or 'n/a'})")
        for lab, col in (("Objective", "objective"), ("Approach", "approach"), ("Research impacts", "research_impacts")):
            if isinstance(r[col], str) and r[col].strip():
                with st.expander(lab):
                    st.write(r[col])
    source_note("NASA PSI investigation records (https://psi.nasa.gov), fetched 2026-11-14; stage tags from the challenge text")

with tab_cmp:
    m, groups = comparison()
    t = m[m["has_table"]].copy()
    labels = [v[0] for v in VARIABLES]
    kinds = {v[0]: v[1] for v in VARIABLES}
    st.markdown(
        "What each investigation's NASA data table records (a cell is filled when the table has a column of that kind; "
        "detected from the column headers of the PSI files). Blue = test conditions, orange = measured outcomes."
    )
    z = [[(1 if kinds[c] == "input" else 2) if row[c] else 0 for c in labels] for _, row in t.iterrows()]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=labels,
            y=t["acronym"],
            zmin=0,
            zmax=2,
            showscale=False,
            xgap=2,
            ygap=2,
            colorscale=[[0, "#F1F5F9"], [0.33, "#F1F5F9"], [0.34, BLUE], [0.66, BLUE], [0.67, ORANGE], [1, ORANGE]],
            customdata=[[f"{n} tests" for _ in labels] for n in t["tests"]],
            hovertemplate="%{y}: %{x}<br>%{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=40 + 26 * len(t),
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(side="top", tickangle=-30),
    )
    st.plotly_chart(fig, width="stretch")
    both = t[t["oxygen"] & t["pressure"]]["acronym"].tolist()
    outc = t[t[[lab for lab in labels if kinds[lab] == "outcome"]].any(axis=1)]["acronym"].tolist()
    st.markdown(
        f"- **Oxygen and pressure both recorded:** {', '.join(both)} ({len(both)} of {len(t)} tables) - "
        "the tables that cover an oxygen x pressure atmosphere such as a Moon base.\n"
        f"- **Any measured outcome in the table:** {', '.join(outc)} ({len(outc)} of {len(t)}); the rest list test "
        "conditions only, their results are in images or publications.\n"
        f"- **No data table:** {', '.join(m[~m['has_table']]['acronym'])} (ground analysis / modelling projects)."
    )
    st.subheader("Shared hardware: investigations that can be compared most directly")
    for g, acr in groups.items():
        st.markdown(f"- **{g}:** {', '.join(acr)}")
    show = m.drop(columns=["hardware_groups", "relevance"]).copy()
    show["hardware"] = m["hardware_groups"].map(", ".join)
    st.download_button(
        "Download the comparison matrix (CSV)", show.to_csv(index=False).encode("utf-8"), "psi_comparison_matrix.csv", "text/csv"
    )
    source_note("NASA PSI Experimental Table headers and investigation records; rules in src/fif/insights/compare.py (ADR-037)")
