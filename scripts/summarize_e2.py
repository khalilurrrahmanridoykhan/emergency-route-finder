"""Compare dry and flood travel times: coverage, people affected, per-upazila change, referral changes.

Reads AccessMod exports from data/interim/accessmod_out/ and writes CSVs to results/ and a map to
docs/img/. Run: .venv/bin/python scripts/summarize_e2.py
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
from rasterio.features import rasterize  # noqa: E402
from scipy import ndimage  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
OUT = ROOT / "data" / "interim" / "accessmod_out"
RESULTS = ROOT / "results"
NULL = 65535
THRESHOLDS = (30, 60, 120, 240)
FLOOD_CLASS = 301
FLOODS = {"flood0708": "2026-07-08", "flood0713": "2026-07-13"}


def read(pattern):
    path = glob.glob(pattern)[0]
    with rasterio.open(path) as src:
        return src.read(1), src.transform


def load(tag):
    travel, transform = read(f"{OUT}/accessibility_{tag}/raster_travel_time_*/*.GeoTIFF")
    nearest, _ = read(f"{OUT}/accessibility_{tag}/raster_cost_allocation_*/*.GeoTIFF")
    return travel, nearest, transform


def flood_land_share(tag, dry_lc, flood_lc):
    land = dry_lc > 0
    return float(((flood_lc == 301) & land).sum() / land.sum())


def main():
    RESULTS.mkdir(exist_ok=True)
    pop, transform = read(f"{IN}/population.tif")
    total = float(pop.sum())
    tags = ["dry", *FLOODS]
    data = {t: load(t) for t in tags}

    rows = []
    for tag in tags:
        travel = data[tag][0]
        ok = travel != NULL
        for limit in THRESHOLDS:
            covered = float(pop[ok & (travel <= limit)].sum())
            rows.append({"scenario": tag, "within_minutes": limit, "people": round(covered),
                         "share_percent": round(100 * covered / total, 1)})
        none = float(pop[~ok].sum())
        rows.append({"scenario": tag, "within_minutes": "no_route_within_300", "people": round(none),
                     "share_percent": round(100 * none / total, 2)})
    coverage = pd.DataFrame(rows)
    coverage.to_csv(RESULTS / "e2_coverage.csv", index=False)
    print(coverage.pivot(index="within_minutes", columns="scenario", values="share_percent").to_string())

    dry_t, dry_n, _ = data["dry"]
    dry_lc = read(f"{IN}/landcover_merged_dry.tif")[0]
    impact = []
    for tag, date in FLOODS.items():
        t, n, _ = data[tag]
        both = (dry_t != NULL) & (t != NULL)
        delta = np.where(both, t.astype(int) - dry_t.astype(int), 0)
        flood_lc = read(f"{IN}/landcover_merged_{tag}.tif")[0]
        with rasterio.open(ROOT / "data" / "interim" / "flood" / f"coverage_{date}.tif") as src:
            cov = src.read(1).astype(bool)
        cov100 = cov.reshape(pop.shape[0], 5, pop.shape[1], 5).mean(axis=(1, 3)) >= 0.5
        impact.append({
            "scenario": tag, "flood_date": date,
            "flooded_share_of_land_percent": round(100 * flood_land_share(tag, dry_lc, flood_lc), 1),
            "sar_coverage_of_grid_percent": round(100 * float(cov100.mean()), 1),
            "mean_minutes_dry": round(float(dry_t[dry_t != NULL].mean()), 1),
            "mean_minutes_flood": round(float(t[t != NULL].mean()), 1),
            "people_time_up_15min": round(float(pop[both & (delta >= 15)].sum())),
            "people_time_up_60min": round(float(pop[both & (delta >= 60)].sum())),
            "people_pushed_beyond_60min": round(float(pop[(dry_t <= 60) & (t > 60)].sum())),
            "people_lose_all_routes": round(float(pop[(dry_t != NULL) & (t == NULL)].sum())),
            "people_nearest_facility_changes": round(float(pop[both & (n != dry_n)].sum())),
            "people_in_unmapped_flood_area": round(float(pop[~cov100].sum())),
        })
    pd.DataFrame(impact).to_csv(RESULTS / "e2_flood_impact.csv", index=False)
    print(pd.DataFrame(impact).T.to_string())

    adm3 = gpd.read_file(ROOT / "data" / "cache" / "bgd_adm3_wide.geojson")
    adm3 = adm3.to_crs("EPSG:32646").reset_index(drop=True)
    ids = rasterize(
        [(g, i + 1) for i, g in enumerate(adm3.geometry)],
        out_shape=pop.shape, transform=transform, fill=0, dtype="int32",
    )
    upazila = []
    for i, row in adm3.iterrows():
        m = ids == i + 1
        if pop[m].sum() < 1000:
            continue
        item = {"adm3_pcode": row["adm3_pcode"], "adm3_name": row["adm3_name"], "district": row["adm2_name"],
                "population_in_grid": round(float(pop[m].sum())),
                "mean_minutes_dry": round(float(dry_t[m & (dry_t != NULL)].mean()), 1)}
        for tag in FLOODS:
            t = data[tag][0]
            item[f"mean_minutes_{tag}"] = round(float(t[m & (t != NULL)].mean()), 1)
            item[f"pushed_beyond_60_{tag}"] = round(float(pop[m & (dry_t <= 60) & (t > 60)].sum()))
        upazila.append(item)
    upz = pd.DataFrame(upazila).sort_values("pushed_beyond_60_flood0708", ascending=False)
    upz.to_csv(RESULTS / "e2_upazila_change.csv", index=False)
    print(upz.head(8).to_string(index=False))

    # Like-for-like check against the earlier road-network study (same flood date, 8 upazilas):
    # people in flooded cells vs its flood exposure, and people within 500 m of flooded road
    # pieces vs its "lost access" population.
    q3 = pd.read_csv(ROOT / "data" / "raw" / "q3_population_by_upazila.csv")
    flood13 = read(f"{IN}/landcover_merged_flood0713.tif")[0]
    flooded = flood13 == FLOOD_CLASS
    road_flooded = flooded & (dry_lc >= 201)
    yy, xx = np.ogrid[-5:6, -5:6]
    near_road = ndimage.binary_dilation(road_flooded, structure=(xx**2 + yy**2) <= 25)
    rows = []
    for i, row in adm3.iterrows():
        if row["adm3_pcode"] in set(q3["adm3_pcode"]):
            m = ids == i + 1
            rows.append({
                "adm3_pcode": row["adm3_pcode"],
                "this_pop_in_flooded_cells": round(float(pop[m & flooded].sum())),
                "this_pop_within_500m_flooded_road": round(float(pop[m & near_road].sum())),
            })
    check = q3.merge(pd.DataFrame(rows), on="adm3_pcode")
    check.to_csv(RESULTS / "e2_validation_vs_earlier_study.csv", index=False)
    pairs = (
        ("population_flood_exposed", "this_pop_in_flooded_cells"),
        ("population_access_loss", "this_pop_within_500m_flooded_road"),
    )
    for earlier, ours in pairs:
        rho = spearmanr(check[earlier], check[ours])[0]
        totals = f"{check[earlier].sum():.0f} vs {check[ours].sum():.0f}"
        print(f"{earlier} vs {ours}: Spearman {rho:.2f}; totals {totals}")

    ref = {}
    for tag in ("dry", "flood0708"):
        path = glob.glob(f"{OUT}/referral_{tag}/table_referral_nearest_by_time_*/*.xlsx")[0]
        ref[tag] = pd.read_excel(path)
    change = ref["dry"].merge(ref["flood0708"], on=["from__cat", "from__name"], suffixes=("_dry", "_flood"))
    change["changed_destination"] = change["to__cat_dry"] != change["to__cat_flood"]
    change["extra_minutes"] = change["time_m_flood"] - change["time_m_dry"]
    # A different destination at the same travel time is a tie between neighbouring hospitals, not a re-route.
    change["rerouted"] = change["changed_destination"] & (change["extra_minutes"] > 0)
    change.to_csv(RESULTS / "e2_referral_change.csv", index=False)
    print(
        f"referral: {len(change)} clinics; {int((change['extra_minutes'] > 0).sum())} slower in the flood; "
        f"{int(change['rerouted'].sum())} re-routed; "
        f"{int((change['changed_destination'] & (change['extra_minutes'] == 0)).sum())} destination ties; "
        f"max extra minutes {int(change['extra_minutes'].max())}"
    )

    x0, y1 = transform.c, transform.f
    extent = (x0, x0 + pop.shape[1] * transform.a, y1 + pop.shape[0] * transform.e, y1)
    fac = gpd.read_file(IN / "facilities.shp")
    fig, axes = plt.subplots(1, 3, figsize=(16, 6.4))
    delta = np.ma.masked_where((dry_t == NULL) | (data["flood0708"][0] == NULL),
                               data["flood0708"][0].astype(int) - dry_t.astype(int))
    panels = ((axes[0], "dry", "Dry season (minutes)"), (axes[1], "flood0708", "Flood 2026-07-08 (minutes)"))
    for ax, tag, title in panels:
        t = data[tag][0]
        im = ax.imshow(np.ma.masked_where(t == NULL, np.minimum(t, 240)), extent=extent, cmap="viridis_r",
                       vmin=0, vmax=240)
        ax.set_title(title)
    fig.colorbar(im, ax=axes[:2], shrink=0.6, label="minutes (capped at 240)")
    im2 = axes[2].imshow(np.minimum(delta, 120), extent=extent, cmap="magma_r", vmin=0, vmax=120)
    axes[2].set_title("Extra minutes in the flood")
    fig.colorbar(im2, ax=axes[2], shrink=0.6, label="extra minutes")
    for ax in axes:
        ax.scatter(fac.geometry.x, fac.geometry.y, s=8, c="white", edgecolors="black", linewidths=0.5)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.savefig(ROOT / "docs" / "img" / "e2_dry_vs_flood.png", dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    main()
