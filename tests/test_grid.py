"""The analysis grid must sit inside the requested WGS84 box so every cell has source data."""
from grid import BBOX_WGS84, CRS, RES, target_grid
from pyproj import Transformer


def test_grid_is_100m_and_non_empty():
    transform, width, height, bounds = target_grid()
    assert RES == 100.0 and transform.a == RES and -transform.e == RES
    assert width > 0 and height > 0
    assert bounds[2] - bounds[0] == width * RES
    assert bounds[3] - bounds[1] == height * RES


def test_all_grid_corners_are_inside_the_wgs84_box():
    _, _, _, (x0, y0, x1, y1) = target_grid()
    to_wgs84 = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
    west, south, east, north = BBOX_WGS84
    for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
        lon, lat = to_wgs84.transform(x, y)
        assert west <= lon <= east and south <= lat <= north
