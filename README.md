# Prometheus-0g

Physics-first, AI-assisted fire-safety insights from NASA microgravity combustion experiments. Built for the challenge "Flame in Freefall".
Team **The Catalyst**, NASA International Space Apps Challenge 2026 (Uralsk local event).

**Live dashboard:** https://prometheus-0g.streamlit.app/ (Streamlit Community Cloud, ADR-040)

> Work in progress. Sections below are filled during the project (stage 12).

## Problem

_TBD._

## Approach

_TBD._

## NASA data and resources

| # | Resource | How it is used |
|---|---|---|
| R1 | [NASA Physical Sciences Informatics](https://psi.nasa.gov/physci/repo/search?q=combustion) | _TBD_ |
| R2 | [Apollo 1 (NASA SMA)](https://sma.nasa.gov/sma-disciplines/accllp/apollo-1) | _TBD_ |
| R3 | [Apollo 13 (NASA SMA)](https://sma.nasa.gov/sma-disciplines/accllp/apollo-13) | _TBD_ |
| R4 | [Fire aboard Mir (NASA History)](https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/) | _TBD_ |
| R5 | [Fireman's Air Tanks (NASA Spinoff)](https://spinoff.nasa.gov/node/9582) | _TBD_ |
| R6 | [Fire Detector (NASA Spinoff)](https://spinoff.nasa.gov/node/9407) | _TBD_ |
| R7 | [Fire Attire (NASA Spinoff)](https://spinoff.nasa.gov/node/9918) | _TBD_ |

## How to run

Tested on 2026-11-14 from a fresh clone on Windows 11 with Python 3.12 (docs/WORKLOG.md, stage 10); the same commands work
on macOS / Linux (`python3`). Dependencies are pinned in `requirements.txt`.

```
git clone https://github.com/ruska51/prometheus-0g
cd prometheus-0g
python run.py setup   # .venv + pinned requirements + the fif package (about 1 min)
python run.py all     # verify raw-data hashes -> build data -> train models -> build insights -> tests (about 2 min)
python run.py app     # dashboard at http://localhost:8501
```

Single steps: `python run.py verify | data | train | validate | insights | test | lint | app`
(`validate` re-runs the stage-6 validation, about 5 min; `lint` needs `pip install -r requirements-dev.txt`).
`make <task>` does the same where make is available. Nothing has to be downloaded: the NASA tables used are in
`data/raw/` (CC0) with sha256 checksums in `data/catalog.yaml`; the 43 MB FLEX report is fetched only by
`scripts/verify_flex_vs_tp.py`. Live version: https://prometheus-0g.streamlit.app/

## Validation

_TBD._

## Use of AI

See [docs/AI_USAGE.md](docs/AI_USAGE.md).

## License

Apache-2.0, see [LICENSE](LICENSE).
