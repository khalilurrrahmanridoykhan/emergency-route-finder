"""Build a regular grid of query points for the Phase E6 web map.

A static site cannot run Docker, so it serves a precomputed set of points instead of an arbitrary
click. This lays a regular grid over the analysis area at GRID_SPACING_M and keeps the cells that
are populated and passable (same filter as the emergency-point sampler in Phase E4). A user's
click snaps to the nearest of these points client-side.

Run: .venv/bin/python scripts/generate_grid_points.py
Writes data/interim/accessmod/e6_grid_points.csv (grid_id, lon, lat, x, y, population_at_cell).
"""
from pathlib import Path

import numpy as np
import rasterio
from prepare_accessmod_inputs import impassable_classes
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
GRID_SPACING_M = 3000
CELL_M = 100


def main():
    with rasterio.open(IN / "population.tif") as src:
        pop, transform = src.read(1), src.transform
    with rasterio.open(IN / "landcover_merged_dry.tif") as src:
        lc = src.read(1)
    passable = ~np.isin(lc, list(impassable_classes()))
    eligible = (pop > 0) & passable

    step = GRID_SPACING_M // CELL_M
    to_wgs84 = Transformer.from_crs("EPSG:32646", "EPSG:4326", always_xy=True)

    rows = []
    for row in range(0, pop.shape[0], step):
        for col in range(0, pop.shape[1], step):
            if not eligible[row, col]:
                continue
            x, y = rasterio.transform.xy(transform, row, col)
            lon, lat = to_wgs84.transform(x, y)
            rows.append((len(rows) + 1, round(lon, 5), round(lat, 5), x, y, round(float(pop[row, col]), 1)))

    out = IN / "e6_grid_points.csv"
    with open(out, "w") as f:
        f.write("grid_id,lon,lat,x,y,population_at_cell\n")
        for r in rows:
            f.write(",".join(str(v) for v in r) + "\n")
    print(f"wrote {len(rows)} grid points ({GRID_SPACING_M} m spacing) to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
