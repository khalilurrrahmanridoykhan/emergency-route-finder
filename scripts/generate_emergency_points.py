"""Sample synthetic emergency start points for Phase E4.

Points are sampled weighted by population, restricted to passable land-cover cells inside the
grid, and each is assigned one of the four real emergency types (round-robin, an even mix, not
a claim about real incidence). Synthetic only -- see README.

Run: .venv/bin/python scripts/generate_emergency_points.py
Writes data/interim/accessmod/e4_points.csv (id, lon, lat, x, y, emergency_id).
"""
import csv
from pathlib import Path

import numpy as np
import rasterio
from prepare_accessmod_inputs import impassable_classes
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
N_POINTS = 40
SEED = 20260922  # today's date at the time this was written; fixed so the sample is reproducible
# The strict district-only snakebite case is a sensitivity variant (Phase E3/E7), not a route type.
EMERGENCIES = ["childbirth_complication", "snakebite", "injury_drowning", "minor_illness"]


def main():
    with rasterio.open(IN / "population.tif") as src:
        pop, transform = src.read(1), src.transform
    with rasterio.open(IN / "landcover_merged_dry.tif") as src:
        lc = src.read(1)
    passable = ~np.isin(lc, list(impassable_classes()))
    weights = np.where(passable, pop, 0.0).astype("float64")
    rows, cols = np.nonzero(weights > 0)
    probs = weights[rows, cols]
    probs /= probs.sum()

    rng = np.random.default_rng(SEED)
    chosen = rng.choice(len(rows), size=N_POINTS, replace=False, p=probs)
    to_wgs84 = Transformer.from_crs("EPSG:32646", "EPSG:4326", always_xy=True)

    out = IN / "e4_points.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "lon", "lat", "x", "y", "population_at_cell", "emergency_id"])
        for i, idx in enumerate(chosen):
            row, col = rows[idx], cols[idx]
            x, y = rasterio.transform.xy(transform, row, col)
            lon, lat = to_wgs84.transform(x, y)
            emergency = EMERGENCIES[i % len(EMERGENCIES)]
            row_out = [i + 1, round(lon, 5), round(lat, 5), x, y, round(float(pop[row, col]), 1), emergency]
            writer.writerow(row_out)
    print(f"wrote {N_POINTS} points to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
