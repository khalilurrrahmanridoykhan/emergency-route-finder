#!/bin/sh
# Phase E6: trace the primary route for every (grid point, emergency) task -- the web map's data.
# Needs Docker running and the AccessMod project already imported (make e1 at least once).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ACCESSMOD_IMAGE:-fredmoser/accessmod:5.9.1}"
VOLUME="${ACCESSMOD_VOLUME:-am5_e1_db}"
OUT_DIR="$ROOT/data/interim/accessmod_out/e6_grid"

"$ROOT/.venv/bin/python" "$ROOT/scripts/generate_grid_points.py"
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_e6_tasks.py"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

docker run --rm \
  -v "$VOLUME":/data/dbgrass \
  -v "$ROOT/scripts/accessmod":/scripts:ro \
  -v "$ROOT/data/interim/accessmod":/data/shared/in:ro \
  -v "$OUT_DIR":/data/shared/out \
  "$IMAGE" Rscript /scripts/grid_paths.R \
    /data/shared/in/e6_tasks.csv /data/shared/in/e4_qualifying_cats.json /data/shared/out \
  2>&1 | grep -E "PRIMARY DIRECTION|TASK|DONE|^Error|ERROR"
