"""Phase E5: route(lon, lat, emergency) -> the full dry-and-flood record for one arbitrary point.

Right facility, travel time, path, mode, backup facility and warnings, for both the dry season and
the flood (2026-07-08). Built the same way as the Phase E4 batch (scripts/route_record.py), but for
one on-demand point instead of the fixed 40-point sample: a cheap rasterio pre-check on the
already-exported Phase E3 rasters decides whether a route exists at all (no Docker needed for a
clear "no route"), and Docker is only started to trace paths when at least one season has one.

Needs Docker running and the AccessMod project already imported (`make e1` at least once, and
`make e3` for the per-emergency rasters this depends on).

CLI:    .venv/bin/python scripts/route.py --lon 91.30 --lat 24.75 --emergency snakebite
Import: from route import route; route(91.30, 24.75, "snakebite")
"""
import argparse
import csv
import glob
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import rasterio
from grid import CRS, target_grid
from pyproj import Transformer
from route_record import IN, build_route_record, facility_lookup, targets

ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = ROOT / "data" / "interim" / "accessmod_out" / "route_query"
IMAGE = "fredmoser/accessmod:5.9.1"
VOLUME = "am5_e1_db"
SEASONS = ("dry", "flood0708")
NULL = 65535
RESULT_COLUMNS = ["id", "season", "kind", "facility_cat", "minutes", "path_file"]


class OutsideAreaError(ValueError):
    """The point falls outside the analysis grid (see grid.BBOX_WGS84)."""


class UnknownEmergencyError(ValueError):
    """The emergency id is not in config/emergencies.csv."""


def _to_utm(lon, lat):
    return Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform(lon, lat)


def _check_inside_area(x, y):
    _, _, _, (x0, y0, x1, y1) = target_grid()
    if not (x0 <= x < x1 and y0 <= y < y1):
        raise OutsideAreaError(
            f"({x:.0f}, {y:.0f}) in EPSG:32646 falls outside the analysis grid {x0, y0, x1, y1}"
        )


def _travel_time_raster(season, emergency):
    pattern = str(ROOT / "data" / "interim" / "accessmod_out" / f"accessibility_{season}_{emergency}"
                  / "raster_travel_time_*" / "*.GeoTIFF")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(
            f"no travel-time raster for {season}/{emergency}; run `make e3` (or `make e2` for dry only) first"
        )
    return matches[0]


def _has_a_route(x, y, emergency):
    """True for a season if the already-published E3 raster has a value (not null) at this point."""
    found = {}
    for season in SEASONS:
        with rasterio.open(_travel_time_raster(season, emergency)) as src:
            value = next(src.sample([(x, y)]))[0]
        found[season] = value != NULL and value == value  # also excludes NaN, just in case
    return found


def _ensure_qualifying_cats():
    path = IN / "e4_qualifying_cats.json"
    if not path.exists():
        script = ROOT / "scripts" / "build_e4_tasks.py"
        subprocess.run([sys.executable, str(script)], check=True)
    return path


def _run_docker(points_csv, cats_json, out_dir):
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{VOLUME}:/data/dbgrass",
        "-v", f"{ROOT / 'scripts' / 'accessmod'}:/scripts:ro",
        "-v", f"{IN}:/data/shared/in:ro",
        "-v", f"{out_dir}:/data/shared/out",
        IMAGE, "Rscript", "/scripts/e4_paths.R",
        f"/data/shared/in/{points_csv.name}", "/data/shared/in/e4_qualifying_cats.json", "/data/shared/out",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or "E4 DONE" not in result.stdout:
        raise RuntimeError(f"AccessMod path tracing failed:\n{result.stdout}\n{result.stderr}")


def route(lon, lat, emergency, keep_query_dir=False):
    """Return the full route record for one point: right facility, time, path, mode, backup,
    warnings, for the dry season and the flood (2026-07-08). Raises OutsideAreaError or
    UnknownEmergencyError for a bad input; raises RuntimeError if Docker or AccessMod fails.
    """
    target = targets()
    if emergency not in target:
        raise UnknownEmergencyError(f"'{emergency}' is not in config/emergencies.csv: {sorted(target)}")
    x, y = _to_utm(lon, lat)
    _check_inside_area(x, y)

    has_route = _has_a_route(x, y, emergency)
    fac = facility_lookup()
    with rasterio.open(IN / "landcover_merged_dry.tif") as src:
        dry_lc, transform = src.read(1), src.transform
    with rasterio.open(IN / "landcover_merged_flood0708.tif") as src:
        flood_lc = src.read(1)
    land_cover = {"dry": (dry_lc, transform), "flood0708": (flood_lc, transform)}
    point = pd.Series({"emergency_id": emergency, "lon": lon, "lat": lat})

    if not any(has_route.values()):
        empty = pd.DataFrame(columns=RESULT_COLUMNS)
        record, _ = build_route_record(1, point, empty, fac, land_cover, target, OUT_ROOT)
        return record

    _ensure_qualifying_cats()
    out_dir = OUT_ROOT
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    points_csv = IN / "route_query_point.csv"
    with open(points_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "lon", "lat", "x", "y", "population_at_cell", "emergency_id"])
        writer.writerow([1, lon, lat, x, y, "", emergency])

    _run_docker(points_csv, IN / "e4_qualifying_cats.json", out_dir)
    res = pd.read_csv(out_dir / "points_result.csv")
    record, _ = build_route_record(1, point, res, fac, land_cover, target, out_dir)
    if not keep_query_dir:
        points_csv.unlink(missing_ok=True)
    return record


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--emergency", required=True,
                         help="childbirth_complication, snakebite, injury_drowning, minor_illness, "
                              "or snakebite_hospital_only")
    parser.add_argument("--json", type=Path, help="write the record here instead of stdout")
    parser.add_argument("--keep", action="store_true", help="keep the query's temp files for inspection")
    args = parser.parse_args()

    try:
        record = route(args.lon, args.lat, args.emergency, keep_query_dir=args.keep)
    except (OutsideAreaError, UnknownEmergencyError, FileNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    text = json.dumps(record, indent=2, default=str)
    if args.json:
        args.json.write_text(text + "\n")
        print(f"wrote {args.json}")
    else:
        print(text)


if __name__ == "__main__":
    main()
