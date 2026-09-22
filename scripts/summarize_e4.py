"""Build the final route record per synthetic point (Phase E4): right facility, time, path, mode,
backup, warning -- for dry and flood0708. Reads the R script's points_result.csv and path GeoJSON
files, and config/speeds.csv for target times and travel mode per path segment.

Run (after scripts/run_e4.sh): .venv/bin/python scripts/summarize_e4.py
Writes results/e4_routes.csv, docs/data/e4_routes.geojson, docs/img/e4_routes.png.
"""
import csv
import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from e4_warnings import build_warnings  # noqa: E402
from shapely.geometry import LineString, mapping  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
PATHS = ROOT / "data" / "interim" / "accessmod_out" / "e4_paths"
MODE_BY_CLASS = {}
FLOOD_CLASS = 301
NULL = 65535


def targets():
    with open(ROOT / "config" / "emergencies.csv", newline="", encoding="utf-8") as f:
        return {r["emergency_id"]: int(r["target_minutes"]) for r in csv.DictReader(f)}


def speed_modes():
    with open(ROOT / "config" / "speeds.csv", newline="", encoding="utf-8") as f:
        return {int(r["class"]): r["mode"] for r in csv.DictReader(f)}


def path_modes(path_file, lc_array, transform):
    """The distinct travel modes a path crosses, in a stable order, from the season's land cover."""
    if not path_file:
        return []
    coords = json.loads((PATHS / path_file).read_text())["features"][0]["geometry"]["coordinates"]
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


def path_crosses_flood(path_file, flood_lc, transform):
    if not path_file:
        return False
    coords = json.loads((PATHS / path_file).read_text())["features"][0]["geometry"]["coordinates"]
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


def main():
    points = pd.read_csv(IN / "e4_points.csv").set_index("id")
    res = pd.read_csv(PATHS / "points_result.csv")
    fac = facility_lookup()
    target = targets()

    with rasterio.open(IN / "landcover_merged_dry.tif") as src:
        dry_lc, transform = src.read(1), src.transform
    with rasterio.open(IN / "landcover_merged_flood0708.tif") as src:
        flood_lc = src.read(1)

    def get(pid, season, kind, col):
        row = res[(res.id == pid) & (res.season == season) & (res.kind == kind)]
        if row.empty:
            return None
        val = row.iloc[0][col]
        return None if pd.isna(val) else val

    rows, features = [], []
    for pid, point in points.iterrows():
        emergency = point["emergency_id"]
        record = {"id": pid, "emergency": emergency, "lon": point["lon"], "lat": point["lat"],
                  "target_minutes": target[emergency]}
        for season, lc in (("dry", dry_lc), ("flood0708", flood_lc)):
            for kind in ("primary", "backup"):
                cat = get(pid, season, kind, "facility_cat")
                minutes = get(pid, season, kind, "minutes")
                path_file = get(pid, season, kind, "path_file")
                name = fac.loc[int(cat), "name"] if cat is not None else None
                modes = path_modes(path_file, lc, transform)
                prefix = f"{season}_{kind}"
                record[f"{prefix}_facility_cat"] = cat
                record[f"{prefix}_facility_name"] = name
                record[f"{prefix}_minutes"] = minutes
                record[f"{prefix}_mode"] = ", ".join(modes) if modes else None
                record[f"{prefix}_within_target"] = (
                    minutes is not None and minutes <= target[emergency]
                )
                if path_file and isinstance(path_file, str) and path_file != "nan":
                    geom = json.loads((PATHS / path_file).read_text())["features"][0]["geometry"]
                    coords = geom["coordinates"]
                    features.append({
                        "type": "Feature", "geometry": mapping(LineString(coords)),
                        "properties": {
                            "point_id": int(pid), "emergency": emergency, "season": season, "kind": kind,
                            "facility_cat": int(cat), "facility_name": name, "minutes": float(minutes),
                        },
                    })
        crosses = path_crosses_flood(get(pid, "flood0708", "primary", "path_file"), flood_lc, transform)
        record["warnings"] = "; ".join(build_warnings(
            record["dry_primary_minutes"], record["flood0708_primary_minutes"],
            record["dry_primary_facility_cat"], record["flood0708_primary_facility_cat"],
            record["dry_backup_minutes"], target[emergency], crosses,
        ))
        rows.append(record)

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "e4_routes.csv", index=False)

    docs_data = ROOT / "docs" / "data"
    docs_data.mkdir(exist_ok=True)
    (docs_data / "e4_routes.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}) + "\n"
    )

    print(f"{len(out)} route records, {len(features)} path features")
    print(f"with a warning: {int((out['warnings'] != '').sum())} of {len(out)}")
    print(out["warnings"].value_counts().head(10).to_string())
    within = out["dry_primary_within_target"].mean() * 100
    print(f"within target time (dry, sample of {len(out)} points): {within:.0f}%")

    # A small map: population-weighted travel time backdrop, plus a handful of example routes.
    with rasterio.open(IN / "population.tif") as src:
        pop, ptransform = src.read(1), src.transform
    x0, y1 = ptransform.c, ptransform.f
    extent = (x0, x0 + pop.shape[1] * ptransform.a, y1 + pop.shape[0] * ptransform.e, y1)
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.imshow(np.ma.masked_where(pop == 0, np.log1p(pop)), extent=extent, cmap="Greys", alpha=0.6)
    colors = {"childbirth_complication": "#1b7837", "snakebite": "#762a83", "injury_drowning": "#b35806",
              "minor_illness": "#2166ac"}
    example_ids = out.groupby("emergency")["id"].apply(lambda s: s.head(3)).tolist()
    for pid in example_ids:
        f = [
            x for x in features
            if x["properties"]["point_id"] == pid
            and x["properties"]["kind"] == "primary"
            and x["properties"]["season"] == "dry"
        ]
        if not f:
            continue
        coords = f[0]["geometry"]["coordinates"]
        xs, ys = zip(*coords)
        color = colors[f[0]["properties"]["emergency"]]
        ax.plot(xs, ys, color=color, linewidth=1.4)
        ax.scatter([xs[0]], [ys[0]], s=22, color=color, zorder=3, marker="o")
        ax.scatter([xs[-1]], [ys[-1]], s=45, color=color, zorder=3, marker="+")
    handles = [plt.Line2D([0], [0], color=c, label=e.replace("_", " ")) for e, c in colors.items()]
    ax.legend(handles=handles, loc="lower left", fontsize=8)
    ax.set_title("Example dry-season routes to the right facility (dot = start, + = facility)")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "img" / "e4_routes.png", dpi=110)


if __name__ == "__main__":
    main()
