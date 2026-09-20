# Roadmap

One branch, one pull request and one tag per phase (`phase-e0` to `phase-e7`). Each phase
ends with a "Done when" gate.

| Phase | Name | Status |
|---|---|---|
| E0 | Scope, data inventory and public repo setup | done |
| E1 | AccessMod setup and dry-season baseline (includes an output spike) | not started |
| E2 | Flood scenario: flood extent, flooded roads, boat mode | not started |
| E3 | Emergency types and the facility capability model | not started |
| E4 | Actual paths (GRASS `r.drain`) and OSRM cross-check | not started |
| E5 | The `route(point, emergency, season)` function | not started |
| E6 | Click-a-point web map | not started |
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
Run AccessMod in Docker, import DEM, land cover, roads, population and facilities, write
the travel scenario table, and run accessibility and referral analysis on the dry network.
Spike questions: what AccessMod exports, how barriers and land cover are imported, run
time, and whether runs can be scripted. Answers go in `docs/accessmod-notes.md`.

### E2: Flood scenario
Import the flood extent as a barrier or slow class, remove or slow flooded roads, add a
boat mode, and compare dry and flood travel times and unreachable areas.

### E3: Emergency types and the capability model
Classify facilities into levels, apply `config/capabilities.csv`, and run the analysis per
emergency type using only qualifying facilities.

### E4: Actual paths and cross-check
Least-cost paths from the cost surface, cross-checked against OSRM on the dry road-only
case.

### E5: The route-finder function
`route(lon, lat, emergency, season)` returning the record above, with tests.

### E6: Click-a-point web map
Static GitHub Pages site over a precomputed grid of start points.

### E7: Validation, limits and release
Sensitivity checks on speeds and flood extent, `RESULTS.md`, and the `v0.1.0` release.
