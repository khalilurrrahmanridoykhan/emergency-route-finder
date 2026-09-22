"""Build the Phase E6 web map data: one GeoJSON per emergency type (dry and flood0708 routes for
every grid point), plus a small points file for client-side click-snapping.

Run (after scripts/run_e6.sh): .venv/bin/python scripts/summarize_e6.py
Writes docs/data/e6_points.geojson and docs/data/e6_routes_<emergency>.geojson.
"""
import json
from pathlib import Path

import pandas as pd
import rasterio
from pyproj import Transformer
from route_record import IN, facility_lookup, path_crosses_flood, path_modes, targets
from shapely.geometry import LineString, mapping

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "interim" / "accessmod_out" / "e6_grid"
DOCS_DATA = ROOT / "docs" / "data"
EMERGENCIES = ["childbirth_complication", "snakebite", "injury_drowning", "minor_illness"]
FLOOD_ADD_MINUTES_WARNING = 15


SIMPLIFY_TOLERANCE_M = 15  # Douglas-Peucker tolerance on the UTM geometry, well under a map pixel


def to_wgs84_coords(paths_dir, path_file):
    coords = json.loads((paths_dir / path_file).read_text())["features"][0]["geometry"]["coordinates"]
    if len(coords) > 2:
        simplified = LineString(coords).simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=False)
        coords = list(mapping(simplified)["coordinates"])
    to_wgs84 = Transformer.from_crs("EPSG:32646", "EPSG:4326", always_xy=True)
    return [list(to_wgs84.transform(x, y)) for x, y in coords]


def main():
    DOCS_DATA.mkdir(exist_ok=True)
    grid = pd.read_csv(IN / "e6_grid_points.csv")
    tasks = pd.read_csv(IN / "e6_tasks.csv")
    res = pd.read_csv(OUT / "tasks_result.csv")
    fac = facility_lookup()
    target = targets()

    with rasterio.open(IN / "landcover_merged_dry.tif") as src:
        dry_lc, transform = src.read(1), src.transform
    with rasterio.open(IN / "landcover_merged_flood0708.tif") as src:
        flood_lc = src.read(1)
    land_cover = {"dry": dry_lc, "flood0708": flood_lc}

    joined = tasks.merge(res, on=["id", "grid_id"], how="left").merge(
        grid[["grid_id", "lon", "lat"]], on="grid_id"
    )

    points_geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [row.lon, row.lat]},
             "properties": {"grid_id": int(row.grid_id)}}
            for row in grid.itertuples()
        ],
    }
    (DOCS_DATA / "e6_points.geojson").write_text(json.dumps(points_geojson) + "\n")

    counts = {}
    for emergency in EMERGENCIES:
        sub = joined[joined.emergency_id == emergency]
        by_grid = {}
        for row in sub.itertuples():
            by_grid.setdefault(row.grid_id, {})[row.season] = row

        features = []
        for grid_id, seasons in by_grid.items():
            dry_row = seasons.get("dry")
            if dry_row is None:
                continue
            lon, lat = dry_row.lon, dry_row.lat
            for season in ("dry", "flood0708"):
                row = seasons.get(season)
                if row is None or pd.isna(row.minutes):
                    continue
                path_file = row.path_file
                if not isinstance(path_file, str) or not path_file:
                    continue
                modes = path_modes(OUT, path_file, land_cover[season], transform)
                crosses = season == "flood0708" and path_crosses_flood(OUT, path_file, flood_lc, transform)
                cat = int(row.facility_cat)
                name = fac.loc[cat, "name"]
                minutes = float(row.minutes)
                within_target = minutes <= target[emergency]
                extra = None
                if season == "flood0708" and dry_row is not None and not pd.isna(dry_row.minutes):
                    extra = minutes - float(dry_row.minutes)
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": to_wgs84_coords(OUT, path_file)},
                    "properties": {
                        "grid_id": int(grid_id), "lon": lon, "lat": lat, "season": season,
                        "facility_cat": cat, "facility_name": name, "minutes": round(minutes, 1),
                        "mode": ", ".join(modes), "target_minutes": target[emergency],
                        "within_target": within_target,
                        "crosses_flood": bool(crosses),
                        "flood_adds_minutes": round(extra, 1) if extra is not None else None,
                    },
                })
        out_path = DOCS_DATA / f"e6_routes_{emergency}.geojson"
        out_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}) + "\n")
        counts[emergency] = len(features)
        print(f"{emergency}: {len(features)} route features -> {out_path.relative_to(ROOT)} "
              f"({out_path.stat().st_size / 1024:.0f} KB)")

    print(f"grid points: {len(grid)}")
    print(f"total route features: {sum(counts.values())}")


if __name__ == "__main__":
    main()
