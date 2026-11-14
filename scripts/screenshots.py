"""Screenshots of every dashboard page (desktop 1400 px and phone 390 px) into docs/figures/ui/.

Requires a running app: ``.venv/Scripts/python -m streamlit run app/main.py --server.port 8599``.
Uses Playwright with the installed Microsoft Edge (no browser download).
Usage: ``.venv/Scripts/python scripts/screenshots.py [port]``
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures" / "ui"
PAGES = {"overview": "", "insights": "insights", "scenario": "scenario", "risk_map": "risk_map",
         "investigations": "investigations", "data_explorer": "data_explorer", "validation": "validation", "method": "method"}


def main(port: int = 8599) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = f"http://localhost:{port}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for device, size in (("desktop", {"width": 1400, "height": 2400}), ("phone", {"width": 390, "height": 2600})):
            page = browser.new_page(viewport=size)
            for name, path in PAGES.items():
                if device == "phone" and name not in ("overview", "scenario", "risk_map"):
                    continue
                page.goto(base + path, wait_until="networkidle", timeout=180_000)
                page.wait_for_selector("h1", timeout=180_000)
                time.sleep(4)  # let charts render
                page.screenshot(path=str(OUT / f"{name}_{device}.png"), full_page=False)  # Streamlit scrolls an inner container: use a tall viewport
                print("saved", name, device)
            page.close()
        browser.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8599)
