# Demo script - 30-second video (ADR-044)

Format chosen by Ruslan: a video of at most 30 seconds with English subtitles. It is a **screen recording of the live
app** (https://prometheus-0g.streamlit.app/), made automatically by `scripts/make_demo_video.py`: Playwright with
Microsoft Edge records the deployed dashboard, loading time is cut out, and ffmpeg burns in the subtitles. No
AI-generated images, video or voice; no NASA logos. Output: `docs/demo/prometheus-0g_demo.mp4` (1280x720, H.264, no
audio) and `docs/demo/subtitles.srt`.

| Time | On screen | Subtitle |
|---|---|---|
| 0:00-0:03 | Overview, headline answer block: "Will it burn on the Moon? Yes - faster, hotter, and less likely to go out by itself", four numbers with evidence badges | Will a fire burn on a Moon base? We asked NASA's ISS fire experiments. |
| 0:03-0:06 | same, the numbers +32 %, 14.1 s, 46 %, 2462 K visible (methanol) | Yes - faster: +32 % burning rate, and flames rarely go out by themselves. |
| 0:06-0:10 | Moon-base scenario, heptane: the "See it burn" animation restarts - microgravity (left, spherical soot flame) vs lunar surface (right, buoyant flame) | Physics (Law & Williams) + machine learning, trained on 274 NASA FLEX tests. |
| 0:10-0:15 | the same animation, droplets shrinking, the 1/6 g droplet burns faster | Same fuel droplet: ISS-like microgravity vs the lunar surface (1/6 g). |
| 0:15-0:20 | Validation page: extrapolation bar chart (physics / pure ML / hybrid on held-out atmospheres) | Validated honestly: on atmospheres it never saw, physics cuts the error 1.2-1.9x. |
| 0:20-0:26 | Ask the data: question "How long does a heptane droplet burn on the ISS?" and the answer with numbers and block citations | Ask the data: AI answers only from NASA data and reports - with sources. |
| 0:26-0:30 | Investigations, Compare tab: matrix of the 24 PSI investigations | 24 NASA investigations compared. Open source: prometheus-0g.streamlit.app |

## How to re-record

```
python -m pip install -r requirements-dev.txt     # playwright, imageio-ffmpeg
python -m playwright install ffmpeg                # Playwright's video encoder (1.3 MB)
python scripts/make_demo_video.py                  # records the live app, ~2 min
```

The script prints the scene marks and the final duration (must be <= 30 s). Check a few frames before uploading.

## Upload

YouTube, visibility "Unlisted" or "Public" (viewable without login), title "Prometheus-0g - Will it burn on the Moon?
(NASA Space Apps 2026)". The subtitles are burned into the picture, so no caption file is needed; `subtitles.srt` can
also be uploaded as English captions.
