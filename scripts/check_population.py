"""Check the WorldPop layer against the 2022 census and test how much its error matters.

Compares WorldPop 2020 totals with the BBS 2022 census population per upazila (HDX cod-ps-bgd),
then rescales each upazila to its census total and recomputes some headline coverage numbers.
Writes results/population_vs_census.csv and results/population_sensitivity.csv.
Run: .venv/bin/python scripts/check_population.py   (after `make e3`)
"""
import glob
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
IN = ROOT / "data" / "interim" / "accessmod"
OUT = ROOT / "data" / "interim" / "accessmod_out"
UA = {"User-Agent": "emergency-route-finder/0.1 (github.com/khalilurrrahmanridoykhan)"}
NULL = 65535


def census_table():
    path = CACHE / "bgd_admpop_adm3_2022.csv"
    if not path.exists():
        api = "https://data.humdata.org/api/3/action/package_show?id=cod-ps-bgd"
        package = requests.get(api, headers=UA, timeout=60).json()["result"]
        url = next(r["url"] for r in package["resources"] if r["name"] == "bgd_admpop_adm3_2022.csv")
        text = requests.get(url, headers=UA, timeout=120).content.decode("utf-8-sig")
        path.write_text(text)
    return pd.read_csv(path)


def short_code(code):
    """Boundary P-codes have 10 characters (BD60900029); the census table uses BD609029."""
    return code[:6] + str(int(code[6:]))


def main():
    census = census_table()
    adm = gpd.read_file(CACHE / "bgd_adm3_wide.geojson").reset_index(drop=True)
    with rasterio.open(CACHE / "bgd_ppp_2020_constrained.tif") as src:
        window = from_bounds(*adm.total_bounds, transform=src.transform).round_offsets().round_lengths()
        array = src.read(1, window=window, masked=True).filled(0)
        transform = src.window_transform(window)
    ids = rasterize([(g, i + 1) for i, g in enumerate(adm.geometry)], out_shape=array.shape,
                    transform=transform, fill=0, dtype="int32")
    adm["worldpop_2020"] = [float(array[ids == i + 1].sum()) for i in range(len(adm))]

    adm["short"] = adm["adm3_pcode"].map(short_code)
    merged = adm.merge(census[["ADM3_PCODE", "T_TL"]], left_on="short", right_on="ADM3_PCODE", how="left")
    # Fall back to name and district for codes that do not convert cleanly.
    census["key"] = (
        census["ADM3_NAME"].str.lower().str.strip() + "|" + census["ADM2_NAME"].str.lower().str.strip()
    )
    merged["key"] = (
        merged["adm3_name"].str.lower().str.strip() + "|" + merged["adm2_name"].str.lower().str.strip()
    )
    by_name = dict(zip(census["key"], census["T_TL"]))
    missing = merged["T_TL"].isna()
    merged.loc[missing, "T_TL"] = merged.loc[missing, "key"].map(by_name)
    matched = merged.dropna(subset=["T_TL"]).copy()
    matched["census_2022"] = matched["T_TL"]
    matched["ratio"] = matched["worldpop_2020"] / matched["census_2022"]
    cols = ["adm3_pcode", "adm3_name", "adm2_name", "census_2022", "worldpop_2020", "ratio"]
    table = matched.sort_values("ratio")[cols].round(3)
    table.to_csv(ROOT / "results" / "population_vs_census.csv", index=False)

    r = matched["ratio"]
    print(f"matched {len(matched)} of {len(adm)} upazilas")
    print(f"total WorldPop {matched.worldpop_2020.sum():,.0f} vs census {matched.census_2022.sum():,.0f}")
    quartiles = f"{r.quantile(.25):.2f}-{r.quantile(.75):.2f}"
    print(f"ratio median {r.median():.2f}, middle half {quartiles}, min {r.min():.2f}, max {r.max():.2f}")
    print(f"within 10%: {int((abs(r - 1) <= .10).sum())}, within 25%: {int((abs(r - 1) <= .25).sum())}")
    print(f"Pearson {pearsonr(matched.worldpop_2020, matched.census_2022)[0]:.3f}, "
          f"Spearman {spearmanr(matched.worldpop_2020, matched.census_2022)[0]:.3f}")

    # Sensitivity: rescale each matched upazila to its census total and recompute coverage.
    with rasterio.open(IN / "population.tif") as src:
        pop, grid_transform = src.read(1), src.transform
    adm_grid = adm.to_crs("EPSG:32646")
    grid_ids = rasterize([(g, i + 1) for i, g in enumerate(adm_grid.geometry)], out_shape=pop.shape,
                         transform=grid_transform, fill=0, dtype="int32")
    scale = np.ones(pop.shape, dtype="float32")
    factor = dict(zip(matched["adm3_pcode"], matched["census_2022"] / matched["worldpop_2020"]))
    for i, row in adm_grid.iterrows():
        if row["adm3_pcode"] in factor:
            scale[grid_ids == i + 1] = factor[row["adm3_pcode"]]
    rescaled = pop * scale

    def read(pattern):
        with rasterio.open(glob.glob(pattern)[0]) as src:
            return src.read(1)

    cases = (
        ("any facility, 60 min, dry", "accessibility_dry", 60),
        ("any facility, 60 min, flood 07-08", "accessibility_flood0708", 60),
        ("childbirth, 120 min, dry", "accessibility_dry_childbirth_complication", 120),
        ("snakebite, district only, 120 min, dry", "accessibility_dry_snakebite_hospital_only", 120),
    )
    rows = []
    for label, folder, limit in cases:
        t = read(f"{OUT}/{folder}/raster_travel_time_*/*.GeoTIFF")
        ok = (t != NULL) & (t <= limit)
        rows.append({"measure": label, "worldpop_percent": round(100 * pop[ok].sum() / pop.sum(), 1),
                     "census_rescaled_percent": round(100 * rescaled[ok].sum() / rescaled.sum(), 1)})
    sens = pd.DataFrame(rows)
    sens.to_csv(ROOT / "results" / "population_sensitivity.csv", index=False)
    print(f"grid total WorldPop {pop.sum():,.0f}; census-rescaled {rescaled.sum():,.0f} "
          f"({100 * (rescaled.sum() / pop.sum() - 1):+.1f}%)")
    print(sens.to_string(index=False))


if __name__ == "__main__":
    main()
