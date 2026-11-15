"""Ask-the-data assistant (ADR-042): retrieval, prompt, citation checks, key handling - all offline (no API calls)."""

import subprocess
from pathlib import Path

import pytest

from fif.assistant import knowledge as kb
from fif.assistant.llm import SYSTEM, api_key, ask, build_prompt, cited_ids

ROOT = Path(__file__).resolve().parents[1]


def test_block_ids_unique_and_reports_registered():
    blocks, *_ = kb.index()
    ids = [b.id for b in blocks]
    assert len(ids) == len(set(ids))
    man = (kb.NTRS_DIR / "MANIFEST.tsv").read_text(encoding="utf-8")
    for b in blocks:
        if b.kind == "report":
            assert b.id.split(":")[1].split("#")[0] in man


@pytest.mark.parametrize(
    "q,expected",
    [
        ("Does helium dilution slow burning?", "D:insight-S2"),
        ("Замедляет ли гелий горение?", "D:insight-S2"),
        ("What happens to solid materials at lunar gravity?", "D:insight-P6"),
        ("Сколько CO выделяется при горении твёрдых материалов?", "D:insight-D1"),
        ("Moon base burning rate of methanol", "D:sim-moon-base--rover-methanol"),
    ],
)
def test_retrieval_finds_the_relevant_result(q, expected):
    assert expected in [b.id for b in kb.search(q, k=6)]


def test_prompt_contains_core_facts_rules_and_truncated_question():
    p = build_prompt("x" * 5000, kb.search("helium", k=3))
    assert "[D:core]" in p and p.count("x") <= 700
    assert "ONLY from the CONTEXT" in SYSTEM and "do not cover" in SYSTEM


def test_citations_are_checked_against_the_context():
    def fake(system, prompt):
        return "Helium speeds burning [D:insight-S2]. Invented [R:99999#1]."

    r = ask("Does helium slow burning?", fake)
    assert [s.id for s in r["sources"]] == ["D:insight-S2"]
    assert r["unknown_citations"] == ["R:99999#1"] and not r["uncited"]
    assert ask("anything", lambda s, p: "No citations here.")["uncited"]
    assert cited_ids("a [D:core] b [D:core] [R:20150023456#3]") == ["D:core", "R:20150023456#3"]
    assert cited_ids("x [R:1#0, R:1#1] [95 % CI] [D:a; D:b]") == ["R:1#0", "R:1#1", "D:a", "D:b"]


def test_api_key_only_from_secrets_or_environment(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert api_key({}) is None
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    assert api_key({}) == "env-key"
    assert api_key({"GEMINI_API_KEY": "secret-key"}) == "secret-key"


def test_no_api_keys_in_tracked_files():
    import re

    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    pat = re.compile(r"AIza[0-9A-Za-z_-]{35}|hf_[A-Za-z0-9]{30,}|sk-ant-[A-Za-z0-9_-]{20,}")
    hits = []
    for f in files:
        p = ROOT / f
        if p.suffix in {".py", ".md", ".toml", ".txt", ".yaml", ".json", ".tsv", ".csv", ".cfg", ""} and p.is_file():
            if pat.search(p.read_text(encoding="utf-8", errors="ignore")):
                hits.append(f)
    assert not hits


def test_model_ranking_prefers_newest_stable_text_flash():
    from fif.assistant.llm import rank_models

    names = [
        "gemini-2.5-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash-preview",
        "gemini-2.5-pro",
        "gemini-3.5-flash-image",
        "gemini-3.5-flash-tts",
        "gemma-4-27b-it",
    ]
    assert rank_models(names) == ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash-preview"]


def test_error_reason_never_contains_the_key():
    from fif.assistant.llm import AllModelsFailed, _reason, friendly_error

    fake = "AI" + "za" + "SyA1234567890abcdefghijklmnopqrstuv"  # assembled so the key scanner does not flag this file
    e = RuntimeError("bad request for key " + fake)
    assert "AIza" not in _reason(e)
    assert friendly_error(AllModelsFailed([("m1", "ClientError 429 RESOURCE_EXHAUSTED")])) == "quota"
    assert friendly_error(AllModelsFailed([("m1", "ServerError 503 overloaded")])) == "other"


def test_unsupported_numbers_flags_invented_values_only():
    from fif.assistant.llm import unsupported_numbers

    src = [b for b in kb.index()[0] if b.id == "D:insight-D1"]
    assert unsupported_numbers("CO rose by a median 45 ppm, 90th percentile 413 ppm [D:insight-D1].", src) == []
    assert unsupported_numbers("CO rose by 999 ppm [D:insight-D1].", src) == ["999"]


def test_search_mixes_results_and_reports():
    ids = [b.id for b in kb.search("How was the droplet burning-rate constant determined in the FLEX experiment?")]
    assert any(i.startswith("D:") for i in ids) and any(i.startswith("R:") for i in ids)


@pytest.mark.parametrize(
    "q",
    ["Чем горение на Луне отличается от горения на МКС?", "Will a fire burn faster on the Moon?", "lunar base fire"],
)
def test_moon_question_gets_the_headline_numbers(q):
    ids = [b.id for b in kb.search(q)]
    assert ids[:2] == ["D:moon-answer-methanol", "D:moon-answer-heptane"]


def test_moon_block_numbers_match_the_overview():
    from fif.insights.moon import moon_answer

    b = next(b for b in kb.index()[0] if b.id == "D:moon-answer-methanol")
    m = moon_answer("Methanol")
    for v in (
        f"{(m['k_ratio'] - 1) * 100:+.0f} %",
        f"{m['burn_time_moon_s']:.1f} s",
        f"{m['burn_time_iss_s']:.1f} s",
        f"{m['self_ext_high_o2'] * 100:.0f} % of {m['n_high_o2']}",
        f"{m['flame_temperature_moon_K']:.0f} K",
    ):
        assert v in b.text


def test_citations_render_as_numbers_in_order_of_first_use():
    from fif.assistant.llm import render_citations

    text = "Faster [D:moon-answer-methanol]. Hotter [D:core, D:moon-answer-methanol]. CI [95 % CI] stays [R:9#9]."
    out, order = render_citations(text, {"D:core", "D:moon-answer-methanol"})
    assert out == "Faster¹. Hotter²˒¹. CI [95 % CI] stays."
    assert order == ["D:moon-answer-methanol", "D:core"]
    assert "D:" not in out and "R:" not in out


def test_ask_returns_display_text_and_numbered_sources():
    r = ask("Will it burn on the Moon?", lambda system, prompt: "Yes, +32 % [D:moon-answer-methanol].")
    assert r["display"] == "Yes, +32 %¹." and [s.id for s in r["sources"]] == ["D:moon-answer-methanol"]
    assert r["unsupported_numbers"] == []


def test_streamed_answer_never_shows_raw_block_ids():
    from fif.assistant.llm import render_partial

    full = "Faster [D:moon-answer-methanol]. Hotter [D:core]."
    assert render_partial("Faster [D:moon-ans", {"D:moon-answer-methanol"}) == "Faster"
    shown = []

    def fake(system, prompt, on_text=None):
        for i in range(1, len(full) + 1):
            on_text(full[:i])
        return full

    r = ask("Will it burn on the Moon?", fake, on_text=shown.append)
    assert len(shown) == len(full)
    assert not any("D:" in s or "[" in s for s in shown)
    assert shown[-1] == r["display"] == "Faster¹. Hotter²."


def test_gemini_generate_streams_with_timeout_and_falls_back_to_thinking_budget(monkeypatch):
    from google import genai

    from fif.assistant import llm

    calls = []

    class Err(Exception):
        code = 400

    class Chunk:
        def __init__(self, text):
            self.text = text

    class Models:
        def generate_content_stream(self, model, contents, config):
            th = config.thinking_config
            calls.append((model, th.thinking_level if th else None, th.thinking_budget if th else None))
            if th is not None and th.thinking_level is not None:
                raise Err("thinking_level not supported")  # a Gemini 2.5-style model
            return iter([Chunk("Yes "), Chunk(None), Chunk("[D:core].")])

    class Client:
        def __init__(self, api_key, http_options):
            assert http_options.timeout == llm.REQUEST_TIMEOUT_MS
            self.models = Models()

    monkeypatch.setattr(genai, "Client", Client)
    gen = llm.gemini_generate("not-a-real-key", "gemini-x-flash")
    seen = []
    assert gen("sys", "prompt", seen.append) == "Yes [D:core]."
    assert seen == ["Yes ", "Yes [D:core]."]
    assert calls == [("gemini-x-flash", llm_level("MINIMAL"), None), ("gemini-x-flash", None, 0)]


def llm_level(name):
    from google.genai import types

    return types.ThinkingConfig(thinking_level=name).thinking_level


def test_best_model_is_retried_after_its_quota_pause(monkeypatch):
    from google import genai

    from fif.assistant import llm

    state = {"quota": True, "now": 1000.0}
    tried = []

    class Quota(Exception):
        code = 429

    class Chunk:
        text = "Ok [D:core]."

    class Models:
        def generate_content_stream(self, model, contents, config):
            tried.append(model)
            if model == "best-flash" and state["quota"]:
                raise Quota("429 RESOURCE_EXHAUSTED")
            return iter([Chunk()])

    class Client:
        def __init__(self, api_key, http_options):
            self.models = Models()

    monkeypatch.setattr(genai, "Client", Client)
    monkeypatch.setattr(llm.time, "monotonic", lambda: state["now"])
    gen = llm.gemini_generate("not-a-real-key", "best-flash")
    gen.candidates[:] = ["best-flash", "lite-flash"]
    gen("s", "p")
    assert tried == ["best-flash", "lite-flash"] and gen.model == "lite-flash" and "429" in gen.failed[0][1]
    tried.clear()
    gen("s", "p")  # inside the pause: the failed model is not asked again
    assert tried == ["lite-flash"]
    state.update(quota=False, now=1000.0 + llm.QUOTA_SKIP_S + 1)
    tried.clear()
    gen("s", "p")  # pause over, quota back: the best model answers again
    assert tried == ["best-flash"] and gen.model == "best-flash"
