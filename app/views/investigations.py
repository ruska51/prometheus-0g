"""PSI combustion investigations: relevance-ranked catalog with filters and details (UI_SPEC page 5, MVP M1/M2)."""

import plotly.graph_objects as go
import streamlit as st
from common import BLUE, ORANGE, PLOT_TEMPLATE, comparison, investigations, next_step, source_note
from i18n import t

from fif.insights.compare import VARIABLES

st.title(t("NASA combustion investigations (PSI)"))
st.markdown(
    t(
        "All 24 Combustion Science investigations in NASA's Physical Sciences Informatics repository, ranked by relevance "
        "to crew fire safety: 0.5 x fire-safety role + 0.3 x usable data + 0.2 x size of the data table (formula in Method "
        "& sources)."
    )
)
tab_rank, tab_cmp = st.tabs([t("Ranked catalog"), t("Compare investigations")])
with tab_rank:
    c = investigations()
    f1, f2, f3 = st.columns(3)
    stage = f1.multiselect(t("Fire-safety stage"), ["prevention", "detection", "suppression", "other"], default=[], format_func=t)
    ftype = f2.multiselect(t("Fuel / subject"), sorted(c["fuel_type"].unique()), default=[], format_func=t)
    only_data = f3.toggle(t("Only investigations with a data table"), value=False)
    v = c.copy()
    if stage:
        v = v[v["stage"].isin(stage)]
    if ftype:
        v = v[v["fuel_type"].isin(ftype)]
    if only_data:
        v = v[v["n_table_rows"] > 0]
    cols = {
        "relevance": t("relevance"),
        "psi_id": "PSI id",
        "acronym": t("acronym"),
        "title": t("title"),
        "stage": t("stage"),
        "fuel_type": t("subject"),
        "flight_platform": t("platform"),
        "start_date": t("start"),
        "end_date": t("end"),
        "n_table_rows": t("tests in table"),
        "n_publications": t("publications"),
        "doi": "DOI",
        "psi_url": t("PSI page"),
    }
    show = v[list(cols)].copy()
    show["stage"] = show["stage"].map(t)
    show["fuel_type"] = show["fuel_type"].map(t)
    show = show.rename(columns=cols)
    st.dataframe(
        show,
        hide_index=True,
        width="stretch",
        column_config={
            t("PSI page"): st.column_config.LinkColumn(display_text=t("open")),
            t("relevance"): st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
        },
    )
    st.download_button(
        t("Download this table (CSV)"), show.to_csv(index=False).encode("utf-8"), "psi_investigations.csv", "text/csv"
    )

    pick = st.selectbox(
        t("Details"), v["psi_id"] + " - " + v["acronym"].replace("", t("(no acronym)")) + " " + v["title"].str[:60]
    )
    if pick:
        r = v[v["psi_id"] == pick.split(" - ")[0]].iloc[0]
        st.markdown(
            f"**{r['title']}** ({r['psi_id']}, {r['flight_platform'] or t('ground')}; "
            + t("hardware:")
            + f" {r['hardware'] or 'n/a'})"
        )
        for lab, col in (("Objective", "objective"), ("Approach", "approach"), ("Research impacts", "research_impacts")):
            if isinstance(r[col], str) and r[col].strip():
                with st.expander(t(lab)):
                    st.write(r[col])
        st.caption(t("Investigation descriptions are NASA PSI record text (English)."))
    source_note(
        t("NASA PSI investigation records (https://psi.nasa.gov), fetched 2026-11-14; stage tags from the challenge text")
    )

with tab_cmp:
    m, groups = comparison()
    tb = m[m["has_table"]].copy()
    labels = [x[0] for x in VARIABLES]
    kinds = {x[0]: x[1] for x in VARIABLES}
    st.markdown(
        t(
            "What each investigation's NASA data table records (a cell is filled when the table has a column of that kind; "
            "detected from the column headers of the PSI files). Blue = test conditions, orange = measured outcomes."
        )
    )
    z = [[(1 if kinds[c] == "input" else 2) if row[c] else 0 for c in labels] for _, row in tb.iterrows()]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=[t(lab) for lab in labels],
            y=tb["acronym"],
            zmin=0,
            zmax=2,
            showscale=False,
            xgap=2,
            ygap=2,
            colorscale=[[0, "#F1F5F9"], [0.33, "#F1F5F9"], [0.34, BLUE], [0.66, BLUE], [0.67, ORANGE], [1, ORANGE]],
            customdata=[[t("{n} tests", n=n) for _ in labels] for n in tb["tests"]],
            hovertemplate="%{y}: %{x}<br>%{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=40 + 26 * len(tb),
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(side="top", tickangle=-30),
    )
    st.plotly_chart(fig, width="stretch")
    both = tb[tb["oxygen"] & tb["pressure"]]["acronym"].tolist()
    outc = tb[tb[[lab for lab in labels if kinds[lab] == "outcome"]].any(axis=1)]["acronym"].tolist()
    st.markdown(
        "- **"
        + t("Oxygen and pressure both recorded:")
        + "** "
        + t(
            "{names} ({n} of {total} tables) - the tables that cover an oxygen x pressure atmosphere such as a Moon base.",
            names=", ".join(both),
            n=len(both),
            total=len(tb),
        )
        + "\n- **"
        + t("Any measured outcome in the table:")
        + "** "
        + t(
            "{names} ({n} of {total}); the rest list test conditions only, their results are in images or publications.",
            names=", ".join(outc),
            n=len(outc),
            total=len(tb),
        )
        + "\n- **"
        + t("No data table:")
        + "** "
        + t("{names} (ground analysis / modelling projects).", names=", ".join(m[~m["has_table"]]["acronym"]))
    )
    st.subheader(t("Shared hardware: investigations that can be compared most directly"))
    for g, acr in groups.items():
        st.markdown(f"- **{t(g)}:** {', '.join(acr)}")
    show = m.drop(columns=["hardware_groups", "relevance"]).copy()
    show["hardware"] = m["hardware_groups"].map(", ".join)
    st.download_button(
        t("Download the comparison matrix (CSV)"),
        show.to_csv(index=False).encode("utf-8"),
        "psi_comparison_matrix.csv",
        "text/csv",
    )
    source_note(
        t("NASA PSI Experimental Table headers and investigation records; rules in src/fif/insights/compare.py (ADR-037)")
    )

next_step("views/investigations.py")
