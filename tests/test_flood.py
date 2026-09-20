"""Pure-function checks for the flood mapping and flood land-cover helpers."""
import numpy as np
from build_flood_extent import db_from_power, otsu_threshold
from prepare_accessmod_inputs import FLOOD_CLASS, flood_tag


def test_flood_tag_is_month_day():
    assert flood_tag("2026-07-08") == "flood0708"
    assert flood_tag("2026-07-13") == "flood0713"


def test_db_conversion_and_nonpositive_values_become_nan():
    db = db_from_power(np.array([1.0, 0.1, 0.0, -5.0]))
    assert np.isclose(db[0], 0.0) and np.isclose(db[1], -10.0)
    assert np.isnan(db[2]) and np.isnan(db[3])


def test_otsu_splits_a_bimodal_distribution():
    rng = np.random.default_rng(0)
    water = rng.normal(-20, 1.5, 5000)
    land = rng.normal(-8, 1.5, 5000)
    threshold = otsu_threshold(np.concatenate([water, land]))
    assert -18 < threshold < -10


def test_flood_class_is_outside_worldcover_and_road_classes():
    assert FLOOD_CLASS > 208
