"""Write AccessMod replay configs (JSON) for the analyses run in Phase E1.

Reads config/speeds.csv for the scenario table and data/interim/accessmod/facilities.shp for the
facility table. AccessMod numbers imported facilities 1..n in file order, which is used as `cat`.
Run: .venv/bin/python scripts/build_accessmod_configs.py --tag flood0708
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


def base(analysis):
    return {"analysis": analysis, "location": PROJECT, "mapset": PROJECT, "args": {}}


def accessibility(tag, season, max_minutes):
    conf = base("amTravelTimeAnalysis")
    outputs = {k: f"{k}__{tag}" for k in ("rSpeed", "rFriction", "rTravelTime", "rNearest")}
    conf["output"] = list(outputs.values())
    conf["args"] = {
        "inputHf": f"vFacility__{PROJECT}",
        "inputMerged": f"rLandCoverMerged__{tag}",
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


def referral(tag, season):
    conf = base("amAnalysisReferral")
    names = {
        "outputSpeed": f"rSpeed__ref_{tag}",
        "outputFriction": f"rFriction__ref_{tag}",
        "outputReferral": f"tReferral__{tag}",
        "outputNearestDist": f"tReferralDist__{tag}",
        "outputNearestTime": f"tReferralTime__{tag}",
        "outputNetDist": f"vReferralNetwork__{tag}",
    }
    exported = ("outputReferral", "outputNearestTime", "outputNearestDist", "outputNetDist")
    conf["output"] = [names[k] for k in exported]
    conf["args"] = {
        "inputHfFrom": f"vFacility__{PROJECT}",
        "inputHfTo": f"vFacility__{PROJECT}",
        "inputMerged": f"rLandCoverMerged__{tag}",
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
    parser.add_argument("--tag", default="dry", help="land cover set: dry, flood0708, ...")
    parser.add_argument("--max-minutes", type=int, default=300)
    args = parser.parse_args()
    season = "dry" if args.tag == "dry" else "flood"
    for name, conf in (
        (f"accessibility_{args.tag}", accessibility(args.tag, season, args.max_minutes)),
        (f"referral_{args.tag}", referral(args.tag, season)),
    ):
        path = IN / f"replay_{name}.json"
        path.write_text(json.dumps(conf, indent=2) + "\n")
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
