"""Keep the public Streamlit Community Cloud app awake (ADR-048).

Community Cloud puts an app to sleep after 12 hours without traffic; a visitor then sees "This app has gone to sleep"
and must click "Yes, get this app back up!". This script visits the app like a person, with a headless browser (a
plain HTTP request does not open an app session), wakes it if it is asleep, and checks that the Overview headline is
shown, then opens the assistant page (no question is asked, so no Gemini quota is used) to warm it up. Run by
.github/workflows/keep-awake.yml every few hours; exit code 1 if the app did not come up.

Usage: python scripts/keep_awake.py [URL]   (KEEP_AWAKE_CHANNEL=msedge to use an installed Edge)
"""

from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://prometheus-0g.streamlit.app/"
HEADLINE = "Faster, hotter"  # first line of the Overview headline block (app/views/overview.py)
WAKE_BUTTON = "Yes, get this app back up"
TIMEOUT_S = 300


def find(page, make):
    """First locator with a match in the page or any of its frames (the app runs inside an iframe), else None."""
    for frame in page.frames:
        try:
            loc = make(frame)
            if loc.count():
                return loc
        except Exception:  # frame detached while the page reloads
            continue
    return None


def main() -> int:
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel=os.environ.get("KEEP_AWAKE_CHANNEL") or None)  # e.g. msedge locally
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(URL, timeout=120_000)
        woke = False
        while time.time() - t0 < TIMEOUT_S:
            button = find(page, lambda f: f.get_by_role("button", name=WAKE_BUTTON))
            if not woke and button is not None:
                button.first.click()
                woke = True
                print("app was asleep: wake-up clicked", flush=True)
            if find(page, lambda f: f.get_by_text(HEADLINE)) is not None:
                page.wait_for_timeout(5_000)  # stay a moment, like a visitor
                # open the assistant page too: it prepares the model list and search index (no question is asked,
                # so no Gemini quota is used) and keeps the first real question fast
                page.goto(URL.rstrip("/") + "/assistant", timeout=120_000)
                page.wait_for_timeout(15_000)
                print(f"app is up ({time.time() - t0:.0f} s{', after wake-up' if woke else ''})", flush=True)
                browser.close()
                return 0
            page.wait_for_timeout(2_000)
        page.screenshot(path="keep_awake_failure.png", full_page=True)
        browser.close()
    print(f"app did not show the Overview headline within {TIMEOUT_S} s", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
