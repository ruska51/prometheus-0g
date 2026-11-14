"""Interface language switch (ADR-041): every literal t("...") key has a Russian entry, the package's generated texts
carry Russian versions, and every page runs in Russian."""

import ast
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from i18n import FLAME_RU, RU  # noqa: E402

PAGES = ["overview", "insights", "assistant", "scenario", "risk_map", "investigations", "data_explorer", "validation", "method"]


def _literal_keys() -> dict[str, str]:
    keys = {}
    for f in [ROOT / "app" / "main.py", ROOT / "app" / "common.py", *(ROOT / "app" / "views").glob("*.py")]:
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Call)
                and getattr(n.func, "id", "") in ("t", "_t")
                and n.args
                and isinstance(n.args[0], ast.Constant)
                and isinstance(n.args[0].value, str)
            ):
                keys[n.args[0].value] = f.name
    return keys


def test_every_literal_key_is_translated():
    missing = {k: f for k, f in _literal_keys().items() if k not in RU}
    assert not missing, missing


def test_placeholders_match():
    import string

    for en, ru in RU.items():
        f_en = {x[1] for x in string.Formatter().parse(en) if x[1]}
        f_ru = {x[1] for x in string.Formatter().parse(ru) if x[1]}
        assert f_en == f_ru, en


def test_dynamic_option_values_are_translated():
    from fif.insights.compare import HARDWARE, VARIABLES
    from fif.insights.flame_sim import ATMOSPHERES
    from fif.insights.scenario import PRESETS
    from fif.validation.core import E_SPECS, EXTRAPOLATION, K_SPECS

    values = [
        *PRESETS,
        *(v["src"] for v in PRESETS.values()),
        *ATMOSPHERES,
        *HARDWARE,
        *(v[0] for v in VARIABLES),
        *E_SPECS,
        *K_SPECS,
        *EXTRAPOLATION,
    ]
    assert not [v for v in values if v not in RU]


def test_generated_texts_have_russian_versions():
    import json

    data = json.loads((ROOT / "docs" / "insights.json").read_text(encoding="utf-8"))
    for i in data["ranked"] + data["history_and_earth"]:
        assert set(i["ru"]) == {"title", "finding", "action"}, i["id"]
    from fif.insights.flame_sim import simulate
    from fif.validation.reliability import reliability

    r = reliability("Methanol", 0.694, 0.30, 0, 0, 3.0)
    assert len(r["reasons_ru"]) == len(r["reasons"]) == 1
    s = simulate("Methanol", 1.0, 0.21, gravity=1 / 6)
    assert len(s["notes_ru"]) == len(s["notes"])


def test_flame_labels_cover_all_keys():
    from flame_view import LABELS_EN

    assert set(FLAME_RU) == set(LABELS_EN)


@pytest.mark.parametrize("page", PAGES)
def test_page_runs_in_russian(page):
    at = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=180)
    at.session_state["lang"] = "ru"
    at.run()
    at.switch_page(f"views/{page}.py")
    at.run()
    assert not at.exception, [e.message for e in at.exception]
    assert at.title[0].value == RU.get(at.title[0].value, at.title[0].value) and any("Ѐ" <= ch <= "ӿ" for ch in at.title[0].value)
