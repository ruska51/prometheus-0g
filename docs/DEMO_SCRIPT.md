# Demo - 7 slides (ADR-046)

Space Apps allows the demo as a video of at most 30 seconds or as at most 7 slides including the title. Ruslan chose
the slides (ADR-046; the 30-second video of ADR-044 was dropped). The deck is in English, every number on it comes
from the project's generated artefacts (the same values as README.md and the Overview page), and the pictures are
screenshots of the live app (docs/figures/ui/). No AI-generated images; no NASA logos.

File: `docs/demo/prometheus-0g_slides.pdf` (7 pages, 16:9). Demo link for the form:
https://github.com/ruska51/prometheus-0g/blob/main/docs/demo/prometheus-0g_slides.pdf (public, no login).

| # | Title | On the slide | Message |
|---|---|---|---|
| 1 | Fire on the Moon | Team, challenge; animation screenshot: the same heptane droplet weightless vs at 1/6 g | What would a fire do in the air planned for a Moon base? |
| 2 | A Moon base will breathe richer air than the ISS, at a sixth of Earth's gravity | ISS air 21 % O2 / 14.7 psi vs Moon base 30 % O2 / 10.2 psi; Apollo 1, Apollo 13, Mir | Fires in space are rare but costly; NASA's answer is scattered over 24 investigations |
| 3 | Faster, hotter, and less likely to go out by itself | +32 % burning rate, 14.1 s vs 18.5 s burn-out, self-extinction 46 % (n 13) vs 86 % (n 58), 2462 K (+238 K), evidence badges | The headline answer, each number labelled with its evidence |
| 4 | Physics first, machine learning for the rest | Pipeline data -> physics -> model -> validation -> insights -> app; 276 tests verified (3288 cells, 0 differences); no leakage; what is new | How the numbers were made |
| 5 | We tested the model on air it had never seen | Leave-a-class-out errors (physics / ML / hybrid) for He, CO2, ~0.7 atm, O2 >= 30 %; failures | Physics makes it 1.2-1.9x more accurate on unseen air |
| 6 | All of it lives in one public dashboard | Module-fire screenshot (crew-quarters wall at lunar gravity, time to the hatch in three gravities); five features; "summarize, rank, interpret" | What the user gets |
| 7 | What a Moon base should do about it | Three actions; who it is for; NASA spinoffs; QR code to the live app | Impact and a call to try it |

The talk at the Uralsk event is about 2-2.5 minutes in Russian (the local event's language); the speaker text is in the
deck's speaker notes. The submission itself is the English PDF.

## How the PDF was made

The deck was laid out as HTML slides (1920x1080) and printed to PDF with Playwright and Microsoft Edge, with the
fonts Space Grotesk and Inter (Google Fonts, SIL Open Font License) and the app screenshots embedded. The QR code on
slide 7 encodes https://prometheus-0g.streamlit.app/ (generated with the segno library and decoded back with OpenCV to
check it).
