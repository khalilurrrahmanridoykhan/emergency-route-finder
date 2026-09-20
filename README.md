# Emergency Route Finder

[![CI](https://github.com/khalilurrrahmanridoykhan/emergency-route-finder/actions/workflows/ci.yml/badge.svg)](https://github.com/khalilurrrahmanridoykhan/emergency-route-finder/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Flood-aware emergency referral routing for Sunamganj, Bangladesh, built on
[WHO AccessMod](https://github.com/unige-geohealth/accessmod).

> **This is an analysis and demonstration project. It is not for real emergencies.**
> Routes, times and facility recommendations are model outputs based on public data and
> stated assumptions. Do not use them to make real dispatch or care decisions.

## The question

An emergency happens at a point. What kind of emergency is it, which facility can handle
it, how long does it take to get there, and which path should the person take, in the dry
season and during a flood?

For a start point, an emergency type and a season, the goal is one record:

| Field | Example |
|---|---|
| Emergency type | Snakebite |
| Right facility | A facility assumed to stock antivenom |
| Travel time | e.g. 48 min (dry) / 95 min (flood) |
| Path | Route line (GeoJSON) |
| Travel mode | Motorbike or ambulance (dry), boat leg plus walking (flood) |
| Backup facility | Second-best qualifying facility |
| Warning | e.g. a road cut in flood, boat route used |

Emergency types: childbirth complication, snakebite, injury or drowning, minor illness.

## Method

1. **Right facility.** Each emergency type maps to the facility levels assumed able to
   handle it (`config/capabilities.csv`).
2. **Travel time.** AccessMod builds a friction surface from land cover, roads, barriers
   and terrain using a travel scenario table (`config/speeds.csv`) and computes travel time
   and referral to the nearest qualifying facility.
3. **Path.** AccessMod gives time and destination but not turn-by-turn routes, so the path
   is traced on the same cost surface with GRASS `r.drain` and cross-checked against OSRM.
4. **Flood.** The same run is repeated with the mapped flood extent as a barrier or slow
   class, flooded roads removed or slowed, and a boat mode added.

## Assumptions are labeled

Public data does not say which facility has antivenom or a surgeon, and boat and
flood-walking speeds are estimates. All of these are editable assumptions in `config/`,
each marked `assumption`, and are shown wherever results are shown.

## Status

Phase E0 (scope, data inventory, repo setup) is done. See [docs/ROADMAP.md](docs/ROADMAP.md)
for the phases and [docs/data-gaps.md](docs/data-gaps.md) for what the inventory found,
including that the original area holds no district-level hospital.

## Data

All inputs are public: OpenStreetMap (ODbL), WorldPop (CC BY 4.0), HDX administrative
boundaries, and a Sentinel-1 flood extent. Start points are synthetic. Provenance,
licences and checksums are in [data/README.md](data/README.md) and
[data/source-manifest.json](data/source-manifest.json).

## Quick start

```sh
make setup   # create .venv and install requirements
make test    # run the tests
```

AccessMod runs in Docker and is set up in Phase E1.

## Related

Reuses public inputs from
[sunamganj-flood-accessibility-gis](https://github.com/khalilurrrahmanridoykhan/sunamganj-flood-accessibility-gis)
and plans an OSRM cross-check based on
[facility-access-equity](https://github.com/khalilurrrahmanridoykhan/facility-access-equity).
There is no code coupling with either.

## Contributing and licence

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and
[SECURITY.md](SECURITY.md). Code is licensed under [Apache 2.0](LICENSE); data licences are
listed in `data/README.md`. If you use this work, see [CITATION.cff](CITATION.cff).
