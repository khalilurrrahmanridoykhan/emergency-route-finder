.PHONY: setup test lint

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check .
