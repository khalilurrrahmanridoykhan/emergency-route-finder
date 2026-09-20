.PHONY: setup data inputs e1 test lint

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Download the public inputs into data/cache/ (not committed)
data:
	.venv/bin/python scripts/fetch_inputs.py

# Phase E1: build inputs, import into AccessMod (Docker), run the dry-season analyses
e1:
	scripts/run_e1.sh
	.venv/bin/python scripts/summarize_e1.py

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check .
