"""Cross-check dry-season primary routes against OSRM road routing (Phase E4).

Compares AccessMod's anisotropic, off-road-capable route against a road-only driving route from
OSRM (bangladesh-latest.osrm, built in the sibling facility-access-equity repo; no code coupling,
just reading its already-built OSRM files). Needs a local OSRM server:

  cd ../facility-access-equity && osrm-routed --algorithm mld --ip 127.0.0.1 --port 5555 \
    --max-table-size 500 data/raw/bangladesh-latest.osrm &

Run: .venv/bin/python scripts/cross_check_osrm.py
Writes results/e4_osrm_cross_check.csv.
"""
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from pyproj import Transformer
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
PATHS = ROOT / "data" / "interim" / "accessmod_out" / "e4_paths"
OSRM = "http://127.0.0.1:5555"


def osrm_route(lon1, lat1, lon2, lat2):
    url = f"{OSRM}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok":
        return None
    route = data["routes"][0]
    return route["duration"] / 60.0, route["distance"] / 1000.0, route["geometry"]["coordinates"]


def path_overlap_km(accessmod_coords_utm, osrm_coords_wgs84, to_utm):
    """Share of the AccessMod path within 100 m of the OSRM route (a coarse, honest overlap metric)."""
    osrm_utm = [to_utm.transform(lon, lat) for lon, lat in osrm_coords_wgs84]
    osrm_line = LineString(osrm_utm)
    am_line = LineString(accessmod_coords_utm)
    if am_line.length == 0:
        return 0.0
    near = am_line.intersection(osrm_line.buffer(100))
    return near.length / am_line.length


def main():
    points = pd.read_csv(IN / "e4_points.csv")
    results = pd.read_csv(PATHS / "points_result.csv")
    fac = gpd.read_file(IN / "facilities.shp").reset_index(drop=True)
    fac["cat"] = fac.index + 1
    fac_wgs84 = fac.to_crs(4326)
    to_utm = Transformer.from_crs(4326, "EPSG:32646", always_xy=True)

    dry_primary = results[(results.season == "dry") & (results.kind == "primary") & results.path_file.notna()]
    rows = []
    for _, r in dry_primary.iterrows():
        point = points[points.id == r.id].iloc[0]
        facility = fac_wgs84[fac_wgs84.cat == r.facility_cat]
        if facility.empty:
            continue
        flon, flat = facility.iloc[0].geometry.x, facility.iloc[0].geometry.y
        osrm = osrm_route(point.lon, point.lat, flon, flat)
        path_geojson = PATHS / str(r.path_file)
        am_coords = json.loads(path_geojson.read_text())["features"][0]["geometry"]["coordinates"]
        row = {
            "id": r.id, "emergency": point.emergency_id, "facility_cat": r.facility_cat,
            "facility_name": facility.iloc[0]["name"], "accessmod_minutes": r.minutes,
        }
        if osrm is None:
            row["osrm_minutes"] = None
            row["note"] = "OSRM could not route (point or facility off the road network)"
        else:
            duration, distance_km, coords = osrm
            row["osrm_minutes"] = round(duration, 1)
            row["osrm_distance_km"] = round(distance_km, 1)
            row["overlap_share"] = round(path_overlap_km(am_coords, coords, to_utm), 2)
            row["note"] = ""
        rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "e4_osrm_cross_check.csv", index=False)
    got_osrm = out[out.osrm_minutes.notna()]
    print(f"{len(out)} dry primary routes checked, {len(got_osrm)} OSRM could route")
    if len(got_osrm):
        diff = got_osrm.accessmod_minutes - got_osrm.osrm_minutes
        print(f"AccessMod minus OSRM minutes: median {diff.median():.1f}, mean {diff.mean():.1f}")
        print(f"median path overlap within 100m: {got_osrm.overlap_share.median():.2f}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
