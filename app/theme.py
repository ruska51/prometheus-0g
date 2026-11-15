"""Visual layer "Mission control" (ADR-056): starfield background, glass cards, gradient headings, glowing controls.

Pure CSS injected once per page run; no content, no numbers. Colours follow .streamlit/config.toml and the slides.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

LOGO = Path(__file__).resolve().parent / "static" / "logo.svg"

CSS = """
<style>
:root{
  --fire:#ff7a1a; --amber:#ffb627; --ember:#ff4d2e; --ice:#38e8ff; --moon:#c9d4ff;
  --glass:rgba(22,30,54,.55); --glass-hi:rgba(34,46,82,.65); --line:rgba(140,170,255,.16);
  --ink:#ede9e1; --muted:#9aa6c2;
}
/* ---------- deep-space background: nebula glow + two drifting star layers ---------- */
.stApp{
  background:
    radial-gradient(1200px 600px at 85% -10%, rgba(255,122,26,.16), transparent 60%),
    radial-gradient(900px 500px at -10% 30%, rgba(56,232,255,.10), transparent 60%),
    radial-gradient(800px 600px at 50% 120%, rgba(127,166,255,.10), transparent 60%),
    #070b16 !important;
}
.stApp::before,.stApp::after{
  content:""; position:fixed; inset:-50%; pointer-events:none; z-index:0;
  background-image:
    radial-gradient(1px 1px at 20px 30px,#fff,transparent),
    radial-gradient(1px 1px at 140px 80px,#cfe0ff,transparent),
    radial-gradient(1.5px 1.5px at 250px 160px,#fff,transparent),
    radial-gradient(1px 1px at 330px 40px,#ffd9b0,transparent),
    radial-gradient(1px 1px at 90px 200px,#fff,transparent),
    radial-gradient(1.2px 1.2px at 380px 230px,#bfe9ff,transparent);
  background-size:400px 260px; opacity:.55; animation:drift 220s linear infinite;
}
.stApp::after{background-size:620px 380px; opacity:.3; animation-duration:340s; animation-direction:reverse}
@keyframes drift{from{transform:translate3d(0,0,0)}to{transform:translate3d(-400px,-260px,0)}}
@media (prefers-reduced-motion: reduce){.stApp::before,.stApp::after{animation:none}}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:transparent !important}
[data-testid="stMain"]{position:relative; z-index:1}
[data-testid="stMainBlockContainer"]{max-width:1240px; padding-top:2.2rem}

/* ---------- headings ---------- */
h1{
  font-size:clamp(2.1rem,4.2vw,3.4rem) !important; font-weight:700 !important; letter-spacing:-.02em; line-height:1.08 !important;
  background:linear-gradient(92deg,#fff3e0 0%,var(--amber) 32%,var(--fire) 58%,var(--ice) 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent !important;
  filter:drop-shadow(0 4px 28px rgba(255,122,26,.25));
}
h2,h3{letter-spacing:-.01em}
[data-testid="stMarkdownContainer"] h2, [data-testid="stHeadingWithActionElements"] h3{position:relative}
h3::before{content:""; display:inline-block; width:6px; height:.9em; margin-right:.55rem; border-radius:3px; vertical-align:-.08em;
  background:linear-gradient(180deg,var(--amber),var(--fire)); box-shadow:0 0 12px rgba(255,122,26,.7)}
.kicker{font:600 .78rem/1 'Space Grotesk',sans-serif; letter-spacing:.22em; text-transform:uppercase; color:var(--ice);
  display:inline-flex; gap:.6rem; align-items:center; padding:.45rem .8rem; border:1px solid rgba(56,232,255,.35);
  border-radius:999px; background:rgba(56,232,255,.07); margin-bottom:.6rem}
.kicker i{width:7px;height:7px;border-radius:50%;background:var(--ice);box-shadow:0 0 10px var(--ice);animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.35}}

/* ---------- glass cards: bordered containers, metrics, expanders, popovers ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) , div[data-testid="stExpander"] details,
[data-testid="stMetric"]{
  background:linear-gradient(160deg,var(--glass-hi),var(--glass)) !important;
  border:1px solid var(--line) !important; border-radius:18px !important;
  backdrop-filter:blur(14px) saturate(140%); -webkit-backdrop-filter:blur(14px) saturate(140%);
  box-shadow:0 10px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.05);
}
[data-testid="stMetric"]{padding:14px 16px 12px; transition:transform .25s, box-shadow .25s, border-color .25s}
[data-testid="stMetric"]:hover{transform:translateY(-3px); border-color:rgba(255,122,26,.45) !important;
  box-shadow:0 14px 44px rgba(255,122,26,.18), inset 0 1px 0 rgba(255,255,255,.06)}
[data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif; font-weight:700;
  background:linear-gradient(90deg,#fff,#ffd7a8); -webkit-background-clip:text; background-clip:text; color:transparent}
[data-testid="stMetricLabel"] p{color:var(--muted) !important; text-transform:uppercase; letter-spacing:.06em; font-size:.74rem !important}

/* ---------- tabs ---------- */
[data-baseweb="tab-list"]{gap:.4rem; border-bottom:1px solid var(--line)}
button[data-baseweb="tab"],[data-testid="stTab"]{border-radius:12px 12px 0 0 !important; padding:.55rem 1rem !important;
  transition:background .2s}
button[data-baseweb="tab"][aria-selected="true"],[data-testid="stTab"][aria-selected="true"]{
  background:linear-gradient(180deg,rgba(255,122,26,.18),rgba(255,122,26,0)) !important}
[data-baseweb="tab-highlight"]{background:linear-gradient(90deg,var(--amber),var(--fire)) !important; height:3px !important;
  box-shadow:0 0 14px var(--fire)}

/* ---------- buttons, links, inputs ---------- */
.stButton>button,.stDownloadButton>button,[data-testid="stPopover"] button{
  border-radius:12px !important; border:1px solid rgba(255,122,26,.45) !important;
  background:linear-gradient(135deg,rgba(255,122,26,.18),rgba(255,182,39,.06)) !important;
  transition:all .2s; font-weight:600}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stPopover"] button:hover{
  border-color:var(--amber) !important; box-shadow:0 0 22px rgba(255,122,26,.35); transform:translateY(-1px)}
[data-testid="stPageLink"] a{border:1px solid var(--line); border-radius:12px; padding:.35rem .7rem;
  background:rgba(22,30,54,.45); transition:all .2s}
[data-testid="stPageLink"] a:hover{border-color:var(--ice); box-shadow:0 0 18px rgba(56,232,255,.25); background:rgba(56,232,255,.06)}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,textarea{background:rgba(10,15,30,.7) !important; border-radius:12px !important}
[data-testid="stSlider"] [role="slider"]{box-shadow:0 0 0 4px rgba(255,122,26,.25), 0 0 16px rgba(255,122,26,.6)}
[data-testid="stChatInput"]{border-radius:16px !important; box-shadow:0 0 0 1px var(--line), 0 0 30px rgba(56,232,255,.12)}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(9,13,26,.92),rgba(12,18,36,.92)) !important;
  border-right:1px solid var(--line); backdrop-filter:blur(10px)}
[data-testid="stSidebarNav"] a{border-radius:10px; transition:background .2s}
[data-testid="stSidebarNav"] a[aria-current="page"]{background:linear-gradient(90deg,rgba(255,122,26,.25),rgba(255,122,26,.04)) !important;
  box-shadow:inset 3px 0 0 var(--fire)}
[data-testid="stNavSectionHeader"]{letter-spacing:.16em; text-transform:uppercase; font-size:.68rem !important; color:var(--ice) !important}
[data-testid="stSidebarHeader"] img{filter:drop-shadow(0 0 10px rgba(127,166,255,.35)); height:2.6rem !important; max-height:none !important}

/* ---------- tables, alerts, code, dividers ---------- */
[data-testid="stDataFrame"],[data-testid="stTable"]{border-radius:14px; overflow:hidden; border:1px solid var(--line)}
[data-testid="stAlert"]{border-radius:14px !important; backdrop-filter:blur(8px)}
hr{border-color:var(--line) !important}
[data-testid="stCaptionContainer"]{color:var(--muted) !important}
iframe{border-radius:16px}
@media (max-width:640px){[data-testid="stMainBlockContainer"]{padding-top:1.2rem} h1{font-size:2rem !important}}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    if LOGO.exists():
        st.logo(str(LOGO), size="large")


def kicker(text: str) -> None:
    """Small glowing label above a page title."""
    st.markdown(f"<div class='kicker'><i></i>{text}</div>", unsafe_allow_html=True)
