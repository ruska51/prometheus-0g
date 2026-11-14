"""PSI combustion investigations: relevance-ranked catalog with filters and details (UI_SPEC page 5, MVP M1/M2)."""
import streamlit as st

from common import investigations, source_note

st.title("NASA combustion investigations (PSI)")
st.markdown("All 24 Combustion Science investigations in NASA's Physical Sciences Informatics repository, ranked by relevance "
            "to crew fire safety: 0.5 x fire-safety role + 0.3 x usable data + 0.2 x size of the data table (formula in Method & sources).")
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
show = v[["relevance", "psi_id", "acronym", "title", "stage", "fuel_type", "flight_platform", "start_date", "end_date",
          "n_table_rows", "n_publications", "doi", "psi_url"]].rename(columns={
    "relevance": "relevance", "psi_id": "PSI id", "acronym": "acronym", "title": "title", "stage": "stage", "fuel_type": "subject",
    "flight_platform": "platform", "start_date": "start", "end_date": "end", "n_table_rows": "tests in table",
    "n_publications": "publications", "doi": "DOI", "psi_url": "PSI page"})
st.dataframe(show, hide_index=True, use_container_width=True,
             column_config={"PSI page": st.column_config.LinkColumn(display_text="open"),
                            "relevance": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f")})
st.download_button("Download this table (CSV)", show.to_csv(index=False).encode("utf-8"), "psi_investigations.csv", "text/csv")

pick = st.selectbox("Details", v["psi_id"] + " - " + v["acronym"].replace("", "(no acronym)") + " " + v["title"].str[:60])
if pick:
    r = v[v["psi_id"] == pick.split(" - ")[0]].iloc[0]
    st.markdown(f"**{r['title']}** ({r['psi_id']}, {r['flight_platform'] or 'ground'}; hardware: {r['hardware'] or 'n/a'})")
    for lab, col in (("Objective", "objective"), ("Approach", "approach"), ("Research impacts", "research_impacts")):
        if isinstance(r[col], str) and r[col].strip():
            with st.expander(lab):
                st.write(r[col])
source_note("NASA PSI investigation records (https://psi.nasa.gov), fetched 2026-11-14; stage tags from the challenge text")
