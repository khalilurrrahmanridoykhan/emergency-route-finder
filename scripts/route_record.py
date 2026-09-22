"""Build one emergency route record from AccessMod outputs. Shared by the E4 batch summary
(scripts/summarize_e4.py) and the E5 on-demand route finder (scripts/route.py), so a query
made through either path is assembled the same way.
"""
import csv
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from e4_warnings import build_warnings
from shapely.geometry import LineString, mapping

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
FLOOD_CLASS = 301


def targets():
    with open(ROOT / "config" / "emergencies.csv", newline="", encoding="utf-8") as f:
        return {r["emergency_id"]: int(r["target_minutes"]) for r in csv.DictReader(f)}


def speed_modes():
    with open(ROOT / "config" / "speeds.csv", newline="", encoding="utf-8") as f:
        return {int(r["class"]): r["mode"] for r in csv.DictReader(f)}


def _path_coords(paths_dir, path_file):
    return json.loads((paths_dir / path_file).read_text())["features"][0]["geometry"]["coordinates"]


def path_modes(paths_dir, path_file, lc_array, transform):
    """The distinct travel modes a path crosses, in a stable order, from the season's land cover."""
    if not path_file:
        return []
    coords = _path_coords(paths_dir, path_file)
    modes, classes = speed_modes(), set()
    for x, y in coords:
        row, col = rasterio.transform.rowcol(transform, x, y)
        if 0 <= row < lc_array.shape[0] and 0 <= col < lc_array.shape[1]:
            classes.add(int(lc_array[row, col]))
    labels = set()
    for c in classes:
        mode = modes.get(c)
        boat = mode == "MOTORIZED" and c == FLOOD_CLASS
        if mode:
            labels.add("boat/wading" if boat else mode)
    order = ["WALKING", "BICYCLING", "MOTORIZED", "boat/wading"]
    return [label for label in order if label in labels]


def path_crosses_flood(paths_dir, path_file, flood_lc, transform):
    if not path_file:
        return False
    coords = _path_coords(paths_dir, path_file)
    for x, y in coords:
        row, col = rasterio.transform.rowcol(transform, x, y)
        in_bounds = 0 <= row < flood_lc.shape[0] and 0 <= col < flood_lc.shape[1]
        if in_bounds and flood_lc[row, col] == FLOOD_CLASS:
            return True
    return False


def facility_lookup():
    fac = gpd.read_file(IN / "facilities.shp").reset_index(drop=True)
    fac["cat"] = fac.index + 1
    return fac.set_index("cat")


def build_route_record(pid, point, res, fac, land_cover_by_season, target_minutes, paths_dir):
    """One point's full record: primary/backup facility, time, mode and warnings for each season
    in `land_cover_by_season` (season -> (array, transform)). `res` is the points_result.csv
    frame (id, season, kind, facility_cat, minutes, path_file) for this point, from
    scripts/accessmod/e4_paths.R. Returns (record dict, list of GeoJSON path features).
    """
    emergency = point["emergency_id"]

    def get(season, kind, col):
        row = res[(res.id == pid) & (res.season == season) & (res.kind == kind)]
        if row.empty:
            return None
        val = row.iloc[0][col]
        return None if pd.isna(val) else val

    record = {"id": pid, "emergency": emergency, "lon": point["lon"], "lat": point["lat"],
              "target_minutes": target_minutes[emergency]}
    features = []
    for season, (lc, transform) in land_cover_by_season.items():
        for kind in ("primary", "backup"):
            cat = get(season, kind, "facility_cat")
            minutes = get(season, kind, "minutes")
            path_file = get(season, kind, "path_file")
            name = fac.loc[int(cat), "name"] if cat is not None else None
            modes = path_modes(paths_dir, path_file, lc, transform)
            prefix = f"{season}_{kind}"
            record[f"{prefix}_facility_cat"] = cat
            record[f"{prefix}_facility_name"] = name
            record[f"{prefix}_minutes"] = minutes
            record[f"{prefix}_mode"] = ", ".join(modes) if modes else None
            record[f"{prefix}_within_target"] = minutes is not None and minutes <= target_minutes[emergency]
            if path_file and isinstance(path_file, str) and path_file != "nan":
                coords = _path_coords(paths_dir, path_file)
                features.append({
                    "type": "Feature", "geometry": mapping(LineString(coords)),
                    "properties": {
                        "point_id": int(pid), "emergency": emergency, "season": season, "kind": kind,
                        "facility_cat": int(cat), "facility_name": name, "minutes": float(minutes),
                    },
                })

    flood_lc, flood_transform = land_cover_by_season.get("flood0708", (None, None))
    crosses = False
    if flood_lc is not None:
        flood_primary_path = get("flood0708", "primary", "path_file")
        crosses = path_crosses_flood(paths_dir, flood_primary_path, flood_lc, flood_transform)
    record["warnings"] = "; ".join(build_warnings(
        record.get("dry_primary_minutes"), record.get("flood0708_primary_minutes"),
        record.get("dry_primary_facility_cat"), record.get("flood0708_primary_facility_cat"),
        record.get("dry_backup_minutes"), target_minutes[emergency], crosses,
    ))
    return record, features
