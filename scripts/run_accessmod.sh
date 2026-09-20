#!/bin/sh
# Rebuild the AccessMod project from prepared inputs and run the analyses for each land-cover tag,
# plus one accessibility run per emergency type (only qualifying facilities count).
#   TAGS="dry flood0708" FLOOD_DATES="2026-07-08" EMERGENCIES="snakebite minor_illness" scripts/run_accessmod.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ACCESSMOD_IMAGE:-fredmoser/accessmod:5.9.1}"
VOLUME="${ACCESSMOD_VOLUME:-am5_e1_db}"
TAGS="${TAGS:-dry}"
FLOOD_DATES="${FLOOD_DATES:-}"
EMERGENCIES="${EMERGENCIES:-}"
PY="$ROOT/.venv/bin/python"

# shellcheck disable=SC2086
"$PY" "$ROOT/scripts/prepare_accessmod_inputs.py" --flood $FLOOD_DATES > /dev/null
rm -f "$ROOT"/data/interim/accessmod/replay_*.json
for tag in $TAGS; do
  # shellcheck disable=SC2086
  "$PY" "$ROOT/scripts/build_accessmod_configs.py" --tag "$tag" --emergencies $EMERGENCIES > /dev/null
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

# One container run for all configs; names decide the export folders.
configs=""
for f in "$ROOT"/data/interim/accessmod/replay_*.json; do
  configs="$configs /data/shared/in/$(basename "$f")"
  rm -rf "$ROOT/data/interim/accessmod_out/$(basename "$f" .json | sed 's/^replay_//')"
done
# shellcheck disable=SC2086
run /scripts/run_analysis.R /data/shared/out $configs 2>&1 | grep -E "ANALYSIS DONE|ERROR"
