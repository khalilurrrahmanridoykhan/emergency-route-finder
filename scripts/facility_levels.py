"""Classify OSM health facilities into levels and decide which emergencies they qualify for.

Rules and overrides live in config/ so every assumption can be edited without touching code.
"""
import csv
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config"
UNCLASSIFIED = "private_or_unclassified"


def _read(name):
    with open(CONFIG / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_rules():
    rows = sorted(_read("facility_rules.csv"), key=lambda r: int(r["priority"]))
    return [(r["match"].lower(), r["level"]) for r in rows]


def load_overrides():
    return {r["osm_id"]: r["level"] for r in _read("facility_overrides.csv")}


def load_capabilities():
    return {r["facility_level"]: r for r in _read("capabilities.csv")}


def classify(osm_id, name, name_orig, rules=None, overrides=None):
    """Return (level, source) where source is 'override', 'rule: <keyword>' or 'default'."""
    rules = load_rules() if rules is None else rules
    overrides = load_overrides() if overrides is None else overrides
    if str(osm_id) in overrides:
        return overrides[str(osm_id)], "override"
    text = f"{name or ''} {name_orig or ''}".lower()
    for keyword, level in rules:
        if keyword in text:
            return level, f"rule: {keyword}"
    return UNCLASSIFIED, "default"


def qualifies(level, capability_column, capabilities=None):
    """True when the facility level is assumed able to handle the emergency (value 'yes')."""
    capabilities = load_capabilities() if capabilities is None else capabilities
    return capabilities[level][capability_column] == "yes"
