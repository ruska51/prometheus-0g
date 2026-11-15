"""Moon-base planner (ADR-057): a base made of cylindrical modules joined by hatches. For each module: free gas volume,
how fast a fire on one of its walls reaches the hatch (NASA-measured spread rates at lunar gravity, scaled to the cabin
atmosphere), what it does to the module air, how many detectors see 90 % of fires within a minute. Sizes are design
inputs; every rate comes from fif.physics.module_fire. Modules are treated separately (hatches closed)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import choice, next_step, source_note
from i18n import t
from theme import kicker

from fif.physics import module_fire as mf

WALL_LABEL = {
    "crew": lambda: t("Crew quarters wall"),
    "lab": lambda: t("Laboratory rack wall"),
    "stowage": lambda: t("Stowage wall"),
    "blank": lambda: t("Blank wall"),
}
ATM = {"moon": (0.30, 10.2 / 14.696), "air": (0.21, 1.0), "sea": (0.34, 8.2 / 14.696)}
ATM_LABEL = {
    "moon": lambda: t("Moon base / rover air (30 % O2, 10.2 psi) - challenge"),
    "air": lambda: t("Test air / ISS cabin air (21 % O2, 14.7 psi) - measured rates"),
    "sea": lambda: t("Exploration atmosphere (34 % O2, 8.2 psi) - NASA FM2 poster"),
}
GRAV = {"moon": lambda: t("Lunar gravity (1/6 g)"), "earth": lambda: t("Earth gravity (1 g)")}

kicker(t("Moon base · design study"))
st.title(t("Moon-base planner"))
st.markdown(
    t(
        "Lay out a base from cylindrical modules - habitat, laboratory, stowage, airlock - with their sizes and wall "
        "types. For every module the planner shows how fast a fire on one of its walls reaches the hatch, what it does to "
        "the module air and how many detectors it needs. Edit the table: add, remove or resize modules."
    )
)
st.caption(
    t(
        "Evidence: model. Spread rates measured by NASA (LUCI at lunar gravity, the same samples on Earth), scaled to the "
        "cabin atmosphere with NASA's flame-spread theory; module sizes and racks are design inputs, not NASA numbers. "
        "Each module is assessed on its own, with its hatches closed."
    )
)

DEFAULT = pd.DataFrame(
    [
        {"name": "Habitat", "wall": "crew", "length_m": 6.0, "diameter_m": 4.0, "racks_pct": 40},
        {"name": "Laboratory", "wall": "lab", "length_m": 6.0, "diameter_m": 4.0, "racks_pct": 50},
        {"name": "Logistics", "wall": "stowage", "length_m": 4.0, "diameter_m": 4.0, "racks_pct": 60},
        {"name": "Airlock", "wall": "blank", "length_m": 3.0, "diameter_m": 2.5, "racks_pct": 30},
    ]
)
if "base_modules" not in st.session_state:
    st.session_state["base_modules"] = DEFAULT.copy()

c1, c2 = st.columns([1.6, 1])
atm = choice(c1.selectbox, t("Cabin atmosphere"), list(ATM), "base_atm", format_func=lambda k: ATM_LABEL[k]())
grav = choice(c2.radio, t("Gravity"), list(GRAV), "base_grav", format_func=lambda k: GRAV[k](), horizontal=True)
x_o2, p_atm = ATM[atm]
fac = round(mf.atmosphere_factor(x_o2, p_atm), 4)

edited = st.data_editor(
    st.session_state["base_modules"],
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="base_editor",
    column_config={
        "name": st.column_config.TextColumn(t("Module"), required=True, max_chars=24),
        "wall": st.column_config.SelectboxColumn(t("Wall type"), options=list(WALL_LABEL), required=True),
        "length_m": st.column_config.NumberColumn(t("Length, m"), min_value=2.0, max_value=15.0, step=0.5, required=True),
        "diameter_m": st.column_config.NumberColumn(
            t("Inner diameter, m"), min_value=2.0, max_value=8.0, step=0.1, required=True
        ),
        "racks_pct": st.column_config.NumberColumn(t("Racks, %"), min_value=0, max_value=80, step=5, required=True),
    },
)
mods = edited.dropna(subset=["name", "wall", "length_m", "diameter_m", "racks_pct"]).reset_index(drop=True)
mods = mods[mods["wall"].isin(list(WALL_LABEL))]


@st.cache_data(show_spinner=t("Assessing the modules..."), max_entries=64)
def assess(wall: str, grav: str, fac: float, free_m3: float, x_o2: float, p_atm: float) -> dict:
    layout = mf.grid(mf.PRESETS[wall])
    env = mf.ENVIRONMENTS[grav] if fac == 1.0 else mf.scaled(mf.ENVIRONMENTS[grav], fac)
    times = mf.arrival_times(layout, mf.IGNITION[wall], env)
    sm = mf.summary(layout, times)
    out = {"hatch_s": sm["hatch_s"], "flammable_m2": sm["flammable_m2"], "o2_end": x_o2, "co2_end": 0.0, "peak_kW": 0.0}
    if sm["time_all_s"] > 0:
        tz = np.linspace(0, sm["time_all_s"], 200)
        z = mf.zone_history(layout, times, tz, free_m3, x_o2, p_atm)
        out.update(o2_end=float(z["x_o2"][-1]), co2_end=float(z["x_co2"][-1]), peak_kW=float(max(z["hrr_kW"].max(), 0)))
    out["detectors"] = mf.detectors_needed(layout, env, 0.9, 5, 8) if sm["flammable_m2"] > 0 else None
    return out


def mins(s: float) -> str:
    return t("not reached") if not math.isfinite(s) else t("{m} min", m=f"{s / 60:.0f}" if s >= 600 else f"{s / 60:.1f}")


rows = []
for _, m in mods.iterrows():
    geo = mf.module_geometry(float(m["length_m"]), float(m["diameter_m"]), float(m["racks_pct"]) / 100)
    a = assess(m["wall"], grav, fac, round(geo["free_volume_m3"], 1), x_o2, p_atm)
    rows.append({**m.to_dict(), **geo, **a})

if not rows:
    st.info(t("Add at least one module to the table."))
else:
    tot_v = sum(r["volume_m3"] for r in rows)
    tot_free = sum(r["free_volume_m3"] for r in rows)
    tot_fl = sum(r["flammable_m2"] * r["sections"] for r in rows)
    fin = [r for r in rows if math.isfinite(r["hatch_s"])]
    worst = min(fin, key=lambda r: r["hatch_s"]) if fin else None
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("Modules"), len(rows))
    k2.metric(t("Pressurized volume"), f"{tot_v:.0f} m³", help=t("Free gas volume {v} m³ after racks.", v=f"{tot_free:.0f}"))
    k3.metric(
        t("Flammable wall material"),
        f"{tot_fl:.0f} m²",
        help=t("Per module: flammable area of one wall x number of 4 m x 2 m wall sections."),
    )
    k4.metric(
        t("Fastest flame to a hatch"),
        mins(worst["hatch_s"]) if worst else t("not reached"),
        help=worst["name"] if worst else None,
    )

    # ---- schematic: modules in a row, length and diameter to scale, colour = time until the flame reaches the hatch
    fig = go.Figure()
    x = 0.0
    gap = 0.8
    hmax = max(r["diameter_m"] for r in rows)
    finite_h = [r["hatch_s"] / 60 for r in rows if math.isfinite(r["hatch_s"])]
    hi = max(finite_h) if finite_h else 1.0

    def colour(hs: float) -> str:
        if not math.isfinite(hs):
            return "rgba(47,210,122,0.30)"
        f = min(1.0, (hs / 60) / max(hi, 1e-9))
        r_, g_, b_ = (255, int(70 + 140 * f), int(40 + 40 * f))
        return f"rgba({r_},{g_},{b_},0.38)"

    for i, r in enumerate(rows):
        L, D = float(r["length_m"]), float(r["diameter_m"])
        x0, x1, y0, y1 = x, x + L, -D / 2, D / 2
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=y0,
            y1=y1,
            line={"color": "#c9d4ff", "width": 2},
            fillcolor=colour(r["hatch_s"]),
            layer="below",
        )
        for k in range(1, int(L)):  # ring frames every metre, like a pressure-shell drawing
            fig.add_shape(type="line", x0=x0 + k, x1=x0 + k, y0=y0, y1=y1, line={"color": "rgba(201,212,255,0.18)", "width": 1})
        fig.add_annotation(
            x=(x0 + x1) / 2, y=0.25, text=f"<b>{r['name']}</b>", showarrow=False, font={"size": 14, "color": "#fff"}
        )
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=-0.35,
            showarrow=False,
            font={"size": 11, "color": "#e6ebf7"},
            text=f"{t('hatch')}: {mins(r['hatch_s'])}<br>{r['free_volume_m3']:.0f} m³ · O2 {r['o2_end'] * 100:.1f} %",
        )
        fig.add_annotation(
            x=(x0 + x1) / 2, y=-hmax / 2 - 0.45, showarrow=False, font={"size": 11, "color": "#8f9bb8"}, text=f"{L:.1f} m"
        )
        fig.add_shape(type="line", x0=x0, x1=x1, y0=-hmax / 2 - 0.25, y1=-hmax / 2 - 0.25, line={"color": "#8f9bb8", "width": 1})
        x = x1
        if i < len(rows) - 1:  # node with a hatch on each side
            fig.add_shape(
                type="rect",
                x0=x,
                x1=x + gap,
                y0=-0.6,
                y1=0.6,
                line={"color": "#7f8aa6", "width": 1.5},
                fillcolor="rgba(92,102,120,0.45)",
            )
            fig.add_shape(type="rect", x0=x - 0.08, x1=x + 0.08, y0=-0.5, y1=0.5, fillcolor="#2fd27a", line={"width": 0})
            fig.add_shape(
                type="rect", x0=x + gap - 0.08, x1=x + gap + 0.08, y0=-0.5, y1=0.5, fillcolor="#2fd27a", line={"width": 0}
            )
            x += gap
    fig.update_xaxes(visible=False, range=[-0.5, x + 0.5])
    fig.update_yaxes(visible=False, range=[-hmax / 2 - 0.9, hmax / 2 + 0.4], scaleanchor="x")
    fig.update_layout(
        height=max(260, int(140 + 520 * hmax / max(x, 1))),
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t("Side view to scale; colour: redder = the flame reaches that module's hatch sooner; green bars = hatches."))

    table = pd.DataFrame(
        [
            {
                t("Module"): r["name"],
                t("Wall type"): WALL_LABEL[r["wall"]](),
                t("Free volume, m³"): round(r["free_volume_m3"], 1),
                t("Wall sections (4 x 2 m)"): round(r["sections"], 1),
                t("Flame at the hatch"): mins(r["hatch_s"]),
                t("Peak fire power, kW"): round(r["peak_kW"], 1),
                t("O2 at the end, %"): round(r["o2_end"] * 100, 1),
                t("CO2 at the end, %"): round(r["co2_end"] * 100, 2),
                t("Detectors for 90 % of fires seen in 1 min"): str(r["detectors"] or "> 8") if r["flammable_m2"] > 0 else "-",
            }
            for r in rows
        ]
    )
    st.dataframe(table, hide_index=True, use_container_width=True)
    if worst:
        st.success(
            t(
                "Fix first: {m} - a fire on its {w} reaches the hatch in {h}. Open it on the Module fire page to find the "
                "firebreak, detector and suppression positions.",
                m=worst["name"],
                w=WALL_LABEL[worst["wall"]]().lower(),
                h=mins(worst["hatch_s"]),
            )
        )
        st.page_link(
            "views/module.py",
            label=t("Open the Module fire page"),
            icon=":material/arrow_forward:",
            query_params={"wall": worst["wall"], "atm": atm},
        )

source_note(
    t(
        "spread rates: NTRS 20250010653 (LUCI) with NASA/TM-20210011385 Eq. 2.2 for other atmospheres; air model and "
        "detector placement: src/fif/physics/module_fire.py (ADR-052, ADR-057); module sizes are user inputs."
    )
)

next_step("views/base.py")
