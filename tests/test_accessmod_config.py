"""Checks on the replay config builder that need no Docker and no downloaded data."""
import csv
from pathlib import Path

from build_accessmod_configs import scenario_table
from prepare_accessmod_inputs import ROAD_CLASSES

CONFIG = Path(__file__).resolve().parent.parent / "config"


def speed_rows():
    with open(CONFIG / "speeds.csv", newline="") as f:
        return list(csv.DictReader(f))


def test_dry_scenario_has_no_flood_only_rows():
    dry = scenario_table("dry")
    flood_only = {int(r["class"]) for r in speed_rows() if r["season"] == "flood"}
    assert not {row["class"] for row in dry} & flood_only


def test_scenario_rows_match_accessmod_format():
    for row in scenario_table("dry"):
        assert set(row) == {"class", "label", "speed", "mode"}
        assert row["mode"] in {"WALKING", "BICYCLING", "MOTORIZED"}


def test_every_road_class_has_a_speed_row():
    classes = {int(r["class"]) for r in speed_rows()}
    for code, _ in ROAD_CLASSES:
        assert code in classes


def test_road_highway_values_map_to_one_class():
    seen = {}
    for code, values in ROAD_CLASSES:
        for value in values:
            assert value not in seen, f"{value} in classes {seen[value]} and {code}"
            seen[value] = code
