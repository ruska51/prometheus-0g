"""Fire-safety insight functions (stage 7). Each function computes its numbers live from the processed data,
the saved models or the physics layer, and returns an Insight. History / spinoff entries quote the official
challenge resources R2-R7 (quotes <= 15 words, docs/RESEARCH_LOG.md) and carry no computed numbers.

Effect sizes from data use one multiple regression on pre-ignition conditions with a bootstrap over test
regimes (cv_group), so that the O2, diluent, pressure and size effects are not confounded:
    ln K = b0 + b1 fuel_methanol + b2 x_O2 + b3 ln p + b4 x_CO2 + b5 x_He + b6 ln d0      (FLEX, ADR-030 rows)
"""

from __future__ import annotations

import functools

import joblib
import numpy as np
import pandas as pd

from fif.data.catalog import REPO_ROOT
from fif.models.features import K_TRAIN_EXCLUDE, conditions_table
from fif.models.train import _aux
from fif.physics.droplet import G_MOON_RATIO, buoyancy_factor, evaluate
from fif.validation.reliability import reliability

from .base import Insight

SEED = 20261114
N_BOOT = 1000
REG_FEATURES = ["fuel_methanol", "x_o2", "ln_p", "x_co2", "x_he", "ln_d0"]
ISS_AIR = {"x_o2": 0.21, "p_atm": 1.0}  # NASA/TP-2015-216046 Table I: FLEX "cabin air", 0.21 O2, 1.0 atm
MOON = {"x_o2": 0.30, "p_atm": 10.2 / 14.696}  # challenge page: "30% or greater", "10.2 psi or less"
SUIT = {"x_o2": 1.0, "p_atm": 4.3 / 14.696}  # challenge page: spacesuit "100% oxygen to only 4.3 psi"
SRC_FLEX = "NASA PSI-69 FLEX Experimental Table (https://psi.nasa.gov), NASA/TP-2015-216046"
SRC_CH = "Challenge page 'Flame in Freefall' (docs/challenge/CHALLENGE.md)"
FUEL_RU = {"Methanol": "метанол", "Heptane": "гептан"}
STATUS_RU = {"in range": "в пределах данных", "extrapolation": "экстраполяция", "unreliable": "ненадёжно"}


@functools.lru_cache(maxsize=1)
def _flex() -> pd.DataFrame:
    f = pd.read_csv(REPO_ROOT / "data" / "processed" / "flex.csv")
    f = f[f["use_in_model"]].copy()
    f["ln_p"] = np.log(f["p_atm"])
    f["ln_d0"] = np.log(f["d0_m"] * 1e3)
    return f


def _boot_ols(df: pd.DataFrame, y: str, feats: list[str] = REG_FEATURES) -> tuple[dict, dict]:
    """OLS coefficients and bootstrap (resampling whole regimes) percentile 95 % intervals."""
    d = df.dropna(subset=[y] + feats)
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in feats])
    Y = d[y].to_numpy(float)
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    groups = d["cv_group"].to_numpy()
    ug = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in ug}
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(N_BOOT):
        rows = np.concatenate([idx[g] for g in rng.choice(ug, len(ug), replace=True)])
        boots.append(np.linalg.lstsq(X[rows], Y[rows], rcond=None)[0])
    boots = np.array(boots)
    names = ["const"] + list(feats)
    return dict(zip(names, beta)), {n: boots[:, i] for i, n in enumerate(names)}, len(d)


@functools.lru_cache(maxsize=1)
def k_regression() -> tuple[dict, dict]:
    f = _flex()
    f = f[~f["flex_identifier"].isin(K_TRAIN_EXCLUDE)].copy()
    f["ln_K"] = np.log(f["K_m2_s"])
    return _boot_ols(f, "ln_K")


@functools.lru_cache(maxsize=1)
def dext_regression() -> tuple[dict, dict]:
    f = _flex().copy()
    f["ln_dext"] = np.log(f["d_ext_over_d0"])
    return _boot_ols(f, "ln_dext")


def _ratio(coef: dict, boots: dict, name: str, delta: float) -> tuple[float, list[float]]:
    """exp(beta * delta) with bootstrap 95 % interval."""
    v = float(np.exp(coef[name] * delta))
    lo, hi = np.exp(np.percentile(boots[name] * delta, [2.5, 97.5]))
    return v, [float(lo), float(hi)], float(coef[name] * delta)


def _pct(r: float) -> str:
    return f"{(r - 1) * 100:+.0f} %"


def _conf(ci: list[float] | None, n: int, extrap: bool = False) -> str:
    sig = ci is not None and (ci[0] > 1 or ci[1] < 1)
    if extrap:
        return "low"
    return "high" if sig and n >= 30 else ("medium" if sig else "low")


# ------------------------------------------------------------------------------------------- prevention


def p1_oxygen_speeds_burning() -> Insight:
    coef, boots, n = k_regression()
    r, ci, le = _ratio(coef, boots, "x_o2", 0.09)
    ru = dict(
        title="Больше кислорода - топливо сгорает быстрее",
        finding=f"Повышение O2 с 21 % до 30 % (прочие условия те же) меняет скорость горения капли на {_pct(r)} "
        f"(95 % ДИ от {_pct(ci[0])} до {_pct(ci[1])}), по {n} тестам FLEX на МКС.",
        action="Считайте каждый лишний процент O2 в модуле ростом пожарной опасности; ужесточайте отбор материалов и контроль "
        "источников зажигания, когда O2 выше, чем в воздухе на уровне моря.",
    )
    return Insight(
        "P1",
        "prevention",
        "More oxygen burns fuel faster",
        f"Raising O2 from 21 % to 30 % (other conditions fixed) changes the droplet burning rate by {_pct(r)} "
        f"(95 % CI {_pct(ci[0])} to {_pct(ci[1])}), from {n} FLEX tests on the ISS.",
        "Treat every percent of extra O2 in a habitat as a fire-hazard increase; tighten material screening and ignition-source "
        "control when O2 is raised above sea-level air.",
        "NASA data",
        n,
        {"name": "K ratio, O2 0.21 -> 0.30", "value": r, "ci": ci, "unit": "-", "log_effect": le},
        [SRC_FLEX, "Regression with regime bootstrap: src/fif/insights/catalog.py"],
        _conf(ci, n),
        related=["H1"],
        ru=ru,
    )


def p2_moon_base_vs_iss() -> Insight:
    m = joblib.load(REPO_ROOT / "models" / "K_hybrid.joblib")
    rows, txt, lab = [], [], []
    for fuel in ("Methanol", "Heptane"):
        c = conditions_table(fuel, [ISS_AIR["p_atm"], MOON["p_atm"]], [ISS_AIR["x_o2"], MOON["x_o2"]], d0_mm=3.0)
        mu, sd = m["model"].predict(c[m["features"]].to_numpy(), aux=_aux(c))
        ratio = float(np.exp(mu[1] - mu[0]))
        lo, hi = np.exp((mu[1] - mu[0]) + np.array([-1.96, 1.96]) * np.hypot(sd[0], sd[1]))
        rel = reliability(fuel, MOON["p_atm"], MOON["x_o2"], 0, 0, 3.0, sigma_log=float(sd[1]))
        rows.append((fuel, ratio, lo, hi))
        lab.append(rel["status"])
        txt.append(f"{fuel.lower()} {_pct(ratio)} (95 % band {_pct(lo)} to {_pct(hi)})")
    worst = max(rows, key=lambda r: r[1])
    ru = dict(
        title="Атмосфера лунной базы ускоряет горение капель по сравнению с воздухом МКС",
        finding="Гибридная модель, капля 3 мм: атмосфера лунной базы (O2 30 %, 10.2 psi) против воздуха кабины МКС "
        "(O2 21 %, 1 атм): "
        + "; ".join(f"{FUEL_RU[f]} {_pct(q)} (95 % полоса от {_pct(a)} до {_pct(b)})" for f, q, a, b in rows)
        + f". Статус: {', '.join(STATUS_RU[x] for x in sorted(set(lab)))} (O2 30 % испытан только начиная с 0.703 атм).",
        action="Рассчитывайте обнаружение пожара и мощность тушения в модулях лунной базы и луноходах на более быстрое "
        "выгорание топлива, чем на МКС; повторно испытайте материалы кабины в планируемой атмосфере.",
    )
    return Insight(
        "P2",
        "prevention",
        "A Moon-base atmosphere burns droplets faster than ISS air",
        f"Hybrid model, 3 mm droplet: Moon-base atmosphere (O2 30 %, 10.2 psi) vs ISS cabin air (O2 21 %, 1 atm): "
        f"{'; '.join(txt)}. Label: {', '.join(sorted(set(lab)))} (O2 30 % was tested only from 0.703 atm).",
        "Size fire-detection response and suppression capacity of Moon-base modules and rovers for faster fuel consumption than "
        "on the ISS; re-test cabin materials at the planned atmosphere.",
        "model",
        int(len(_flex())),
        {
            "name": f"K ratio Moon/ISS ({worst[0].lower()})",
            "value": worst[1],
            "ci": [float(worst[2]), float(worst[3])],
            "unit": "-",
            "log_effect": float(np.log(worst[1])),
        },
        [SRC_CH + " (Moon-base atmosphere)", "NASA/TP-2015-216046 Table I (ISS cabin air)", "models/K_hybrid.joblib"],
        "low" if "extrapolation" in lab or "unreliable" in lab else "medium",
        extrapolation="in range" not in lab,
        related=["H1", "H2"],
        ru=ru,
    )


def p3_low_pressure_does_not_help() -> Insight:
    coef, boots, n = k_regression()
    r, ci, le = _ratio(coef, boots, "ln_p", float(np.log(0.7)))
    ru = dict(
        title="Снижение давления в кабине почти не замедляет горение",
        finding=f"Переход с 1.0 на 0.7 атм при той же доле O2 меняет скорость горения на {_pct(r)} "
        f"(95 % ДИ от {_pct(ci[0])} до {_pct(ci[1])}; {n} тестов FLEX).",
        action="Не рассчитывайте, что пониженное давление в модуле компенсирует добавочную опасность повышенной доли O2.",
    )
    return Insight(
        "P3",
        "prevention",
        "Lowering cabin pressure barely slows burning",
        f"Going from 1.0 to 0.7 atm at the same O2 fraction changes the burning rate by {_pct(r)} "
        f"(95 % CI {_pct(ci[0])} to {_pct(ci[1])}; {n} FLEX tests).",
        "Do not count on reduced habitat pressure to offset the added hazard of a higher O2 fraction.",
        "NASA data",
        n,
        {"name": "K ratio, 1.0 -> 0.7 atm", "value": r, "ci": ci, "unit": "-", "log_effect": le},
        [SRC_FLEX],
        _conf(ci, n),
        related=["P2"],
        ru=ru,
    )


def p4_gas_flames_ignite_at_high_o2() -> Insight:
    c = pd.read_csv(REPO_ROOT / "data" / "processed" / "cfig.csv")
    inv = c[(c["table"] == "inverse") & c["ignited"].notna()]
    hi = inv[inv["x_o2_oxidizer"] >= 0.5]
    lo = inv[inv["x_o2_oxidizer"] < 0.3]
    p_hi, p_lo = hi["ignited"].mean(), lo["ignited"].mean()
    ru = dict(
        title="В потоках, богатых O2, газообразное топливо поджигается почти всегда",
        finding=f"Обращённые пламёна ACME CFI-G на МКС: воспламенение в {p_hi * 100:.0f} % из {len(hi)} попыток при O2 в "
        f"окислителе не ниже 50 % (до {inv['x_o2_oxidizer'].max() * 100:.0f} %) против {p_lo * 100:.0f} % из {len(lo)} "
        "попыток ниже 30 %.",
        action="Считайте кислородные магистрали, редукторы и выходы генераторов O2 главными зонами риска воспламенения "
        "(держите углеводороды и источники электрического нагрева подальше от них).",
    )
    return Insight(
        "P4",
        "prevention",
        "In O2-rich streams gaseous fuels ignite almost every time",
        f"ACME CFI-G inverse flames on the ISS: ignition in {p_hi * 100:.0f} % of {len(hi)} attempts with oxidizer O2 >= 50 % "
        f"(up to {inv['x_o2_oxidizer'].max() * 100:.0f} %), vs {p_lo * 100:.0f} % of {len(lo)} attempts below 30 %.",
        "Treat O2 lines, regulators and O2-generator outlets as top-priority ignition hazards (keep hydrocarbons and "
        "electrical heat sources away from them).",
        "NASA data",
        int(len(hi) + len(lo)),
        {
            "name": "ignition share O2>=0.5 vs <0.3",
            "value": float(p_hi / p_lo) if p_lo else float("nan"),
            "ci": None,
            "unit": "-",
            "log_effect": float(np.log(p_hi / p_lo)) if p_lo and p_hi else None,
        },
        ["NASA PSI-159 ACME CFI-G Experimental Tables (https://psi.nasa.gov)"],
        "medium",
        related=["H2", "H3"],
        ru=ru,
    )


# ------------------------------------------------------------------------------------------- detection


def d1_co_from_burning_solids() -> Insight:
    b = pd.read_csv(REPO_ROOT / "data" / "raw" / "psi_tables" / "PSI-25_Experimental table_BASS-II.csv", encoding="cp1252")
    b.columns = [str(x).strip().lstrip("﻿").lstrip("ï»¿") for x in b.columns]

    def num(s: pd.Series) -> pd.Series:
        return pd.to_numeric(s, errors="coerce")

    co0, co1 = num(b["Initial CO (ppm)"]), num(b["Final CO (ppm)"])
    o0, o1 = num(b["Calibrated  initial O2 % by vol"]), num(b["Calibrated final O2 % by vol"])
    ok = co0.notna() & co1.notna() & o0.notna() & o1.notna() & (o1 <= o0 + 0.5)  # drop rows with O2 rising (anomaly)
    dco = (co1 - co0)[ok]
    ru = dict(
        title="Горящие твёрдые материалы выделяют CO - контролируйте газы, а не только дым",
        finding=f"В {int(ok.sum())} тестах BASS-II (небольшие твёрдые образцы в перчаточном боксе МКС) CO вырос по медиане на "
        f"{dco.median():.0f} ppm, 90-й перцентиль {dco.quantile(0.9):.0f} ppm, максимум {dco.max():.0f} ppm за тест.",
        action="Дополняйте дымовые извещатели датчиками CO (и CO2) в обитаемых объёмах: экипаж Apollo 1 погиб от токсичных "
        "газов, а не от жара.",
    )
    return Insight(
        "D1",
        "detection",
        "Burning solids release CO - detect gases, not only smoke",
        f"In {int(ok.sum())} BASS-II tests (small solid samples in the ISS glovebox) CO rose by a median "
        f"{dco.median():.0f} ppm, 90th percentile {dco.quantile(0.9):.0f} ppm, maximum {dco.max():.0f} ppm per test.",
        "Pair smoke detection with CO (and CO2) sensing in crew volumes; toxic gas, not heat, killed the Apollo 1 crew.",
        "NASA data",
        int(ok.sum()),
        {
            "name": "median CO rise per test",
            "value": float(dco.median()),
            "ci": None,
            "unit": "ppm",
            "log_effect": float(np.log((co1[ok].median() + 1) / (co0[ok].median() + 1))),
        },
        ["NASA PSI-25 BASS-II Experimental Table (https://psi.nasa.gov)"],
        "medium",
        related=["H1", "H3"],
        ru=ru,
    )


def d2_cool_flames() -> Insight:
    c = pd.read_csv(REPO_ROOT / "data" / "processed" / "cfig.csv")
    norm = c[c["table"] == "normal"]
    yes = norm["cool_flame"].fillna("").str.lower().str.startswith("yes") | norm["comments"].fillna("").str.contains("ool flame")
    ru = dict(
        title="Холодные пламёна: топливо может реагировать и после погасания видимого пламени",
        finding=f"Холодные пламёна зафиксированы в {int(yes.sum())} из {len(norm)} тестов ACME CFI-G с нормальным пламенем; "
        "в заметках к тестам FLEX описано холодное горение капель гептана после погасания видимого пламени "
        "(NASA/TP-2015-216046).",
        action="Не объявляйте пожар потушенным только по оптическим признакам (видимое или УФ-пламя); подтверждайте газовыми "
        "датчиками и температурой.",
    )
    return Insight(
        "D2",
        "detection",
        "Cool flames: fuel can keep reacting after the visible flame is gone",
        f"Cool flames were recorded in {int(yes.sum())} of {len(norm)} ACME CFI-G normal-flame tests; FLEX test notes "
        "report cool-flame burning after visible-flame extinction of heptane droplets (NASA/TP-2015-216046).",
        "Do not declare a fire out on optical (visible/UV flame) evidence alone; confirm with gas sensing and temperature.",
        "NASA data",
        int(yes.sum()),
        {"name": "cool-flame observations", "value": int(yes.sum()), "ci": None, "unit": "tests", "log_effect": None},
        ["NASA PSI-159 ACME CFI-G (https://psi.nasa.gov)", "NASA/TP-2015-216046 test notes"],
        "medium",
        related=["H3"],
        ru=ru,
    )


def d3_smoke_detection_data() -> Insight:
    s = pd.read_csv(REPO_ROOT / "data" / "raw" / "psi_tables" / "PSI-101_Experimental table_SAME-R.csv", encoding="cp1252")
    s.columns = [str(x).strip() for x in s.columns]
    col = [x for x in s.columns if "Sample Type" in x][0]
    mats = sorted(s[col].dropna().astype(str).str.strip().unique())
    ru = dict(
        title="Дым от материалов космических аппаратов измерен в невесомости",
        finding=f"SAME-R провёл на МКС {len(s.dropna(how='all'))} дымовых тестов с {len(mats)} материалами "
        f"({', '.join(mats)}) - это база для дымовых извещателей, настроенных на дым в невесомости.",
        action="При выборе извещателей для новых кораблей опирайтесь на данные SAME/SAME-R о частицах, а не на земные стандарты.",
    )
    return Insight(
        "D3",
        "detection",
        "Smoke from spacecraft materials has been measured in microgravity",
        f"SAME-R ran {len(s.dropna(how='all'))} smoke tests on the ISS with {len(mats)} materials ({', '.join(mats)}) - "
        "the data base for smoke detectors tuned to microgravity smoke.",
        "Use SAME/SAME-R particle data when specifying detectors for new spacecraft rather than terrestrial detector standards.",
        "NASA data",
        int(len(s.dropna(how="all"))),
        {"name": "materials tested", "value": len(mats), "ci": None, "unit": "-", "log_effect": None},
        ["NASA PSI-101 SAME-R Experimental Table (https://psi.nasa.gov)"],
        "medium",
        related=["E2"],
        ru=ru,
    )


def d4_microgravity_vs_earth() -> Insight:
    x = np.array([[0.21, 0.79, 0.0, 0.0]] * 2)
    r = evaluate(np.array(["methanol", "heptane"]), np.full(2, 101325.0), x, d0_m=np.full(2, 3e-3))
    fac = (1 + r["f_B"]).to_numpy()
    ru = dict(
        title="Без плавучести та же капля горит медленнее, чем на Земле",
        finding=f"Поправка Law & Williams на плавучесть для капли 3 мм в воздухе при 1 атм: на Земле скорость горения в "
        f"{fac[0]:.1f} раза (метанол) и в {fac[1]:.1f} раза (гептан) выше, чем в невесомости (корреляция применена далеко за "
        f"пределами диапазона подгонки, Gr = {r['Gr'].iloc[0]:.0f}).",
        action="Не переносите земные результаты по горючести и времени обнаружения на корабли без данных невесомости: пламя в "
        "невесомости меньше и медленнее, его могут обнаружить позже.",
    )
    return Insight(
        "D4",
        "detection",
        "Without buoyancy the same droplet burns slower than on Earth",
        f"Law & Williams buoyancy correction for a 3 mm droplet in air at 1 atm: Earth burning rate is "
        f"{fac[0]:.1f}x (methanol) and {fac[1]:.1f}x (heptane) the microgravity rate (correlation used far outside its "
        f"fitted range, Gr = {r['Gr'].iloc[0]:.0f}).",
        "Do not transfer Earth flammability or detection-time results to spacecraft without microgravity data; "
        "microgravity flames are smaller and slower, so they may be detected later.",
        "physics theory",
        0,
        {"name": "K_Earth/K_ISS (heptane)", "value": float(fac[1]), "ci": None, "unit": "-", "log_effect": float(np.log(fac[1]))},
        ["Law & Williams, Combust. Flame 19 (1972) Eq. (9); docs/PHYSICS.md section 4"],
        "low",
        extrapolation=True,
        ru=ru,
    )


def p5_lunar_surface_bound() -> Insight:
    x = np.array([[MOON["x_o2"], 1 - MOON["x_o2"], 0.0, 0.0]] * 2)
    r = evaluate(np.array(["methanol", "heptane"]), np.full(2, MOON["p_atm"] * 101325.0), x, d0_m=np.full(2, 3e-3))
    fac = buoyancy_factor(r["Gr"].to_numpy(), G_MOON_RATIO)
    gr = r["Gr"].to_numpy() * G_MOON_RATIO
    ru = dict(
        title="На поверхности Луны капля горит со скоростью между МКС и Землёй",
        finding=f"Воздух лунной базы (O2 0.30, 10.2 psi), капля 3 мм при 1/6 g: скорость горения лежит между скоростью в "
        f"невесомости и {fac[0]:.2f}x (метанол) / {fac[1]:.2f}x (гептан) от неё (поправка Law & Williams на плавучесть, "
        f"Gr = {gr[0]:.2f} / {gr[1]:.2f}, внутри диапазона подгонки Gr <= 1). Нижняя граница - невесомость; данных при "
        "частичной гравитации в PSI нет.",
        action="Рассчитывайте противопожарную защиту лунной базы на скорость горения вплоть до верхней границы, а время "
        "выгорания по данным МКС считайте медленным пределом.",
    )
    return Insight(
        "P5",
        "prevention",
        "On the lunar surface a droplet burns between its ISS and Earth rates",
        f"Moon-base air (O2 0.30, 10.2 psi), 3 mm droplet at 1/6 g: the burning rate lies between the microgravity rate and "
        f"{fac[0]:.2f}x (methanol) / {fac[1]:.2f}x (heptane) that rate (Law & Williams buoyancy correction, Gr = "
        f"{gr[0]:.2f} / {gr[1]:.2f}, inside its fitted range Gr <= 1). Lower bound = microgravity; no partial-gravity data in PSI.",
        "Size Moon-base fire response for a burning rate up to the upper bound, and treat ISS-derived burn times as the slow limit.",
        "physics theory",
        0,
        {
            "name": "K(1/6 g)/K(0 g) upper bound (heptane)",
            "value": float(fac[1]),
            "ci": None,
            "unit": "-",
            "log_effect": float(np.log(fac[1])),
        },
        [
            "Law & Williams, Combust. Flame 19 (1972) Eq. (9); docs/PHYSICS.md section 4",
            "NTRS 20250004015 (lunar gravity = 1/6 of Earth gravity)",
        ],
        "low",
        extrapolation=True,
        related=["P2", "D4", "P6"],
        ru=ru,
    )


def p6_lunar_gravity_solids() -> Insight:
    ru = dict(
        title="NASA: для твёрдых материалов лунная гравитация может быть самым пожароопасным условием",
        finding='NASA Glenn сообщает, что для твёрдых материалов "Lunar gravity is nearly the most flammable condition" '
        "(скорость распространения пламени максимальна, а кислородный предел минимален вблизи лунной g), а пожар в модуле при "
        'частичной гравитации ожидается "substantially worse than in 0-g and potentially worse than even 1-g". '
        "Эксперимент FM2 должен измерить это на Луне.",
        action="Не считайте материал, прошедший отбор при 1 g, безопасным для лунной базы; закладывайте запас, пока нет "
        "лунных данных (FM2).",
    )
    return Insight(
        "P6",
        "prevention",
        "NASA: for solid materials, lunar gravity may be the most flammable condition",
        'NASA Glenn reports that "Lunar gravity is nearly the most flammable condition" for solid materials (flame spread peaks '
        'and the oxygen limit is lowest near lunar g), and a partial-g habitat fire is expected to be "substantially worse than '
        'in 0-g and potentially worse than even 1-g". The FM2 experiment is to measure this on the Moon.',
        "Do not assume a material that passes the 1-g screening test is safe in a Moon base; add margin until lunar data (FM2) exist.",
        "NASA literature",
        0,
        {"name": "-", "value": None, "ci": None, "unit": "-", "log_effect": None},
        ["NTRS 20210020516 (Fire on the Moon, NASA GRC)", "NTRS 20260000646 (Ferkul et al., LPSC 2026)"],
        "medium",
        related=["P5", "H1"],
        ru=ru,
    )


# ------------------------------------------------------------------------------------------- suppression


def s1_co2_dilution() -> Insight:
    coef, boots, n = k_regression()
    r, ci, le = _ratio(coef, boots, "x_co2", 0.30)
    ru = dict(
        title="Разбавление CO2 замедляет горение",
        finding=f"Замена 30 % азота на CO2 (при тех же O2 и давлении) меняет скорость горения на {_pct(r)} "
        f"(95 % ДИ от {_pct(ci[0])} до {_pct(ci[1])}; {n} тестов FLEX).",
        action="CO2 - эффективный разбавитель для тушения в невесомости; оставляйте его в системе пожаротушения.",
    )
    return Insight(
        "S1",
        "suppression",
        "CO2 dilution slows burning",
        f"Replacing 30 % of the nitrogen by CO2 (same O2 and pressure) changes the burning rate by {_pct(r)} "
        f"(95 % CI {_pct(ci[0])} to {_pct(ci[1])}; {n} FLEX tests).",
        "CO2 is an effective diluent suppressant in microgravity; keep it in the suppression design.",
        "NASA data",
        n,
        {"name": "K ratio, 30 % N2 -> CO2", "value": r, "ci": ci, "unit": "-", "log_effect": le},
        [SRC_FLEX],
        _conf(ci, n),
        ru=ru,
    )


def s2_helium_dilution() -> Insight:
    coef, boots, n = k_regression()
    r, ci, le = _ratio(coef, boots, "x_he", 0.30)
    ru = dict(
        title="Разбавление гелием не замедляет горение, а ускоряет его",
        finding=f"Замена 30 % азота на гелий меняет скорость горения на {_pct(r)} "
        f"(95 % ДИ от {_pct(ci[0])} до {_pct(ci[1])}; {n} тестов FLEX): гелий быстрее подводит тепло к капле.",
        action="Гелий не заменяет CO2 как огнетушащий разбавитель; учитывайте это, если гелий используется как разбавитель "
        "атмосферы кабины.",
    )
    return Insight(
        "S2",
        "suppression",
        "Helium dilution does not slow burning - it speeds it up",
        f"Replacing 30 % of the nitrogen by helium changes the burning rate by {_pct(r)} "
        f"(95 % CI {_pct(ci[0])} to {_pct(ci[1])}; {n} FLEX tests): helium conducts heat to the droplet faster.",
        "Helium is not a substitute for CO2 as a fire-suppressing diluent; account for it if He is used as a cabin diluent.",
        "NASA data",
        n,
        {"name": "K ratio, 30 % N2 -> He", "value": r, "ci": ci, "unit": "-", "log_effect": le},
        [SRC_FLEX],
        _conf(ci, n),
        ru=ru,
    )


def s3_less_oxygen_earlier_extinction() -> Insight:
    coef, boots, n = dext_regression()
    r, ci, le = _ratio(coef, boots, "x_o2", -0.06)
    ru = dict(
        title="При меньшем содержании кислорода пламя гаснет раньше",
        finding=f"Снижение O2 с 21 % до 15 % меняет размер капли в момент погасания пламени (относительно начального) на "
        f"{_pct(r)} (95 % ДИ от {_pct(ci[0])} до {_pct(ci[1])}; {n} тестов FLEX с погасанием): больше топлива остаётся "
        "несгоревшим.",
        action="Снижение O2 (сброс давления, заполнение инертным газом) - эффективный способ сократить пожар в невесомости.",
    )
    return Insight(
        "S3",
        "suppression",
        "Less oxygen makes flames go out earlier",
        f"Lowering O2 from 21 % to 15 % changes the droplet size at flame extinction (relative to the initial size) by "
        f"{_pct(r)} (95 % CI {_pct(ci[0])} to {_pct(ci[1])}; {n} FLEX tests with extinction): more fuel is left unburned.",
        "Reducing O2 (venting, inert flooding) is an effective way to shorten a microgravity fire.",
        "NASA data",
        n,
        {"name": "d_ext/d0 ratio, O2 0.21 -> 0.15", "value": r, "ci": ci, "unit": "-", "log_effect": le},
        [SRC_FLEX],
        _conf(ci, n),
        related=["H3"],
        ru=ru,
    )


def s4_high_o2_removes_self_extinction() -> Insight:
    f = _flex()
    lab = f[f["extinct_finite_d"].notna() & (f["diluent"] == "N2")]
    hi, lo = lab[lab["x_o2"] >= 0.30], lab[lab["x_o2"] <= 0.21]
    s_hi, s_lo = 1 - hi["extinct_finite_d"].mean(), 1 - lo["extinct_finite_d"].mean()
    ru = dict(
        title="При 30 % O2 пламя капли почти никогда не гаснет само",
        finding=f"Тесты FLEX с разбавлением N2: пламя выжгло каплю без погасания в {s_hi * 100:.0f} % из {len(hi)} тестов при "
        f"O2 не ниже 30 % против {s_lo * 100:.0f} % из {len(lo)} тестов при O2 не выше 21 %.",
        action="При повышенном O2 исходите из того, что пожар сам не погаснет: активное тушение нужно немедленно.",
    )
    return Insight(
        "S4",
        "suppression",
        "At 30 % O2 droplet flames rarely put themselves out",
        f"N2-diluted FLEX tests: the flame burned the droplet out without extinguishing in {s_hi * 100:.0f} % of {len(hi)} tests "
        f"at O2 >= 30 %, vs {s_lo * 100:.0f} % of {len(lo)} tests at O2 <= 21 %.",
        "At elevated O2 assume a fire will not self-extinguish; active suppression must be immediate.",
        "NASA data",
        int(len(hi) + len(lo)),
        {
            "name": "share without extinction, O2>=0.30 / O2<=0.21",
            "value": float(s_hi / s_lo) if s_lo else float("nan"),
            "ci": None,
            "unit": "-",
            "log_effect": float(np.log(s_hi / s_lo)) if s_lo and s_hi else None,
        },
        [SRC_FLEX],
        "medium",
        related=["H1"],
        ru=ru,
    )


# ------------------------------------------------------------------------------------------- history / Earth


def _history_and_earth_en() -> list[Insight]:
    z = {"name": "-", "value": None, "ci": None, "unit": "-", "log_effect": None}
    return [
        Insight(
            "H1",
            "history",
            "Apollo 1: pure oxygen turned a spark into a flash fire",
            '"Because of the pure oxygen atmosphere, the fire spread quickly"; the crew died of "asphyxia from carbon '
            'monoxide and other toxic gases" (NASA SMA).',
            "Our data show the same physics at milder O2 levels (P1, S4) and the CO hazard (D1).",
            "NASA history",
            0,
            z,
            ["https://sma.nasa.gov/sma-disciplines/accllp/apollo-1"],
            "high",
            related=["P1", "S4", "D1"],
        ),
        Insight(
            "H2",
            "history",
            "Apollo 13: oxygen system plus electrical heat",
            'Heaters in the oxygen tank overheated, "degrading the Teflon insulation"; the redesign sheathed wiring "in stainless steel" (NASA SMA).',
            "O2-rich hardware is where ignition-source control matters most (P4).",
            "NASA history",
            0,
            z,
            ["https://sma.nasa.gov/sma-disciplines/accllp/apollo-13"],
            "high",
            related=["P4", "P2"],
        ),
        Insight(
            "H3",
            "history",
            "Mir 1997: a real fire in microgravity",
            'An oxygen generator burned; "The flame blocked the evacuation route to the Soyuz spacecraft"; smoke was cleared '
            '"over several hours" (NASA History).',
            "Microgravity fires produce lasting smoke and gases (D1, D2) and can cut off escape routes: detection and immediate "
            "suppression (S3) are critical.",
            "NASA history",
            0,
            z,
            ["https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/"],
            "high",
            related=["D1", "D2", "S3"],
        ),
        Insight(
            "E1",
            "earth",
            "Lighter firefighter air tanks",
            'Developed with NASA Johnson Space Center: "20 pounds for 30 minute air supply" (NASA Spinoff, 1976).',
            "Benefit on Earth of NASA life-support work.",
            "NASA spinoff",
            0,
            z,
            ["https://spinoff.nasa.gov/node/9582"],
            "high",
        ),
        Insight(
            "E2",
            "earth",
            "Incipient fire detector from the Space Shuttle",
            'Signals fire "before appearance of flame and smoke" and is "less susceptible to false alarms" (NASA Spinoff, 1978).',
            "Space detection technology already protects mines and buildings; SAME data (D3) can do the same.",
            "NASA spinoff",
            0,
            z,
            ["https://spinoff.nasa.gov/node/9407"],
            "high",
            related=["D3"],
        ),
        Insight(
            "E3",
            "earth",
            "Fire-resistant gear from Apollo materials",
            'Project FIRES used "lightweight, fire-resistant, heat-protective materials" from space suits (NASA Spinoff, 1982).',
            "Materials screened for O2-rich cabins protect firefighters on Earth.",
            "NASA spinoff",
            0,
            z,
            ["https://spinoff.nasa.gov/node/9918"],
            "high",
        ),
    ]


DATA_INSIGHTS = [
    p1_oxygen_speeds_burning,
    p2_moon_base_vs_iss,
    p3_low_pressure_does_not_help,
    p4_gas_flames_ignite_at_high_o2,
    p5_lunar_surface_bound,
    p6_lunar_gravity_solids,
    d1_co_from_burning_solids,
    d2_cool_flames,
    d3_smoke_detection_data,
    d4_microgravity_vs_earth,
    s1_co2_dilution,
    s2_helium_dilution,
    s3_less_oxygen_earlier_extinction,
    s4_high_o2_removes_self_extinction,
]


def all_insights() -> list[Insight]:
    return [f() for f in DATA_INSIGHTS] + history_and_earth()


def cabin_atmospheres() -> pd.DataFrame:
    """ISS air, Moon base and spacesuit atmospheres: hybrid K (where applicable), theory K, reliability label."""
    m = joblib.load(REPO_ROOT / "models" / "K_hybrid.joblib")
    rows = []
    for name, a, src in (
        ("ISS cabin air", ISS_AIR, "NASA/TP-2015-216046 Table I"),
        ("Moon base / pressurized rover (planned)", MOON, SRC_CH),
        ("Spacesuit", SUIT, SRC_CH),
    ):
        for fuel in ("Methanol", "Heptane"):
            c = conditions_table(fuel, a["p_atm"], a["x_o2"], d0_mm=3.0)
            mu, sd = m["model"].predict(c[m["features"]].to_numpy(), aux=_aux(c))
            rel = reliability(fuel, a["p_atm"], a["x_o2"], 0, 0, 3.0, sigma_log=float(sd[0]))
            rows.append(
                {
                    "atmosphere": name,
                    "O2": a["x_o2"],
                    "p_atm": round(a["p_atm"], 3),
                    "p_psi": round(a["p_atm"] * 14.696, 1),
                    "fuel": fuel,
                    "K_hybrid_mm2_s": float(np.exp(mu[0]) * 1e6) if rel["status"] != "unreliable" else None,
                    "sigma_ln": float(sd[0]),
                    "K_theory_mm2_s": float(c["K_theory"].iloc[0] * 1e6),
                    "status": rel["status"],
                    "reasons": "; ".join(rel["reasons"]),
                    "source": src,
                }
            )
    return pd.DataFrame(rows)


HISTORY_RU = {
    "H1": {
        "title": "Apollo 1: чистый кислород превратил искру во вспышку пожара",
        "finding": 'Цитаты NASA SMA: "Because of the pure oxygen atmosphere, the fire spread quickly"; экипаж погиб от "asphyxia from carbon monoxide and other toxic gases".',
        "action": "Наши данные показывают ту же физику при более умеренном O2 (P1, S4) и опасность CO (D1).",
    },
    "H2": {
        "title": "Apollo 13: кислородная система плюс электрический нагрев",
        "finding": 'Нагреватели в кислородном баке перегрелись, "degrading the Teflon insulation"; после доработки проводку поместили "in stainless steel" (NASA SMA).',
        "action": "Оборудование с высоким содержанием O2 - место, где контроль источников зажигания важнее всего (P4).",
    },
    "H3": {
        "title": '"Мир", 1997: реальный пожар в невесомости',
        "finding": 'Загорелся генератор кислорода; "The flame blocked the evacuation route to the Soyuz spacecraft"; дым удаляли "over several hours" (NASA History).',
        "action": "Пожар в невесомости даёт долго не рассеивающийся дым и газы (D1, D2) и может отрезать пути эвакуации: критичны обнаружение и немедленное тушение (S3).",
    },
    "E1": {
        "title": "Облегчённые дыхательные баллоны пожарных",
        "finding": 'Разработаны вместе с Johnson Space Center NASA: "20 pounds for 30 minute air supply" (NASA Spinoff, 1976).',
        "action": "Польза на Земле от работ NASA по системам жизнеобеспечения.",
    },
    "E2": {
        "title": "Детектор пожара на ранней стадии от Space Shuttle",
        "finding": 'Сигнализирует о пожаре "before appearance of flame and smoke" и "less susceptible to false alarms" (NASA Spinoff, 1978).',
        "action": "Космическая технология обнаружения уже защищает шахты и здания; данные SAME (D3) могут сделать то же.",
    },
    "E3": {
        "title": "Огнестойкое снаряжение из материалов Apollo",
        "finding": 'Проект FIRES использовал "lightweight, fire-resistant, heat-protective materials" от скафандров (NASA Spinoff, 1982).',
        "action": "Материалы, отобранные для кабин с высоким O2, защищают пожарных на Земле.",
    },
}


def history_and_earth() -> list[Insight]:
    out = _history_and_earth_en()
    for i in out:
        i.ru = HISTORY_RU[i.id]
    return out
