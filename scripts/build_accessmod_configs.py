"""Write AccessMod replay configs (JSON) for the analyses run in Phase E1.

Reads config/speeds.csv for the scenario table and data/interim/accessmod/facilities.shp for the
facility table. AccessMod numbers imported facilities 1..n in file order, which is used as `cat`.
Run: .venv/bin/python scripts/build_accessmod_configs.py --season dry
"""
import argparse
import csv
import json
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
PROJECT = "e1dry"


def scenario_table(season):
    with open(ROOT / "config" / "speeds.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["season"] in (season, "both")]
    return [
        {"class": int(r["class"]), "label": r["label"], "speed": float(r["speed_kmh"]), "mode": r["mode"]}
        for r in rows
    ]


def facility_rows(select):
    fac = gpd.read_file(IN / "facilities.shp").reset_index(drop=True)
    return [
        {"amSelect": bool(select(row)), "cat": i + 1, "name": row["name"]} for i, row in fac.iterrows()
    ]


def base(analysis, tag):
    return {"analysis": analysis, "location": PROJECT, "mapset": PROJECT, "args": {}, "tag": tag}


def accessibility(season, max_minutes):
    conf = base("amTravelTimeAnalysis", season)
    outputs = {k: f"{k}__{season}" for k in ("rSpeed", "rFriction", "rTravelTime", "rNearest")}
    conf["output"] = list(outputs.values())
    conf["args"] = {
        "inputHf": f"vFacility__{PROJECT}",
        "inputMerged": f"rLandCoverMerged__{PROJECT}",
        "outputSpeed": outputs["rSpeed"],
        "outputFriction": outputs["rFriction"],
        "outputTravelTime": outputs["rTravelTime"],
        "outputNearest": outputs["rNearest"],
        "typeAnalysis": "anisotropic",
        "knightMove": True,
        "towardsFacilities": True,
        "addNearest": True,  # without this AccessMod drops the nearest-facility raster
        "joinField": "cat",
        "maxTravelTime": max_minutes,
        "useMaxSpeedMask": False,
        "timeoutValue": -1,
        "tableScenario": scenario_table(season),
        "tableFacilities": facility_rows(lambda r: True),
    }
    return conf


def referral(season):
    conf = base("amAnalysisReferral", season)
    names = {
        "outputSpeed": f"rSpeed__ref_{season}",
        "outputFriction": f"rFriction__ref_{season}",
        "outputReferral": f"tReferral__{season}",
        "outputNearestDist": f"tReferralDist__{season}",
        "outputNearestTime": f"tReferralTime__{season}",
        "outputNetDist": f"vReferralNetwork__{season}",
    }
    exported = ("outputReferral", "outputNearestTime", "outputNearestDist", "outputNetDist")
    conf["output"] = [names[k] for k in exported]
    conf["args"] = {
        "inputHfFrom": f"vFacility__{PROJECT}",
        "inputHfTo": f"vFacility__{PROJECT}",
        "inputMerged": f"rLandCoverMerged__{PROJECT}",
        **names,
        "maxTravelTime": 0,
        "useMaxSpeedMask": False,
        "idField": "cat",
        "labelField": "name",
        "idFieldTo": "cat",
        "labelFieldTo": "name",
        "typeAnalysis": "anisotropic",
        "knightMove": False,
        "limitClosest": False,
        "parallel": False,
        "permuteGroups": False,
        "keepNetDist": True,
        "snapToGrid": True,
        "resol": 100,
        "unitCost": "m",
        "unitDist": "km",
        "roundingMethod": "ceil",
        "tableScenario": scenario_table(season),
        "tableFacilities": facility_rows(lambda r: r["amenity"] == "clinic"),
        "tableFacilitiesTo": facility_rows(lambda r: r["amenity"] == "hospital"),
    }
    return conf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="dry", choices=["dry", "flood"])
    parser.add_argument("--max-minutes", type=int, default=300)
    args = parser.parse_args()
    for name, conf in (
        (f"accessibility_{args.season}", accessibility(args.season, args.max_minutes)),
        (f"referral_{args.season}", referral(args.season)),
    ):
        path = IN / f"replay_{name}.json"
        path.write_text(json.dumps(conf, indent=2) + "\n")
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
