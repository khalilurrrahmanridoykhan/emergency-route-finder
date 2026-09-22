"""Write the qualifying-facility list per emergency, in the same cat numbering AccessMod uses.

AccessMod numbers imported facilities 1..n in the row order of facilities.shp (see
build_accessmod_configs.py). This writes that same list, keyed by emergency id, so the E4 R
script (scripts/accessmod/e4_paths.R) selects exactly the facilities Phase E3's accessibility()
runs did.
Run: .venv/bin/python scripts/build_e4_tasks.py
"""
import json
from pathlib import Path

import geopandas as gpd
from build_accessmod_configs import emergencies
from facility_levels import load_capabilities, qualifies

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"


def main():
    fac = gpd.read_file(IN / "facilities.shp").reset_index(drop=True)
    caps = load_capabilities()
    out = {}
    for emergency_id, column in emergencies().items():
        out[emergency_id] = [i + 1 for i, level in enumerate(fac["level"]) if qualifies(level, column, caps)]
    path = IN / "e4_qualifying_cats.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    for k, v in out.items():
        print(k, len(v), "qualifying facilities")
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
