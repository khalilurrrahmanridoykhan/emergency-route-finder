"""Map newly flooded land from Sentinel-1 RTC over the analysis grid (20 m, EPSG:32646).

Same method as geohealth-risk-mapping Phase H5: VV backscatter to dB, Otsu threshold from the
"before" scene, water = below threshold, newly flooded = water during but not before, then drop
components under 20,000 m2 (SAR speckle). Scenes come from Microsoft Planetary Computer.
Writes data/interim/flood/flood_<during>.tif and coverage_<during>.tif (1 = both dates observed).
Run: .venv/bin/python scripts/build_flood_extent.py --before 2026-06-19 --during 2026-07-08
"""
import argparse
import json
from pathlib import Path

import numpy as np
import planetary_computer
import rasterio
from grid import BBOX_WGS84, CRS, target_grid
from pystac_client import Client
from rasterio.transform import from_origin
from rasterio.warp import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "interim" / "flood"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
RES = 20.0
MIN_AREA_M2 = 20000


def db_from_power(power):
    power = power.astype("float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        return (10.0 * np.log10(np.where(power > 0, power, np.nan))).astype("float32")


def otsu_threshold(values, n_bins=256):
    finite = values[np.isfinite(values)]
    hist, edges = np.histogram(finite, bins=n_bins)
    centers = (edges[:-1] + edges[1:]) / 2
    below = np.cumsum(hist)
    above = hist.sum() - below
    mean_below = np.cumsum(hist * centers) / np.where(below == 0, 1, below)
    mean_above = (np.sum(hist * centers) - np.cumsum(hist * centers)) / np.where(above == 0, 1, above)
    return float(centers[np.argmax(below * above * (mean_below - mean_above) ** 2)])


def read_vv(date, bounds, shape):
    """Mosaic the VV backscatter (linear power) of all scenes on `date` onto the 20 m grid."""
    catalog = Client.open(STAC, modifier=planetary_computer.sign_inplace)
    search = catalog.search(collections=["sentinel-1-rtc"], bbox=BBOX_WGS84, datetime=f"{date}/{date}")
    items = list(search.items())
    if not items:
        raise SystemExit(f"no Sentinel-1 RTC scenes on {date}")
    mosaic = np.full(shape, np.nan, dtype="float32")
    for item in items:
        with rasterio.open(item.assets["vv"].href) as src:
            window = from_bounds(*bounds, transform=src.transform)
            data = src.read(
                1, window=window, out_shape=shape, boundless=True, fill_value=0,
                resampling=Resampling.average,
            ).astype("float32")
        fill = np.isnan(mosaic) & (data > 0)
        mosaic[fill] = data[fill]
    orbits = sorted({it.properties.get("sat:relative_orbit") for it in items})
    print(f"{date}: {len(items)} scenes, relative orbit {orbits}, valid {np.isfinite(mosaic).mean():.1%}")
    return mosaic, orbits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", default="2026-06-19")
    parser.add_argument("--during", required=True)
    args = parser.parse_args()

    _, _, _, bounds = target_grid()
    width, height = int((bounds[2] - bounds[0]) / RES), int((bounds[3] - bounds[1]) / RES)
    shape = (height, width)
    transform = from_origin(bounds[0], bounds[3], RES, RES)

    before_db = db_from_power(read_vv(args.before, bounds, shape)[0])
    during_db = db_from_power(read_vv(args.during, bounds, shape)[0])
    threshold = otsu_threshold(before_db)
    before_water = np.where(np.isnan(before_db), False, before_db < threshold)
    during_water = np.where(np.isnan(during_db), False, during_db < threshold)
    covered = np.isfinite(before_db) & np.isfinite(during_db)
    flood = during_water & ~before_water & covered

    labels, n = ndimage.label(flood)
    sizes = ndimage.sum(flood, labels, index=np.arange(1, n + 1))
    keep = np.isin(labels, 1 + np.flatnonzero(sizes * RES * RES >= MIN_AREA_M2))
    flood = keep

    OUT.mkdir(parents=True, exist_ok=True)
    profile = {"driver": "GTiff", "height": height, "width": width, "count": 1, "dtype": "uint8",
               "crs": CRS, "transform": transform, "compress": "deflate"}
    for name, array in ((f"flood_{args.during}.tif", flood), (f"coverage_{args.during}.tif", covered)):
        with rasterio.open(OUT / name, "w", **profile) as dst:
            dst.write(array.astype("uint8"), 1)
    summary = {
        "before": args.before, "during": args.during, "otsu_threshold_db": round(threshold, 2),
        "covered_share_of_grid": round(float(covered.mean()), 4),
        "newly_flooded_share_of_covered": round(float(flood.sum() / covered.sum()), 4),
        "flooded_km2": round(float(flood.sum() * RES * RES / 1e6), 1),
        "components_kept": int(len(np.unique(labels[keep])) - (1 if 0 in np.unique(labels[keep]) else 0)),
    }
    (OUT / f"summary_{args.during}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
