"""Summarise the Phase E1 dry-season baseline: population coverage and catchments.

Reads the AccessMod exports in data/interim/accessmod_out/ and writes small CSVs to results/
and a map to docs/img/. Run: .venv/bin/python scripts/summarize_e1.py
"""
import glob
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
OUT = ROOT / "data" / "interim" / "accessmod_out"
THRESHOLDS = (30, 60, 120, 240)
NODATA_MINUTES = 65535


def read(path):
    with rasterio.open(path) as src:
        return src.read(1), src.transform


def main():
    season = "dry"
    travel, transform = read(glob.glob(f"{OUT}/accessibility_{season}/raster_travel_time_*/*.GeoTIFF")[0])
    nearest, _ = read(glob.glob(f"{OUT}/accessibility_{season}/raster_cost_allocation_*/*.GeoTIFF")[0])
    pop, _ = read(IN / "population.tif")
    fac = gpd.read_file(IN / "facilities.shp").reset_index(drop=True)
    fac["cat"] = fac.index + 1

    total = float(pop.sum())
    reachable = travel != NODATA_MINUTES
    rows = []
    for limit in THRESHOLDS:
        covered = float(pop[reachable & (travel <= limit)].sum())
        rows.append({"season": season, "within_minutes": limit, "population": round(covered),
                     "share_percent": round(100 * covered / total, 1)})
    unreachable = float(pop[~reachable].sum())
    rows.append({"season": season, "within_minutes": "no_route_within_300", "population": round(unreachable),
                 "share_percent": round(100 * unreachable / total, 2)})
    coverage = pd.DataFrame(rows)
    coverage.to_csv(ROOT / "results" / "e1_coverage_dry.csv", index=False)

    catch = []
    for row in fac.itertuples():
        mask = nearest == row.cat
        if mask.any():
            catch.append({"cat": row.cat, "name": row.name, "amenity": row.amenity,
                          "cells": int(mask.sum()), "population": round(float(pop[mask].sum())),
                          "mean_minutes": round(float(travel[mask & reachable].mean()), 1)})
    pd.DataFrame(catch).sort_values("population", ascending=False).to_csv(
        ROOT / "results" / "e1_catchments_dry.csv", index=False)

    for path in glob.glob(f"{OUT}/referral_{season}/table_referral_nearest_by_time_*/*.xlsx"):
        pd.read_excel(path).to_csv(ROOT / "results" / "e1_referral_nearest_by_time_dry.csv", index=False)

    shown = np.ma.masked_where(~reachable, np.minimum(travel, 240))
    x0, y1 = transform.c, transform.f
    extent = (x0, x0 + travel.shape[1] * transform.a, y1 + travel.shape[0] * transform.e, y1)
    fig, ax = plt.subplots(figsize=(7, 8))
    im = ax.imshow(shown, extent=extent, cmap="viridis_r", vmin=0, vmax=240)
    ax.scatter(fac.geometry.x, fac.geometry.y, s=14, c="white", edgecolors="black", linewidths=0.6)
    ax.set_title("Dry-season travel time to the nearest facility (minutes)")
    ax.set_xlabel("Easting (m, UTM 46N)")
    ax.set_ylabel("Northing (m)")
    fig.colorbar(im, ax=ax, shrink=0.7, label="minutes (capped at 240)")
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "img" / "e1_dry_travel_time.png", dpi=110)

    print(coverage.to_string(index=False))
    print("mean travel time (reachable cells):", round(float(travel[reachable].mean()), 1), "min")
    print("total population on grid:", round(total))
    print("facilities with a catchment:", len(catch), "of", len(fac))


if __name__ == "__main__":
    main()
