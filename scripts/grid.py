"""Shared analysis grid: the wider area in UTM zone 46N at 100 m."""
from math import ceil, floor

from pyproj import Transformer
from rasterio.transform import from_origin

# Wider area for facilities and roads (see docs/data-gaps.md).
BBOX_WGS84 = (90.95, 24.4, 91.75, 25.2)
CRS = "EPSG:32646"
RES = 100.0


def target_grid():
    """Return (transform, width, height, bounds) of the 100 m grid covering BBOX_WGS84."""
    t = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    corners = [(x, y) for x in (BBOX_WGS84[0], BBOX_WGS84[2]) for y in (BBOX_WGS84[1], BBOX_WGS84[3])]
    xs, ys = zip(*[t.transform(x, y) for x, y in corners])
    west, east = floor(min(xs) / RES) * RES, ceil(max(xs) / RES) * RES
    south, north = floor(min(ys) / RES) * RES, ceil(max(ys) / RES) * RES
    width, height = int((east - west) / RES), int((north - south) / RES)
    return from_origin(west, north, RES, RES), width, height, (west, south, east, north)
