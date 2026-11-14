"""Record the 30-second demo video from the LIVE app with burned-in English subtitles (stage 12, ADR-044).

Playwright (Microsoft Edge) records the deployed dashboard; loading and waiting are cut out, only the marked scene
windows are kept; ffmpeg (bundled with imageio-ffmpeg) trims, concatenates and burns the subtitles from DEMO_SCENES.
The video is a screen recording of our own app - no AI-generated imagery.
Output: docs/demo/prometheus-0g_demo.mp4 (<= 30 s, 1280x720, H.264) and docs/demo/subtitles.srt.
Usage: ``python scripts/make_demo_video.py [base_url]`` (requirements-dev.txt: playwright, imageio-ffmpeg)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo"
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://prometheus-0g.streamlit.app"
W, H = 1280, 720

# (scene id, seconds, subtitle lines shown one after another, split evenly over the scene)
DEMO_SCENES = [
    (
        "answer",
        6.0,
        [
            "Will a fire burn on a Moon base? We asked NASA's ISS fire experiments.",
            "Yes - faster: +32 % burning rate, and flames rarely go out by themselves.",
        ],
    ),
    (
        "burn",
        9.0,
        [
            "Physics (Law & Williams) + machine learning, trained on 274 NASA FLEX tests.",
            "Same fuel droplet: ISS-like microgravity vs the lunar surface (1/6 g).",
        ],
    ),
    ("validation", 5.0, ["Validated honestly: on atmospheres it never saw, physics cuts the error 1.2-1.9x."]),
    ("assistant", 6.0, ["Ask the data: AI answers only from NASA data and reports - with sources."]),
    ("catalog", 4.0, ["24 NASA investigations compared. Open source: prometheus-0g.streamlit.app"]),
]


def app_frame(page, selector: str = "h1", timeout_s: int = 240):
    end = time.time() + timeout_s
    while time.time() < end:
        for f in page.frames:
            try:
                if f.locator(selector).count():
                    return f
            except Exception:
                pass
        time.sleep(1)
    raise RuntimeError(f"app not ready: {selector}")


def record(tmp: Path) -> tuple[Path, list[tuple[str, float, float]]]:
    marks = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        ctx = b.new_context(
            viewport={"width": W, "height": H}, record_video_dir=str(tmp), record_video_size={"width": W, "height": H}
        )
        page = ctx.new_page()
        t0 = time.time()

        def mark(name: str, dur: float) -> None:
            s = time.time() - t0
            time.sleep(dur)
            marks.append((name, s, s + dur))

        # 1 answer block
        page.goto(BASE + "/", wait_until="domcontentloaded", timeout=240_000)
        fr = app_frame(page, "text=Yes - faster")
        time.sleep(3)
        fr.locator("h1").first.scroll_into_view_if_needed()
        page.mouse.wheel(0, 120)
        time.sleep(1)
        mark("answer", DEMO_SCENES[0][1])

        # 2 animation: Moon base microgravity vs lunar surface, replay at 1x
        page.goto(BASE + "/scenario", wait_until="domcontentloaded", timeout=240_000)
        fr = app_frame(page, "text=See it burn")
        fr.get_by_text("Heptane", exact=True).first.click()  # sooty fuel: the most visible flame
        time.sleep(6)
        for _ in range(60):
            if fr.locator("iframe").count():
                break
            time.sleep(1)
        time.sleep(4)
        anim = fr.locator("iframe").first
        anim.scroll_into_view_if_needed()
        page.mouse.wheel(0, 260)
        time.sleep(1)
        inner = fr.frame_locator("iframe").first
        inner.locator("#replay").click()
        mark("burn", DEMO_SCENES[1][1])

        # 3 validation: extrapolation chart
        page.goto(BASE + "/validation", wait_until="domcontentloaded", timeout=240_000)
        fr = app_frame(page, "text=Extrapolation: train without")
        time.sleep(4)
        page.mouse.move(W * 0.6, H * 0.5)
        page.mouse.wheel(0, 520)
        time.sleep(2)
        mark("validation", DEMO_SCENES[2][1])

        # 4 assistant: ask, wait for the answer (cut), then show question + answer
        page.goto(BASE + "/assistant", wait_until="domcontentloaded", timeout=240_000)
        fr = app_frame(page, "[data-testid=stChatInputTextArea]")
        inp = fr.locator("[data-testid=stChatInputTextArea]")
        inp.fill("How long does a heptane droplet burn on the ISS?")
        inp.press("Enter")
        for _ in range(90):
            time.sleep(1)
            if fr.locator("[data-testid=stChatMessage]").count() >= 2:
                break
        print("assistant messages:", fr.locator("[data-testid=stChatMessage]").count(), flush=True)
        time.sleep(2)
        fr.locator("[data-testid=stChatMessage]").first.scroll_into_view_if_needed()
        time.sleep(1)
        mark("assistant", DEMO_SCENES[3][1])

        # 5 comparison matrix of the 24 investigations
        page.goto(BASE + "/investigations", wait_until="domcontentloaded", timeout=240_000)
        fr = app_frame(page, "text=Compare investigations")
        time.sleep(3)
        fr.get_by_role("tab", name="Compare investigations").click()
        time.sleep(4)
        page.mouse.move(W * 0.6, H * 0.5)
        page.mouse.wheel(0, 140)
        time.sleep(1)
        mark("catalog", DEMO_SCENES[4][1])

        print("marks:", [(n, round(a, 1), round(b, 1)) for n, a, b in marks], flush=True)
        video = Path(page.video.path())
        ctx.close()
        b.close()
    return video, marks


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        video, marks = record(tmp)
        parts = []
        for i, (_, s, e) in enumerate(marks):
            part = tmp / f"part{i}.mp4"
            subprocess.run(
                [
                    ff,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(video),
                    "-ss",
                    f"{s:.3f}",
                    "-to",
                    f"{e:.3f}",
                    "-vf",
                    f"scale={W}:{H},fps=25",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(part),
                ],
                check=True,
            )
            parts.append(part)
        (tmp / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
        subprocess.run(
            [ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "joined.mp4"],
            cwd=tmp,
            check=True,
        )
        srt, t, n = [], 0.0, 1
        for _, dur, lines in DEMO_SCENES:
            step = dur / len(lines)
            for line in lines:
                srt.append(f"{n}\n{srt_time(t)} --> {srt_time(t + step - 0.05)}\n{line}\n")
                t += step
                n += 1
        (tmp / "subs.srt").write_text("\n".join(srt), encoding="utf-8")
        style = (
            "FontName=Arial,FontSize=12,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,BorderStyle=4,Outline=0,"
            "Shadow=0,MarginV=22,Alignment=2"
        )
        subprocess.run(
            [
                ff,
                "-y",
                "-loglevel",
                "error",
                "-i",
                "joined.mp4",
                "-vf",
                f"subtitles=subs.srt:force_style='{style}'",
                "-t",
                "30",
                "-c:v",
                "libx264",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "demo.mp4",
            ],
            cwd=tmp,
            check=True,
        )
        shutil.copy(tmp / "demo.mp4", OUT / "prometheus-0g_demo.mp4")
        shutil.copy(tmp / "subs.srt", OUT / "subtitles.srt")
    dur = subprocess.run([ff, "-i", str(OUT / "prometheus-0g_demo.mp4")], capture_output=True, text=True).stderr
    print(
        [ln.strip() for ln in dur.splitlines() if "Duration" in ln][0],
        (OUT / "prometheus-0g_demo.mp4").stat().st_size // 1024,
        "KB",
    )


if __name__ == "__main__":
    main()
