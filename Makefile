.PHONY: setup data e1 e2 test lint

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Download the public inputs into data/cache/ (not committed)
data:
	.venv/bin/python scripts/fetch_inputs.py

# Phase E1: build inputs, import into AccessMod (Docker), run the dry-season analyses
e1:
	TAGS="dry" scripts/run_accessmod.sh
	.venv/bin/python scripts/summarize_e1.py

# Phase E2: flood extents from Sentinel-1, then dry and flood analyses
e2:
	cd scripts && ../.venv/bin/python build_flood_extent.py --during 2026-07-08
	cd scripts && ../.venv/bin/python build_flood_extent.py --during 2026-07-13
	TAGS="dry flood0708 flood0713" FLOOD_DATES="2026-07-08 2026-07-13" scripts/run_accessmod.sh
	.venv/bin/python scripts/summarize_e2.py

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check .
