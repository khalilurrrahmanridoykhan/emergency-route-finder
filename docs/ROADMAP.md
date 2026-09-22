# Roadmap

One branch, one pull request and one tag per phase (`phase-e0` to `phase-e7`). Each phase
ends with a "Done when" gate.

| Phase | Name | Status |
|---|---|---|
| E0 | Scope, data inventory and public repo setup | done |
| E1 | AccessMod setup and dry-season baseline (includes an output spike) | done |
| E2 | Flood scenario: flood extent, flooded roads, boat mode | done |
| E3 | Emergency types and the facility capability model | done |
| E3b | Extend the analysis area with a facility buffer, check the population layer | done |
| E4 | Complete paths (`r.walk.accessmod` + `r.drain`) and OSRM cross-check | done |
| E5 | The `route(point, emergency, season)` function | done |
| E6 | Click-a-point web map | done |
| E7 | Validation, limits and release (`v0.1.0`) | not started |

## What the tool will return

For a start point, an emergency type and a season:

| Field | Meaning |
|---|---|
| Emergency type | Childbirth complication, snakebite, injury or drowning, minor illness |
| Right facility | Nearest facility assumed able to handle that emergency |
| Travel time | Minutes, for the chosen season |
| Path | Route line as GeoJSON |
| Travel mode | Motorized, bicycle, walk, or a boat leg in flood |
| Backup facility | Second-best qualifying facility with its own time and path |
| Warning | For example a cut road, or no qualifying facility reachable |

## Phases

### E0: Scope, data inventory and public repo setup
Public repo with description, topics, labels, milestones, licence, citation, contributing
guide, code of conduct, security policy, issue and PR templates, CI, and the data
inventory. **Done.** See `docs/data-gaps.md` for what the inventory found.

### E1: AccessMod setup and dry-season baseline
**Done.** AccessMod 5.9.1 runs headless in Docker, scripted end to end (`make e1`, about 49 s).
The spike answers are in `docs/accessmod-notes.md`; the dry-season numbers are in `RESULTS.md`.
Main finding: AccessMod's referral analysis does export path lines, but shared route pieces are
not repeated, so a complete path needs one run per origin-destination pair.

### E2: Flood scenario
**Done.** Sentinel-1 flood layers for the whole wider area (main date 2026-07-08, comparison
2026-07-13), flooded land and submerged road pieces modelled at boat or wading speed, dry-vs-flood
comparison with a check against the earlier road-network study. See `RESULTS.md`. The flood
effect in this model is modest (mean +2.3 min, 75,000 people pushed beyond 60 min), and it is
sensitive to the flood date.

### E3: Emergency types and the capability model
**Done.** Facilities are classified into levels (keyword rules plus manual overrides), mapped to
emergencies through an editable assumption table, and AccessMod is run once per emergency type and
season with only the qualifying facilities selected. Target times now cite sources. See
`RESULTS.md` and `docs/capabilities.md`. Main findings: three emergency types share the same 13
qualifying facilities under the current table, and a strict antivenom assumption cuts 2-hour coverage
from 94.3% to 56.1%.

### E3b: Extend the analysis area
**Done.** The area now reaches west to 90.60, east to 92.00 and south to 24.05, taking in the
neighbouring district hospitals; roads, land cover, DEM, population, facilities and flood mapping were
refetched and E1 to E3 were rerun (`RESULTS.md` compares before and after). Two facility errors were
fixed on the way (duplicate filter, laboratories), and WorldPop was checked against the 2022 census.

### E4: Complete paths and cross-check
**Done.** AccessMod's own referral export deduplicates shared route segments across a
multi-destination run (found in E1), so this phase reruns `r.walk.accessmod` itself (verified to
reproduce AccessMod's own published rasters exactly) to get a movement-direction raster, then
traces one complete path per point with GRASS `r.drain`. 40 synthetic points, dry and flood
0708, primary and backup facility, 160 complete paths, cross-checked against OSRM for the dry
case (median overlap 0.97). See `RESULTS.md` and `docs/accessmod-notes.md`.

### E5: The route-finder function
**Done.** `scripts/route.py`: `route(lon, lat, emergency)` returns the full dry-and-flood record
for one point, reusing Phase E4's r.walk.accessmod + r.drain technique on demand. A fast, Docker-free
pre-check on the Phase E3 rasters answers "no route" in about a second; a real route takes about
30 s (fresh direction rasters, no caching yet). Verified to reproduce two of Phase E4's 40 points
exactly. See `RESULTS.md`.

### E6: Click-a-point web map
**Done.** A static page (`docs/index.html`, `docs/app.js`, Leaflet) over a precomputed grid of 335
points x 4 emergency types x 2 seasons (2,680 evaluations, primary route only -- see
`scripts/accessmod/grid_paths.R`). A click snaps to the nearest grid point; the page shows the
right facility, time, mode, target status and flood warnings, with links to the assumption table
and full results. See `RESULTS.md`.

### E7: Validation, limits and release
Sensitivity checks on speeds and flood extent, `RESULTS.md`, and the `v0.1.0` release.
