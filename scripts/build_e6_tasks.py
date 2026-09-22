"""Expand the E6 grid points into (point, emergency) task rows for the R path tracer.

Every grid point is evaluated against each of the four real emergency types (not the strict
snakebite sensitivity variant -- that stays an E3/E7 analysis case, not a map option).

Run (after generate_grid_points.py): .venv/bin/python scripts/build_e6_tasks.py
Writes data/interim/accessmod/e6_tasks.csv (id, grid_id, x, y, emergency_id) and
data/interim/accessmod/e6_qualifying_cats.json (reuses build_e4_tasks's per-emergency cat lists).
"""
import csv
from pathlib import Path

from build_e4_tasks import main as build_qualifying_cats

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "interim" / "accessmod"
EMERGENCIES = ["childbirth_complication", "snakebite", "injury_drowning", "minor_illness"]


def main():
    build_qualifying_cats()  # writes e4_qualifying_cats.json; e6 reuses it as-is
    with open(IN / "e6_grid_points.csv", newline="") as f:
        points = list(csv.DictReader(f))

    out = IN / "e6_tasks.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "grid_id", "x", "y", "emergency_id"])
        task_id = 1
        for p in points:
            for emergency in EMERGENCIES:
                writer.writerow([task_id, p["grid_id"], p["x"], p["y"], emergency])
                task_id += 1
    print(f"wrote {task_id - 1} tasks ({len(points)} points x {len(EMERGENCIES)} emergencies) to "
          f"{out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
