"""Visual layer "Technical report" (ADR-062): white paper, dark ink, thin grey rules, one orange accent, IBM Plex type,
numbers in a monospaced face; the fire animations stay dark windows, like photographs in a report. Pure CSS.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

LOGO = Path(__file__).resolve().parent / "static" / "logo.svg"

CSS = """
<style>
:root{--bg:#fbfaf7; --panel:#ffffff; --line:#e3e0d9; --line-hi:#c9c4ba; --ink:#1c1e22; --muted:#6a6f78;
  --accent:#d2571f; --accent-ink:#ffffff; --cyan:#1f5fa8}
.stApp{background:var(--bg) !important}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:transparent !important}
[data-testid="stMainBlockContainer"]{max-width:1180px; padding-top:2.4rem}

/* type */
h1{font-weight:600 !important; letter-spacing:-.015em; font-size:clamp(1.9rem,3.4vw,2.6rem) !important; color:var(--ink) !important;
  padding-bottom:.5rem !important; border-bottom:1px solid var(--line); margin-bottom:.6rem !important}
h2,h3{font-weight:600 !important; letter-spacing:-.005em}
.kicker{font:500 .72rem/1 'IBM Plex Mono',monospace; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
  margin-bottom:.4rem}
.kicker i{display:none}
[data-testid="stMetricValue"]{font-family:'IBM Plex Mono',monospace !important; font-weight:500 !important; color:var(--ink) !important;
  font-size:1.9rem !important}
[data-testid="stMetricLabel"] p{color:var(--muted) !important; font-size:.78rem !important; letter-spacing:.02em}
[data-testid="stCaptionContainer"]{color:var(--muted) !important}

/* cards: flat panels with a thin rule */
[data-testid="stMetric"]{background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:12px 14px 10px}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line) !important; border-radius:6px !important}
div[data-testid="stExpander"] details{border:1px solid var(--line) !important; border-radius:6px !important; background:transparent}

/* numbered steps and table of contents (Fire designer) */
.toc{display:flex; flex-wrap:wrap; gap:0; border:1px solid var(--line); border-radius:6px; overflow:hidden; margin:.4rem 0 1.2rem}
.toc a{flex:1 1 auto; padding:.55rem .8rem; color:var(--ink) !important; text-decoration:none !important; font-size:.86rem;
  border-right:1px solid var(--line); white-space:nowrap}
.toc a:last-child{border-right:0}
.toc a:hover{background:var(--panel)}
.toc a b{font:500 .78rem 'IBM Plex Mono',monospace; color:var(--accent); margin-right:.45rem}
.step{display:flex; align-items:baseline; gap:.8rem; margin:2.2rem 0 .3rem; padding-top:.9rem; border-top:1px solid var(--line-hi);
  scroll-margin-top:70px}
.step b{font:500 .95rem 'IBM Plex Mono',monospace; color:var(--accent)}
.step span{font-size:1.35rem; font-weight:600; color:var(--ink)}

/* controls */
.stButton>button,.stDownloadButton>button,[data-testid="stPopover"] button,[data-testid="stFormSubmitButton"] button{
  border-radius:5px !important; border:1px solid var(--line-hi) !important; background:var(--panel) !important; font-weight:500 !important;
  box-shadow:none !important}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stPopover"] button:hover{border-color:var(--accent) !important}
button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]{background:var(--accent) !important;
  color:var(--accent-ink) !important; border-color:var(--accent) !important}
[data-testid="stPageLink"] a{border:1px solid var(--line); border-radius:5px; padding:.3rem .65rem}
[data-testid="stPageLink"] a:hover{border-color:var(--accent); background:var(--panel)}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,textarea{border-radius:5px !important}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line); border-radius:6px; overflow:hidden}
[data-testid="stAlert"]{border-radius:6px !important}
hr{border-color:var(--line) !important}
iframe{border-radius:6px}

/* sidebar */
[data-testid="stSidebar"]{background:#f4f2ed !important; border-right:1px solid var(--line)}
[data-testid="stSidebarNav"] a{border-radius:4px}
[data-testid="stSidebarNav"] a[aria-current="page"]{background:var(--panel) !important; box-shadow:inset 2px 0 0 var(--accent)}
[data-testid="stNavSectionHeader"]{font-family:'IBM Plex Mono',monospace !important; letter-spacing:.12em; text-transform:uppercase;
  font-size:.68rem !important; color:var(--muted) !important}

/* AI pilot: a plain, clearly labelled button in the bottom-right corner (above Streamlit Cloud's "Manage app") */
.st-key-pilot_fab{position:fixed !important; right:24px; bottom:84px; z-index:1000; width:auto !important}
.st-key-pilot_fab [data-testid="stPopover"] > div > button{background:var(--accent) !important; color:var(--accent-ink) !important;
  border:0 !important; border-radius:6px !important; padding:.65rem 1.05rem !important; font-weight:600 !important;
  box-shadow:0 4px 14px rgba(0,0,0,.18) !important}
[data-testid="stPopoverBody"]{min-width:340px}
@media (max-width:640px){.st-key-pilot_fab{right:12px; bottom:76px} [data-testid="stMainBlockContainer"]{padding-top:1.2rem}
  .toc a{flex:1 1 45%}}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    if LOGO.exists():
        st.logo(str(LOGO), size="large")


def kicker(text: str) -> None:
    """Small monospaced label above a page title."""
    st.markdown(f"<div class='kicker'>{text}</div>", unsafe_allow_html=True)
