# Data

All inputs are public. Nothing here is real patient, incident, ambulance or household
data. Emergency start points used later in the project are synthetic.

Provenance, licence, checksum and retrieval date for every file are in
[`source-manifest.json`](source-manifest.json). Edit that file and this table together.

## Inputs (`raw/`)

| File | What it is | Source | Licence |
|---|---|---|---|
| `flood_extent_sunamganj_2026-07-13.geojson` | Newly flooded area, Sentinel-1 change detection (2026-06-19 vs 2026-07-13) | Sentinel-1 RTC via Microsoft Planetary Computer, method from `geohealth-risk-mapping` | Copernicus open data; derived layer |
| `health_facilities_sunamganj.geojson` | 13 health facilities in the original analysis area | OpenStreetMap | ODbL 1.0 |
| `roads_sunamganj.geojson` | 3,398 road segments in the original analysis area | OpenStreetMap (Overpass) | ODbL 1.0 |
| `upazila_boundaries_sunamganj_aoi.geojson` | 8 upazilas, keyed on `adm3_pcode` | HDX cod-ab-bgd (BBS/ITOS via UNOCHA ROAP) | As stated on the HDX page |
| `worldpop_2020_sunamganj_aoi.tif` | Population raster, 717,209 people | WorldPop 2020 | CC BY 4.0 |
| `health_facilities_osm_extended.geojson` | 221 OSM hospital, clinic and doctors features in the analysis area (frozen snapshot) | OpenStreetMap (Overpass) | ODbL 1.0 |

The first five files were prepared for the earlier, smaller study area in
[`sunamganj-flood-accessibility-gis`](https://github.com/khalilurrrahmanridoykhan/sunamganj-flood-accessibility-gis),
copied here unchanged (WGS84 versions only). They cover the original box only; the analysis now uses
the extended inputs below. The facility snapshot is made by `scripts/fetch_inputs.py` and frozen in
git, because Overpass results change over time.

## Fetched inputs (`cache/`, not committed)

`scripts/fetch_inputs.py` downloads these into `data/cache/`. Checksums and retrieval dates are
in `source-manifest.json` (OSM extracts change over time, so a rerun may differ slightly).

| File | What it is | Source | Licence |
|---|---|---|---|
| `osm_roads_wide.json` | 73,559 OSM highway ways in the analysis area | OpenStreetMap (Overpass) | ODbL 1.0 |
| `bgd_ppp_2020_constrained.tif` | WorldPop 2020 constrained population, Bangladesh | WorldPop | CC BY 4.0 |
| `worldcover_wide_4326.tif` | ESA WorldCover 2021 land cover | Microsoft Planetary Computer | CC BY 4.0 |
| `dem_wide_4326.tif` | Copernicus DEM GLO-30 | Microsoft Planetary Computer | Copernicus DEM licence |
| `bgd_adm3_wide.geojson` | 76 upazila boundaries with official P-codes |
| `bgd_admpop_adm3_2022.csv` | 2022 census population by upazila, used only to check WorldPop | HDX cod-ps-bgd | CC BY-IGO | HDX cod-ab-bgd | CC BY-IGO |

`scripts/prepare_accessmod_inputs.py` turns these into AccessMod-ready layers in
`data/interim/` (a 100 m UTM 46N grid, roads burnt into the land cover, cells outside
the official upazila polygons set to no data). Nothing in `cache/` or `interim/` is committed.

Phase E6's web-map grid (`e6_grid_points.csv`, `e6_tasks.csv`) is generated the same way and is
also not committed; its output -- what the published map actually serves -- is committed under
`docs/data/` instead, since GitHub Pages needs it.

Flood layers (Phase E2) are built by `scripts/build_flood_extent.py` from Sentinel-1 RTC on
Microsoft Planetary Computer into `data/interim/flood/` (before 2026-06-19; during 2026-07-08 and
2026-07-13). `raw/q3_population_by_upazila.csv` is a small table from the earlier road-network
study, used only to check the results.

## Analysis area

Bounding box `(90.60, 24.05, 92.00, 25.20)`, a 100 m UTM 46N grid of 1,401 x 1,255 cells (the largest
UTM rectangle inside the box). It was widened in Phase E3b from the earlier box
`(90.95, 24.4, 91.75, 25.2)` so that the district hospitals of Habiganj, Sylhet, Moulvibazar,
Netrokona and Kishoreganj are inside it. The original flood-mapping box `(91.15, 24.5, 91.5, 24.8)` spans
8 upazilas; the upazila spelled "Dirai" in the flood-mapping notes is "Derai" in the official boundary
data, and all joins here use `adm3_pcode`, never names.

## Known gaps (details in `docs/data-gaps.md`)

- Facility levels are guessed from OSM names; 62 of the 131 facilities are private or unclassified and
  their capabilities are unknown. OSM may be missing government facilities.
- The Sentinel-1 flood layers cover only part of the area (72.8% on 2026-07-08, 33.9% on
  2026-07-13); unobserved cells are treated as not flooded.
- Water comes from the ESA WorldCover water class, a single 2021 snapshot, so haor water in the dry
  and wet seasons is approximate.
- WorldPop is a modelled population layer; per-upazila totals agree with the 2022 census within about
  10% for most upazilas but not for cities and haor upazilas (`RESULTS.md`).

## Cross-check dependency (Phase E4, not part of this repo)

`scripts/cross_check_osrm.py` reads (never modifies) the pre-built OSRM road network from the
sibling `facility-access-equity` repo (`../facility-access-equity/data/raw/bangladesh-latest.osrm*`,
built from a Geofabrik Bangladesh OSM extract). No code coupling; running the cross-check needs
that repo checked out next to this one and an `osrm-routed` server started against its files.

## Attribution

Contains information from OpenStreetMap contributors (ODbL 1.0), WorldPop
(CC BY 4.0), and Humanitarian Data Exchange boundary data.

Large derived rasters are not committed. They are regenerated by scripts or attached to
a release, and the manifest records checksums.
