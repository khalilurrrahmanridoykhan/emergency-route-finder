#!/bin/sh
# Rebuild the AccessMod project from prepared inputs and run the analyses for each land-cover tag.
# Needs Docker running (colima start) and the inputs from scripts/fetch_inputs.py.
#   TAGS="dry flood0708" FLOOD_DATES="2026-07-08" scripts/run_accessmod.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ACCESSMOD_IMAGE:-fredmoser/accessmod:5.9.1}"
VOLUME="${ACCESSMOD_VOLUME:-am5_e1_db}"
TAGS="${TAGS:-dry}"
FLOOD_DATES="${FLOOD_DATES:-}"
PY="$ROOT/.venv/bin/python"

# shellcheck disable=SC2086
"$PY" "$ROOT/scripts/prepare_accessmod_inputs.py" --flood $FLOOD_DATES > /dev/null
for tag in $TAGS; do
  "$PY" "$ROOT/scripts/build_accessmod_configs.py" --tag "$tag"
done

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
for tag in $TAGS; do
  for name in accessibility referral; do
    rm -rf "$ROOT/data/interim/accessmod_out/${name}_$tag"
    run /scripts/run_analysis.R "/data/shared/in/replay_${name}_$tag.json" "/data/shared/out/${name}_$tag" 2>&1 \
      | grep -E "ANALYSIS DONE|^Error|ERROR"
  done
done
