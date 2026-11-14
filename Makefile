# One-command pipeline. Targets are filled in stages 3-11.
PY ?= .venv/Scripts/python

setup:
	py -3.12 -m venv .venv && $(PY) -m pip install -r requirements.txt && $(PY) -m pip install -e .

data:
	$(PY) scripts/build_data.py

train:
	$(PY) scripts/train_models.py

test:
	$(PY) -m pytest -q

app:
	$(PY) -m streamlit run app/main.py

.PHONY: setup data train test app
