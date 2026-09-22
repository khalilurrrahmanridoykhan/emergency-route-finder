#!/bin/sh
# Phase E4: complete least-cost paths (primary and backup) for the synthetic emergency points.
# Needs Docker running and the AccessMod project already imported (make e1/e2/e3 already ran).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ACCESSMOD_IMAGE:-fredmoser/accessmod:5.9.1}"
VOLUME="${ACCESSMOD_VOLUME:-am5_e1_db}"
OUT_DIR="$ROOT/data/interim/accessmod_out/e4_paths"

"$ROOT/.venv/bin/python" "$ROOT/scripts/generate_emergency_points.py"
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_e4_tasks.py"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

docker run --rm \
  -v "$VOLUME":/data/dbgrass \
  -v "$ROOT/scripts/accessmod":/scripts:ro \
  -v "$ROOT/data/interim/accessmod":/data/shared/in:ro \
  -v "$OUT_DIR":/data/shared/out \
  "$IMAGE" Rscript /scripts/e4_paths.R \
    /data/shared/in/e4_points.csv /data/shared/in/e4_qualifying_cats.json /data/shared/out \
  2>&1 | grep -E "PRIMARY DIRECTION|BACKUP DIRECTION|^POINT|E4 DONE|^Error|ERROR"
