"""Shared analysis grid: the wider area in UTM zone 46N at 100 m."""
from math import ceil, floor

from pyproj import Transformer
from rasterio.transform import from_origin

# Wider area for facilities and roads (see docs/data-gaps.md).
BBOX_WGS84 = (90.95, 24.4, 91.75, 25.2)
CRS = "EPSG:32646"
RES = 100.0


def target_grid():
    """Return (transform, width, height, bounds) of the 100 m grid.

    The grid is the largest UTM rectangle inside BBOX_WGS84, so every cell has source data.
    """
    t = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    west, south, east, north = BBOX_WGS84
    sw, se = t.transform(west, south), t.transform(east, south)
    nw, ne = t.transform(west, north), t.transform(east, north)
    x0, x1 = ceil(max(sw[0], nw[0]) / RES) * RES, floor(min(se[0], ne[0]) / RES) * RES
    y0, y1 = ceil(max(sw[1], se[1]) / RES) * RES, floor(min(nw[1], ne[1]) / RES) * RES
    width, height = int((x1 - x0) / RES), int((y1 - y0) / RES)
    return from_origin(x0, y1, RES, RES), width, height, (x0, y0, x1, y1)
