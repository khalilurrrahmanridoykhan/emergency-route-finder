"""Validation in route.py that needs no Docker, no AccessMod outputs and no network: unknown
emergency ids and points outside the analysis grid are both rejected before any file is touched.
"""
import pytest
from route import OutsideAreaError, UnknownEmergencyError, _check_inside_area, _to_utm, route


def test_unknown_emergency_is_rejected_before_touching_any_data():
    with pytest.raises(UnknownEmergencyError):
        route(91.3, 24.75, "not_a_real_emergency")


def test_point_far_outside_bangladesh_is_rejected():
    with pytest.raises(OutsideAreaError):
        route(50.0, 10.0, "snakebite")


def test_check_inside_area_accepts_a_point_in_the_middle_of_the_grid():
    x, y = _to_utm(91.3, 24.75)
    _check_inside_area(x, y)  # no error


def test_check_inside_area_rejects_a_point_just_outside_the_grid():
    with pytest.raises(OutsideAreaError):
        _check_inside_area(0.0, 0.0)


def test_to_utm_roundtrips_to_approximately_the_original_point():
    from grid import CRS
    from pyproj import Transformer

    x, y = _to_utm(91.3, 24.75)
    back = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform(x, y)
    assert back[0] == pytest.approx(91.3, abs=1e-4)
    assert back[1] == pytest.approx(24.75, abs=1e-4)
