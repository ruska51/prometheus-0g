"""Knowledge base of the "Ask the data" assistant (stage 9, variant C, ADR-042).

Two kinds of context blocks, each with a stable id that the model must cite:
- ``D:...`` - our own verified results, generated from the same artefacts the dashboard shows (docs/insights.json,
  docs/validation_results.json, the scenario model, the PSI catalog, the comparison matrix);
- ``R:<ntrs id>#<n>`` - excerpts of public-use NASA NTRS reports (data/raw/ntrs_text, ADR-042), split into ~1100-character
  passages.
Retrieval is BM25 over all blocks (no embedding service, no network). A short "core facts" block that states what the
data cover and do not cover is always included, so the model can say "no data" correctly.
"""

from __future__ import annotations

import functools
import json
import math
import re
from collections import Counter
from dataclasses import dataclass

import pandas as pd

from fif.data.catalog import REPO_ROOT

NTRS_DIR = REPO_ROOT / "data" / "raw" / "ntrs_text"
CHUNK_CHARS = 1100
CHUNK_OVERLAP = 150
TOKEN = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")
CYR = re.compile(r"[а-яё]+")
STOP = set(
    "the a an of and or in on at to for by with from is are was were be been this that these those it its as into than "
    "which what how why when where who does do did can could would should will not no yes".split()
)

# Russian question words -> English search terms (prefix match on the Russian stem). Retrieval only; the model reads the
# original question. Covers the domain vocabulary of the dashboard.
RU_EN = {
    "кислород": "oxygen o2",
    "азот": "nitrogen n2",
    "гели": "helium he",
    "углекисл": "co2 carbon dioxide",
    "угарн": "co carbon monoxide",
    "давлен": "pressure",
    "горени": "burning combustion",
    "горит": "burning burn",
    "гор": "burn",
    "сгора": "burning burn",
    "пламя": "flame",
    "пламен": "flame",
    "капл": "droplet",
    "скорост": "rate",
    "константа": "constant",
    "затуха": "extinction",
    "погас": "extinction extinguish",
    "самозатух": "self extinction",
    "диаметр": "diameter",
    "размер": "size diameter",
    "метанол": "methanol",
    "гептан": "heptane",
    "топлив": "fuel",
    "лун": "moon lunar",
    "марс": "mars martian",
    "гравитац": "gravity",
    "невесом": "microgravity",
    "земл": "earth 1g",
    "мкс": "iss space station",
    "станци": "station",
    "корабл": "spacecraft",
    "кабин": "cabin",
    "атмосфер": "atmosphere",
    "модул": "module habitat",
    "баз": "base habitat",
    "скафандр": "spacesuit",
    "луноход": "rover",
    "дым": "smoke",
    "частиц": "particle",
    "датчик": "detector sensor",
    "обнаружен": "detection detector",
    "тушени": "suppression",
    "огнетуш": "suppression",
    "разбав": "diluent dilution",
    "инертн": "inert",
    "твёрд": "solid",
    "тверд": "solid",
    "материал": "material",
    "ткан": "fabric",
    "распростран": "spread",
    "воспламен": "ignition",
    "зажиган": "ignition",
    "искр": "ignition spark",
    "газ": "gas",
    "сажа": "soot",
    "саж": "soot",
    "излучен": "radiation",
    "температур": "temperature",
    "холодн": "cool",
    "модел": "model",
    "точност": "accuracy error",
    "ошибк": "error",
    "валидац": "validation",
    "провер": "verification",
    "данн": "data",
    "тест": "test",
    "эксперимент": "experiment",
    "исследован": "investigation",
    "отчёт": "report",
    "отчет": "report",
    "пожар": "fire",
    "опасн": "hazard",
    "безопасн": "safety",
    "аполлон": "apollo",
    "мир": "mir",
    "экипаж": "crew",
    "вентиляц": "ventilation flow",
    "поток": "flow",
    "окислител": "oxidizer",
}


def expand_query(q: str) -> str:
    """Add English search terms for Russian words (longest matching stem wins)."""
    extra = []
    for w in CYR.findall(q.lower()):
        for stem in sorted(RU_EN, key=len, reverse=True):
            if w.startswith(stem):
                extra.append(RU_EN[stem])
                break
    return q + (" " + " ".join(extra) if extra else "")


@dataclass(frozen=True)
class Block:
    id: str
    title: str
    text: str
    kind: str  # "data" or "report"
    url: str = ""


def _tokens(s: str) -> list[str]:
    return [w for w in TOKEN.findall(s.lower()) if w not in STOP and len(w) > 1]


def _clean(raw: str) -> str:
    s = re.sub(r"</?p>", "\n", raw)
    s = re.sub(r"<[^>]{1,40}>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def _chunks(text: str) -> list[str]:
    out, i = [], 0
    while i < len(text):
        j = min(len(text), i + CHUNK_CHARS)
        if j < len(text):  # end on a sentence or line break if one is near
            k = max(text.rfind(". ", i + CHUNK_CHARS // 2, j), text.rfind("\n", i + CHUNK_CHARS // 2, j))
            j = k + 1 if k > 0 else j
        piece = text[i:j].strip()
        if len(piece) > 80:
            out.append(piece)
        if j >= len(text):
            break
        i = max(j - CHUNK_OVERLAP, i + 1)
    return out


def report_blocks() -> list[Block]:
    man = pd.read_csv(NTRS_DIR / "MANIFEST.tsv", sep="\t", dtype=str)
    blocks = []
    for _, r in man.iterrows():
        text = _clean((NTRS_DIR / f"{r['ntrs_id']}.txt").read_text(encoding="utf-8", errors="replace"))
        for n, c in enumerate(_chunks(text)):
            blocks.append(
                Block(
                    f"R:{r['ntrs_id']}#{n}",
                    f"NTRS {r['ntrs_id']}: {r['title']}",
                    c,
                    "report",
                    f"https://ntrs.nasa.gov/citations/{r['ntrs_id']}",
                )
            )
    return blocks


def _fmt(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def data_blocks() -> list[Block]:
    """Our verified results as short text blocks (English, numbers computed by the package)."""
    blocks = []
    ins = json.loads((REPO_ROOT / "docs" / "insights.json").read_text(encoding="utf-8"))
    for rank, i in enumerate(ins["ranked"], 1):
        blocks.append(
            Block(
                f"D:insight-{i['id']}",
                f"Insight {i['id']} (rank {rank}): {i['title']}",
                f"{i['finding']} Recommended action: {i['action']} Evidence type: {i['evidence_type']}; "
                f"tests: {i['n_tests']}; confidence: {i['confidence']}"
                + ("; extrapolation beyond tested conditions" if i["extrapolation"] else "")
                + f". Sources: {'; '.join(i['sources'])}.",
                "data",
            )
        )
    for i in ins["history_and_earth"]:
        blocks.append(
            Block(
                f"D:insight-{i['id']}",
                f"{i['evidence_type']} {i['id']}: {i['title']}",
                f"{i['finding']} {i['action']} Source: {i['sources'][0]}.",
                "data",
            )
        )

    v = json.loads((REPO_ROOT / "docs" / "validation_results.json").read_text(encoding="utf-8"))
    s = v["repeated_cv"]["summary"]
    kline = "; ".join(
        f"{m}: RMSE ln K {_fmt(d['RMSE_log']['mean'], 3)}, MAE {_fmt(d['MAE']['mean'], 3)} mm2/s" for m, d in s["K"].items()
    )
    eline = "; ".join(f"{m}: AUC {_fmt(d['AUC']['mean'], 3)}" for m, d in s["extinction"].items() if "AUC" in d)
    blocks.append(
        Block(
            "D:validation-cv",
            "Validation: model accuracy and error - grouped cross-validation (5 folds by test regime, 5 seeds)",
            f"Burning-rate constant K models - {kline}. Extinction classifiers - {eline}. Inside the tested conditions the "
            "hybrid and the pure machine-learning model are equally accurate; the typical error of the hybrid is about "
            f"+-{(math.exp(s['K']['hybrid']['RMSE_log']['mean']) - 1) * 100:.0f} % on K.",
            "data",
        )
    )
    ex = v["extrapolation"]
    lines = []
    for name, e in ex.items():
        if e["K"]:
            lines.append(
                f"{name}: physics {_fmt(e['K']['physics']['RMSE_log'], 3)}, pure ML {_fmt(e['K']['pure_ml_gp']['RMSE_log'], 3)}, "
                f"hybrid {_fmt(e['K']['hybrid']['RMSE_log'], 3)}"
            )
    blocks.append(
        Block(
            "D:validation-extrapolation",
            "Validation: extrapolation tests (train without a class of conditions, predict it; RMSE ln K)",
            "; ".join(lines) + ". The hybrid is 1.2-1.9x more accurate than pure ML for held-out He, CO2, ~0.7 atm and "
            "O2 >= 0.30; no model transfers reliably to a fuel it has not seen.",
            "data",
        )
    )

    from fif.insights.scenario import PRESETS, predict

    lines = []
    for name, a in PRESETS.items():
        for fuel in ("Methanol", "Heptane"):
            r = predict(fuel, a["p_atm"], a["x_o2"])
            k = r["K_hybrid_mm2_s"]
            lines.append(
                f"{name} (O2 {a['x_o2']:.2f}, {a['p_atm'] * 14.696:.1f} psi), {fuel.lower()} 3 mm droplet: "
                f"K hybrid {'withheld (too uncertain)' if k is None else _fmt(k) + ' mm2/s'}, K physics "
                f"{_fmt(r['K_theory_mm2_s'])} mm2/s, flame temperature {r['T_f_K']:.0f} K, ratio vs ISS air "
                f"{(r['ratio_vs_iss'] - 1) * 100:+.0f} %, P(self-extinction) {r['P_extinction'] * 100:.0f} %, Earth 1 g "
                f"factor x{r['earth_factor']:.1f}, lunar-surface factor 1.0-{r['moon_factor']:.2f}, reliability "
                f"{r['reliability']['status']}"
            )
    blocks.append(Block("D:scenario-cabins", "Scenario model results for cabin atmospheres", ". ".join(lines) + ".", "data"))

    cat = pd.read_csv(REPO_ROOT / "data" / "processed" / "psi_investigations.csv")
    for _, r in cat.iterrows():
        obj = str(r.get("objective") or "")[:400]
        blocks.append(
            Block(
                f"D:psi-{r['psi_id']}",
                f"PSI investigation {r['psi_id']} {r['acronym'] if isinstance(r['acronym'], str) else ''}",
                f"{r['title']}. Platform: {r['flight_platform']}; hardware: {r['hardware']}; tests in data table: "
                f"{int(r['n_table_rows'])}; publications: {r['n_publications']}. Objective: {obj}",
                "data",
            )
        )

    from fif.insights.compare import VARIABLES, comparison_matrix, hardware_groups

    m = comparison_matrix()
    tb = m[m["has_table"]]
    outcome_cols = [v[0] for v in VARIABLES if v[1] == "outcome"]
    both = tb[tb["oxygen"] & tb["pressure"]]["acronym"].tolist()
    outc = tb[tb[outcome_cols].any(axis=1)]["acronym"].tolist()
    groups = "; ".join(f"{g}: {', '.join(a)}" for g, a in hardware_groups(m).items())
    blocks.append(
        Block(
            "D:compare",
            "Comparison of the 24 PSI combustion investigations (from the PSI data-table headers)",
            f"Tables that record both oxygen and pressure: {', '.join(both)} ({len(both)} of {len(tb)} tables). Tables with "
            f"a measured outcome: {', '.join(outc)} ({len(outc)} of {len(tb)}); the others list test conditions only. No data "
            f"table: {', '.join(m[~m['has_table']]['acronym'])}. Shared hardware families - {groups}.",
            "data",
        )
    )

    fx = pd.read_csv(REPO_ROOT / "data" / "processed" / "flex.csv")
    used = fx[fx["use_in_model"]]
    blocks.append(
        Block(
            "D:flex-coverage",
            "FLEX data coverage (PSI-69, NASA/TP-2015-216046)",
            f"{len(fx)} FLEX tests ({len(used)} used for modelling), fuels: "
            + ", ".join(f"{k} {v}" for k, v in used["fuel"].value_counts().items())
            + f"; O2 mole fraction {used['x_o2'].min():.2f}-{used['x_o2'].max():.2f}; pressure "
            f"{used['p_atm'].min():.2f}-{used['p_atm'].max():.2f} atm; diluents "
            + ", ".join(f"{k} {v}" for k, v in used["diluent"].value_counts().items())
            + f"; initial droplet diameter {used['d0_mm_orig'].min():.1f}-{used['d0_mm_orig'].max():.1f} mm. The PSI table "
            "was checked cell by cell against the NASA technical report: 0 differences; 2 tests missing from PSI were "
            "added from the report.",
            "data",
        )
    )
    return blocks


CORE_FACTS = Block(
    "D:core",
    "What this tool covers (always read first)",
    "Prometheus-0g analyses NASA Physical Sciences Informatics (PSI) combustion data. Quantitative models: FLEX droplet "
    "combustion on the ISS (methanol and n-heptane only, ISS ambient ~298 K): burning-rate constant K (Law & Williams "
    "physics + Gaussian-process correction), self-extinction probability, extinction diameter. Also used: ACME CFI-G "
    "gaseous flames (ignition, self-extinction), BASS-II solids (CO and O2 change only, no flame-spread rates), SAME-R "
    "smoke tests (materials list). Not covered by data: partial gravity (Moon/Mars only as physics bounds), other fuels, "
    "solid flame-spread rates, detector performance, cabin-scale fires, costs or policy. Earth (1 g) numbers are a "
    "physics extrapolation. The Moon-base atmosphere (30 % O2, 10.2 psi) lies just outside the tested pressure range for "
    "30 % O2 (tested from 0.703 atm), so its predictions are labelled extrapolation.",
    "data",
)


@functools.lru_cache(maxsize=1)
def index() -> tuple[list[Block], list[Counter], dict[str, float], float]:
    blocks = data_blocks() + report_blocks()
    docs = [Counter(_tokens(b.title + " " + b.text)) for b in blocks]
    n = len(docs)
    df = Counter(w for d in docs for w in d)
    idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}
    avg = sum(sum(d.values()) for d in docs) / n
    return blocks, docs, idf, avg


def search(query: str, k: int = 8, k1: float = 1.5, b: float = 0.75, data_boost: float = 1.3) -> list[Block]:
    """BM25 top-k blocks for the query; our own data blocks get a mild boost over report excerpts."""
    blocks, docs, idf, avg = index()
    q = _tokens(expand_query(query))
    scores = []
    for blk, d in zip(blocks, docs, strict=True):
        dl = sum(d.values())
        sc = sum(idf.get(w, 0.0) * d[w] * (k1 + 1) / (d[w] + k1 * (1 - b + b * dl / avg)) for w in q if w in d)
        scores.append(sc * (data_boost if blk.kind == "data" else 1.0))
    order = sorted(range(len(blocks)), key=lambda i: scores[i], reverse=True)
    return [blocks[i] for i in order[:k] if scores[i] > 0]
