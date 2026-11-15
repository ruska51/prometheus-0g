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

from fif.insights.moon import moon_answer
from fif.physics import module_fire as mf

ROOT = Path(__file__).resolve().parents[2]
COLORS = {"F": "#c9a66b", "A": "#8ecae6", "M": "#8d939c", ".": "#f3f4f6", "H": "#2e9d5b"}
BURNING, BURNT = "#ff5a1f", "#3b2a24"
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
PRESET_LABEL = {
    "crew": lambda: t("Crew quarters wall"),
    "lab": lambda: t("Laboratory rack wall"),
    "stowage": lambda: t("Stowage wall"),
}


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
c1, c2, c3 = st.columns([1.2, 1.2, 1.6])
preset = c1.selectbox(t("Module wall"), list(mf.PRESETS), format_func=lambda k: PRESET_LABEL[k]())
env_key = c2.radio(t("Gravity"), ENV_ORDER, format_func=env_label)
mode = c3.radio(
    t("Click on the wall to..."),
    ["ignite", "paint"],
    format_func=lambda m: t("set the ignition point") if m == "ignite" else t("paint material (click or box-select)"),
    horizontal=True,
)
paint = c3.selectbox(
    t("Material to paint"), ["F", "A", "M", ".", "H"], format_func=lambda k: MATERIAL_LABEL[k](), disabled=mode != "paint"
)

state = st.session_state.setdefault("module", {})
if state.get("preset") != preset:
    state.update(preset=preset, layout=mf.grid(mf.PRESETS[preset]).tolist(), ignition=mf.IGNITION[preset], selection=None)
if st.button(t("Reset this wall")):
    state.update(layout=mf.grid(mf.PRESETS[preset]).tolist(), ignition=mf.IGNITION[preset], selection=None)
layout = np.array(state["layout"])
h, w = layout.shape
rows, cols = np.indices((h, w))

editor = go.Figure()
for code in ["F", "A", "M", ".", "H"]:
    m = layout == code
    if m.any():
        editor.add_trace(
            go.Scatter(
                x=cols[m],
                y=rows[m],
                mode="markers",
                marker={"symbol": "square", "size": 17, "color": COLORS[code], "line": {"width": 0.5, "color": "#ffffff"}},
                name=MATERIAL_LABEL[code](),
                hovertemplate="%{x}, %{y}<extra>" + MATERIAL_LABEL[code]() + "</extra>",
            )
        )
r0, c0 = state["ignition"]
editor.add_trace(
    go.Scatter(
        x=[c0],
        y=[r0],
        mode="markers",
        marker={"symbol": "star", "size": 20, "color": BURNING, "line": {"width": 1, "color": "#000"}},
        name=t("Ignition"),
        hoverinfo="skip",
    )
)
editor.update_layout(
    height=430,
    margin={"l": 10, "r": 10, "t": 10, "b": 10},
    plot_bgcolor="#ffffff",
    legend={"orientation": "h", "y": -0.05},
    xaxis={"visible": False, "range": [-1, w]},
    yaxis={"visible": False, "autorange": "reversed", "scaleanchor": "x"},
    dragmode="select" if mode == "paint" else False,
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
st.caption(t("Each square is 10 x 10 cm; the wall is 4 m x 2 m. Up is up (gravity), ventilation blows from left to right."))

# ---- spread in the three environments -------------------------------------------------------------------------
ign = tuple(state["ignition"])
times = {k: mf.arrival_times(layout, ign, mf.ENVIRONMENTS[k]) for k in ENV_ORDER}
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
    col.metric(
        env_label(k),
        minutes(s["hatch_s"]),
        help=t("Time until the flame reaches material next to the hatch."),
    )
    col.caption(
        t(
            "Flame reaches {a} of {b} m2 of material; all of it burning after {m}.",
            a=f"{s['reached_m2']:.2f}",
            b=f"{s['flammable_m2']:.2f}",
            m=minutes(s["time_all_s"]),
        )
    )

tk = times[env_key]
finite = tk[np.isfinite(tk)]
t_end = float(finite.max()) if finite.size else 0.0
if t_end > 0:
    n_frames = 36
    t_grid = np.linspace(0, t_end, n_frames)
    window = max(60.0, t_end / 12)  # how long a cell is drawn as "burning" (display only)
    base = np.array([COLORS[c] for c in layout.ravel()], dtype=object)
    flat_t = tk.ravel()

    def colors_at(now: float) -> list[str]:
        c = base.copy()
        c[(flat_t <= now) & (flat_t > now - window)] = BURNING
        c[flat_t <= now - window] = BURNT
        return c.tolist()

    anim = go.Figure(
        data=[
            go.Scatter(
                x=cols.ravel(),
                y=rows.ravel(),
                mode="markers",
                marker={"symbol": "square", "size": 17, "color": colors_at(0.0)},
                hoverinfo="skip",
                showlegend=False,
            )
        ],
        frames=[
            go.Frame(data=[go.Scatter(marker={"symbol": "square", "size": 17, "color": colors_at(x)})], name=f"{x / 60:.1f}")
            for x in t_grid
        ],
    )
    anim.update_layout(
        height=470,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        plot_bgcolor="#ffffff",
        title={"text": env_label(env_key), "x": 0.01, "font": {"size": 14}},
        xaxis={"visible": False, "range": [-1, w]},
        yaxis={"visible": False, "autorange": "reversed", "scaleanchor": "x"},
        updatemenus=[
            {
                "type": "buttons",
                "x": 0.0,
                "y": -0.02,
                "xanchor": "left",
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "▶ " + t("Play"),
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 250, "redraw": True}, "fromcurrent": True}],
                    },
                    {"label": "❚❚", "method": "animate", "args": [[None], {"mode": "immediate", "frame": {"duration": 0}}]},
                ],
            }
        ],
        sliders=[
            {
                "x": 0.12,
                "len": 0.88,
                "y": -0.02,
                "currentvalue": {"prefix": t("minutes after ignition: ")},
                "steps": [
                    {
                        "label": f.name,
                        "method": "animate",
                        "args": [[f.name], {"mode": "immediate", "frame": {"duration": 0, "redraw": True}}],
                    }
                    for f in anim.frames
                ],
            }
        ],
    )
    st.plotly_chart(anim, use_container_width=True)
    st.caption(t("Orange: flame front; dark: burnt; green: hatch. Choose the gravity above to animate another case."))

    t_all = max(summ[k]["time_all_s"] for k in ENV_ORDER)
    grid_t = np.linspace(0, t_all, 120)
    curve = go.Figure()
    for k in ENV_ORDER:
        curve.add_trace(go.Scatter(x=grid_t / 60, y=mf.burned_area_curve(times[k], grid_t), mode="lines", name=env_label(k)))
    curve.update_layout(
        height=300,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        xaxis_title=t("minutes after ignition"),
        yaxis_title=t("area reached by the flame, m2"),
        legend={"orientation": "h", "y": -0.3},
    )
    st.plotly_chart(curve, use_container_width=True)

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
