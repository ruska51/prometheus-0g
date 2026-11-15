"""Visual layer "Editorial" (ADR-063; follows the "Technical report" of ADR-062): white paper, dark ink, thin grey rules, one orange accent, IBM Plex type,
numbers in a monospaced face; the fire animations stay dark windows, like photographs in a report. Pure CSS.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

LOGO = Path(__file__).resolve().parent / "static" / "logo.svg"

CSS = """
<style>
:root{--bg:#f7f5f0; --panel:#ffffff; --line:#e2ded5; --line-hi:#c8c2b6; --ink:#16181c; --muted:#5b5f66;
  --accent:#c8501d; --accent-ink:#ffffff}
.stApp{background:var(--bg) !important}
[data-testid="stAppViewContainer"]{background:transparent !important}
[data-testid="stDecoration"]{display:none}
[data-testid="stMainBlockContainer"]{max-width:1120px; padding-top:4.2rem}

/* editorial type: serif headings, readable body, no monospace labels */
h1{font-family:'Newsreader',Georgia,serif !important; font-weight:500 !important; letter-spacing:-.02em;
  font-size:clamp(2.2rem,4vw,3.1rem) !important; line-height:1.08 !important; color:var(--ink) !important; margin-bottom:.4rem !important}
h2,h3{font-family:'Newsreader',Georgia,serif !important; font-weight:500 !important; letter-spacing:-.01em; color:var(--ink) !important}
h3{font-size:1.55rem !important}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li{max-width:74ch; line-height:1.6}
[data-testid="stCaptionContainer"]{color:var(--muted) !important; font-size:.9rem !important; line-height:1.55; max-width:80ch}
.kicker{font-size:.78rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); margin-bottom:.5rem}

/* numbers: big serif figures over a thin rule, no boxes */
[data-testid="stMetric"]{background:transparent; border:0; border-top:2px solid var(--ink); border-radius:0; padding:10px 2px 4px}
[data-testid="stMetricValue"]{font-family:'Newsreader',Georgia,serif !important; font-weight:500 !important; font-size:2.4rem !important;
  color:var(--ink) !important; font-variant-numeric:tabular-nums}
[data-testid="stMetricLabel"] p{color:var(--muted) !important; font-size:.85rem !important}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line) !important; border-radius:4px !important; background:var(--panel)}
div[data-testid="stExpander"] details{border:0 !important; border-top:1px solid var(--line) !important; border-radius:0 !important}

/* Fire designer: contents line and numbered steps */
.toc{display:flex; flex-wrap:wrap; gap:.3rem 1.4rem; margin:.6rem 0 1.4rem; padding:.7rem 0; border-top:1px solid var(--line);
  border-bottom:1px solid var(--line)}
.toc a{color:var(--ink) !important; text-decoration:none !important; font-size:.92rem}
.toc a:hover{color:var(--accent) !important}
.toc a b{color:var(--accent); font-weight:600; margin-right:.35rem}
.step{display:flex; align-items:baseline; gap:.9rem; margin:3rem 0 .4rem; scroll-margin-top:80px}
.step b{font-weight:600; color:var(--accent); font-size:1rem}
.step span{font-family:'Newsreader',Georgia,serif; font-size:2rem; font-weight:500; color:var(--ink); letter-spacing:-.01em}

/* controls: quiet */
.stButton>button,.stDownloadButton>button,[data-testid="stPopover"] button,[data-testid="stFormSubmitButton"] button{
  border-radius:4px !important; box-shadow:none !important; font-weight:500 !important}
button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]{background:var(--accent) !important;
  color:var(--accent-ink) !important; border-color:var(--accent) !important}
[data-testid="stPageLink"] a{border-bottom:1px solid var(--line-hi); border-radius:0; padding:.2rem 0}
[data-testid="stPageLink"] a:hover{border-color:var(--accent)}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line); border-radius:4px; overflow:hidden}
[data-testid="stAlert"]{border-radius:4px !important}
iframe{border-radius:4px}

/* top-right: language and glossary */
.st-key-lang_bar{position:fixed !important; top:62px; right:24px; z-index:1001; width:auto !important}
.st-key-gloss_bar{position:fixed !important; top:62px; right:150px; z-index:1001; width:auto !important}

/* AI pilot: one clear button, bottom-right (above Streamlit Cloud's "Manage app") */
.st-key-pilot_fab{position:fixed !important; right:24px; bottom:84px; z-index:1000; width:auto !important}
.st-key-pilot_fab [data-testid="stPopover"] > div > button{background:var(--ink) !important; color:#fff !important; border:0 !important;
  border-radius:999px !important; padding:.65rem 1.15rem !important; font-weight:500 !important; box-shadow:0 6px 18px rgba(0,0,0,.18) !important}
[data-testid="stPopoverBody"]{min-width:340px}
@media (max-width:640px){.st-key-pilot_fab{right:12px; bottom:76px} [data-testid="stMainBlockContainer"]{padding-top:5.5rem}
  .st-key-lang_bar{top:58px; right:12px} .st-key-gloss_bar{top:58px; right:130px}}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    if LOGO.exists():
        st.logo(str(LOGO), size="large")


def kicker(text: str) -> None:
    """Small monospaced label above a page title."""
    st.markdown(f"<div class='kicker'>{text}</div>", unsafe_allow_html=True)
