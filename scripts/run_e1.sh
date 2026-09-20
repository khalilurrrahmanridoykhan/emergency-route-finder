#!/bin/sh
# Phase E1: rebuild the AccessMod project from prepared inputs and run the dry-season analyses.
# Needs Docker running (colima start) and the inputs from scripts/fetch_inputs.py.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ACCESSMOD_IMAGE:-fredmoser/accessmod:5.9.1}"
VOLUME="${ACCESSMOD_VOLUME:-am5_e1_db}"
SEASON="${SEASON:-dry}"

"$ROOT/.venv/bin/python" "$ROOT/scripts/prepare_accessmod_inputs.py" > /dev/null
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_accessmod_configs.py" --season "$SEASON"

docker volume rm "$VOLUME" > /dev/null 2>&1 || true
docker volume create "$VOLUME" > /dev/null

run() {
  docker run --rm \
    -v "$VOLUME":/data/dbgrass \
    -v "$ROOT/scripts/accessmod":/scripts:ro \
    -v "$ROOT/data/interim/accessmod":/data/shared/in:ro \
    -v "$ROOT/data/interim/accessmod_out":/data/shared/out \
    "$IMAGE" Rscript "$@"
}

run /scripts/import_project.R e1dry /data/shared/in 2>&1 | grep -E "IMPORT DONE|Error"
for name in accessibility referral; do
  rm -rf "$ROOT/data/interim/accessmod_out/${name}_$SEASON"
  run /scripts/run_analysis.R "/data/shared/in/replay_${name}_$SEASON.json" "/data/shared/out/${name}_$SEASON" 2>&1 \
    | grep -E "ANALYSIS DONE|^Error|ERROR"
done
