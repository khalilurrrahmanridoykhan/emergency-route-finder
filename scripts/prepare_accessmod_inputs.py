"""Build AccessMod-ready inputs from data/cache/ into data/interim/accessmod/.

All rasters share one grid (EPSG:32646, 100 m, see grid.py). Roads are burnt into the
land-cover raster (classes 201-208), which is what AccessMod calls the merged land cover.
Run: .venv/bin/python scripts/prepare_accessmod_inputs.py
"""
import csv
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from grid import BBOX_WGS84, CRS, RES, target_grid
from rasterio.features import rasterize
from rasterio.warp import Resampling, reproject
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "data" / "interim" / "accessmod"

# OSM highway value -> AccessMod road class (config/speeds.csv). Listed lowest priority first,
# so higher-class roads overwrite lower ones where they share a cell.
ROAD_CLASSES = [
    (208, ["path", "footway", "pedestrian", "steps", "cycleway", "bridleway"]),
    (207, ["track"]),
    (206, ["service"]),
    (205, ["residential", "living_street"]),
    (204, ["unclassified"]),
    (203, ["tertiary", "tertiary_link"]),
    (202, ["secondary", "secondary_link"]),
    (201, ["primary", "primary_link", "trunk", "trunk_link", "motorway", "motorway_link"]),
]
FACILITY_KINDS = {"hospital", "clinic"}
DEDUP_METRES = 150


def write_raster(path, array, transform, dtype, nodata=None):
    profile = {
        "driver": "GTiff", "height": array.shape[0], "width": array.shape[1], "count": 1,
        "dtype": dtype, "crs": CRS, "transform": transform, "nodata": nodata, "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array.astype(dtype), 1)


def warp(src_path, dst_shape, dst_transform, resampling, dtype, window_bounds=None):
    with rasterio.open(src_path) as src:
        dst = np.zeros(dst_shape, dtype=dtype)
        if window_bounds:
            win = src.window(*window_bounds).round_offsets().round_lengths()
            data = src.read(1, window=win, masked=True).filled(0)
            src_transform = src.window_transform(win)
        else:
            data, src_transform = src.read(1), src.transform
        reproject(
            data, dst, src_transform=src_transform, src_crs=src.crs,
            dst_transform=dst_transform, dst_crs=CRS, resampling=resampling,
        )
    return dst, data


def roads_gdf():
    ways = json.loads((CACHE / "osm_roads_wide.json").read_text())["elements"]
    lookup = {value: code for code, values in ROAD_CLASSES for value in values}
    rows = []
    for way in ways:
        code = lookup.get(way.get("tags", {}).get("highway"))
        pts = [(p["lon"], p["lat"]) for p in way.get("geometry", [])]
        if code and len(pts) > 1:
            rows.append({"osm_id": way["id"], "Class": code, "geometry": LineString(pts)})
    return gpd.GeoDataFrame(rows, crs="EPSG:4326").to_crs(CRS)


def facilities_gdf():
    src = gpd.read_file(ROOT / "data" / "raw" / "health_facilities_wide_osm_2026-09-20.geojson").to_crs(CRS)
    kind = src["amenity"].where(src["amenity"].isin(FACILITY_KINDS), src.get("healthcare"))
    src = src[kind.isin(FACILITY_KINDS | {"centre"})].copy()
    src["named"] = src["name"].notna()
    src = src.sort_values("named", ascending=False)  # keep the named node of a duplicate pair
    keep = []
    for idx, row in src.iterrows():
        if all(row.geometry.distance(src.loc[k].geometry) > DEDUP_METRES for k in keep):
            keep.append(idx)
    out = src.loc[keep].copy()
    out["name_orig"] = out["name"].fillna("")
    out["name"] = [
        n if n.isascii() and n else f"OSM {i} ({'bangla name' if n else 'unnamed'})"
        for n, i in zip(out["name_orig"], out["osm_id"])
    ]
    out["osm_id"] = out["osm_id"].astype(str)
    out["amenity"] = out["amenity"].fillna(out["healthcare"])
    return out[["name", "osm_id", "amenity", "name_orig", "geometry"]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    transform, width, height, bounds = target_grid()
    shape = (height, width)
    summary = {"grid": {"crs": CRS, "res_m": RES, "width": width, "height": height, "bounds": bounds}}

    dem, _ = warp(CACHE / "dem_wide_4326.tif", shape, transform, Resampling.bilinear, "float32")
    write_raster(OUT / "dem.tif", dem, transform, "float32")
    summary["dem_m"] = {"min": float(dem.min()), "max": float(dem.max())}

    lc, _ = warp(CACHE / "worldcover_wide_4326.tif", shape, transform, Resampling.mode, "uint16")
    roads = roads_gdf()
    shapes = [
        (geom, code) for code, _ in ROAD_CLASSES for geom in roads.loc[roads["Class"] == code].geometry
    ]
    lc = rasterize(shapes, out=lc, transform=transform, all_touched=True)
    write_raster(OUT / "landcover_merged.tif", lc, transform, "uint16")
    classes, counts = np.unique(lc, return_counts=True)
    summary["landcover_classes"] = {int(c): int(n) for c, n in zip(classes, counts)}
    known = {int(r["class"]) for r in csv.DictReader(open(ROOT / "config" / "speeds.csv"))}
    missing = sorted(set(summary["landcover_classes"]) - known)
    if missing:
        raise SystemExit(f"classes without a speed row in config/speeds.csv: {missing}")
    summary["road_segments"] = {int(k): int(v) for k, v in roads["Class"].value_counts().items()}

    pop, src_pop = warp(
        CACHE / "bgd_ppp_2020_constrained.tif", shape, transform, Resampling.sum, "float32", BBOX_WGS84
    )
    write_raster(OUT / "population.tif", pop, transform, "float32")
    summary["population"] = {"source_window_sum": float(src_pop.sum()), "grid_sum": float(pop.sum())}

    fac = facilities_gdf()
    fac.to_file(OUT / "facilities.shp", encoding="UTF-8")
    summary["facilities"] = len(fac)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
