"""Step 1 of the Moon-base fire designer (ADR-059): the base as a list of modules - type and size only - with a to-scale
side view, the per-module assessment and the choice of the module to design. Module sizes, rack shares and the
type-to-wall mapping are design inputs, not NASA numbers; every rate and air value comes from fif.physics.module_fire.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from i18n import t

from fif.physics import module_fire as mf

# module type -> (wall layout preset, share of the volume taken by racks and equipment): design defaults
KINDS = {
    "Habitat": ("crew", 0.40),
    "Laboratory": ("lab", 0.50),
    "Stowage": ("stowage", 0.60),
    "Airlock": ("blank", 0.30),
}
# size class -> (length m, inner diameter m): design defaults, so nobody has to compute an area
SIZES = {"S": (3.0, 2.5), "M": (6.0, 4.0), "L": (9.0, 4.5)}
SIZE_LABEL = {"S": "S - 3 m x 2.5 m", "M": "M - 6 m x 4 m", "L": "L - 9 m x 4.5 m"}
DEFAULT = pd.DataFrame(
    [
        {"name": "Habitat", "kind": "Habitat", "size": "M"},
        {"name": "Lab", "kind": "Laboratory", "size": "M"},
        {"name": "Logistics", "kind": "Stowage", "size": "S"},
        {"name": "Airlock", "kind": "Airlock", "size": "S"},
    ]
)


def mins(s: float) -> str:
    return t("not reached") if not math.isfinite(s) else t("{m} min", m=f"{s / 60:.0f}" if s >= 600 else f"{s / 60:.1f}")


@st.cache_data(show_spinner=t("Assessing the modules..."), max_entries=64)
def assess(wall: str, fac: float, free_m3: float, x_o2: float, p_atm: float) -> dict:
    """One wall of the module at lunar gravity, fire at the preset ignition point, in the cabin atmosphere."""
    layout = mf.grid(mf.PRESETS[wall])
    env = mf.ENVIRONMENTS["moon"] if fac == 1.0 else mf.scaled(mf.ENVIRONMENTS["moon"], fac)
    times = mf.arrival_times(layout, mf.IGNITION[wall], env)
    sm = mf.summary(layout, times)
    out = {"hatch_s": sm["hatch_s"], "flammable_m2": sm["flammable_m2"], "o2_end": x_o2, "co2_end": 0.0, "peak_kW": 0.0}
    if sm["time_all_s"] > 0:
        tz = np.linspace(0, sm["time_all_s"], 200)
        z = mf.zone_history(layout, times, tz, free_m3, x_o2, p_atm)
        out.update(o2_end=float(z["x_o2"][-1]), co2_end=float(z["x_co2"][-1]), peak_kW=float(max(z["hrr_kW"].max(), 0)))
    out["detectors"] = mf.detectors_needed(layout, env, 0.9, 5, 8) if sm["flammable_m2"] > 0 else None
    return out


def modules_table(x_o2: float, p_atm: float, fac: float) -> list[dict]:
    """The editable base table and the assessment of every module (lunar gravity, this atmosphere)."""
    if "base_modules" not in st.session_state:
        st.session_state["base_modules"] = DEFAULT.copy()
    edited = st.data_editor(
        st.session_state["base_modules"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="base_editor",
        column_config={
            "name": st.column_config.TextColumn(t("Module"), required=True, max_chars=20),
            "kind": st.column_config.SelectboxColumn(t("Type"), options=list(KINDS), required=True),
            "size": st.column_config.SelectboxColumn(
                t("Size (length x diameter)"), options=list(SIZES), required=True, format_func=lambda k: SIZE_LABEL[k]
            ),
        },
    )
    mods = edited.dropna(subset=["name", "kind", "size"])
    mods = mods[mods["kind"].isin(list(KINDS)) & mods["size"].isin(list(SIZES))].reset_index(drop=True)
    rows = []
    for _, m in mods.iterrows():
        wall, racks = KINDS[m["kind"]]
        length, dia = SIZES[m["size"]]
        geo = mf.module_geometry(length, dia, racks)
        a = assess(wall, fac, round(geo["free_volume_m3"], 1), x_o2, p_atm)
        rows.append(
            {
                "name": str(m["name"]),
                "kind": m["kind"],
                "size": m["size"],
                "wall": wall,
                "racks": racks,
                "length_m": length,
                "diameter_m": dia,
                **geo,
                **a,
            }
        )
    return rows


def side_view(rows: list[dict], selected: str | None) -> go.Figure:
    """Modules in a row, length and diameter to scale; colour = how soon a fire reaches that module's hatch."""
    fig = go.Figure()
    x, gap = 0.0, 0.8
    hmax = max(r["diameter_m"] for r in rows)
    fin = [r["hatch_s"] / 60 for r in rows if math.isfinite(r["hatch_s"])]
    hi = max(fin) if fin else 1.0
    for i, r in enumerate(rows):
        L, D = r["length_m"], r["diameter_m"]
        x0, x1, y0, y1 = x, x + L, -D / 2, D / 2
        if math.isfinite(r["hatch_s"]):
            f = min(1.0, (r["hatch_s"] / 60) / max(hi, 1e-9))
            fill = f"rgba(232,{int(110 + 110 * f)},{int(70 + 90 * f)},0.55)"
        else:
            fill = "rgba(47,160,100,0.25)"
        sel = r["name"] == selected
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=y0,
            y1=y1,
            fillcolor=fill,
            layer="below",
            line={"color": "#D2571F" if sel else "#5b616b", "width": 3.5 if sel else 1.5},
        )
        for k in range(1, int(L)):
            fig.add_shape(type="line", x0=x0 + k, x1=x0 + k, y0=y0, y1=y1, line={"color": "rgba(0,0,0,0.10)", "width": 1})
        fig.add_annotation(
            x=(x0 + x1) / 2, y=0.3, text=f"<b>{r['name']}</b>", showarrow=False, font={"size": 14, "color": "#1c1e22"}
        )
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=-0.35,
            showarrow=False,
            font={"size": 11, "color": "#2b2e34"},
            text=f"{t('hatch')}: {mins(r['hatch_s'])}<br>{r['free_volume_m3']:.0f} m³",
        )
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=-hmax / 2 - 0.45,
            showarrow=False,
            font={"size": 11, "color": "#6a6f78"},
            text=f"{L:.0f} m x {D:.1f} m",
        )
        x = x1
        if i < len(rows) - 1:
            fig.add_shape(
                type="rect",
                x0=x,
                x1=x + gap,
                y0=-0.6,
                y1=0.6,
                line={"color": "#9aa0a8", "width": 1.2},
                fillcolor="rgba(150,155,165,0.35)",
            )
            for xx in (x, x + gap):
                fig.add_shape(type="rect", x0=xx - 0.08, x1=xx + 0.08, y0=-0.5, y1=0.5, fillcolor="#2fd27a", line={"width": 0})
            x += gap
    fig.update_xaxes(visible=False, range=[-0.5, x + 0.5])
    fig.update_yaxes(visible=False, range=[-hmax / 2 - 0.9, hmax / 2 + 0.4], scaleanchor="x")
    fig.update_layout(
        height=max(220, int(120 + 520 * hmax / max(x, 1))),
        margin={"l": 0, "r": 0, "t": 6, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def summary_table(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                t("Module"): r["name"],
                t("Type"): t(r["kind"]),
                t("Size"): f"{r['length_m']:.0f} x {r['diameter_m']:.1f} m",
                t("Floor area, m²"): round(r["floor_m2"], 1),
                t("Free volume, m³"): round(r["free_volume_m3"], 1),
                t("Flame at the hatch"): mins(r["hatch_s"]),
                t("Peak fire power, kW"): round(r["peak_kW"], 1),
                t("O2 at the end, %"): round(r["o2_end"] * 100, 1),
                t("Detectors for 90 % of fires seen in 1 min"): str(r["detectors"] or "> 8") if r["flammable_m2"] > 0 else "-",
            }
            for r in rows
        ]
    )
