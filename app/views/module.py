"""Moon-base module: draw a module wall, light a fire and watch it spread at NASA-measured rates in three gravities;
solid materials at lunar gravity; a fire-safety checklist with the evidence for each item (ADR-049, steps 2-4)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from common import source_note
from i18n import t, tr_insight
from plotly.subplots import make_subplots

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


def dark_layout(fig: go.Figure, height: int, axes: bool = False) -> None:
    fig.update_layout(height=height, margin={"l": 10, "r": 10, "t": 36, "b": 10}, paper_bgcolor=BG, plot_bgcolor=BG)
    if axes:
        fig.update_xaxes(color="#cfd6e4", gridcolor="#26304a", zeroline=False)
        fig.update_yaxes(color="#cfd6e4", gridcolor="#26304a", zeroline=False)
    else:
        fig.update_xaxes(visible=False, range=[-0.6, 39.6])
        fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")


def env_obj(env: str, vent: int) -> mf.Environment:
    """Measured rates for the gravity; in microgravity the ventilation direction decides which way is 'with the flow'."""
    return mf.iss_with_flow(vent) if env == "iss" else mf.ENVIRONMENTS[env]


def _grid(key: tuple[str, ...]) -> np.ndarray:
    return np.array([list(r) for r in key])


@st.cache_data(show_spinner=False, max_entries=64)
def _arrival(key: tuple[str, ...], ign: tuple[int, int], env: str, vent: int) -> np.ndarray:
    return mf.arrival_times(_grid(key), ign, env_obj(env, vent))


@st.cache_data(show_spinner=False, max_entries=64)
def _to_hatch(key: tuple[str, ...], env: str, vent: int) -> np.ndarray:
    return mf.time_to_hatch(_grid(key), env_obj(env, vent))


@st.cache_data(show_spinner=t("Trying every 50 cm strip..."), max_entries=32)
def _firebreak(key: tuple[str, ...], ign: tuple[int, int], env: str, vent: int):
    return mf.best_firebreak(_grid(key), ign, env_obj(env, vent))


@st.cache_data(show_spinner=t("Trying every 50 cm strip..."), max_entries=32)
def _firebreak_anywhere(key: tuple[str, ...], env: str, vent: int):
    return mf.best_firebreak_anywhere(_grid(key), env_obj(env, vent))


def minutes(s: float) -> str:
    return t("not reached") if not math.isfinite(s) else t("{m} min", m=f"{s / 60:.0f}" if s >= 600 else f"{s / 60:.1f}")


st.title(t("Fire in a Moon-base module"))
st.markdown(
    t(
        "Draw a wall of a module, choose where a fire starts and watch it spread. Every material spreads fire at the "
        "rate NASA measured for it in that gravity (Saffire on the ISS, LUCI at lunar gravity, the same samples on "
        "Earth). This is a sketch on measured rates, not a fire simulation: see the limits below."
    )
)
st.caption(
    t(
        "Evidence: model (sketch on measured NASA rates). Rates measured in air (21-22 % O2): in Moon-base air (30 % O2) a fire is expected to spread faster, so the times are upper bounds."
    )
)

# ---- module designer -------------------------------------------------------------------------------------------
c1, c2 = st.columns([1.1, 1.9])
preset = c1.selectbox(t("Module wall"), list(mf.PRESETS), format_func=lambda k: PRESET_LABEL[k]())
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
vent = c1.radio(
    t("Ventilation in microgravity (ISS case)"),
    [1, -1],
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
for code in ["F", "A", "M", ".", "H"]:
    m = layout == code
    if m.any():
        editor.add_trace(
            go.Scatter(
                x=cols[m],
                y=rows[m],
                mode="markers",
                marker={"symbol": "square", "size": 16, "color": COLORS[code], "line": {"width": 1, "color": BG}},
                name=MATERIAL_SHORT[code](),
                hovertemplate=MATERIAL_LABEL[code]() + "<extra></extra>",
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
dark_layout(editor, 400)
editor.update_layout(
    legend={"orientation": "h", "y": -0.02, "font": {"color": "#cfd6e4"}}, dragmode="select" if mode == "paint" else False
)
event = st.plotly_chart(
    editor, key=f"wall-{preset}", on_select="rerun", selection_mode=("points", "box"), use_container_width=True
)
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
times = {k: _arrival(key, ign, k, vent) for k in ENV_ORDER}
summ = {k: mf.summary(layout, times[k]) for k in ENV_ORDER}

st.subheader(t("How the fire spreads"))
st.caption(
    t(
        "Time until the flame reaches the hatch, for the same wall and the same ignition point. In these NASA tests "
        "fabric spread more slowly at lunar gravity than on Earth, but lunar-gravity flames lasted longer and some "
        "materials burn there that go out on Earth (see below) - and Moon-base air is richer in oxygen than the test air."
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

t_end = max(summ[k]["time_all_s"] for k in ENV_ORDER)
if t_end > 0:
    n_frames = 40
    t_grid = np.linspace(0, t_end * 1.05, n_frames)
    window = max(45.0, t_end / 14)  # display only: how long a cell glows before it turns to embers and char
    base = np.vectorize(CODE_Z.get)(layout).astype(float)

    def z_at(tk: np.ndarray, now: float) -> np.ndarray:
        age = now - tk
        z = base.copy()
        for lo, hi, val in ((0, 0.3, 5), (0.3, 0.7, 6), (0.7, 1.2, 7), (1.2, 2.0, 8)):
            z[(age >= lo * window) & (age < hi * window)] = val
        z[age >= 2.0 * window] = 9
        return z

    race = make_subplots(
        rows=3,
        cols=1,
        vertical_spacing=0.07,
        subplot_titles=[f"{env_label(k)} - {t('hatch')}: {minutes(summ[k]['hatch_s'])}" for k in ENV_ORDER],
    )
    for i, k in enumerate(ENV_ORDER, 1):
        race.add_trace(heat(z_at(times[k], 0.0)), row=i, col=1)
        race.update_xaxes(visible=False, range=[-0.5, w - 0.5], row=i, col=1)
        race.update_yaxes(visible=False, autorange="reversed", scaleanchor=f"x{'' if i == 1 else i}", row=i, col=1)
    race.frames = [
        go.Frame(data=[heat(z_at(times[k], x)) for k in ENV_ORDER], traces=[0, 1, 2], name=f"{x / 60:.1f}") for x in t_grid
    ]
    race.update_annotations(font={"color": "#e8ecf4", "size": 13})
    race.update_layout(
        height=1080,
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        updatemenus=[
            {
                "type": "buttons",
                "x": 0.0,
                "y": -0.01,
                "xanchor": "left",
                "yanchor": "top",
                "bgcolor": "#ff7a1a",
                "font": {"color": "#0d1322"},
                "buttons": [
                    {
                        "label": "▶ " + t("Play"),
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 220, "redraw": True}, "fromcurrent": True}],
                    },
                    {"label": "❚❚", "method": "animate", "args": [[None], {"mode": "immediate", "frame": {"duration": 0}}]},
                ],
            }
        ],
        sliders=[
            {
                "x": 0.14,
                "len": 0.86,
                "y": -0.01,
                "font": {"color": "#cfd6e4"},
                "currentvalue": {"prefix": t("minutes after ignition: "), "font": {"color": "#ffb627"}},
                "steps": [
                    {
                        "label": f.name,
                        "method": "animate",
                        "args": [[f.name], {"mode": "immediate", "frame": {"duration": 0, "redraw": True}}],
                    }
                    for f in race.frames
                ],
            }
        ],
    )
    st.plotly_chart(race, use_container_width=True)
    st.caption(
        t(
            "Same wall, same spark, three gravities. White-yellow: new flame; orange-red: burning; dark red: embers; black: burnt; green: hatch."
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
    fb = _firebreak(key, ign, denv, vent)
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
    tmap = _to_hatch(key, denv, vent)
    fb = _firebreak_anywhere(key, denv, vent)
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
fig.add_trace(heat(np.vectorize(CODE_Z.get)(layout).astype(float)))
fig.add_trace(
    go.Heatmap(
        z=mins,
        colorscale=[[0, "#fff1a8"], [0.25, "#ffb627"], [0.55, "#ff5a1f"], [0.8, "#9e2a1b"], [1, "#3b1414"]],
        reversescale=goal == "anywhere",
        xgap=1,
        ygap=1,
        colorbar={"title": {"text": t("min"), "font": {"color": "#cfd6e4"}}, "tickfont": {"color": "#cfd6e4"}, "thickness": 12},
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
dark_layout(fig, 420)
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
            "Not included: heating of nearby materials by the flame, oxygen use, smoke and toxic gases, suppression, "
            "flames jumping across gaps, the 3-D shape of a module. The rates come from thin fabric and acrylic samples "
            "in air; Moon-base air (30 % O2) is expected to spread fire faster. The sketch shows how layout and gravity "
            "change the timeline, not how long a real fire would take."
        )
    )

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
        t("Our model: burning rate {k} vs ISS air for a 3 mm droplet (extrapolation).", k=f"{(ma['k_ratio'] - 1) * 100:+.0f} %"),
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
            "In the crew-quarters sketch above the flame reaches the hatch in {m} at lunar gravity; a metal strip or a gap stops it.",
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

source_note(
    t(
        "flame-spread rates from NTRS 20170008805 (Saffire) and NTRS 20250010653 (LUCI); quotes from NTRS 20210020516, "
        "20240008623, 20260000646; FLEX numbers from fif.insights.moon; spread sketch: src/fif/physics/module_fire.py "
        "(ADR-049)."
    )
)
