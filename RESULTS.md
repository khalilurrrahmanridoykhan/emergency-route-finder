# Results

Real numbers per phase. Everything here rests on public data and labeled assumptions, and is
not for real emergencies.

## Phase E1: dry-season baseline (AccessMod)

Area: the wider box (90.95, 24.4, 91.75, 25.2), analysed on a 100 m UTM 46N grid of 797 x 875
cells, 5,113,180 people (WorldPop 2020, cells outside Bangladesh removed). Travel to the nearest
of 37 facilities of any level, anisotropic, knight move, with the dry speed table in
`config/speeds.csv` (all speeds are assumptions).

| Reach a facility within | People | Share |
|---|---|---|
| 30 min | 2,824,022 | 55.2% |
| 60 min | 4,494,324 | 87.9% |
| 120 min | 4,839,362 | 94.6% |
| 240 min | 4,924,917 | 96.3% |
| No route within 300 min | 175,236 | 3.4% |

Mean travel time over reachable cells: 46.1 min. The longest times are in the haor area in the
south-west, where permanent water blocks routes (`docs/img/e1_dry_travel_time.png`).

Files: `results/e1_coverage_dry.csv`, `results/e1_catchments_dry.csv` (people per nearest
facility) and `results/e1_referral_nearest_by_time_dry.csv` (nearest hospital-type destination
for each of 15 clinics).

Caveats:
- "Any facility" includes community clinics. Emergency-specific results (only qualifying
  facilities) come in Phase E3.
- The 37 facilities include name-guessed levels; the "hospital" group in the referral test mixes
  health complexes, union centres and general hospitals.
- The land cover is a single 2021 snapshot, so dry-season haor water is approximate.
- Sunamganj General Hospital serves about 284,000 people in the nearest-facility catchment.

## Phase E2: flood scenario (AccessMod)

**Flood layers.** Newly flooded land from Sentinel-1 (VV backscatter, Otsu threshold, before
2026-06-19), same method as the earlier flood mapping in this project family. Two "during" dates:

| Date | Orbit | Share of the grid observed | Flooded share of land |
|---|---|---|---|
| 2026-07-08 (main) | 41, same as the "before" scene | 97.9% | 5.4% |
| 2026-07-13 | 114 | 57.1% | 2.9% |

2026-07-08 is the main layer because it covers almost the whole area and shares the orbit of the
"before" scene. The 2026-07-13 scene misses the eastern part of the area, so its results
understate the flood there. Validation of the mapping against the earlier 2026-07-13 flood layer,
inside the original box: 4.2% flooded here vs 4.1% there, IoU 0.75 (the scene covers 87% of that
box).

**Flood scenario.** Flooded land cells and submerged road pieces become one class at 2 km/h
(boat or wading, slower than dry walking); open water stays impassable in both seasons, so the
difference isolates the flood. All speeds are assumptions in `config/speeds.csv`.

**People within reach of a facility (any level; 5.1 million people):**

| Within | Dry | Flood 07-08 | Flood 07-13 (partial) |
|---|---|---|---|
| 30 min | 55.2% | 52.4% | 53.8% |
| 60 min | 87.9% | 86.4% | 86.8% |
| 120 min | 94.6% | 94.2% | 94.3% |
| No route within 300 min | 3.43% | 3.51% | 3.58% |

**Flood 2026-07-08 impact:** mean travel time 46.1 to 48.4 min; 155,193 people gain at least
15 min; nobody gains 60 min or more; 75,393 people are pushed from within 60 min to beyond it;
4,239 lose every route; 241,396 people get a different nearest facility.

**Referral, 15 clinics to hospital-type destinations:** no clinic changes its nearest
destination and the median extra time is 0 min (one clinic gains 1 min). Their short routes
avoid the flooded stretches.

**Largest upazila effects (people pushed beyond 60 min, 07-08):** Moulvibazar Sadar 34,207
(eastern area only observed on 07-08, not cross-checked), Madan 5,879, Nabiganj 5,327,
Baniachong 4,849, Ajmiriganj 4,128, Derai 3,541. Shalla, the top priority in the earlier
road-network study, changes very little here: mean 22.0 to 22.3 min, 42 people pushed beyond 60.

**Check against the earlier road-network study (same flood date, 8 upazilas):**

| Measure | Rank agreement (Spearman) | Totals, earlier vs here |
|---|---|---|
| People in flooded areas | 0.90 | 20,904 vs 38,380 |
| People within 500 m of lost or flooded road | 0.76 | 87,902 vs 191,041 |

The ranking agrees; totals here are about 2 times larger. Causes: whole 100 m cells count as
flooded when half their pixels are, the earlier polygons were cleaned and simplified, and the
earlier study counted roads that lost connectivity while this one counts flooded road pieces.
A travel-time measure ("pushed beyond 60 min") does not rank upazilas like the earlier
road-loss measure (Spearman -0.12 for 07-08 and 0.44 for 07-13, not significant), because
it also uses facilities outside the original box and lets people walk off-road.

**Caveats:**
- Sentinel-1 "newly flooded" misses land already wet on the "before" date, so haor flooding is
  understated. The east of the area rests on one date only (07-08).
- The two flood dates give visibly different local results (for example Madan: +10.7 min on
  07-08, +29.2 min on 07-13). The flood date is a large uncertainty (Phase E7).
- Off-road walking at 3 km/h anywhere softens the effect of road cuts. Wet fields would be
  slower. Also to be varied in Phase E7.
- Facilities are assumed open and reachable during the flood; nothing models boat availability.
- The effect on the four emergency types comes in Phase E3.

Files: `results/e2_coverage.csv`, `e2_flood_impact.csv`, `e2_upazila_change.csv`,
`e2_referral_change.csv`, `e2_validation_vs_earlier_study.csv`, map `docs/img/e2_dry_vs_flood.png`.
