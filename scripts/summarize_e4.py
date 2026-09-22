"""Build the final route record per synthetic point (Phase E4): right facility, time, path, mode,
backup, warning -- for dry and flood0708. Reads the R script's points_result.csv and path GeoJSON
files. Assembly logic (per-point record, path mode, flood crossing) lives in
scripts/route_record.py, shared with the on-demand scripts/route.py (Phase E5).

Run (after scripts/run_e4.sh): .venv/bin/python scripts/summarize_e4.py
Writes results/e4_routes.csv, docs/data/e4_routes.geojson, docs/img/e4_routes.png.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from route_record import IN, build_route_record, facility_lookup, targets  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PATHS = ROOT / "data" / "interim" / "accessmod_out" / "e4_paths"


def main():
    points = pd.read_csv(IN / "e4_points.csv").set_index("id")
    res = pd.read_csv(PATHS / "points_result.csv")
    fac = facility_lookup()
    target = targets()

    with rasterio.open(IN / "landcover_merged_dry.tif") as src:
        dry_lc, transform = src.read(1), src.transform
    with rasterio.open(IN / "landcover_merged_flood0708.tif") as src:
        flood_lc = src.read(1)
    land_cover = {"dry": (dry_lc, transform), "flood0708": (flood_lc, transform)}

    rows, features = [], []
    for pid, point in points.iterrows():
        record, feats = build_route_record(pid, point, res, fac, land_cover, target, PATHS)
        rows.append(record)
        features.extend(feats)

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
