# AccessMod notes

What was verified by running AccessMod 5.9.1 (`fredmoser/accessmod:5.9.1`, arm64 image, on a Mac
via Colima with 4 CPUs and about 5.8 GB memory) in Phase E1. The scripts are in
`scripts/accessmod/` and `scripts/run_e1.sh`.

## How it runs

- Maintained at `unige-geohealth/accessmod` (LGPL-3.0), by the University of Geneva GeoHealth
  group with WHO. R + Shiny on GRASS GIS 8.3.2, packaged as Docker images. The image includes
  AccessMod's own `r.walk.accessmod` module.
- The image is native arm64 (928 MB on disk), so no emulation is needed on Apple silicon.
- The shipped test suite (`Rscript tests/start.R`) passes all 44 checks headless in about 79 s.
- **Everything can be scripted without the web UI.** From R inside the container:
  `amProjectCreateFromDem` creates a project from a DEM, `amUploadRaster` and `amUploadVector`
  import layers, and `amAnalysisReplayExec` runs an analysis from a JSON config and exports the
  results. Configs are plain JSON (`scripts/build_accessmod_configs.py`).
- The upload functions delete the files they are given, so scripts pass temporary copies.

## Spike answers

1. **Accessibility outputs.** `rTravelTime` (uint16 minutes, 65535 = no data), `rSpeed` (int32,
   speed and mode encoded), `rFriction` (isotropic runs only) and `rNearest`, exported as
   `raster_cost_allocation` (the `cat` of the nearest facility per cell). `rNearest` is only
   produced when the config sets `"addNearest": true`.
2. **Referral outputs.** `table_referral` (every from x to pair with `distance_km` and `time_m`),
   `table_referral_nearest_by_time` and `..._by_dist`, and `vReferralNetwork`, a GeoPackage of
   path lines with `from__cat`, `to__cat`, `km` and `m`. **AccessMod does export path lines.**
3. **Path caveat.** When one run has several destinations, path pieces shared between routes are
   not repeated. In the dry test 128 of 300 path geometries were only about 28 m long even
   though their distance and time were correct. A run with one origin and `limitClosest: true`
   (or a single destination) gives one complete line: the test path was 1.48 km against a table
   distance of 2 km (rounded up). Complete paths therefore need one run per origin-destination
   pair (see Phase E4).
4. **Travel modes.** The scenario table accepts only `WALKING`, `BICYCLING` and `MOTORIZED`.
   There is no boat mode, so boats will be modelled as `MOTORIZED` on water classes in Phase E2.
5. **Barriers.** Cells with no data (or a class with speed 0) are impassable. E1 sets cells
   outside Bangladesh to no data and gives permanent water speed 0. Roads are burnt into the
   land cover raster and imported as the merged land cover, so no separate road layer is needed.
6. **Referral origins are points in the facility layer.** Arbitrary emergency start points must
   be imported as a facility layer before they can be referral origins.
7. **Facilities on impassable cells fail.** A facility on a water cell made the referral run stop
   with "No start points found in vector map". The preparation script moves such facilities to
   the nearest passable cell and records the distance.

## Run times (this Mac, 697,000 cells at 100 m, 37 facilities)

| Step | Time |
|---|---|
| Import (DEM, land cover, population, facilities) | about 2 s of R work |
| Accessibility, anisotropic, knight move, 300 min cap | 2.3 s |
| Referral, 15 origins x 20 destinations (300 pairs) | 20 s |
| Referral, 1 origin nearest-only | 3 s |
| Whole `make e1` pipeline including container start-up | about 49 s |

## Flood scenario notes (Phase E2)

- One AccessMod project holds several merged land covers (`rLandCoverMerged__dry`,
  `__flood0708`, `__flood0713`) and each analysis picks one, so a flood scenario is just another
  land-cover raster plus a scenario table.
- Every class present in the raster needs a row in the scenario table, or the run fails.
- With no boat mode, flooded cells use a `MOTORIZED` class at boat speed. This keeps slope from
  affecting the boat leg; the segment's class identifies it as a boat leg in the path.
- Boats on open water were left out on purpose. With boats faster than dry walking, flooding
  made some areas look better off. Flooding is therefore strictly slower than dry.

## Emergency-type runs (Phase E3)

- An accessibility run counts only the facilities whose `amSelect` is true in `tableFacilities`, so an
  emergency type is just another run with a different selection. The exported nearest-facility raster
  (`raster_cost_allocation`) then holds the nearest *qualifying* facility.
- All configs run in one container session (`run_analysis.R` takes many configs), which avoids the
  start-up cost of a container per run: 21 analyses in about 2 minutes.
- Facility levels are stored in the facility shapefile (`level`), so the config builder needs nothing
  beyond the shapefile and `config/`.

## Larger grid (Phase E3b)

- The extended area is 1,401 x 1,255 cells (1.76 million). In the same 5.8 GB Docker VM an accessibility
  run takes about 4 s, a referral run for 115 origins takes about 100 s, and the whole `make e3`
  pipeline (21 analyses) takes about 7 minutes. No memory changes were needed.

## Complete paths without the referral analysis (Phase E4)

AccessMod's replay/analysis functions do not expose the direction raster `r.walk.accessmod`
computes internally (see `outdir=` in its own source), so it cannot be read back after an
accessibility run. `scripts/accessmod/e4_paths.R` reruns `r.walk.accessmod` itself with the exact
inputs and flags `amAnalysisTravelTime.R` uses for an anisotropic run:

```
r.walk.accessmod -s -t -k elevation=rDem__dem@PERMANENT friction=rSpeed__<season>_<emergency> \
  start_points=<qualifying facilities> output=... outdir=... nearest=...
```

(`-s` = friction input is a speed map, matching this project's scenario tables; `-t` = "towards
facilities", matching `towardsFacilities: true` in every config; `-k` = knight's move, matching
`knightMove: true`.) Checked against the published rasters at several points, in every case both
the travel time and the nearest-facility id matched exactly. `r.drain -d` then traces one complete
path per point using this direction raster and the already-published travel-time raster as the
cost surface. One direction raster is shared by every point with the same (season, emergency); a
second one, excluding the point's own nearest facility, gives the backup path.

`r.what` returns pipe-separated fields `east|north|<label>|value`, with `*` for a null cell; the
label field is present (and blank) even when only one raster is queried, so the value is at index
4, not 3 -- worth a note, since indexing it wrong just silently returns nothing rather than an
error.
