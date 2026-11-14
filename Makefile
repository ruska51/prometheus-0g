# Thin wrapper around run.py (the cross-platform pipeline; Windows users run `python run.py <task>` directly).
PY ?= python3

setup:
	$(PY) run.py setup
all:
	$(PY) run.py all
verify data train validate insights test lint app:
	$(PY) run.py $@

.PHONY: setup all verify data train validate insights test lint app
