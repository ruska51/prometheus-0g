"""Moon-base module: draw a module wall, light a fire and watch it spread at NASA-measured rates in three gravities;
solid materials at lunar gravity; a fire-safety checklist with the evidence for each item (ADR-049, steps 2-4)."""

from __future__ import annotations

import json
import math
from datetime import UTC
from pathlib import Path

import base_view as bv
import blueprint as bp
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from common import choice, external_params, next_step, qp_get, share_link, source_note
from i18n import t, tr_insight
from module_view import render as render_fire
from plotly.subplots import make_subplots
from theme import kicker

from fif.insights.moon import moon_answer
from fif.physics import module_fire as mf

ROOT = Path(__file__).resolve().parents[2]
BG = "#0d1322"  # module interior
COLORS = {"F": "#c9a66b", "A": "#5fb3d9", "M": "#5c6678", ".": "#1a2235", "H": "#2fd27a"}
FLAME = ["#fff1a8", "#ffb627", "#ff5a1f", "#9e2a1b", "#120c0b"]  # new flame -> burning -> embers -> char
CODE_Z = {".": 0, "M": 1, "F": 2, "A": 3, "H": 4}
_PALETTE = [COLORS["."], COLORS["M"], COLORS["F"], COLORS["A"], COLORS["H"], *FLAME]
DISCRETE = [x for i, c in enumerate(_PALETTE) for x in ([i / len(_PALETTE), c], [(i + 1) / len(_PALETTE), c])]
ENV_COLOR = {"moon": "#c9d4ff", "iss": "#38e8ff", "earth": "#ff7a1a"}
ENV_ORDER = ["moon", "iss", "earth"]


def env_label(key: str) -> str:
    return {
        "iss": t("Microgravity, ventilation 20 cm/s (ISS)"),
        "moon": t("Lunar gravity (1/6 g)"),
        "earth": t("Earth gravity (1 g)"),
    }[key]


MATERIAL_LABEL = {
    "F": lambda: t("Fabric (cotton/fiberglass, e.g. stowage bags, clothing)"),
    "A": lambda: t("Acrylic (PMMA) panel"),
    "M": lambda: t("Metal / non-flammable"),
    ".": lambda: t("Open space"),
    "H": lambda: t("Hatch (escape route)"),
}
MATERIAL_SHORT = {
    "F": lambda: t("Fabric"),
    "A": lambda: t("Acrylic"),
    "M": lambda: t("Metal"),
    ".": lambda: t("Open space"),
    "H": lambda: t("Hatch"),
}
PRESET_LABEL = {
    "crew": lambda: t("Crew quarters wall"),
    "lab": lambda: t("Laboratory rack wall"),
    "stowage": lambda: t("Stowage wall"),
    "blank": lambda: t("Empty wall - draw your own"),
}


def heat(z: np.ndarray) -> go.Heatmap:
    """Wall as a heatmap of cell codes (0-4 materials, 5-9 flame stages): scales with the screen, crisp on phones."""
    return go.Heatmap(
        z=z, colorscale=DISCRETE, zmin=-0.5, zmax=len(_PALETTE) - 0.5, showscale=False, xgap=1, ygap=1, hoverinfo="skip"
    )


def sheet(fig: go.Figure, layout_: np.ndarray, height: int) -> None:
    """The wall as an engineering drawing: blueprint image, axes in metres, transparent background."""
    hh, ww = layout_.shape
    fig.add_trace(go.Image(source=bp.data_uri(layout_), x0=-0.5, dx=1 / bp.PX, y0=-0.5, dy=1 / bp.PX, hoverinfo="skip"), row=None)
    fig.data = (fig.data[-1], *fig.data[:-1])  # drawing below everything else
    tick = {
        "color": "#8f9bb8",
        "tickfont": {"size": 11, "family": "Space Grotesk, sans-serif"},
        "showgrid": False,
        "zeroline": False,
        "ticks": "outside",
        "ticklen": 5,
        "tickcolor": "#3a4a72",
        "showline": True,
        "linecolor": "#3a4a72",
    }
    fig.update_xaxes(
        **tick,
        range=[-0.6, ww - 0.4],
        tickvals=[-0.5 + 10 * k for k in range(ww // 10 + 1)],
        ticktext=[f"{k} m" for k in range(ww // 10 + 1)],
    )
    fig.update_yaxes(
        **tick,
        range=[hh - 0.4, -0.6],
        tickvals=[-0.5 + 10 * k for k in range(hh // 10 + 1)],
        ticktext=[f"{k} m" for k in range(hh // 10 + 1)],
        scaleanchor="x",
    )
    fig.update_layout(
        height=height,
        margin={"l": 44, "r": 10, "t": 36, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )


def legend_html() -> str:
    chips = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:6px;margin-right:16px'>"
        f"<span style='width:14px;height:14px;border-radius:3px;background:rgb{bp.FILL[c]};"
        f"border:1.5px solid rgb{bp.EDGE[c]}'></span>{MATERIAL_SHORT[c]()}</span>"
        for c in ["F", "A", "M", "H"]
    )
    return (
        f"<div style='font-size:.85rem;color:#c9d2e6;margin:-6px 0 6px 44px'>{chips}"
        f"<span style='color:#ffd27a'>★ {t('Ignition')}</span></div>"
    )


def dark_layout(fig: go.Figure, height: int, axes: bool = False) -> None:
    fig.update_layout(height=height, margin={"l": 10, "r": 10, "t": 36, "b": 10}, paper_bgcolor=BG, plot_bgcolor=BG)
    if axes:
        fig.update_xaxes(color="#cfd6e4", gridcolor="#26304a", zeroline=False)
        fig.update_yaxes(color="#cfd6e4", gridcolor="#26304a", zeroline=False)
    else:
        fig.update_xaxes(visible=False, range=[-0.6, 39.6])
        fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")


def env_obj(env: str, vent: int, factor: float = 1.0) -> mf.Environment:
    """Measured rates for the gravity; in microgravity the ventilation direction decides which way is 'with the flow';
    ``factor`` scales all rates for another atmosphere (physics theory, ADR-051)."""
    vent = vent if vent in (1, -1) else 1  # never trust a widget value here (see common.choice)
    base = mf.iss_with_flow(vent) if env == "iss" else mf.ENVIRONMENTS[env]
    return base if factor == 1.0 else mf.scaled(base, factor)


def _grid(key: tuple[str, ...]) -> np.ndarray:
    return np.array([list(r) for r in key])


@st.cache_data(show_spinner=False)
def _bass2() -> dict:
    return mf.bass2_co2_per_o2()


@st.cache_data(show_spinner=False, max_entries=64)
def _arrival(key: tuple[str, ...], ign: tuple[int, int], env: str, vent: int, fac: float = 1.0) -> np.ndarray:
    return mf.arrival_times(_grid(key), ign, env_obj(env, vent, fac))


@st.cache_data(show_spinner=False, max_entries=64)
def _to_hatch(key: tuple[str, ...], env: str, vent: int, fac: float = 1.0) -> np.ndarray:
    return mf.time_to_hatch(_grid(key), env_obj(env, vent, fac))


@st.cache_data(show_spinner=t("Placing detectors..."), max_entries=32)
def _detectors(key: tuple[str, ...], env: str, vent: int, fac: float, n: int, radius: float) -> dict:
    return mf.place_detectors(_grid(key), env_obj(env, vent, fac), n, radius)


@st.cache_data(show_spinner=False, max_entries=32)
def _suppression(key: tuple[str, ...], env: str, vent: int, fac: float, n: int, reach: float) -> dict:
    return mf.place_suppression(_grid(key), env_obj(env, vent, fac), n, reach)


def ring(fig: go.Figure, r: int, c: int, radius: float, color: str, dash: str) -> None:
    fig.add_shape(
        type="circle",
        x0=c - radius,
        x1=c + radius,
        y0=r - radius,
        y1=r + radius,
        line={"color": color, "width": 1.6, "dash": dash},
        fillcolor=color.replace("1)", "0.08)"),
        layer="above",
    )


@st.cache_data(show_spinner=t("Trying every 50 cm strip..."), max_entries=32)
def _firebreak(key: tuple[str, ...], ign: tuple[int, int], env: str, vent: int, fac: float = 1.0):
    return mf.best_firebreak(_grid(key), ign, env_obj(env, vent, fac))


@st.cache_data(show_spinner=t("Trying every 50 cm strip..."), max_entries=32)
def _firebreak_anywhere(key: tuple[str, ...], env: str, vent: int, fac: float = 1.0):
    return mf.best_firebreak_anywhere(_grid(key), env_obj(env, vent, fac))


def minutes(s: float) -> str:
    return t("not reached") if not math.isfinite(s) else t("{m} min", m=f"{s / 60:.0f}" if s >= 600 else f"{s / 60:.1f}")


kicker(t("Moon base · fire design studio"))
st.title(t("Moon-base fire designer"))
st.markdown(
    t(
        "Everything on one page: lay out the base, pick a module, draw its wall, light a fire and watch it spread at the "
        "rates NASA measured (Saffire on the ISS, LUCI at lunar gravity, the same samples on Earth), protect the hatch "
        "with a firebreak, detectors and extinguishers - and download one report. A sketch on measured rates, not a fire "
        "simulation: its limits are in step 05."
    )
)
STEPS = ["Base", "Module wall", "Fire", "Module air", "Protect", "Lunar gravity & checklist", "Report"]
st.markdown(
    "<nav class='toc'>"
    + "".join(f"<a href='#step-{i}'><b>{i:02d}</b>{t(name)}</a>" for i, name in enumerate(STEPS, 1))
    + "</nav>",
    unsafe_allow_html=True,
)


def step(n: int, where=st) -> None:
    """Numbered step heading with an anchor for the table of contents."""
    where.markdown(f"<div class='step' id='step-{n}'><b>{n:02d}</b><span>{t(STEPS[n - 1])}</span></div>", unsafe_allow_html=True)


st.caption(
    t(
        "Evidence: model (sketch on NASA rates measured in air, 21-22 % O2). For another cabin atmosphere the rates are scaled with NASA's flame-spread theory (physics theory, not measured)."
    )
)


# ---- module designer -------------------------------------------------------------------------------------------
def encode_wall(layout: np.ndarray) -> str:
    """Run-length code of the wall for the page address: 'F12.3M40' = 12 fabric, 3 open, 40 metal cells (row by row)."""
    flat, out, i = "".join("".join(r) for r in layout), [], 0
    while i < len(flat):
        j = i
        while j < len(flat) and flat[j] == flat[i]:
            j += 1
        out.append(f"{flat[i]}{j - i}")
        i = j
    return "".join(out)


def decode_wall(code: str, shape: tuple[int, int]) -> np.ndarray:
    import re

    parts = re.findall(r"([FAM.H])(\d+)", code)
    if "".join(f"{c}{n}" for c, n in parts) != code:
        raise ValueError("bad wall code")
    flat = "".join(c * int(n) for c, n in parts)
    if len(flat) != shape[0] * shape[1]:
        raise ValueError("wrong wall size")
    return np.array(list(flat)).reshape(shape)


ss = st.session_state
WALLS = list(mf.PRESETS)
if "mod_wall" not in ss or external_params("module"):  # first visit or a link (ADR-055)
    keep = ss.get("module", {}).get("preset", WALLS[0])
    wall = qp_get("wall", lambda v: v if v in WALLS else int("x"), keep)
    ss["mod_wall"] = wall
    ss["mod_vent"] = qp_get("vent", lambda v: int(v) if int(v) in (1, -1) else int("x"), 1)
    ss["mod_atm"] = qp_get("atm", lambda v: v if v in ("air", "moon", "sea", "custom") else int("x"), "air")
    ss["mod_o2"] = qp_get("o2", lambda v: min(max(int(v), 17), 40), 30)
    ss["mod_psi"] = qp_get("psi", lambda v: min(max(round(float(v), 1), 5.0), 15.0), 10.2)
    if "L" in st.query_params or "ign" in st.query_params:
        shape = mf.grid(mf.PRESETS[wall]).shape
        lay = qp_get("L", lambda v: decode_wall(v, shape), mf.grid(mf.PRESETS[wall]))
        ign0 = qp_get("ign", lambda v: tuple(int(x) for x in v.split("-")), mf.IGNITION[wall])
        if not (len(ign0) == 2 and 0 <= ign0[0] < shape[0] and 0 <= ign0[1] < shape[1] and lay[ign0] in mf.FLAMMABLE):
            ign0 = mf.IGNITION[wall]  # an unreadable or non-flammable point falls back to the wall's default
        ss["module"] = {"preset": wall, "layout": lay.tolist(), "ignition": tuple(ign0), "selection": None}
_linked = external_params("module")

# ---- step 1: the base (ADR-059) -----------------------------------------------------------------------------------
step(1)
st.caption(
    t(
        "One cabin atmosphere for the whole base; each module has a type (sets its wall layout and racks) and a size "
        "class - no areas to compute. Sizes, racks and layouts are design inputs, not NASA numbers; each module is "
        "assessed on its own at lunar gravity, hatches closed."
    )
)
# ---- atmosphere (ADR-051): measured rates in test air, other air by NASA's flame-spread theory -----------------
ATM = {
    "air": (0.21, 1.0),
    "moon": (0.30, 10.2 / 14.696),
    "sea": (0.34, 8.2 / 14.696),
}
ATM_LABEL = {
    "air": lambda: t("Test air / ISS cabin air (21 % O2, 14.7 psi) - measured rates"),
    "moon": lambda: t("Moon base / rover air (30 % O2, 10.2 psi) - challenge"),
    "sea": lambda: t("Exploration atmosphere (34 % O2, 8.2 psi) - NASA FM2 poster"),
    "custom": lambda: t("Your own atmosphere"),
}
a1, a2, a3 = st.columns([1.6, 1, 1])
atm = choice(a1.selectbox, t("Cabin atmosphere"), list(ATM_LABEL), "mod_atm", format_func=lambda k: ATM_LABEL[k]())
if atm == "custom":
    # Streamlit forgets the state of a widget that was not shown on the last run: restore the defaults, not the minimum
    ss.setdefault("mod_o2", 30)
    ss.setdefault("mod_psi", 10.2)
    x_o2 = a2.slider(t("Oxygen, %"), 17, 40, key="mod_o2") / 100
    p_atm = a3.slider(t("Pressure, psi"), 5.0, 15.0, step=0.1, key="mod_psi") / 14.696
else:
    x_o2, p_atm = ATM[atm]
fac = round(mf.atmosphere_factor(x_o2, p_atm), 4)
tf, ta = mf.flame_temperature_K(round(x_o2, 4), round(p_atm, 4)), mf.flame_temperature_K(*mf.AIR)
if atm == "air":
    st.caption(t("Spread rates as NASA measured them (air, 21-22 % O2)."))
else:
    st.caption(
        t(
            "Flame temperature {tf} K vs {ta} K in the test air, so every spread rate is multiplied by {f} - NASA's "
            "flame-spread theory for thin solids (BASS-II report NTRS 20210011385, Eq. 2.2: rate proportional to flame "
            "temperature minus 673 K); flame temperature from chemical equilibrium for a hydrocarbon stand-in. Evidence: "
            "physics theory, not measured.",
            tf=f"{tf:.0f}",
            ta=f"{ta:.0f}",
            f=f"x{fac:.2f}",
        )
    )

base_rows = bv.modules_table(x_o2, p_atm, fac)
sel = None
if base_rows:
    st.plotly_chart(bv.side_view(base_rows, ss.get("base_pick")), use_container_width=True)
    st.caption(t("Side view to scale; colour: redder = the flame reaches that module's hatch sooner; green bars = hatches."))
    with st.expander(t("All modules: areas, air and detectors"), expanded=False):
        st.dataframe(bv.summary_table(base_rows), hide_index=True, use_container_width=True)
    fin = [r for r in base_rows if math.isfinite(r["hatch_s"])]
    worst = min(fin, key=lambda r: r["hatch_s"]) if fin else base_rows[0]
    names = [r["name"] for r in base_rows]
    if fin:
        st.warning(
            t(
                "Fix first: {m} - a fire on one of its walls reaches the hatch in {h}.",
                m=worst["name"],
                h=bv.mins(worst["hatch_s"]),
            )
        )
    step(2)
    pick = choice(st.selectbox, t("Module to design"), names, "base_pick", default=worst["name"])
    sel = next(r for r in base_rows if r["name"] == pick)
    if ss.get("_last_pick") != pick:  # a new module: load its wall type (unless a link or the pilot just set one)
        if not _linked:
            ss["mod_wall"] = sel["wall"]
        ss["_last_pick"] = pick
    st.caption(
        t(
            "{m}: {k}, {l:.0f} m long, {d:.1f} m across - floor {f:.0f} m², interior wall {w:.0f} m² (about {n:.0f} walls "
            "like the one below), free air {v:.0f} m³ after {r:.0f} % racks.",
            m=sel["name"],
            k=t(sel["kind"]).lower(),
            l=sel["length_m"],
            d=sel["diameter_m"],
            f=sel["floor_m2"],
            w=sel["wall_m2"],
            n=sel["sections"],
            v=sel["free_volume_m3"],
            r=sel["racks"] * 100,
        )
    )
else:
    st.info(t("Add at least one module to the table."))

c1, c2 = st.columns([1.1, 1.9])
preset = choice(c1.selectbox, t("Module wall"), WALLS, "mod_wall", format_func=lambda k: PRESET_LABEL[k]())
mode = c2.radio(
    t("Click on the wall to..."),
    ["ignite", "paint"],
    format_func=lambda m: t("set the ignition point") if m == "ignite" else t("paint material (click or box-select)"),
    horizontal=True,
)
paint = c2.radio(
    t("Material to paint"),
    ["F", "A", "M", ".", "H"],
    format_func=lambda k: MATERIAL_SHORT[k](),
    horizontal=True,
    disabled=mode != "paint",
)

state = st.session_state.setdefault("module", {})
if state.get("preset") != preset:
    state.update(preset=preset, layout=mf.grid(mf.PRESETS[preset]).tolist(), ignition=mf.IGNITION[preset], selection=None)
vent = choice(
    c1.radio,
    t("Ventilation in microgravity (ISS case)"),
    [1, -1],
    "mod_vent",
    format_func=lambda d: t("blows towards the hatch") if d == 1 else t("blows away from the hatch"),
)
if c1.button(t("Reset this wall")):
    state.update(layout=mf.grid(mf.PRESETS[preset]).tolist(), ignition=mf.IGNITION[preset], selection=None)
layout = np.array(state["layout"])
h, w = layout.shape
rows, cols = np.indices((h, w))
if mode == "paint":
    st.caption(
        t("Click a square to paint it, or pick the box tool in the chart's toolbar and drag over the wall to paint many at once.")
    )

editor = go.Figure()
editor.add_trace(  # invisible cell centres: they carry the clicks and box selections
    go.Scatter(
        x=cols.ravel(),
        y=rows.ravel(),
        mode="markers",
        marker={"symbol": "square", "size": 14, "opacity": 0.01, "color": "#ffffff"},
        text=[MATERIAL_LABEL[c]() for c in layout.ravel()],
        hovertemplate="%{text}<br>x %{customdata[0]:.1f} m, y %{customdata[1]:.1f} m<extra></extra>",
        customdata=np.stack([cols.ravel() / 10 + 0.05, rows.ravel() / 10 + 0.05], axis=1),
        selected={"marker": {"opacity": 0.35, "color": "#38e8ff"}},
        unselected={"marker": {"opacity": 0.01}},
    )
)
r0, c0 = state["ignition"]
editor.add_trace(
    go.Scatter(
        x=[c0],
        y=[r0],
        mode="markers",
        marker={"symbol": "star", "size": 22, "color": "#fff1a8", "line": {"width": 1.5, "color": "#ff5a1f"}},
        name=t("Ignition"),
        hoverinfo="skip",
    )
)
sheet(editor, layout, 420)
editor.update_layout(dragmode="select" if mode == "paint" else False)
event = st.plotly_chart(
    editor, key=f"wall-{preset}", on_select="rerun", selection_mode=("points", "box"), use_container_width=True
)
st.markdown(legend_html(), unsafe_allow_html=True)
pts = [(int(round(p["y"])), int(round(p["x"]))) for p in (event.selection.points if event else [])]
sig = (mode, paint, tuple(pts))
if pts and state.get("selection") != sig:
    state["selection"] = sig
    if mode == "ignite":
        r, c = pts[0]
        if layout[r, c] in mf.FLAMMABLE:
            state["ignition"] = (r, c)
        else:
            st.warning(t("A fire can only start on fabric or acrylic - pick another cell."))
    else:
        for r, c in pts:
            layout[r, c] = paint
        state["layout"] = layout.tolist()
    st.rerun()
st.caption(
    t("Each square is 10 x 10 cm; the wall is 4 m x 2 m. Up is up (gravity); the hatch is on the right.")
    + " "
    + t(
        "Ventilation: NASA measured how fire spreads with and against a 20 cm/s air flow in microgravity (Saffire), so "
        "its direction is used for the ISS case. With the fans off there is no measured spread rate for these materials; "
        "NASA's BASS-II tested the hypothesis that materials in microgravity, with adequate ventilation, burn as well if "
        "not better than in normal gravity. At lunar gravity and on Earth the sketch uses the measured buoyant spread "
        "only; ventilation on top of it was not measured."
    )
)

# ---- the same fire in three gravities ---------------------------------------------------------------------------
ign = tuple(state["ignition"])
key = tuple("".join(r) for r in layout)
shared = {"wall": preset, "vent": str(vent), "atm": atm, "ign": f"{ign[0]}-{ign[1]}"}
if atm == "custom":
    shared |= {"o2": str(round(x_o2 * 100)), "psi": f"{p_atm * 14.696:.1f}"}
else:
    for k in ("o2", "psi"):
        if k in st.query_params:
            del st.query_params[k]
if not np.array_equal(layout, mf.grid(mf.PRESETS[preset])):
    shared["L"] = encode_wall(layout)
elif "L" in st.query_params:
    del st.query_params["L"]
sh1, sh2, _ = st.columns([1.2, 1.5, 1.5])
with sh1:
    share_link(shared, "module")
report_slot = sh2.empty()  # filled at the end of the page, when all results are known
vol = round(sel["free_volume_m3"], 1) if sel else 30.0  # free air of the module picked in step 1
times = {k: _arrival(key, ign, k, vent, fac) for k in ENV_ORDER}
summ = {k: mf.summary(layout, times[k]) for k in ENV_ORDER}

t_end = max(summ[k]["time_all_s"] for k in ENV_ORDER)

tab_spread, tab_air, tab_protect, tab_moon, tab_report = (st.container() for _ in range(5))
for n, box in zip((3, 4, 5, 6, 7), (tab_spread, tab_air, tab_protect, tab_moon, tab_report), strict=True):
    step(n, box)
tab_design = tab_detect = tab_protect
with tab_spread:
    st.subheader(t("How the fire spreads"))
    st.caption(
        t(
            "Time until the flame reaches the hatch, for the same wall and the same ignition point. In these NASA tests "
            "fabric spread more slowly at lunar gravity than on Earth, but lunar-gravity flames lasted longer and some "
            "materials burn there that go out on Earth (step 06) - and Moon-base air is richer in oxygen than the test air."
        )
    )
    mcols = st.columns(3)
    for col, k in zip(mcols, ENV_ORDER, strict=True):
        s = summ[k]
        col.metric(env_label(k), minutes(s["hatch_s"]), help=t("Time until the flame reaches material next to the hatch."))
        col.caption(
            t(
                "Flame reaches {a} of {b} m2 of material; all of it burning after {m}.",
                a=f"{s['reached_m2']:.2f}",
                b=f"{s['flammable_m2']:.2f}",
                m=minutes(s["time_all_s"]),
            )
        )

    if t_end > 0:
        render_fire(
            layout,
            [{"label": env_label(k), "kind": k, "t": times[k], "hatch": summ[k]["hatch_s"]} for k in ENV_ORDER],
            {
                "play": "▶ " + t("Play"),
                "pause": "❚❚ " + t("Pause"),
                "replay": "↺ " + t("Replay"),
                "clock": t("{m} min after ignition"),
                "hatch": t("hatch: {m} min"),
                "reached": t("flame at the hatch"),
                "never": t("hatch not reached"),
            },
            height=760,
            vent=vent,
        )
        st.caption(
            t(
                "Same wall, same spark, three gravities. White-yellow: new flame; orange-red: burning; dark red: embers; "
                "black: burnt; green: hatch. The front is drawn smoothly between the 10 cm cells of the calculation; glow "
                "and flicker are illustrative."
            )
        )

        grid_t = np.linspace(0, t_end, 120)
        curve = go.Figure()
        for k in ENV_ORDER:
            curve.add_trace(
                go.Scatter(
                    x=grid_t / 60,
                    y=mf.burned_area_curve(times[k], grid_t),
                    mode="lines",
                    name=env_label(k),
                    line={"width": 3, "color": ENV_COLOR[k]},
                )
            )
        dark_layout(curve, 300, axes=True)
        curve.update_layout(
            xaxis_title=t("minutes after ignition"),
            yaxis_title=t("area reached by the flame, m2"),
            legend={"orientation": "h", "y": -0.3, "font": {"color": "#cfd6e4"}},
        )
        st.plotly_chart(curve, use_container_width=True)
    else:
        st.info(t("Nothing burns yet: paint some fabric or acrylic, then click on it to set the ignition point."))

with tab_air:
    if t_end > 0:
        # ---- the module air: well-mixed zone model (ADR-052) ------------------------------------------------------
        st.subheader(t("What the fire does to the module air"))
        st.caption(
            t(
                "A well-mixed zone model, the simplest of the compartment-fire models engineers use (fans mix the cabin air in "
                "microgravity). Oxygen used by the burnt fabric: 0.28 g per 18 cm2 of SIBAL fabric (NTRS 20210020516); heat: "
                "13.1 kJ per gram of oxygen (NASA BASS-II report); one CO2 per O2 for cellulose. Acrylic is not counted (no "
                "burnt mass per area in our sources). Evidence: model."
            )
        )
        z1, z2 = st.columns([1, 2])
        z1.metric(t("Free air in the module"), f"{vol:.0f} m³")
        z1.caption(t("From the module type and size in step 1."))
        tz = np.linspace(0, t_end, 160)
        zones = {k: mf.zone_history(layout, times[k], tz, float(vol), x_o2, p_atm) for k in ENV_ORDER}
        zk = zones["moon"]
        z2.metric(t("Heat released by the burnt fabric"), f"{zk['heat_MJ'][-1]:.1f} MJ")
        m1, m2, m3 = z2.columns(3)
        m1.metric(t("Peak fire power, lunar gravity"), f"{max(zk['hrr_kW'].max(), 0):.1f} kW")
        m2.metric(t("Oxygen at the end"), f"{zk['x_o2'][-1] * 100:.1f} %", f"{(zk['x_o2'][-1] - x_o2) * 100:+.1f} {t('points')}")
        m3.metric("CO2", f"{zk['x_co2'][-1] * 100:.2f} %")
        air = make_subplots(rows=1, cols=2, subplot_titles=[t("Oxygen, %"), "CO2, %"])
        for k in ENV_ORDER:
            air.add_trace(
                go.Scatter(
                    x=tz / 60, y=zones[k]["x_o2"] * 100, mode="lines", name=env_label(k), line={"width": 3, "color": ENV_COLOR[k]}
                ),
                row=1,
                col=1,
            )
            air.add_trace(
                go.Scatter(
                    x=tz / 60, y=zones[k]["x_co2"] * 100, mode="lines", showlegend=False, line={"width": 3, "color": ENV_COLOR[k]}
                ),
                row=1,
                col=2,
            )
        dark_layout(air, 320, axes=True)
        air.update_annotations(font={"color": "#e8ecf4", "size": 13})
        air.update_xaxes(title_text=t("minutes after ignition"))
        air.update_layout(legend={"orientation": "h", "y": -0.35, "font": {"color": "#cfd6e4"}})
        st.plotly_chart(air, use_container_width=True)
        st.caption(
            t(
                "Cross-check: Saffire-1 burned SIBAL fabric at 1200 W for 420 s over a 40.6 cm x 94 cm sample, {a} MJ per m2; "
                "the oxygen-based value used here is {b} MJ per m2 (same order; the Saffire sample did not burn completely). "
                "Not modelled: heat loss to walls, smoke, CO, the crew's own breathing, air revitalisation.",
                a=f"{mf.SAFFIRE1_MJ_PER_M2:.2f}",
                b=f"{mf.O2_G_PER_M2_FABRIC * mf.KJ_PER_G_O2 / 1000:.2f}",
            )
        )

        # ---- science check against NASA data and the equations (ADR-053) --------------------------------------------
        st.subheader(t("Science check: does the oxygen balance hold?"))
        chk = _bass2()
        tb = chk["table"]
        sc = go.Figure()
        sc.add_trace(
            go.Scatter(
                x=tb["o2_used_pct"],
                y=tb["co2_formed_pct"] + tb["co_formed_pct"].fillna(0),
                mode="markers",
                name=t("BASS-II burns: CO2 + CO formed"),
                marker={"size": 9, "color": "#ffb627", "line": {"width": 1, "color": "#0d1322"}},
                text=tb["material"],
                hovertemplate="%{text}<br>O2 %{x:.1f} -> CO2+CO %{y:.2f}<extra></extra>",
            )
        )
        xs = np.array([0, float(tb["o2_used_pct"].max()) * 1.05])
        sc.add_trace(
            go.Scatter(
                x=xs,
                y=xs * mf.PMMA_CO2_PER_O2,
                mode="lines",
                name=t("PMMA stoichiometry, 5/6"),
                line={"color": "#38e8ff", "width": 3},
            )
        )
        sc.add_trace(
            go.Scatter(
                x=xs,
                y=xs * mf.CELLULOSE_CO2_PER_O2,
                mode="lines",
                name=t("cellulose (fabric), 1"),
                line={"color": "#c9a66b", "width": 2, "dash": "dash"},
            )
        )
        dark_layout(sc, 380, axes=True)
        sc.update_layout(
            xaxis_title=t("oxygen used, % of the glovebox air"),
            yaxis_title=t("CO2 + CO formed, %"),
            legend={"orientation": "h", "y": -0.3, "font": {"color": "#cfd6e4"}},
        )
        st.plotly_chart(sc, use_container_width=True)
        st.markdown(
            t(
                "The zone model above turns the oxygen a fire uses into CO2 by chemistry: 1 CO2 per O2 for cellulose (fabric), "
                "5/6 for PMMA. NASA's BASS-II measured O2, CO2 and CO before and after {n} solid burns in the ISS glovebox (almost "
                "all PMMA). Fitted CO2 per O2: **{s:.3f}**; with the carbon in CO: **{sc:.3f}** - the PMMA chemistry predicts "
                "**{p:.3f}**. The balance the model rests on is confirmed by NASA measurements. ({left} of 129 rows left out: O2 "
                "drop below 0.3 points, unreadable, or O2 rising.) Evidence: NASA data.",
                n=chk["n_used"],
                s=chk["slope"],
                sc=chk["slope_with_co"],
                p=mf.PMMA_CO2_PER_O2,
                left=chk["n_left_out"],
            )
        )
        with st.expander(t("The equations behind this page")):
            st.markdown(
                t(
                    "**1. Flame spread over the wall** (each 10 cm step at the rate NASA measured for that material, gravity and direction; earliest arrival by Dijkstra's shortest-path algorithm):"
                )
            )
            st.latex(
                r"t(c) = \min_{\text{paths } s \to c} \sum_{\text{steps}} \frac{\Delta \ell}{V_{\text{material, gravity, direction}}}"
            )
            st.markdown(
                t(
                    "**2. Another cabin atmosphere** (NASA/TM-20210011385, Eq. 2.2, thin solids, thermal regime; T_v = 673 K from the same report; T_f from chemical equilibrium):"
                )
            )
            st.latex(
                r"V_f = \frac{F\,\lambda_g\,(T_f - T_v)}{\rho_s c_s \tau\,(T_v - T_\infty)} \;\Rightarrow\; \frac{V}{V_{\text{air}}} = \frac{T_f - T_v}{T_{f,\text{air}} - T_v}"
            )
            st.markdown(
                t(
                    "**3. Module air** (well-mixed zone; oxygen use of SIBAL fabric from NTRS 20210020516, 13.1 kJ per g O2 from the BASS-II report):"
                )
            )
            st.latex(
                r"m_{O_2}(t) = m^{\prime\prime}_{O_2}\,A_f(t),\quad Q(t) = 13.1\,\tfrac{\text{kJ}}{\text{g}}\;m_{O_2}(t),\quad \dot Q(t) = \frac{Q(t) - Q(t-60\,\text{s})}{60\,\text{s}}"
            )
            st.latex(
                r"x_{O_2}(t) = x_{O_2,0} - \frac{m_{O_2}(t)/M_{O_2}}{n},\quad x_{CO_2}(t) = \nu\,\frac{m_{O_2}(t)/M_{O_2}}{n},\quad n = \frac{pV}{RT}"
            )
            st.markdown(
                t(
                    "**4. Firebreak for a fire anywhere** (time from every cell to the hatch by Dijkstra run backwards from the hatch; the strip that most shrinks the area that can reach it):"
                )
            )
            st.latex(
                r"\tau(c) = \min_{\text{paths } c \to \text{hatch}} \sum \frac{\Delta \ell}{V},\qquad A_{\text{danger}} = \sum_{c:\,\tau(c) < \infty} A_{\text{cell}}"
            )
    else:
        st.info(t("Nothing burns yet: paint some fabric or acrylic, then click on it to set the ignition point."))

with tab_design:
    # ---- design a safer module -------------------------------------------------------------------------------------
    st.subheader(t("Design a safer module"))
    d1, d2 = st.columns([1.1, 1.9])
    denv = d1.radio(t("Gravity for the map and the firebreak"), ENV_ORDER, format_func=env_label)
    goal = d2.radio(
        t("Find the 50 cm metal strip that best protects the hatch..."),
        ["here", "anywhere"],
        format_func=lambda g: t("from this fire") if g == "here" else t("from a fire that starts anywhere"),
    )
    if goal == "here":
        tmap = times[denv]
        fb = _firebreak(key, ign, denv, vent, fac)
        before = summ[denv]["hatch_s"]
        if fb is None:
            msg = (
                t("The flame does not reach the hatch from this ignition point - nothing to protect.")
                if not math.isfinite(before)
                else t("No single strip helps here.")
            )
        elif not math.isfinite(fb.hatch_s):
            msg = t(
                "A metal strip at the marked place keeps this fire away from the hatch (it reached it in {m} before).",
                m=minutes(before),
            )
        else:
            msg = t(
                "A metal strip at the marked place delays the flame at the hatch from {a} to {b}.",
                a=minutes(before),
                b=minutes(fb.hatch_s),
            )
        map_title = t("When the flame arrives (minutes after ignition)")
    else:
        tmap = _to_hatch(key, denv, vent, fac)
        fb = _firebreak_anywhere(key, denv, vent, fac)
        area = mf.hatch_catchment_m2(tmap)
        if fb is None:
            msg = t("No fire on this wall can reach the hatch.") if area == 0 else t("No single strip helps here.")
        else:
            msg = t(
                "Material from which a fire can reach the hatch: {a} m2 now, {b} m2 with a metal strip at the marked place.",
                a=f"{area:.2f}",
                b=f"{fb.reached_m2:.2f}",
            )
        map_title = t("How fast a fire starting here reaches the hatch (minutes)")

    mins = np.where(np.isfinite(tmap), tmap / 60, np.nan)
    fig = go.Figure()
    top = float(np.nanmax(mins)) if np.isfinite(mins).any() else 1.0
    step = next(v for v in (1, 2, 5, 10, 15, 20, 30, 60) if top / v <= 9)
    fig.add_trace(  # isochrones: filled translucent bands + labelled lines, as on a fire-engineering drawing
        go.Contour(
            z=mins,
            contours={
                "start": 0,
                "end": top,
                "size": step,
                "showlabels": True,
                "labelfont": {"color": "#fff6e0", "size": 11, "family": "Space Grotesk, sans-serif"},
            },
            colorscale=[[0, "#fff1a8"], [0.25, "#ffb627"], [0.55, "#ff5a1f"], [0.8, "#9e2a1b"], [1, "#3b1414"]],
            reversescale=goal == "anywhere",
            opacity=0.62,
            line={"width": 1.4, "color": "rgba(255,240,210,0.85)"},
            connectgaps=False,
            colorbar={
                "title": {"text": t("min"), "font": {"color": "#cfd6e4"}},
                "tickfont": {"color": "#cfd6e4"},
                "thickness": 12,
            },
            hovertemplate=t("{m} min").replace("{m}", "%{z:.1f}") + "<extra></extra>",
        )
    )
    if goal == "here":
        fig.add_trace(
            go.Scatter(
                x=[ign[1]],
                y=[ign[0]],
                mode="markers",
                marker={"symbol": "star", "size": 20, "color": "#fff1a8", "line": {"width": 1.5, "color": "#ff5a1f"}},
                hoverinfo="skip",
                showlegend=False,
            )
        )
    if fb is not None:
        fr, fc = zip(*fb.cells, strict=True)
        fig.add_trace(
            go.Scatter(
                x=list(fc),
                y=list(fr),
                mode="markers",
                marker={"symbol": "square-open", "size": 18, "color": "#38e8ff", "line": {"width": 3}},
                name=t("firebreak"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    sheet(fig, layout, 440)
    fig.update_layout(title={"text": map_title, "font": {"color": "#e8ecf4", "size": 14}, "x": 0.01})
    st.plotly_chart(fig, use_container_width=True)
    (st.success if fb is not None else st.info)(msg)
    if fb is not None and st.button(t("Put this firebreak into the wall")):
        state["layout"] = mf.with_metal(layout, fb.cells).tolist()
        st.rerun()
    st.caption(
        t(
            "The search tries every straight 50 cm strip on the burning material and keeps the one that protects the hatch best. Apply it, then search again to add the next one."
        )
    )

    with st.expander(t("Rates used and the limits of this sketch")):
        for k in ENV_ORDER:
            e = mf.ENVIRONMENTS[k]
            fab, acr = e.rates["F"], e.rates["A"]
            st.markdown(
                t(
                    "**{env}** - fabric {f1} mm/s along the flow, {f2} mm/s otherwise; acrylic {a1} / {a2} mm/s. Source: {src}.",
                    env=env_label(k),
                    f1=fab[0],
                    f2=fab[1],
                    a1=acr[0],
                    a2=acr[1],
                    src=e.source,
                )
            )
        st.markdown(
            t(
                "Not included: heating of nearby materials by the flame, the effect of the fire on its own oxygen supply, smoke and toxic gases, suppression, "
                "flames jumping across gaps, the 3-D shape of a module. The rates come from thin fabric and acrylic samples "
                "in air; other atmospheres are scaled with NASA's flame-spread theory, not measured. The sketch shows how layout and gravity "
                "change the timeline, not how long a real fire would take."
            )
        )

with tab_detect:
    st.subheader(t("Where to put detectors and suppression"))
    st.caption(
        t(
            "A design aid on the same NASA-measured spread rates. A detector counts a fire as seen when the flame reaches "
            "material within its coverage radius - a conservative stand-in: real smoke and gas detectors can react "
            "earlier. Detectors are placed one by one where they cut the average detection time most, over fires that "
            "start anywhere on the wall. Suppression points (portable extinguisher or fire port) cover first the material "
            "from which a fire reaches the hatch soonest - the crew's way out. Radius and reach are design inputs, not "
            "NASA numbers. Evidence: model."
        )
    )
    q1, q2, q3 = st.columns(3)
    genv = choice(q1.radio, t("Gravity"), ENV_ORDER, "det_env", format_func=env_label)
    n_det = q2.slider(t("Detectors"), 1, 8, 3, key="det_n")
    rad_cm = q2.slider(t("Detector coverage radius, cm"), 20, 150, 50, step=10, key="det_r")
    n_sup = q3.slider(t("Suppression points"), 0, 4, 1, key="sup_n")
    reach_cm = q3.slider(t("Suppression reach, cm"), 50, 300, 100, step=10, key="sup_r")
    det = _detectors(key, genv, vent, fac, n_det, rad_cm / 10)
    sup = _suppression(key, genv, vent, fac, n_sup, reach_cm / 10)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        t("Mean time to detect"),
        minutes(det["mean_s"]),
        help=t("Average over fires starting on any flammable cell that a detector sees."),
    )
    k2.metric(t("Slowest detection"), minutes(det["worst_s"]))
    k3.metric(t("Fires seen within 1 min"), f"{det['share_1min'] * 100:.0f} %")
    k4.metric(
        t("Hatch-critical material covered"),
        f"{sup['covered_share'] * 100:.0f} %" if n_sup else "-",
        help=t("Share of the material from which a fire reaches the hatch, weighted by how soon it gets there."),
    )
    if det["share_detected"] < 1:
        st.warning(
            t(
                "{p} % of the material is never seen: a fire there never reaches a coverage zone. Add a detector or widen the radius.",
                p=f"{(1 - det['share_detected']) * 100:.0f}",
            )
        )
    dm = np.where(np.isfinite(det["time"]), det["time"] / 60, np.nan)
    dfig = go.Figure()
    top = float(np.nanmax(dm)) if np.isfinite(dm).any() else 1.0
    step = next(v for v in (0.5, 1, 2, 5, 10, 15, 20, 30, 60) if top / v <= 9)
    dfig.add_trace(
        go.Contour(
            z=dm,
            contours={
                "start": 0,
                "end": top,
                "size": step,
                "showlabels": True,
                "labelfont": {"color": "#eafcff", "size": 11, "family": "Space Grotesk, sans-serif"},
            },
            colorscale=[[0, "#0b3d4f"], [0.35, "#1aa6c9"], [0.7, "#ffb627"], [1, "#ff4d2e"]],
            opacity=0.6,
            line={"width": 1.2, "color": "rgba(220,250,255,0.8)"},
            colorbar={
                "title": {"text": t("min"), "font": {"color": "#cfd6e4"}},
                "tickfont": {"color": "#cfd6e4"},
                "thickness": 12,
            },
            hovertemplate=t("seen after {m} min").replace("{m}", "%{z:.1f}") + "<extra></extra>",
        )
    )
    for r, c in det["cells"]:
        ring(dfig, r, c, rad_cm / 10, "rgba(56,232,255,1)", "solid")
    for r, c in sup["cells"]:
        ring(dfig, r, c, reach_cm / 10, "rgba(255,90,90,1)", "dash")
    if det["cells"]:
        dr, dc = zip(*det["cells"], strict=True)
        dfig.add_trace(
            go.Scatter(
                x=list(dc),
                y=list(dr),
                mode="markers+text",
                text=[f"D{i + 1}" for i in range(len(dr))],
                textposition="top center",
                textfont={"color": "#38e8ff", "size": 12},
                marker={"symbol": "circle", "size": 13, "color": "#38e8ff", "line": {"width": 2, "color": "#04151c"}},
                hoverinfo="skip",
            )
        )
    if sup["cells"]:
        sr, sc_ = zip(*sup["cells"], strict=True)
        dfig.add_trace(
            go.Scatter(
                x=list(sc_),
                y=list(sr),
                mode="markers+text",
                text=[f"S{i + 1}" for i in range(len(sr))],
                textposition="bottom center",
                textfont={"color": "#ff8080", "size": 12},
                marker={"symbol": "diamond", "size": 15, "color": "#ff4d4d", "line": {"width": 2, "color": "#2a0606"}},
                hoverinfo="skip",
            )
        )
    sheet(dfig, layout, 460)
    dfig.update_layout(
        title={
            "text": t("How soon a fire starting here is seen (minutes); D = detector, S = suppression point"),
            "font": {"color": "#e8ecf4", "size": 14},
            "x": 0.01,
        }
    )
    st.plotly_chart(dfig, use_container_width=True)
    pos = ", ".join(f"D{i + 1} ({c / 10:.1f} m, {r / 10:.1f} m)" for i, (r, c) in enumerate(det["cells"]))
    pos += "".join(f", S{i + 1} ({c / 10:.1f} m, {r / 10:.1f} m)" for i, (r, c) in enumerate(sup["cells"]))
    st.caption(t("Positions from the left and top edge of the wall:") + " " + pos)

    st.markdown("**" + t("Gas sensor in the module air") + "**")
    g1, g2 = st.columns([1, 2])
    rise_pct = g1.slider(t("CO2 alarm: rise above the start, %-points"), 0.02, 0.5, 0.1, step=0.02, key="gas_rise")
    g1.caption(t("A design input; the well-mixed air model gives the CO2 rise from the burnt fabric (step 04)."))
    if t_end > 0:
        tz2 = np.linspace(0, t_end, 400)
        rows_ = []
        for k in ENV_ORDER:
            zk2 = mf.zone_history(layout, times[k], tz2, float(vol), x_o2, p_atm)
            ga = mf.gas_alarm_time(tz2, zk2["x_co2"], rise_pct / 100)
            rows_.append((env_label(k), minutes(ga)))
        gcols = g2.columns(3)
        for col, (lab, val) in zip(gcols, rows_, strict=True):
            col.metric(lab, val, help=t("Time after ignition when the CO2 alarm would sound, this fire, {v} m3 of air.", v=vol))
    else:
        g2.info(t("Nothing burns yet: paint some fabric or acrylic, then click on it to set the ignition point."))

with tab_moon:
    # ---- solids at lunar gravity -------------------------------------------------------------------------------------
    st.subheader(t("Solid materials at lunar gravity: what NASA has found"))
    FACTS = [
        (
            "20210020516",
            t("Lunar gravity may be the most flammable condition"),
            "Lunar gravity is nearly the most flammable condition. Oxygen concentration for flammability reaches a minimum value in the vicinity of g = gMoon",
        ),
        (
            "20240008623",
            t("A fabric that goes out on Earth burns at lunar gravity"),
            "SIBAL fabric has been found to only burn downward in air in lunar gravity (via Lunar gravity centrifuge and parabolic flight) where on Earth’s gravity it extinguishes immediately after ignition.",
        ),
        (
            "20250010653",
            t("Slower, but longer: lunar-gravity flames on a sounding rocket"),
            "1-g extinction happens ~ 45 seconds sooner than partial-g extinction",
        ),
        (
            "20210020516",
            t("Switching off the fans is not enough on the Moon: buoyant flow remains"),
            "if a small (1-cm), engulfed, burning sample on Earth has U1 ≈ 100 cm/s, then on the Moon the same sample would have U1 ≈ 40 cm/s",
        ),
        (
            "20260000646",
            t("NASA expects a habitat fire on the Moon to be worse than on the ISS"),
            "partial-g fire in an extraterrestrial habitat is a real hazard that is expected to be substantially worse than in 0-g and potentially worse than even 1-g.",
        ),
    ]
    for ntrs_id, head, quote in FACTS:
        st.markdown(
            f'**{head}** · `{t("NASA literature")}`  \n> "{quote}"  \n[NTRS {ntrs_id}](https://ntrs.nasa.gov/citations/{ntrs_id})'
        )
    st.caption(
        t(
            "LUCI measured fabric spreading at 0.9 mm/s at lunar gravity vs 1.5 mm/s at 1 g (flame base), yet the flame "
            "lived about 45 s longer: slower is not safer."
        )
    )

    # ---- checklist ---------------------------------------------------------------------------------------------------
    st.subheader(t("Fire-safety checklist for a Moon-base module"))
    ins = {x["id"]: x for x in json.loads((ROOT / "docs" / "insights.json").read_text(encoding="utf-8"))["ranked"]}
    ma = moon_answer("Methanol")
    crew = mf.grid(mf.PRESETS["crew"])
    crew_moon = mf.summary(crew, mf.arrival_times(crew, mf.IGNITION["crew"], mf.ENVIRONMENTS["moon"]))["hatch_s"]
    CHECK = [
        (
            t("Suppress at once - do not wait for the fire to go out by itself."),
            t(
                "In NASA FLEX tests the flame went out by itself in {hi} % of {nhi} tests at 30 % O2 or more, vs {lo} % of {nlo} at 21 % or less.",
                hi=f"{ma['self_ext_high_o2'] * 100:.0f}",
                nhi=ma["n_high_o2"],
                lo=f"{ma['self_ext_low_o2'] * 100:.0f}",
                nlo=ma["n_low_o2"],
            ),
            "NASA data",
            "S4",
        ),
        (
            t("Expect faster, hotter fires in Moon-base air."),
            t(
                "Our model: burning rate {k} vs ISS air for a 3 mm droplet (extrapolation).",
                k=f"{(ma['k_ratio'] - 1) * 100:+.0f} %",
            ),
            "model",
            "P2",
        ),
        (
            t("Do not rely on switching off ventilation."),
            t("At 1/6 g buoyant flow still feeds the flame (about 40 cm/s where Earth has 100 cm/s, NTRS 20210020516)."),
            "NASA literature",
            "P6",
        ),
        (
            t("Re-test cabin materials at lunar gravity and in the Moon-base atmosphere."),
            t(
                "NASA's 1-g screening test (NASA-STD-6001B Test 1) may not be conservative: a fabric that goes out on Earth burns at lunar gravity (NTRS 20260000646, 20240008623)."
            ),
            "NASA literature",
            "P6",
        ),
        (
            t("Detect CO and other gases, not only smoke."),
            tr_insight(ins["D1"], "finding") if "D1" in ins else "",
            "NASA data",
            "D1",
        ),
        (
            t("Keep continuous runs of fabric away from the hatch; break them with metal or gaps."),
            t(
                "In the crew-quarters wall (step 03, test air) the flame reaches the hatch in {m} at lunar gravity; a metal strip or a gap stops it.",
                m=minutes(crew_moon),
            ),
            "model",
            "",
        ),
        (
            t("Plan an escape route a fire cannot cut off."),
            t('Mir 1997: "The flame blocked the evacuation route to the Soyuz spacecraft" (NASA History).'),
            "NASA history",
            "H3",
        ),
    ]
    for i, (action, why, ev, ref) in enumerate(CHECK, 1):
        tag = f" · {t('insight')} {ref}" if ref else ""
        st.markdown(f"**{i}. {action}** `{t(ev)}`{tag}  \n{why}")


# ---- downloadable report (ADR-055) ------------------------------------------------------------------------------
def module_report() -> str:
    """One Markdown report for the whole design: base, the module designed, fire, air, firebreak, detectors,
    suppression, checklist, sources and limits (ADR-059)."""
    from datetime import datetime
    from urllib.parse import urlencode

    out = [
        "# Moon-base fire design report - Prometheus-0g",
        "",
        f"Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC by https://prometheus-0g.streamlit.app/ (Moon-base fire designer).",
        "Evidence: model - a sketch on NASA-measured flame-spread rates, not a fire simulation. Module sizes, racks,",
        "detector radius, suppression reach and alarm threshold are design inputs, not NASA numbers.",
        "",
        "## 1. Base",
        f"Cabin atmosphere: {x_o2 * 100:.0f} % O2 at {p_atm * 14.696:.1f} psi; spread rates x{fac:.2f} (NASA flame-spread",
        "theory, NTRS 20210011385 Eq. 2.2; 1.00 = measured rates). Each module: one wall, fire at its default point,",
        "lunar gravity, hatches closed.",
        "",
        "| Module | Type | Size, m | Floor, m2 | Free air, m3 | Flame at the hatch | Peak fire power, kW | O2 at the end, % | Detectors for 90 % of fires in 1 min |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in base_rows:
        det_n = str(r["detectors"] or "> 8") if r["flammable_m2"] > 0 else "-"
        out.append(
            f"| {r['name']} | {r['kind']} | {r['length_m']:.0f} x {r['diameter_m']:.1f} | {r['floor_m2']:.1f} | "
            f"{r['free_volume_m3']:.1f} | {bv.mins(r['hatch_s'])} | {r['peak_kW']:.1f} | {r['o2_end'] * 100:.1f} | {det_n} |"
        )
    out += [
        "",
        f"## 2. Module designed: {sel['name'] if sel else '-'}",
        f"- Wall: {PRESET_LABEL[preset]()} (4 m x 2 m, 10 cm cells){' - edited by the user' if 'L' in shared else ''}",
        f"- Ignition point: {ign[1] / 10:.1f} m from the left, {ign[0] / 10:.1f} m from the top",
        f"- Ventilation in microgravity: {'towards' if vent == 1 else 'away from'} the hatch, 20 cm/s",
        f"- Free air for the air model: {vol:.0f} m3",
        "",
        "| Gravity | Flame at the hatch | Material reached, m2 | All of it burning after |",
        "|---|---|---|---|",
    ]
    for k in ENV_ORDER:
        sm = summ[k]
        out.append(
            f"| {env_label(k)} | {minutes(sm['hatch_s'])} | {sm['reached_m2']:.2f} of {sm['flammable_m2']:.2f} | "
            f"{minutes(sm['time_all_s'])} |"
        )
    if t_end > 0:
        tz = np.linspace(0, t_end, 160)
        out += [
            "",
            "### Module air (well-mixed zone model)",
            "| Gravity | Heat, MJ | Peak fire power, kW | O2 at the end, % | CO2 at the end, % |",
            "|---|---|---|---|---|",
        ]
        for k in ENV_ORDER:
            z = mf.zone_history(layout, times[k], tz, float(vol), x_o2, p_atm)
            out.append(
                f"| {env_label(k)} | {z['heat_MJ'][-1]:.1f} | {max(z['hrr_kW'].max(), 0):.1f} | {z['x_o2'][-1] * 100:.1f} | "
                f"{z['x_co2'][-1] * 100:.2f} |"
            )
        fbm = _firebreak(key, ign, "moon", vent, fac)
        out += ["", "## 3. Protection", "### Firebreak (lunar gravity)"]
        if fbm is None:
            out.append("- No single 50 cm metal strip changes when the flame reaches the hatch from this ignition point.")
        else:
            cells = ", ".join(f"({c / 10:.1f} m, {r / 10:.1f} m)" for r, c in fbm.cells)
            after = "never" if not math.isfinite(fbm.hatch_s) else minutes(fbm.hatch_s)
            out.append(f"- Metal strip at {cells}: flame at the hatch {minutes(summ['moon']['hatch_s'])} -> {after}.")
    out += [
        "",
        f"### Detectors ({env_label(genv)}, coverage radius {rad_cm} cm)",
        *[f"- D{i + 1}: {c / 10:.1f} m from the left, {r / 10:.1f} m from the top" for i, (r, c) in enumerate(det["cells"])],
        f"- Mean time to detect {minutes(det['mean_s'])}, slowest {minutes(det['worst_s'])}, fires seen within 1 min "
        f"{det['share_1min'] * 100:.0f} %, never seen {(1 - det['share_detected']) * 100:.0f} % of the material.",
        "",
        f"### Suppression points (reach {reach_cm} cm)",
        *[f"- S{i + 1}: {c / 10:.1f} m from the left, {r / 10:.1f} m from the top" for i, (r, c) in enumerate(sup["cells"])],
        f"- Hatch-critical material covered: {sup['covered_share'] * 100:.0f} %" if n_sup else "- none placed",
    ]
    if t_end > 0:
        out += ["", f"### CO2 alarm (rise of {rise_pct:.2f} %-points in {vol:.0f} m3)"]
        out += [f"- {lab}: {val}" for lab, val in rows_]
    out += ["", "## 4. Checklist"]
    out += [f"{i}. {action} ({ev})" for i, (action, _why, ev, _ref) in enumerate(CHECK, 1)]
    out += [
        "",
        "## Sources and limits",
        "- Flame-spread rates: Saffire (NTRS 20170008805), LUCI sounding rocket (NTRS 20250010653).",
        "- Oxygen use of SIBAL fabric: NTRS 20210020516; heat per gram of O2: NASA BASS-II report (NTRS 20210011385).",
        "- A detector counts a fire when the flame reaches material within its radius (conservative stand-in).",
        "- Not included: heating of nearby materials, the fire's effect on its own oxygen supply, smoke and toxic gases,",
        "  suppression itself, flames jumping across gaps or hatches, the 3-D shape of a module.",
        "",
        "Link to reopen this design: https://prometheus-0g.streamlit.app/module?" + urlencode(shared),
    ]
    return "\n".join(out) + "\n"


REPORT = module_report()
report_slot.download_button(
    t("Download the design report"), REPORT, "moon_base_fire_report.md", "text/markdown", icon=":material/download:"
)
with tab_report:
    st.markdown("### " + t("One report for the whole design"))
    st.caption(t("Base, the module you designed, fire, air, firebreak, detectors, extinguishers, checklist and sources."))
    st.download_button(
        t("Download the design report"),
        REPORT,
        "moon_base_fire_report.md",
        "text/markdown",
        icon=":material/download:",
        type="primary",
        key="report_dl_tab",
    )
    with st.container(border=True):
        st.markdown(REPORT.replace("# Moon-base fire design report - Prometheus-0g", "#### Moon-base fire design report", 1))

source_note(
    t(
        "flame-spread rates from NTRS 20170008805 (Saffire) and NTRS 20250010653 (LUCI); quotes from NTRS 20210020516, "
        "20240008623, 20260000646; FLEX numbers from fif.insights.moon; spread sketch: src/fif/physics/module_fire.py "
        "(ADR-049)."
    )
)

next_step("views/module.py")
