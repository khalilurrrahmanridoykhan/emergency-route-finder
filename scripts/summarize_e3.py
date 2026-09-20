"""Summarise travel time to the right facility for each emergency type, dry and flood.

Reads AccessMod exports and the replay configs, writes CSVs to results/ and a figure to docs/img/.
Run: .venv/bin/python scripts/summarize_e3.py
"""
import csv
import glob
import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from facility_levels import load_capabilities, qualifies  # noqa: E402
from rasterio.features import rasterize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
OUT = ROOT / "data" / "interim" / "accessmod_out"
RESULTS = ROOT / "results"
NULL = 65535
TAGS = ["dry", "flood0708", "flood0713"]


def read(pattern):
    with rasterio.open(glob.glob(pattern)[0]) as src:
        return src.read(1), src.transform


def emergencies():
    with open(ROOT / "config" / "emergencies.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    pop, transform = read(f"{IN}/population.tif")
    total = float(pop.sum())
    fac = gpd.read_file(IN / "facilities.shp").reset_index(drop=True)
    fac["cat"] = fac.index + 1
    caps = load_capabilities()
    emgs = emergencies()

    rows, times, nearest = [], {}, {}
    for tag in TAGS:
        for e in emgs:
            key = f"{tag}_{e['emergency_id']}"
            t, _ = read(f"{OUT}/accessibility_{key}/raster_travel_time_*/*.GeoTIFF")
            n, _ = read(f"{OUT}/accessibility_{key}/raster_cost_allocation_*/*.GeoTIFF")
            times[key], nearest[key] = t, n
            conf = json.load(open(IN / f"replay_accessibility_{key}.json"))
            qualifying = sum(r["amSelect"] for r in conf["args"]["tableFacilities"])
            ok = t != NULL
            target = int(e["target_minutes"])
            row = {"scenario": tag, "emergency": e["emergency_id"], "qualifying_facilities": qualifying,
                   "target_minutes": target}
            row["people_within_target"] = round(float(pop[ok & (t <= target)].sum()))
            row["percent_within_target"] = round(100 * row["people_within_target"] / total, 1)
            for limit in (60, 120, 240):
                row[f"percent_within_{limit}"] = round(100 * float(pop[ok & (t <= limit)].sum()) / total, 1)
            row["percent_no_route_within_300"] = round(100 * float(pop[~ok].sum()) / total, 2)
            row["mean_minutes_pop_weighted"] = round(float((t[ok] * pop[ok]).sum() / pop[ok].sum()), 1)
            rows.append(row)
    coverage = pd.DataFrame(rows)
    coverage.to_csv(RESULTS / "e3_coverage.csv", index=False)
    pivot = coverage.pivot(index="emergency", columns="scenario", values="percent_within_target")
    print(pivot[TAGS].to_string())
    print(coverage[coverage.scenario == "dry"][["emergency", "qualifying_facilities", "target_minutes",
          "percent_within_60", "percent_within_120", "percent_no_route_within_300",
          "mean_minutes_pop_weighted"]].to_string(index=False))

    # Flood effect per emergency type (main flood date).
    effect = []
    for e in emgs:
        d, f = times[f"dry_{e['emergency_id']}"], times[f"flood0708_{e['emergency_id']}"]
        target = int(e["target_minutes"])
        effect.append({
            "emergency": e["emergency_id"], "target_minutes": target,
            "people_pushed_beyond_target": round(float(pop[(d <= target) & (f > target)].sum())),
            "people_lose_all_routes": round(float(pop[(d != NULL) & (f == NULL)].sum())),
            "extra_minutes_pop_weighted": round(float(
                ((f.astype(int) - d.astype(int)) * pop)[(d != NULL) & (f != NULL)].sum()
                / pop[(d != NULL) & (f != NULL)].sum()), 2),
        })
    pd.DataFrame(effect).to_csv(RESULTS / "e3_flood_effect.csv", index=False)
    print(pd.DataFrame(effect).to_string(index=False))

    # Facility list with the emergencies each is assumed to handle, and its dry catchment per emergency.
    listing = fac[["cat", "name", "osm_id", "amenity", "level", "lvl_src"]].copy()
    for e in emgs:
        listing[e["emergency_id"]] = [qualifies(lv, e["capability_column"], caps) for lv in fac["level"]]
        n = nearest[f"dry_{e['emergency_id']}"]
        listing[f"people_nearest_{e['emergency_id']}_dry"] = [
            round(float(pop[n == c].sum())) for c in fac["cat"]
        ]
    listing = listing.rename(columns={"lvl_src": "level_source"})
    listing.to_csv(RESULTS / "e3_facility_levels.csv", index=False)

    # Per-upazila share within target (dry vs flood) for each emergency type.
    adm3 = gpd.read_file(ROOT / "data" / "cache" / "bgd_adm3_wide.geojson").to_crs("EPSG:32646")
    adm3 = adm3.reset_index(drop=True)
    ids = rasterize([(g, i + 1) for i, g in enumerate(adm3.geometry)], out_shape=pop.shape,
                    transform=transform, fill=0, dtype="int32")
    upz = []
    for i, r in adm3.iterrows():
        m = ids == i + 1
        if pop[m].sum() < 1000:
            continue
        item = {"adm3_pcode": r["adm3_pcode"], "adm3_name": r["adm3_name"], "district": r["adm2_name"],
                "population_in_grid": round(float(pop[m].sum()))}
        for e in emgs:
            for tag in ("dry", "flood0708"):
                t = times[f"{tag}_{e['emergency_id']}"]
                within = pop[m & (t != NULL) & (t <= int(e["target_minutes"]))].sum()
                share = 100 * float(within / pop[m].sum())
                item[f"pct_within_target_{e['emergency_id']}_{tag}"] = round(share, 1)
        upz.append(item)
    upz = pd.DataFrame(upz).sort_values("pct_within_target_childbirth_complication_dry")
    upz.to_csv(RESULTS / "e3_upazila_within_target.csv", index=False)
    print(upz[["adm3_name", "population_in_grid", "pct_within_target_childbirth_complication_dry",
               "pct_within_target_childbirth_complication_flood0708"]].head(6).to_string(index=False))

    # Figure: dry travel-time maps per emergency type and a bar chart of coverage within target.
    x0, y1 = transform.c, transform.f
    extent = (x0, x0 + pop.shape[1] * transform.a, y1 + pop.shape[0] * transform.e, y1)
    fig, axes = plt.subplots(2, 3, figsize=(15, 11), layout="constrained")
    flat = axes.ravel()
    for ax, e in zip(flat[:5], emgs):
        t = times[f"dry_{e['emergency_id']}"]
        im = ax.imshow(np.ma.masked_where(t == NULL, np.minimum(t, 240)), extent=extent, cmap="viridis_r",
                       vmin=0, vmax=240)
        q = fac[[qualifies(lv, e["capability_column"], caps) for lv in fac["level"]]]
        ax.scatter(q.geometry.x, q.geometry.y, s=14, c="white", edgecolors="black", linewidths=0.6)
        ax.set_title(f"{e['label']}\n({len(q)} qualifying facilities, dry)", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.colorbar(im, ax=list(flat[:5]), location="bottom", shrink=0.45, pad=0.02,
                 label="minutes to nearest qualifying facility (capped at 240)")
    ax = flat[5]
    labels = [e["emergency_id"].replace("_", "\n") for e in emgs]
    xs = np.arange(len(emgs))
    for k, (tag, color) in enumerate((("dry", "#2a7f62"), ("flood0708", "#c0562b"))):
        vals = [float(pivot.loc[e["emergency_id"], tag]) for e in emgs]
        ax.bar(xs + (k - 0.5) * 0.38, vals, 0.38, label=tag, color=color)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("% of people within the target time")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right")
    ax.set_title("Coverage within target time")
    fig.savefig(ROOT / "docs" / "img" / "e3_emergency_types.png", dpi=90)


if __name__ == "__main__":
    main()
