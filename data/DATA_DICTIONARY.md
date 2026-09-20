# Data dictionary

Variables, units, missing-value conventions and allowed values for the inputs and the
editable assumption tables. Coordinates are WGS84 (EPSG:4326) unless stated.

## Inputs (`data/raw/`)

### `health_facilities_sunamganj.geojson`, `health_facilities_wide_osm_2026-09-20.geojson`
Point features from OpenStreetMap.

| Field | Meaning | Allowed values / notes |
|---|---|---|
| `osm_type`, `osm_id` | OSM element type and id | `node`, `way` or `relation`; id is an integer |
| `amenity` | OSM amenity tag | e.g. `hospital`, `clinic`, `doctors` |
| `healthcare` | OSM healthcare tag | optional, missing when not tagged |
| `name`, `name:en`, `name:bn` | Facility name | optional, may be English or Bangla, may be misspelled. Missing means unnamed |
| `operator` | Operating body | optional, missing means unknown |

The OSM `amenity` tag does not say the facility's level or services. Level and capability
are assumptions (see `config/capabilities.csv`).

### `roads_sunamganj.geojson`
LineString features from OpenStreetMap, 3,398 segments.

| Field | Meaning | Allowed values / notes |
|---|---|---|
| `osm_id` | OSM way id | integer |
| `highway` | Road class | `primary`, `secondary`, `tertiary`, `unclassified`, `residential`, `track`, `path`, `footway`, `service`, `living_street`, `construction` |
| `name` | Road name | optional, missing when not tagged |
| `surface` | Surface type | optional, missing when not tagged |

Rural OSM coverage is incomplete, so missing roads are possible (see `docs/data-gaps.md`).

### `flood_extent_sunamganj_2026-07-13.geojson`
Polygon features, 418 polygons of newly flooded area (Sentinel-1 change detection,
before 2026-06-19, during 2026-07-13). Field `id` is a polygon counter. Areas outside the
original analysis box are unmapped, not "dry".

### `upazila_boundaries_sunamganj_aoi.geojson`
Polygon features, 8 upazilas. Key fields: `adm3_pcode` (official upazila P-code, the join
key), `adm3_name` (upazila name), `adm2_name` / `adm2_pcode` (district), `adm1_name` /
`adm1_pcode` (division), `area_sqkm` (km²), `valid_on` / `valid_to` (validity dates).
Join on P-codes, never on names.

### `worldpop_2020_sunamganj_aoi.tif`
Raster, 420 x 360 cells, about 0.000833 degrees (roughly 90 m) per cell. Cell value is the
estimated number of people in the cell (WorldPop 2020, building-constrained). NoData is
`-99999`. Total for the area is 717,209 people. These are modelled estimates, not a census.

## Editable assumption tables (`config/`)

All are assumptions unless a source is given in `basis` or `target_basis`.

### `emergencies.csv`
| Field | Meaning | Allowed values |
|---|---|---|
| `emergency_id` | Machine id | `childbirth_complication`, `snakebite`, `injury_drowning`, `minor_illness` |
| `label` | Display name | text |
| `capability_column` | Column in `capabilities.csv` used for filtering | must exist in `capabilities.csv` |
| `target_minutes` | Target travel time | positive integer, minutes |
| `target_basis` | Where the target came from | text; currently placeholders |

### `capabilities.csv`
| Field | Meaning | Allowed values |
|---|---|---|
| `facility_level` | Facility level | `community_clinic`, `union_health_family_welfare_centre`, `upazila_health_complex`, `district_general_hospital`, `medical_college_hospital` |
| `minor_illness`, `childbirth_complication`, `snakebite`, `injury_drowning` | Whether the level can handle the emergency | `yes`, `no`, `basic`, `first_aid`. Only `yes` qualifies as the destination; `basic` and `first_aid` are fallbacks |
| `basis` | Source of the value | text; currently `assumption` |

### `speeds.csv`
| Field | Meaning | Allowed values |
|---|---|---|
| `class` | Road or land class | e.g. `highway_primary`, `off_road_dry_land`, `flooded_land`, `water_country_boat` |
| `mode` | Travel mode | `walk`, `bicycle`, `motorized`, `boat` |
| `speed_kmh` | Speed | positive number, km/h |
| `season` | When the row applies | `dry`, `flood`, `both` |
| `basis` | Source of the value | text; currently `assumption` |

## Missing values

Empty string or absent property means "not tagged" or "unknown". No value is imputed.
