# One-command pipeline. Targets are filled in stages 3-11.
PY ?= .venv/Scripts/python

setup:
	py -3.12 -m venv .venv && $(PY) -m pip install -r requirements.txt && $(PY) -m pip install -e .

data:
	@echo "stage 3: not implemented yet"

train:
	@echo "stage 5: not implemented yet"

test:
	$(PY) -m pytest -q

app:
	$(PY) -m streamlit run app/main.py

.PHONY: setup data train test app
