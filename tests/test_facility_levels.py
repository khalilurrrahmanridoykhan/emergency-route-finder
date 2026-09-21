"""The facility classifier and the capability lookup."""
import csv
from pathlib import Path

from facility_levels import EXCLUDED, UNCLASSIFIED, classify, load_capabilities, qualifies

CONFIG = Path(__file__).resolve().parent.parent / "config"


def test_english_and_bangla_upazila_health_complexes():
    assert classify("1", "Nabiganj Upazila Health Complex", "")[0] == "upazila_health_complex"
    assert classify("2", "OSM 2 (bangla name)", "বানিয়াচং ঊপজেলা স্বাস্থ্য কমপ্লেক্স")[0] == "upazila_health_complex"


def test_union_and_community_levels_including_osm_misspelling():
    union = "union_health_family_welfare_centre"
    assert classify("1", "Union health and family welfare center", "")[0] == union
    assert classify("2", "Kartikpur Commuinity Clinic", "")[0] == "community_clinic"
    assert classify("3", "Kamarkandi Community Clinic", "")[0] == "community_clinic"


def test_override_beats_rules_and_unknown_names_are_unclassified():
    assert classify("2332856927", "Sunamganj General Hospital", "")[1] == "override"
    assert classify("999", "Some Private Clinic", "")[0] == UNCLASSIFIED
    assert classify("998", "", "")[0] == UNCLASSIFIED


def test_spelling_variants_and_word_orders_of_health_complexes():
    assert classify("1", "Nikli Upazilla Health Complex", "")[0] == "upazila_health_complex"
    assert classify("2", "Upazila Fenchugonj Health Complex", "")[0] == "upazila_health_complex"
    assert classify("3", "Health & Family Wlfare Center", "")[0] == "union_health_family_welfare_centre"


def test_laboratories_and_specialist_hospitals_are_excluded():
    assert classify("1", "Apollo Diagonostic Center", "")[0] == EXCLUDED
    assert classify("2", "Jalalabad Eye Hospital", "")[0] == EXCLUDED
    assert classify("3", "Sylhet Pet Care", "")[0] == EXCLUDED


def test_every_level_in_rules_and_overrides_has_a_capability_row():
    levels = set(load_capabilities()) | {EXCLUDED}
    with open(CONFIG / "facility_rules.csv", newline="", encoding="utf-8") as f:
        assert {r["level"] for r in csv.DictReader(f)} <= levels
    with open(CONFIG / "facility_overrides.csv", newline="", encoding="utf-8") as f:
        assert {r["level"] for r in csv.DictReader(f)} <= levels
    assert UNCLASSIFIED in levels


def test_qualification_follows_the_capability_table():
    assert qualifies("upazila_health_complex", "childbirth_complication")
    assert not qualifies("union_health_family_welfare_centre", "childbirth_complication")  # basic only
    assert not qualifies("community_clinic", "injury_drowning")  # first aid only
    assert qualifies("district_general_hospital", "snakebite_hospital_only")
    assert not qualifies("upazila_health_complex", "snakebite_hospital_only")
