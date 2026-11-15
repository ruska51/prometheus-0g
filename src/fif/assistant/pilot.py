"""AI pilot (ADR-058): turns a request in plain English or Russian into an action on the dashboard - which page to open
and which inputs to set - plus a one-line reply. A language model (Gemini, via fif.assistant.llm.gemini_generate)
proposes the action as JSON; this module validates every field against the allowed values and ranges, so the model can
only choose among real pages and real settings. Without a model (no key, quota out) a rule-based parser does the same
for the common requests. The pilot never states numbers itself: results always come from the pages.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable

PAGES = {
    "overview": "views/overview.py",
    "assistant": "views/assistant.py",
    "scenario": "views/scenario.py",
    "module": "views/module.py",
    "base": "views/base.py",
    "risk_map": "views/risk_map.py",
    "insights": "views/insights.py",
    "investigations": "views/investigations.py",
    "data_explorer": "views/data_explorer.py",
    "validation": "views/validation.py",
    "method": "views/method.py",
}
SCENARIO_PRESETS = ["ISS cabin air", "Moon base / rover (planned)", "Spacesuit", "Custom"]
FUELS = ["Methanol", "Heptane"]
DILUENTS = ["none", "CO2", "He"]
WALLS = ["crew", "lab", "stowage", "blank"]
ATMS = ["air", "moon", "sea", "custom"]
TABS = ["spread", "air", "design", "detect", "moon"]

SYSTEM = """You are the pilot of Prometheus-0g, a dashboard on NASA microgravity fire data. You do not answer science
questions yourself: you open the right page and set its inputs. Reply with ONE JSON object and nothing else:
{"say": str, "page": str|null, "scenario": {...}|null, "module": {...}|null, "question": str|null}
- "say": one short sentence in the user's language saying what you opened and set. No numbers that are not settings.
- "page": one of overview, assistant, scenario, module, base, risk_map, insights, investigations, data_explorer,
  validation, method.
  overview = headline answer; scenario = one fuel droplet in a chosen cabin atmosphere (burning rate, flame temperature,
  animation); module = a 4 m x 2 m module wall, fire spread in three gravities, module air, firebreak, detectors and
  suppression; base = a whole Moon base of modules; risk_map = burning rate over oxygen x pressure; insights = ranked
  fire-safety findings; investigations = the 24 NASA PSI investigations; data_explorer = raw NASA rows; validation =
  how accurate the model is; method = method, sources, glossary; assistant = questions about the data.
- "scenario" (only for page scenario): preset one of "ISS cabin air", "Moon base / rover (planned)",
  "Spacesuit" (100 % O2, 4.3 psi), "Custom"; fuel "Methanol"|"Heptane"; o2 (mole fraction 0.10-1.00, needs preset Custom);
  psi (3-45, needs Custom); dil "none"|"CO2"|"He"; xdil (0-0.7); d0 (droplet diameter mm, 1-5).
- "module" (only for page module): wall "crew"|"lab"|"stowage"|"blank"; atm "air"|"moon"|"sea"|"custom"
  (air = ISS/test air 21 % O2 14.7 psi, moon = Moon base 30 % O2 10.2 psi, sea = 34 % O2 8.2 psi); o2 (percent 17-40,
  needs atm custom); psi (5-15, needs custom); vent 1 (towards the hatch) | -1; tab "spread"|"air"|"design"|"detect"|"moon"
  (design = firebreak, detect = detectors and suppression, moon = lunar-gravity facts and checklist).
- "question": if the user asks a factual question about fires, data or NASA results, copy it here and set page
  "assistant" - the data assistant will answer it with sources.
Leave out anything the user did not ask for."""


def _num(v, lo: float, hi: float) -> float | None:
    try:
        x = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return min(max(x, lo), hi)


def validate(raw: dict) -> dict:
    """Keep only allowed pages and settings; convert settings into the query parameters the pages read."""
    out: dict = {"say": str(raw.get("say") or "").strip()[:300], "page": None, "params": {}, "question": None}
    page = raw.get("page")
    if page in PAGES:
        out["page"] = page
    q = raw.get("question")
    if isinstance(q, str) and q.strip():
        out["question"] = q.strip()[:600]
        out["page"] = "assistant"
        out["params"] = {"q": out["question"]}
        return out
    if out["page"] == "scenario" and isinstance(raw.get("scenario"), dict):
        s, p = raw["scenario"], {}
        if s.get("preset") in SCENARIO_PRESETS:
            p["preset"] = s["preset"]
        if s.get("fuel") in FUELS:
            p["fuel"] = s["fuel"]
        if s.get("dil") in DILUENTS:
            p["dil"] = s["dil"]
        for k, lo, hi, fmt in (
            ("o2", 0.10, 1.0, "{:.2f}"),
            ("psi", 3.0, 45.0, "{:.1f}"),
            ("xdil", 0.0, 0.7, "{:.2f}"),
            ("d0", 1.0, 5.0, "{:.1f}"),
        ):
            v = _num(s.get(k), lo, hi) if s.get(k) is not None else None
            if v is not None:
                p[k] = fmt.format(v)
        if ("o2" in p or "psi" in p) and "preset" not in p:
            p["preset"] = "Custom"
        out["params"] = p
    if out["page"] == "module" and isinstance(raw.get("module"), dict):
        m, p = raw["module"], {}
        if m.get("wall") in WALLS:
            p["wall"] = m["wall"]
        if m.get("atm") in ATMS:
            p["atm"] = m["atm"]
        o2, psi = _num(m.get("o2"), 17, 40), _num(m.get("psi"), 5, 15)
        if m.get("o2") is not None and o2 is not None:
            p["o2"], p["atm"] = str(round(o2)), "custom"
        if m.get("psi") is not None and psi is not None:
            p["psi"], p["atm"] = f"{psi:.1f}", "custom"
        if str(m.get("vent")) in ("1", "-1"):
            p["vent"] = str(m["vent"])
        if m.get("tab") in TABS:
            p["tab"] = m["tab"]
        out["params"] = p
    return out


def parse_json(text: str) -> dict:
    """The first JSON object in the model's reply (models sometimes wrap it in a code fence)."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in the reply")
    return json.loads(m.group(0))


# ---- rule-based fallback (no AI): English and Russian keywords ---------------------------------------------------
_PAGE_WORDS = [
    ("base", r"\bbase planner\b|планировщик|всю базу|базу из модул|модули базы|\bwhole base\b|plan (a|the) base"),
    ("module", r"\bmodule\b|модул|\bwall\b|стен|detector|датчик|suppress|тушен|огнетуш|firebreak|преград|люк|hatch"),
    ("scenario", r"scenario|сценари|droplet|капл|\bfuel\b|топлив|heptane|гептан|methanol|метанол|animation|анимац"),
    ("risk_map", r"risk map|карт[ау]? риска|heat ?map|карт[ау]"),
    ("validation", r"validat|валидац|accura|точност|trust|доверя"),
    ("investigations", r"investigation|исследовани|\bpsi\b|experiments list|список экспериментов"),
    ("data_explorer", r"raw data|сыры|data explorer|скачать данные|download"),
    ("insights", r"insight|вывод|recommend|рекомендац"),
    ("method", r"method|метод|source|источник|glossary|глоссари"),
    ("overview", r"overview|home|главн|обзор|начал"),
]


def rule_plan(text: str) -> dict:
    """Common requests without a language model."""
    low = text.lower()
    raw: dict = {"page": None}
    for page, pat in _PAGE_WORDS:
        if re.search(pat, low):
            raw["page"] = page
            break
    o2 = re.search(r"(\d{2}(?:[.,]\d)?)\s*%", low)
    psi = re.search(r"(\d+(?:[.,]\d+)?)\s*psi", low)
    moon = re.search(r"\bmoon|лун", low)
    iss = re.search(r"\biss\b|мкс", low)
    if raw["page"] == "scenario":
        s: dict = {}
        if re.search(r"heptane|гептан", low):
            s["fuel"] = "Heptane"
        if re.search(r"methanol|метанол", low):
            s["fuel"] = "Methanol"
        if moon:
            s["preset"] = "Moon base / rover (planned)"
        elif iss:
            s["preset"] = "ISS cabin air"
        if o2:
            s["o2"] = float(o2.group(1).replace(",", ".")) / 100
        if psi:
            s["psi"] = psi.group(1)
        d = re.search(r"(\d(?:[.,]\d)?)\s*(?:mm|мм)", low)
        if d:
            s["d0"] = d.group(1)
        raw["scenario"] = s
    if raw["page"] == "module":
        m: dict = {}
        for wall, pat in (
            ("lab", r"\blab|лаборат"),
            ("stowage", r"stowage|склад|хранени"),
            ("crew", r"crew|каюта|экипаж|жил"),
            ("blank", r"blank|empty|пуст|сво[её] стен"),
        ):
            if re.search(pat, low):
                m["wall"] = wall
                break
        if o2 or psi:
            m["atm"] = "custom"
            if o2:
                m["o2"] = o2.group(1)
            if psi:
                m["psi"] = psi.group(1)
        elif moon:
            m["atm"] = "moon"
        elif iss:
            m["atm"] = "air"
        for tab, pat in (
            ("detect", r"detector|датчик|suppress|тушен|огнетуш|обнаруж"),
            ("design", r"firebreak|преград|безопасн"),
            ("air", r"\bair\b|воздух|кислород в модуле|co2"),
            ("moon", r"checklist|чек-?лист"),
        ):
            if re.search(pat, low):
                m["tab"] = tab
                break
        raw["module"] = m
    if raw["page"] is None and (
        text.strip().endswith("?") or re.match(r"^(how|why|what|does|is|can|как|почему|что|сколько|есть ли|можно ли)\b", low)
    ):
        raw["question"] = text.strip()
    return validate(raw)


def plan(text: str, generate: Callable[..., str] | None = None) -> dict:
    """Action for ``text``: model proposal (validated) when a generator is given and works, else the rule parser.
    ``used_ai`` tells which one decided."""
    if generate is not None:
        try:
            out = validate(parse_json(generate(SYSTEM, text)))
            if out["page"] or out["question"]:
                out["used_ai"] = True
                return out
        except Exception:  # quota, timeout, unreadable JSON: fall back to the rules
            pass
    out = rule_plan(text)
    out["used_ai"] = False
    return out
