.PHONY: setup data e1 e2 e3 population e4 test lint

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

# Phase E3: dry and flood scenarios plus one run per emergency type, then all summaries
e3:
	TAGS="dry flood0708 flood0713" FLOOD_DATES="2026-07-08 2026-07-13" \
	EMERGENCIES="childbirth_complication snakebite snakebite_hospital_only injury_drowning minor_illness" \
	scripts/run_accessmod.sh
	.venv/bin/python scripts/summarize_e1.py
	.venv/bin/python scripts/summarize_e2.py
	.venv/bin/python scripts/summarize_e3.py

# Check WorldPop against the 2022 census (run after e3)
population:
	.venv/bin/python scripts/check_population.py

# Phase E4: complete paths per synthetic point, cross-checked against OSRM
e4:
	scripts/run_e4.sh
	.venv/bin/python scripts/summarize_e4.py
	@echo "For the OSRM cross-check, start osrm-routed on ../facility-access-equity's data first, then:"
	@echo "  .venv/bin/python scripts/cross_check_osrm.py"

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check .
