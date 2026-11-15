"""Fire spread over the wall of a Moon-base module, from measured NASA flame-spread rates (ADR-049, step 2).

What it is: a wall of a module (racks, stowage bags, panels) drawn as a grid of 10 cm cells. Each flammable cell takes
fire from a burning neighbour after (distance / spread rate), with the rate measured by NASA for that material in that
gravity; the earliest arrival time of the flame in every cell is found with Dijkstra's shortest-path algorithm.

What it is not: a CFD fire model. It ignores heating of neighbouring materials, oxygen depletion, smoke, suppression,
the 3-D shape of a real module and flames jumping across gaps (only touching cells, including diagonal ones, ignite).
The rates were measured on thin fabric and acrylic samples in air (21-22 % O2); in Moon-base air (30 % O2) a flame is
expected to spread faster (not measured), so the times shown are upper bounds. Display label: "model (sketch on
measured NASA rates)".

Rates (mm/s), "fast" = along the flow (upward in gravity, downstream with ventilation), "slow" = every other direction:

* Microgravity, ventilation 20 cm/s - NTRS 20170008805 (Saffire, large-scale spacecraft flammability tests): SIBAL
  cotton/fiberglass fabric, 40.6 cm wide sample, "average concurrent-flow flame spread rate is 1.8 mm/s. The
  opposed-flow flame average spread rate 1.3 mm/s". Thick PMMA (Saffire-2): "The flames remain anchored at the base of
  the sample" -> no spread (0).
* Lunar gravity - NTRS 20250010653 (LUCI rotating sounding rocket): SIBAL "Partial-G (mm/s)": flame base 0.9, flame
  tip 1.1; PMMA flame tip 0.15 cm/s = 1.5 mm/s; PMMA flame base "increases linearly from 0 to ~.6 mm/s" -> 0.6.
* Earth 1 g - same report, 1-G column: SIBAL flame base 1.5, flame tip 2.8 mm/s; PMMA flame tip 0.40 cm/s = 4.0 mm/s,
  "Flame base location is ~constant" -> 0.

Units: cells of CELL_MM, times in s, rates in mm/s.
"""

from __future__ import annotations

import dataclasses
import functools
import heapq
import math
from dataclasses import dataclass

import numpy as np

CELL_MM = 100.0  # one grid cell = 10 cm
FLAMMABLE = ("F", "A")  # fabric (SIBAL-type cotton/fiberglass), acrylic (PMMA)
CODES = {
    "F": "Fabric (cotton/fiberglass, e.g. stowage bags, clothing)",
    "A": "Acrylic (PMMA) panel",
    "M": "Metal / non-flammable",
    ".": "Open space",
    "H": "Hatch (escape route)",
}


@dataclass(frozen=True)
class Environment:
    key: str
    label: str
    fast_axis: tuple[int, int]  # (dx, dy) of the flow: up in gravity, downstream with ventilation
    rates: dict[str, tuple[float, float]]  # material -> (fast, slow) mm/s
    source: str
    note: str


ENVIRONMENTS = {
    "iss": Environment(
        "iss",
        "Microgravity, ventilation 20 cm/s (ISS)",
        (1, 0),  # ventilation blows along the wall, left to right
        {"F": (1.8, 1.3), "A": (0.0, 0.0)},
        "NTRS 20170008805 (Saffire-1 and -2, microgravity, 20 cm/s air flow)",
        "Acrylic: flames stayed anchored at the base of thick PMMA (no spread).",
    ),
    "moon": Environment(
        "moon",
        "Lunar gravity (1/6 g)",
        (0, 1),  # buoyant flow: upward
        {"F": (1.1, 0.9), "A": (1.5, 0.6)},
        "NTRS 20250010653 (LUCI, rotating sounding rocket at lunar gravity)",
        "Acrylic base spread grew from 0 to about 0.6 mm/s; 0.6 is used.",
    ),
    "earth": Environment(
        "earth",
        "Earth gravity (1 g)",
        (0, 1),
        {"F": (2.8, 1.5), "A": (4.0, 0.0)},
        "NTRS 20250010653 (LUCI 1-g reference burns)",
        "Acrylic: the flame base stayed in place, only the tip spread upward.",
    ),
}


def iss_with_flow(direction: int) -> Environment:
    """Microgravity case with the ventilation blowing left -> right (direction 1) or right -> left (-1): the measured
    concurrent rate (1.8 mm/s for fabric) applies downstream, the opposed rate (1.3 mm/s) upstream."""
    return dataclasses.replace(ENVIRONMENTS["iss"], fast_axis=(1 if direction >= 0 else -1, 0))


# Layouts: one string per row, top row first ("up" = towards row 0). 40 x 20 cells = a 4 m x 2 m wall section.
PRESETS = {
    "crew": [
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
        "M..FFFFFF....AAAAAA....FFFFFFFFF......HM",
        "M..FFFFFF....AAAAAA....FFFFFFFFF......HM",
        "M..FFFFFF....AAAAAA....FFFFFFFFF......HM",
        "M..MMMMMM....AAAAAA....FFFFFFFFF......HM",
        "M..FFFFFF....AAAAAA....FFFFFFFFF......HM",
        "M..FFFFFF....MMMMMM....FFFFFFFFF......HM",
        "M..FFFFFF..............FFFFFFFFF......HM",
        "M..MMMMMM..............FFFFFFFFF......HM",
        "M..FFFFFFFFFFFFFFFF....FFFFFFFFF......HM",
        "M..FFFFFFFFFFFFFFFF....FFFFFFFFFFFFFFFHM",
        "M..FFFFFFFFFFFFFFFF....FFFFFFFFFFFFFFFHM",
        "M..MMMMMMMMMMMMMMMM....FFFFFFFFFFFFFFFHM",
        "M..FFFFF..FFFFF........FFFFFFFFFFFFFFFHM",
        "M..FFFFF..FFFFF........FFFFFFFFFFFFFFFHM",
        "M..FFFFF..FFFFF........MMMMMMMMMMMMM..HM",
        "M.....................................HM",
        "M.....................................HM",
        "M.....................................HM",
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    ],
    "lab": [
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAMFFFFF.H",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAMFFFFF.H",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAMFFFFF.H",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAMFFFFF.H",
        "MMMMMMMMMMMMFFFFFFFFFFMMMMMMMMMMMFFFFF.H",
        "MFFFFFFFFFFMFFFFFFFFFFMFFFFFFFFFMFFFFF.H",
        "MFFFFFFFFFFMMMMMMMMMMMMFFFFFFFFFMFFFFF.H",
        "MFFFFFFFFFFMFFFFFFFFFFMFFFFFFFFFMMMMMM.H",
        "MFFFFFFFFFFMFFFFFFFFFFMFFFFFFFFFM.....FH",
        "MMMMMMMMMMMMFFFFFFFFFFMMMMMMMMMMM.....FH",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAM.....FH",
        "MAAAAAAAAAAMMMMMMMMMMMMAAAAAAAAAM.....FH",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAM.....FH",
        "MAAAAAAAAAAMFFFFFFFFFFMAAAAAAAAAM.....FH",
        "MMMMMMMMMMMMFFFFFFFFFFMMMMMMMMMMM.....FH",
        "M...........FFFFFFFFFFFFFFFFFFFFFFFFFFFH",
        "M...........FFFFFFFFFFFFFFFFFFFFFFFFFFFH",
        "M...........FFFFFFFFFFFFFFFFFFFFFFFFFFFH",
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    ],
    "stowage": [
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFH",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFH",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MFFFFFFF.FFFFFFF.FFFFFFF.FFFFFFF.FFFFF.H",
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM.H",
        "M......................................H",
        "M......................................H",
        "M......................................H",
        "M......................................H",
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    ],
}

PRESETS["blank"] = [
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "M.....................................HM",
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
]  # draw your own: frame and hatch only
IGNITION = {"crew": (14, 24), "lab": (16, 14), "stowage": (12, 3), "blank": (10, 5)}  # default ignition cell (row, col)


def grid(rows: list[str]) -> np.ndarray:
    """Layout strings -> 2-D array of single-character codes (row 0 = top)."""
    width = max(len(r) for r in rows)
    return np.array([list(r.ljust(width, ".")) for r in rows])


def _rate(env: Environment, material: str, dx: int, dy: int) -> float:
    """Spread rate (mm/s) into a cell of ``material`` along the step (dx, dy); dy < 0 is a step up (row index falls)."""
    if material not in env.rates:
        return 0.0
    fast, slow = env.rates[material]
    fx, fy = env.fast_axis
    along = dx * fx + (-dy) * fy  # positive = with the flow (up is -dy in row coordinates)
    return fast if along > 0 else slow


def arrival_times(layout: np.ndarray, ignition: tuple[int, int], env: Environment) -> np.ndarray:
    """Earliest time (s) at which the flame reaches each cell; inf where it never does. ``ignition`` = (row, col) of a
    flammable cell. Steps go to the 8 neighbours (diagonal step = sqrt(2) cells)."""
    h, w = layout.shape
    t = np.full((h, w), math.inf)
    r0, c0 = ignition
    if layout[r0, c0] not in FLAMMABLE:
        return t
    t[r0, c0] = 0.0
    heap = [(0.0, r0, c0)]
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    while heap:
        tc, r, c = heapq.heappop(heap)
        if tc > t[r, c]:
            continue
        for dr, dc in steps:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w) or layout[rr, cc] not in FLAMMABLE:
                continue
            v = _rate(env, layout[rr, cc], dc, dr)
            if v <= 0:
                continue
            tn = tc + CELL_MM * math.hypot(dr, dc) / v
            if tn < t[rr, cc]:
                t[rr, cc] = tn
                heapq.heappush(heap, (tn, rr, cc))
    return t


def hatch_time(layout: np.ndarray, times: np.ndarray) -> float:
    """Time (s) when the flame first reaches a cell touching the hatch (8-neighbourhood); inf if never."""
    h, w = layout.shape
    best = math.inf
    for r, c in zip(*np.where(layout == "H"), strict=True):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    best = min(best, times[rr, cc])
    return best


def summary(layout: np.ndarray, times: np.ndarray) -> dict:
    """Burnable area, area the flame reaches, time to reach it all, time to reach the hatch (cell area 0.01 m2)."""
    cell_m2 = (CELL_MM / 1000) ** 2
    flammable = np.isin(layout, FLAMMABLE)
    reached = np.isfinite(times)
    return {
        "flammable_m2": float(flammable.sum() * cell_m2),
        "reached_m2": float(reached.sum() * cell_m2),
        "time_all_s": float(times[reached].max()) if reached.any() else 0.0,
        "hatch_s": hatch_time(layout, times),
    }


def burned_area_curve(times: np.ndarray, t_grid: np.ndarray) -> np.ndarray:
    """Area (m2) the flame has reached at each time of ``t_grid``."""
    cell_m2 = (CELL_MM / 1000) ** 2
    reached = np.sort(times[np.isfinite(times)])
    return np.searchsorted(reached, t_grid, side="right") * cell_m2


@dataclass(frozen=True)
class Firebreak:
    cells: tuple[tuple[int, int], ...]  # (row, col) of flammable cells replaced by metal
    hatch_s: float  # time to reach the hatch with the firebreak (inf = never)
    reached_m2: float


def with_metal(layout: np.ndarray, cells) -> np.ndarray:
    out = layout.copy()
    for r, c in cells:
        out[r, c] = "M"
    return out


def best_firebreak(layout: np.ndarray, ignition: tuple[int, int], env: Environment, length: int = 5) -> Firebreak | None:
    """The straight metal strip of ``length`` cells (vertical or horizontal) that delays the flame at the hatch most;
    ties broken by the smaller burnt area. Only strips that lie on cells the flame reaches before the hatch are tried
    (a strip elsewhere cannot change the hatch time); the ignition cell itself is never covered. None if the flame does
    not reach the hatch in the first place or no candidate helps."""
    base = arrival_times(layout, ignition, env)
    t_hatch = hatch_time(layout, base)
    if not math.isfinite(t_hatch):
        return None
    h, w = layout.shape
    on_path = [(r, c) for r, c in zip(*np.where(base <= t_hatch), strict=True) if (r, c) != tuple(ignition)]
    best = None
    seen = set()
    for r, c in on_path:
        for dr, dc in ((1, 0), (0, 1)):
            for shift in range(length):
                cells = tuple(
                    (r + (k - shift) * dr, c + (k - shift) * dc)
                    for k in range(length)
                    if 0 <= r + (k - shift) * dr < h and 0 <= c + (k - shift) * dc < w
                )
                cells = tuple((int(a), int(b)) for a, b in cells if layout[a, b] in FLAMMABLE and (a, b) != tuple(ignition))
                if not cells or cells in seen:
                    continue
                seen.add(cells)
                lay = with_metal(layout, cells)
                tt = arrival_times(lay, ignition, env)
                cand = Firebreak(cells, hatch_time(lay, tt), float(np.isfinite(tt).sum() * (CELL_MM / 1000) ** 2))
                key = (cand.hatch_s, -cand.reached_m2)
                if best is None or key > (best.hatch_s, -best.reached_m2):
                    best = cand
    if best is None or best.hatch_s <= t_hatch:
        return None
    return best


def time_to_hatch(layout: np.ndarray, env: Environment) -> np.ndarray:
    """For every cell: the time (s) a fire that starts there needs to reach a cell touching the hatch (inf = never).
    Same rates and steps as ``arrival_times``, run backwards from the hatch (reverse Dijkstra)."""
    h, w = layout.shape
    t = np.full((h, w), math.inf)
    heap = []
    for r, c in zip(*np.where(layout == "H"), strict=True):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and layout[rr, cc] in FLAMMABLE and t[rr, cc] > 0:
                    t[rr, cc] = 0.0
                    heap.append((0.0, rr, cc))
    heapq.heapify(heap)
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    while heap:
        tv, r, c = heapq.heappop(heap)
        if tv > t[r, c]:
            continue
        for dr, dc in steps:  # predecessor u = (r - dr, c - dc) spreads into v = (r, c) with the step (dr, dc)
            ur, uc = r - dr, c - dc
            if not (0 <= ur < h and 0 <= uc < w) or layout[ur, uc] not in FLAMMABLE:
                continue
            v = _rate(env, layout[r, c], dc, dr)
            if v <= 0:
                continue
            tu = tv + CELL_MM * math.hypot(dr, dc) / v
            if tu < t[ur, uc]:
                t[ur, uc] = tu
                heapq.heappush(heap, (tu, ur, uc))
    return t


def hatch_catchment_m2(times_to_hatch: np.ndarray) -> float:
    """Area (m2) of material from which a fire can reach the hatch."""
    return float(np.isfinite(times_to_hatch).sum() * (CELL_MM / 1000) ** 2)


def best_firebreak_anywhere(layout: np.ndarray, env: Environment, length: int = 5) -> Firebreak | None:
    """The straight metal strip of ``length`` cells (vertical or horizontal, centred on a cell) that most reduces the
    area of material from which a fire, wherever it starts, can reach the hatch; ties broken by the longer median time
    to the hatch. ``hatch_s`` = that median time, ``reached_m2`` = the remaining area. None if nothing improves."""
    base = time_to_hatch(layout, env)
    base_area = hatch_catchment_m2(base)
    if base_area == 0:
        return None
    h, w = layout.shape
    best, best_key, seen = None, None, set()
    half = length // 2
    for r, c in zip(*np.where(np.isfinite(base)), strict=True):
        for dr, dc in ((1, 0), (0, 1)):
            cells = tuple(
                (int(r + k * dr), int(c + k * dc))
                for k in range(-half, length - half)
                if 0 <= r + k * dr < h and 0 <= c + k * dc < w and layout[r + k * dr, c + k * dc] in FLAMMABLE
            )
            if not cells or cells in seen:
                continue
            seen.add(cells)
            tt = time_to_hatch(with_metal(layout, cells), env)
            area = hatch_catchment_m2(tt)
            med = float(np.median(tt[np.isfinite(tt)])) if np.isfinite(tt).any() else math.inf
            key = (-area, med)
            if best_key is None or key > best_key:
                best_key, best = key, Firebreak(cells, med, area)
    if best is None or best.reached_m2 >= base_area:
        return None
    return best


# ---- atmosphere (ADR-051): physics-theory scaling of the measured rates ------------------------------------------
# NASA/TM-20210011385 (BASS-II summary report), Eq. (2.2), thermal limit of flame spread over a thin solid (de Ris):
# V_f = F * lambda_g * (T_f - T_v) / (rho_s * c_s * tau * (T_v - T_inf)). For the same material and flow, a change of
# atmosphere changes V_f through the flame temperature only: V / V_air = (T_f - T_v) / (T_f,air - T_v); pressure does not
# enter this regime (lambda_g does not depend on pressure). T_v = 673 K is the "vaporization temperature" the report
# uses for thin PMMA; T_f comes from the project's equilibrium flame temperature (fif.physics.flame, Cantera with NASA
# thermodynamic data) for a hydrocarbon surrogate (n-heptane vapour entering at T_v), because NASA's data set has no
# PMMA monomer or cellulose. Label: physics theory, not measured (no NASA spread data above 21-22 % O2 in our sources).
T_V_K = 673.0
T_AMB_K = 298.15
AIR = (0.21, 1.0)  # O2 mole fraction, atm: the air of the Saffire / LUCI tests (21-22 % O2 at about 1 atm)


@functools.lru_cache(maxsize=256)
def flame_temperature_K(x_o2: float, p_atm: float) -> float:
    from .flame import adiabatic_flame_temperature

    x = np.array([x_o2, 1.0 - x_o2, 0.0, 0.0])
    return adiabatic_flame_temperature("heptane", T_V_K, x, T_AMB_K, p_atm * 101325.0)


def atmosphere_factor(x_o2: float, p_atm: float) -> float:
    """Spread-rate multiplier relative to the test air (1.0 at 21 % O2, 1 atm); 0 if the flame would be colder than T_v."""
    tf, ta = flame_temperature_K(round(x_o2, 4), round(p_atm, 4)), flame_temperature_K(*AIR)
    return max(0.0, (tf - T_V_K) / (ta - T_V_K))


def scaled(env: Environment, factor: float) -> Environment:
    """The same environment with every measured rate multiplied by ``factor``."""
    rates = {m: (a * factor, b * factor) for m, (a, b) in env.rates.items()}
    return dataclasses.replace(env, rates=rates)


# ---- well-mixed zone model of the module air (ADR-052) -----------------------------------------------------------
# Like the single-zone ("well-mixed") option of compartment fire models: in microgravity the fans mix the cabin air, so
# one uniform gas volume is a fair first picture. Only burnt FABRIC is counted:
#   * oxygen use of SIBAL fabric: NTRS 20210020516, "0.28 g ... the amount of oxygen consumed by burning: 0.24 g
#     cellulose (about 18 cm2 SIBAL fabric)" -> 0.28 g O2 per 18 cm2;
#   * heat release: NASA/TM-20210011385 (BASS-II), "the constant 13.1 kJ of heat released per gram of O2 consumed".
# Cross-check: Saffire-1 (NTRS 20170008805), 1200 W for 420 s over a 40.6 cm x 94 cm SIBAL sample = 1.32 MJ/m2, against
# 2.04 MJ/m2 from the two numbers above (same order; the Saffire sample did not burn completely).
# Cellulose C6H10O5 + 6 O2 -> 6 CO2 + 5 H2O: one mole of CO2 per mole of O2 used (water vapour is not tracked).
# The air warms by the released heat at constant volume with no loss to walls or equipment: an upper bound.
O2_G_PER_M2_FABRIC = 0.28 / 18e-4  # g O2 per m2 of SIBAL fabric burnt
KJ_PER_G_O2 = 13.1
SAFFIRE1_MJ_PER_M2 = 1200 * 420 / (0.406 * 0.94) / 1e6
R_J_MOL_K = 8.314462618
T0_K = 298.15


def _cv_air_J_per_mol_K(x_o2: float) -> float:
    import cantera as ct

    gas = ct.Solution(
        thermo="ideal-gas", species=[s for s in ct.Species.list_from_file("nasa_gas.yaml") if s.name in ("O2", "N2")]
    )
    gas.TPX = T0_K, ct.one_atm, {"O2": x_o2, "N2": 1 - x_o2}
    return gas.cv_mole / 1000.0  # J/kmol/K -> J/mol/K


def zone_history(layout: np.ndarray, times: np.ndarray, t_grid: np.ndarray, volume_m3: float, x_o2: float, p_atm: float) -> dict:
    """Cabin air over time for a well-mixed module of ``volume_m3`` (free gas volume) at (x_o2, p_atm), from the fabric
    area the flame has reached by each time of ``t_grid``. Returns arrays: burnt fabric m2, heat MJ, heat release rate
    kW (averaged over the last 60 s), O2 and CO2 mole fractions, temperature rise K (upper bound)."""
    cell_m2 = (CELL_MM / 1000) ** 2
    fab = np.sort(times[(layout == "F") & np.isfinite(times)])
    area = np.searchsorted(fab, t_grid, side="right") * cell_m2
    o2_g = area * O2_G_PER_M2_FABRIC
    heat_J = o2_g * KJ_PER_G_O2 * 1000
    n_gas = p_atm * 101325.0 * volume_m3 / (R_J_MOL_K * T0_K)  # mol of cabin gas
    n_o2_used = o2_g / 31.998
    x_o2_t = np.maximum(0.0, (x_o2 * n_gas - n_o2_used) / n_gas)
    x_co2_t = n_o2_used / n_gas
    dT = heat_J / (n_gas * _cv_air_J_per_mol_K(x_o2))
    # fire power averaged over the last minute: the burnt area grows in 10 cm steps, so a point derivative would spike
    window = 60.0
    heat_before = np.interp(t_grid - window, t_grid, heat_J, left=0.0)
    hrr_kW = (heat_J - heat_before) / window / 1000
    return {"area_m2": area, "heat_MJ": heat_J / 1e6, "hrr_kW": hrr_kW, "x_o2": x_o2_t, "x_co2": x_co2_t, "dT_K": dT}


# ---- check of the oxygen balance against NASA data (ADR-053) ----------------------------------------------------
# The zone model turns oxygen used into CO2 formed by stoichiometry (cellulose 1 mol CO2 per mol O2; PMMA,
# C5H8O2 + 6 O2 -> 5 CO2 + 4 H2O, 5/6). BASS-II (PSI-25 Experimental Table) measured O2, CO2 and CO before and after
# each burn in the Microgravity Science Glovebox; almost all of its samples are PMMA. Tests with an O2 drop too small to
# read (the table gives O2 to 0.1 %) or with O2 rising are left out and counted.
PMMA_CO2_PER_O2 = 5 / 6
CELLULOSE_CO2_PER_O2 = 1.0


def bass2_co2_per_o2(min_drop_pct: float = 0.3) -> dict:
    """Measured CO2 formed per O2 used in BASS-II. Returns the per-test table, the median ratio, the least-squares slope
    through the origin, the same with CO added (carbon in CO), and how many rows were used / left out."""
    import pandas as pd

    from fif.data.catalog import REPO_ROOT

    b = pd.read_csv(REPO_ROOT / "data" / "raw" / "psi_tables" / "PSI-25_Experimental table_BASS-II.csv", encoding="cp1252")
    b.columns = [str(x).strip().lstrip("﻿").lstrip("ï»¿") for x in b.columns]

    def num(c: str) -> pd.Series:
        return pd.to_numeric(b[c], errors="coerce")

    d = pd.DataFrame(
        {
            "material": b["Fuel Sample Material"].astype(str).str.strip(),
            "o2_used_pct": num("Calibrated  initial O2 % by vol") - num("Calibrated final O2 % by vol"),
            "co2_formed_pct": num("Final CO2 % by vol") - num("Initial CO2 % by vol"),
            "co_formed_pct": (num("Final CO (ppm)") - num("Initial CO (ppm)")) / 1e4,
        }
    )
    ok = d["o2_used_pct"].notna() & d["co2_formed_pct"].notna() & (d["o2_used_pct"] >= min_drop_pct) & (d["o2_used_pct"] < 5)
    u = d[ok].copy()
    u["ratio"] = u["co2_formed_pct"] / u["o2_used_pct"]
    x, y = u["o2_used_pct"].to_numpy(), u["co2_formed_pct"].to_numpy()
    yc = y + u["co_formed_pct"].fillna(0).to_numpy()
    return {
        "table": u,
        "n_used": int(ok.sum()),
        "n_left_out": int((~ok).sum()),
        "median": float(u["ratio"].median()),
        "slope": float((x * y).sum() / (x * x).sum()),
        "slope_with_co": float((x * yc).sum() / (x * x).sum()),
    }


# ---- detection and suppression placement (ADR-057): design aids on the measured spread rates ---------------------
# No NASA data say where detectors should go. The sketch uses the same measured rates: a detector "sees" a fire when
# the flame reaches material within its coverage radius (a conservative proxy - real smoke and gas detectors can react
# earlier); the radius is a design input. Suppression points (portable extinguisher or fire port) are placed to reach
# first the material from which a fire gets to the hatch soonest - the crew's way out. Evidence: model (design aid).
def time_to_cells(layout: np.ndarray, env: Environment, seeds: np.ndarray) -> np.ndarray:
    """For every cell: the time (s) a fire that starts there needs to reach any flammable cell of ``seeds`` (bool mask);
    inf = never. Reverse Dijkstra with the same rates and steps as ``arrival_times``."""
    h, w = layout.shape
    t = np.full((h, w), math.inf)
    heap = [(0.0, int(r), int(c)) for r, c in zip(*np.where(seeds & np.isin(layout, FLAMMABLE)), strict=True)]
    for _, r, c in heap:
        t[r, c] = 0.0
    heapq.heapify(heap)
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    while heap:
        tv, r, c = heapq.heappop(heap)
        if tv > t[r, c]:
            continue
        for dr, dc in steps:
            ur, uc = r - dr, c - dc
            if not (0 <= ur < h and 0 <= uc < w) or layout[ur, uc] not in FLAMMABLE:
                continue
            v = _rate(env, layout[r, c], dc, dr)
            if v <= 0:
                continue
            tu = tv + CELL_MM * math.hypot(dr, dc) / v
            if tu < t[ur, uc]:
                t[ur, uc] = tu
                heapq.heappush(heap, (tu, ur, uc))
    return t


def disc(shape: tuple[int, int], r: int, c: int, radius_cells: float) -> np.ndarray:
    """Cells whose centres lie within ``radius_cells`` of cell (r, c)."""
    rr, cc = np.indices(shape)
    return (rr - r) ** 2 + (cc - c) ** 2 <= radius_cells**2 + 1e-9


def candidates(layout: np.ndarray, step: int = 2) -> list[tuple[int, int]]:
    """Mounting positions on a ``step``-cell lattice inside the wall frame (any material: detectors sit on racks too)."""
    h, w = layout.shape
    return [(r, c) for r in range(1, h - 1, step) for c in range(1, w - 1, step) if layout[r, c] != "H"]


def place_detectors(layout: np.ndarray, env: Environment, n: int, radius_cells: float = 5, step: int = 2) -> dict:
    """Greedy placement of ``n`` detectors that minimises the mean time to detect a fire starting on any flammable cell.
    A fire never reaching any coverage zone counts as undetected (penalty: the longest finite time + 10 min).
    Returns positions, the per-cell detection time (s, inf = never) and summary numbers."""
    fl = np.isin(layout, FLAMMABLE)
    if not fl.any() or n <= 0:
        return {
            "cells": [],
            "time": np.full(layout.shape, math.inf),
            "mean_s": math.inf,
            "worst_s": math.inf,
            "share_1min": 0.0,
            "share_detected": 0.0,
        }
    cand = candidates(layout, step)
    taus = np.array([time_to_cells(layout, env, disc(layout.shape, r, c, radius_cells))[fl] for r, c in cand])
    finite = taus[np.isfinite(taus)]
    penalty = (float(finite.max()) if finite.size else 0.0) + 600.0
    capped = np.where(np.isfinite(taus), taus, penalty)
    chosen: list[int] = []
    best = np.full(fl.sum(), penalty)
    share_by_n = []  # greedy is nested: the first k of n detectors are the k-detector answer
    for _ in range(min(n, len(cand))):
        scores = np.minimum(capped, best).mean(axis=1)
        if chosen:
            scores[chosen] = np.inf
        k = int(np.argmin(scores))
        chosen.append(k)
        best = np.minimum(best, capped[k])
        share_by_n.append(float((best <= 60).mean()))
    det = np.full(layout.shape, math.inf)
    raw = np.min(taus[chosen], axis=0)
    det[fl] = raw
    ok = np.isfinite(raw)
    return {
        "cells": [cand[k] for k in chosen],
        "time": det,
        "mean_s": float(raw[ok].mean()) if ok.any() else math.inf,
        "worst_s": float(raw[ok].max()) if ok.any() else math.inf,
        "share_1min": float((raw <= 60).mean()),
        "share_detected": float(ok.mean()),
        "share_1min_by_n": share_by_n,
    }


def detectors_needed(
    layout: np.ndarray, env: Environment, share: float = 0.9, radius_cells: float = 5, n_max: int = 8
) -> int | None:
    """Smallest number of greedily placed detectors that see ``share`` of the fires within 1 min; None if ``n_max`` do not."""
    res = place_detectors(layout, env, n_max, radius_cells)
    return next((i + 1 for i, v in enumerate(res.get("share_1min_by_n", [])) if v >= share), None)


def place_suppression(layout: np.ndarray, env: Environment, n: int, reach_cells: float = 10, step: int = 2) -> dict:
    """Greedy placement of ``n`` suppression points (reach ``reach_cells``) covering first the material from which a fire
    reaches the hatch soonest: weight of a cell = 1 / (1 + time to the hatch in minutes); cells that never reach the
    hatch weigh 0. Returns positions and the covered share of that weight ("hatch-critical material")."""
    th = time_to_hatch(layout, env)
    wgt = np.where(np.isfinite(th), 1.0 / (1.0 + th / 60.0), 0.0)
    total = float(wgt.sum())
    if total == 0 or n <= 0:
        return {"cells": [], "covered_share": 0.0, "weight": wgt}
    cand = candidates(layout, step)
    masks = np.array([disc(layout.shape, r, c, reach_cells).ravel() for r, c in cand])
    covered = np.zeros(layout.size, dtype=bool)
    chosen: list[int] = []
    w = wgt.ravel()
    for _ in range(min(n, len(cand))):
        gain = (masks & ~covered) @ w
        if chosen:
            gain[chosen] = -1
        k = int(np.argmax(gain))
        if gain[k] <= 0:
            break
        chosen.append(k)
        covered |= masks[k]
    return {"cells": [cand[k] for k in chosen], "covered_share": float(w[covered].sum() / total), "weight": wgt}


def gas_alarm_time(t_grid: np.ndarray, x_co2: np.ndarray, rise: float) -> float:
    """First time (s) the well-mixed CO2 mole fraction has risen by ``rise`` (e.g. 0.001 = 0.1 %-points); inf if never."""
    hit = np.nonzero(x_co2 >= rise)[0]
    return float(t_grid[hit[0]]) if hit.size else math.inf


# ---- module and base geometry (ADR-057): design inputs, no dimensions from our sources -------------------------
WALL_SECTION_M2 = 4.0 * 2.0  # the drawn wall: 40 x 20 cells of 10 cm


def module_geometry(length_m: float, diameter_m: float, outfitting: float) -> dict:
    """Cylindrical module: total and free gas volume (m3; ``outfitting`` = share of the volume taken by racks and
    equipment), interior lateral wall area (m2) and how many 4 m x 2 m wall sections it holds."""
    vol = math.pi * diameter_m**2 / 4 * length_m
    wall = math.pi * diameter_m * length_m
    return {
        "volume_m3": vol,
        "free_volume_m3": vol * (1 - outfitting),
        "wall_m2": wall,
        "sections": wall / WALL_SECTION_M2,
        "floor_m2": length_m * diameter_m,
    }
