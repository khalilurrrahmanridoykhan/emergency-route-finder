"""Sanity checks for the editable assumption tables in config/."""
import csv
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config"

CAPABILITY_VALUES = {"yes", "no", "basic", "first_aid"}
SEASONS = {"dry", "flood", "both"}
MODES = {"walk", "bicycle", "motorized", "boat"}


def read(name):
    with open(CONFIG / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_capability_values_are_known():
    rows = read("capabilities.csv")
    assert rows
    for row in rows:
        for key, value in row.items():
            if key in ("facility_level", "basis"):
                continue
            assert value in CAPABILITY_VALUES, f"{row['facility_level']}.{key}={value}"


def test_every_emergency_maps_to_a_capability_column():
    columns = set(read("capabilities.csv")[0].keys())
    for row in read("emergencies.csv"):
        assert row["capability_column"] in columns, row["emergency_id"]
        assert int(row["target_minutes"]) > 0


def test_speeds_are_positive_and_use_known_values():
    rows = read("speeds.csv")
    assert rows
    for row in rows:
        assert float(row["speed_kmh"]) > 0, row["class"]
        assert row["mode"] in MODES, row["class"]
        assert row["season"] in SEASONS, row["class"]


def test_every_assumption_row_is_labeled():
    for name in ("capabilities.csv", "speeds.csv"):
        for row in read(name):
            assert row["basis"], f"{name} has an unlabeled row"
