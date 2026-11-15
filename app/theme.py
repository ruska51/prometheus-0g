"""Visual layer "Science agency" (ADR-064; follows ADR-062/063): white paper, dark ink, thin grey rules, one orange accent, IBM Plex type,
numbers in a monospaced face; the fire animations stay dark windows, like photographs in a report. Pure CSS.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

LOGO = Path(__file__).resolve().parent / "static" / "logo.svg"

CSS = """
<style>
:root{--bg:#ffffff; --band:#0b0d12; --line:#e2e4e8; --ink:#111318; --muted:#5a606b; --accent:#d9461e; --accent-ink:#ffffff}
.stApp{background:var(--bg) !important}
[data-testid="stDecoration"]{display:none}
[data-testid="stMainBlockContainer"]{max-width:1200px; padding-top:3.6rem}

/* bold grotesque headings, plain body */
h1{font-weight:800 !important; letter-spacing:-.025em; font-size:clamp(2.3rem,4.4vw,3.5rem) !important; line-height:1.04 !important;
  color:var(--ink) !important}
h2,h3{font-weight:800 !important; letter-spacing:-.015em; color:var(--ink) !important}
h3{font-size:1.6rem !important}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{max-width:76ch; line-height:1.6}
[data-testid="stCaptionContainer"]{color:var(--muted) !important; font-size:.88rem !important; max-width:82ch}
.kicker{font-size:.76rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); margin-bottom:.6rem}

/* dark cover band across the full width (home page) */
.st-key-hero{background:var(--band); margin:0 0 2rem; padding:2.8rem 2.6rem 2.4rem !important}
.st-key-hero h1,.st-key-hero p,.st-key-hero strong{color:#ffffff !important}
.st-key-hero [data-testid="stCaptionContainer"]{color:#9aa3b2 !important}
.st-key-hero img{border-radius:2px}

/* figures: big bold numbers over a thin rule */
[data-testid="stMetric"]{background:transparent; border:0; border-top:3px solid var(--ink); border-radius:0; padding:10px 0 4px}
[data-testid="stMetricValue"]{font-weight:800 !important; font-size:2.5rem !important; letter-spacing:-.02em; color:var(--ink) !important;
  font-variant-numeric:tabular-nums}
[data-testid="stMetricLabel"] p{color:var(--muted) !important; font-size:.85rem !important; font-weight:600 !important}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line) !important; border-radius:2px !important}
div[data-testid="stExpander"] details{border:0 !important; border-top:1px solid var(--line) !important; border-radius:0 !important}

/* Fire designer: contents line and numbered steps */
.toc{display:flex; flex-wrap:wrap; gap:.3rem 1.4rem; margin:.6rem 0 1.4rem; padding:.75rem 0; border-top:3px solid var(--ink);
  border-bottom:1px solid var(--line)}
.toc a{color:var(--ink) !important; text-decoration:none !important; font-size:.92rem; font-weight:600}
.toc a:hover{color:var(--accent) !important}
.toc a b{color:var(--accent); margin-right:.35rem}
.step{display:flex; align-items:baseline; gap:.9rem; margin:3.2rem 0 .5rem; padding-top:.8rem; border-top:3px solid var(--ink);
  scroll-margin-top:80px}
.step b{font-weight:800; color:var(--accent); font-size:1.05rem}
.step span{font-size:2rem; font-weight:800; letter-spacing:-.02em; color:var(--ink)}

/* controls */
.stButton>button,.stDownloadButton>button,[data-testid="stPopover"] button,[data-testid="stFormSubmitButton"] button{
  border-radius:2px !important; box-shadow:none !important; font-weight:600 !important}
button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]{background:var(--accent) !important;
  color:var(--accent-ink) !important; border-color:var(--accent) !important}
[data-testid="stPageLink"] a{border-bottom:2px solid var(--ink); border-radius:0; padding:.2rem 0; font-weight:600}
[data-testid="stPageLink"] a:hover{border-color:var(--accent)}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line); border-radius:2px; overflow:hidden}
[data-testid="stAlert"]{border-radius:2px !important}
iframe{border-radius:2px}

/* top-right: language and glossary */
.st-key-lang_bar{position:fixed !important; top:62px; right:24px; z-index:1001; width:auto !important}
.st-key-gloss_bar{position:fixed !important; top:62px; right:150px; z-index:1001; width:auto !important}

/* AI pilot */
.st-key-pilot_fab{position:fixed !important; right:24px; bottom:84px; z-index:1000; width:auto !important}
.st-key-pilot_fab [data-testid="stPopover"] > div > button{background:var(--accent) !important; color:#fff !important; border:0 !important;
  border-radius:2px !important; padding:.7rem 1.2rem !important; font-weight:700 !important; box-shadow:0 6px 18px rgba(0,0,0,.2) !important}
[data-testid="stPopoverBody"]{min-width:340px}
@media (max-width:640px){.st-key-pilot_fab{right:12px; bottom:76px} [data-testid="stMainBlockContainer"]{padding-top:5rem}
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
