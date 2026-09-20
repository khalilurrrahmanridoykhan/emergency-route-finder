"""Build AccessMod-ready inputs from data/cache/ into data/interim/accessmod/.

All rasters share one grid (EPSG:32646, 100 m, see grid.py). Roads are burnt into the
land-cover raster (classes 201-208), which is what AccessMod calls the merged land cover.
Run: .venv/bin/python scripts/prepare_accessmod_inputs.py
"""
import argparse
import csv
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from grid import BBOX_WGS84, CRS, RES, target_grid
from rasterio.features import rasterize, shapes
from rasterio.warp import Resampling, reproject
from shapely.geometry import LineString
from shapely.geometry import shape as to_shape

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
FLOOD_CLASS = 301
FLOOD_CELL_SHARE = 0.5  # a 100 m land cell counts as flooded if half of its 20 m pixels are
FLOOD_ROAD_MIN_M = 30  # ignore slivers of flooded road shorter than this
FLOOD_RES = 20
DEDUP_METRES = 150
SNAP_LIMIT_CELLS = 10  # move a facility on an impassable cell at most this far (1 km at 100 m)


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


def bangladesh_polygon():
    return gpd.read_file(CACHE / "bgd_adm0.geojson").to_crs(CRS).union_all()


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


def impassable_classes():
    """Classes with speed 0 in every season they apply to, plus 0 (no data)."""
    with open(ROOT / "config" / "speeds.csv", newline="") as f:
        return {0} | {int(r["class"]) for r in csv.DictReader(f) if float(r["speed_kmh"]) == 0}


def snap_to_passable(fac, lc, transform):
    """Move facilities that sit on an impassable cell to the nearest passable cell centre."""
    blocked = np.isin(lc, list(impassable_classes()))
    snapped = []
    for point in fac.geometry:
        row, col = rasterio.transform.rowcol(transform, point.x, point.y)
        if not blocked[row, col]:
            snapped.append((point, 0.0))
            continue
        best = None
        for dr in range(-SNAP_LIMIT_CELLS, SNAP_LIMIT_CELLS + 1):
            for dc in range(-SNAP_LIMIT_CELLS, SNAP_LIMIT_CELLS + 1):
                r, c = row + dr, col + dc
                if 0 <= r < lc.shape[0] and 0 <= c < lc.shape[1] and not blocked[r, c]:
                    dist = (dr * dr + dc * dc) ** 0.5 * RES
                    if best is None or dist < best[0]:
                        best = (dist, r, c)
        if best is None:
            snapped.append((None, None))
        else:
            x, y = rasterio.transform.xy(transform, best[1], best[2])
            snapped.append((type(point)(x, y), best[0]))
    fac = fac.copy()
    fac["snap_m"] = [d for _, d in snapped]
    fac["geometry"] = [g for g, _ in snapped]
    return fac[fac.geometry.notna()]


def flood_tag(date):
    return "flood" + date[5:].replace("-", "")


def flood_landcover(dry_lc, roads, date, transform):
    """Return (flood land cover, stats). Flooded land and submerged road pieces become class 301."""
    with rasterio.open(ROOT / "data" / "interim" / "flood" / f"flood_{date}.tif") as src:
        fine, fine_transform = src.read(1).astype(bool), src.transform
    k = int(RES / FLOOD_RES)
    h, w = dry_lc.shape
    share = fine.reshape(h, k, w, k).mean(axis=(1, 3))
    lc = dry_lc.copy()
    is_road = lc >= 201
    land = ~is_road & ~np.isin(lc, (0, 80, 90))
    flooded_land = (share >= FLOOD_CELL_SHARE) & land
    lc[flooded_land] = FLOOD_CLASS

    found = shapes(fine.astype("uint8"), mask=fine, transform=fine_transform)
    polygons = [to_shape(g) for g, v in found if v]
    flood = gpd.GeoDataFrame(geometry=polygons, crs=CRS)
    pieces = gpd.overlay(roads[["geometry"]], flood, how="intersection", keep_geom_type=True)
    pieces = pieces[pieces.length >= FLOOD_ROAD_MIN_M]
    lc = rasterize([(g, FLOOD_CLASS) for g in pieces.geometry], out=lc, transform=transform, all_touched=True)
    stats = {
        "flooded_land_cells": int(flooded_land.sum()),
        "flooded_road_pieces": int(len(pieces)),
        "road_cells_flooded": int(((dry_lc >= 201) & (lc == FLOOD_CLASS)).sum()),
        "road_cells_total": int(is_road.sum()),
    }
    return lc, stats


def facilities_gdf(country):
    src = gpd.read_file(ROOT / "data" / "raw" / "health_facilities_wide_osm_2026-09-20.geojson").to_crs(CRS)
    kind = src["amenity"].where(src["amenity"].isin(FACILITY_KINDS), src.get("healthcare"))
    src = src[kind.isin(FACILITY_KINDS | {"centre"}) & src.within(country)].copy()
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


def inside_grid(fac, bounds):
    x0, y0, x1, y1 = bounds
    in_x = (fac.geometry.x >= x0) & (fac.geometry.x < x1)
    in_y = (fac.geometry.y >= y0) & (fac.geometry.y < y1)
    return fac[in_x & in_y]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flood", nargs="*", default=[], help="flood dates (built by build_flood_extent.py)")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    transform, width, height, bounds = target_grid()
    shape = (height, width)
    summary = {"grid": {"crs": CRS, "res_m": RES, "width": width, "height": height, "bounds": bounds}}

    country = bangladesh_polygon()
    mask = rasterize([(country, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8")
    inside = mask.astype(bool)

    dem, _ = warp(CACHE / "dem_wide_4326.tif", shape, transform, Resampling.bilinear, "float32")
    write_raster(OUT / "dem.tif", dem, transform, "float32")
    summary["dem_m"] = {"min": float(dem.min()), "max": float(dem.max())}

    lc, _ = warp(CACHE / "worldcover_wide_4326.tif", shape, transform, Resampling.mode, "uint16")
    roads = roads_gdf()
    shapes = [
        (geom, code) for code, _ in ROAD_CLASSES for geom in roads.loc[roads["Class"] == code].geometry
    ]
    lc = rasterize(shapes, out=lc, transform=transform, all_touched=True)
    lc[~inside] = 0  # outside Bangladesh: no data, so nothing can be routed across the border
    write_raster(OUT / "landcover_merged_dry.tif", lc, transform, "uint16", nodata=0)
    summary["flood"] = {}
    for date in args.flood:
        flooded, stats = flood_landcover(lc, roads, date, transform)
        flooded[~inside] = 0
        write_raster(OUT / f"landcover_merged_{flood_tag(date)}.tif", flooded, transform, "uint16", nodata=0)
        summary["flood"][date] = stats
    classes, counts = np.unique(lc[inside], return_counts=True)
    summary["landcover_classes"] = {int(c): int(n) for c, n in zip(classes, counts)}
    summary["cells_outside_bangladesh"] = int((~inside).sum())
    known = {int(r["class"]) for r in csv.DictReader(open(ROOT / "config" / "speeds.csv"))}
    missing = sorted(set(summary["landcover_classes"]) - known)
    if missing:
        raise SystemExit(f"classes without a speed row in config/speeds.csv: {missing}")
    summary["road_segments"] = {int(k): int(v) for k, v in roads["Class"].value_counts().items()}

    pop, src_pop = warp(
        CACHE / "bgd_ppp_2020_constrained.tif", shape, transform, Resampling.sum, "float32", BBOX_WGS84
    )
    pop[~inside] = 0
    write_raster(OUT / "population.tif", pop, transform, "float32")
    summary["population"] = {"source_window_sum": float(src_pop.sum()), "grid_sum": float(pop.sum())}

    fac = inside_grid(facilities_gdf(country), bounds)
    before = len(fac)
    fac = snap_to_passable(fac, lc, transform)
    summary["facilities_moved_to_passable_cell"] = int((fac["snap_m"] > 0).sum())
    summary["facilities_dropped_no_passable_cell"] = before - len(fac)
    fac.to_file(OUT / "facilities.shp", encoding="UTF-8")
    summary["facilities"] = len(fac)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
