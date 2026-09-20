# Results

Real numbers per phase. Everything here rests on public data and labeled assumptions, and is
not for real emergencies.

## Phase E1: dry-season baseline (AccessMod)

Area: the wider box (90.95, 24.4, 91.75, 25.2), analysed on a 100 m UTM 46N grid of 797 x 875
cells, 5,084,411 people (WorldPop 2020, cells outside the official upazila polygons removed).
Travel to the nearest of 35 facilities of any level, anisotropic, knight move, with the dry speed
table in `config/speeds.csv` (all speeds are assumptions).

| Reach a facility within | People | Share |
|---|---|---|
| 30 min | 2,710,868 | 53.3% |
| 60 min | 4,449,270 | 87.5% |
| 120 min | 4,810,594 | 94.6% |
| 240 min | 4,896,148 | 96.3% |
| No route within 300 min | 175,236 | 3.45% |

Mean travel time over reachable cells: 46.7 min. The longest times are in the haor area in the
south-west, where permanent water blocks routes (`docs/img/e1_dry_travel_time.png`).

Files: `results/e1_coverage_dry.csv`, `results/e1_catchments_dry.csv` (people per nearest
facility) and `results/e1_referral_nearest_by_time_dry.csv` (nearest hospital-type destination
for each of 15 clinics).

**Correction made in Phase E3.** The first E1 and E2 runs included two "PHC" features on the
border line ("Dangar, PHC" and "Ryngku, PHC", Indian-style names) that lie in no official upazila
polygon; Ryngku alone had a 193,000-person catchment. They are now excluded, the country mask uses
the official upazila polygons, and the E1 and E2 numbers here were regenerated.

Caveats:
- "Any facility" includes community clinics. Emergency-specific results are in Phase E3.
- The land cover is a single 2021 snapshot, so dry-season haor water is approximate.

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

**People within reach of a facility (any level; 5.08 million people):**

| Within | Dry | Flood 07-08 | Flood 07-13 (partial) |
|---|---|---|---|
| 30 min | 53.3% | 50.5% | 51.9% |
| 60 min | 87.5% | 86.0% | 86.4% |
| 120 min | 94.6% | 94.2% | 94.2% |
| No route within 300 min | 3.45% | 3.53% | 3.60% |

**Flood 2026-07-08 impact:** mean travel time 46.7 to 49.0 min; 155,504 people gain at least
15 min; nobody gains 60 min or more; 78,212 people are pushed from within 60 min to beyond it;
4,239 lose every route; 239,302 people get a different nearest facility.

**Referral, 15 clinics to hospital-type destinations:** no clinic changes its nearest
destination; 14 keep the same time and one gains 1 min. Their short routes avoid the flooded
stretches.

**Largest upazila effects (people pushed beyond 60 min, 07-08):** Moulvibazar Sadar 34,207
(eastern area only observed on 07-08, not cross-checked), Madan 5,879, Nabiganj 5,327,
Dowarabazar 4,924, Baniachong 4,849, Ajmiriganj 4,128, Derai 3,541. Shalla, the top priority in the earlier
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

## Phase E3: emergency types and the capability model

**Facility levels.** The 35 facilities are classified from OSM names with keyword rules
(`config/facility_rules.csv`) and 5 manual overrides (`config/facility_overrides.csv`), then mapped to
emergencies through the assumption table `config/capabilities.csv` (also in `docs/capabilities.md`):
13 community clinics, 5 union health and family welfare centres, 12 Upazila Health Complexes, 1
district hospital (Sunamganj General Hospital, assumed to be the district hospital) and 4 private or
unclassified facilities (2 have no name). The list is in `results/e3_facility_levels.csv`.

**Target times (sources in `config/emergencies.csv`):** 120 min for childbirth complication (WHO 2-hour
emergency obstetric care access indicator), snakebite (2 hours is the usual maximum ideal time to
antivenom in accessibility studies) and injury or drowning (Lancet Commission on Global Surgery, 2 hours
to essential surgical care); 60 min for minor illness (common primary-care convention). These are
population access standards, not clinical time limits. The sources were checked through search
summaries, not read in full.

**People within the target time (5.08 million people):**

| Emergency | Qualifying facilities | Target | Dry | Flood 07-08 | Flood 07-13 (partial) |
|---|---|---|---|---|---|
| Childbirth complication | 13 | 120 min | 94.3% | 93.6% | 93.9% |
| Snakebite | 13 | 120 min | 94.3% | 93.6% | 93.9% |
| Injury or drowning | 13 | 120 min | 94.3% | 93.6% | 93.9% |
| Minor illness | 35 | 60 min | 87.5% | 86.0% | 86.4% |
| Snakebite, antivenom only at the district hospital | 1 | 120 min | 56.1% | 51.2% | 55.2% |

**What this shows**
- Under the current assumption table, childbirth, snakebite and injury or drowning qualify the same 13
  facilities (12 Upazila Health Complexes and the district hospital), so their results are identical.
  They would only differ if a source shows that some health complexes lack emergency obstetric care,
  antivenom or surgery. Public OSM data cannot show that.
- The antivenom assumption matters most. If only the district hospital stocks antivenom, coverage in
  2 hours falls from 94.3% to 56.1% in the dry season, and to 51.2% in the flood; 244,477 people would be
  pushed beyond 2 hours by the flood and 27,823 would lose every route (5.6% have no route within 300
  min even in the dry season).
- The flood effect for the 13-facility emergencies: 33,625 people pushed beyond 2 hours, a
  population-weighted 3.7 extra minutes.
- Upazilas with the lowest childbirth coverage in the dry season are mostly ones cut by the edge of the
  analysis area (see below). Among sizeable ones: Itna 48.2%, Mithamain 75.0%, Khaliajuri 85.4%, Madan
  88.7% (73.7% in the flood), Baniachong 93.5%.

**Caveats**
- **Facilities outside the box are not modelled.** The Habiganj district hospital lies just south of the
  box and the Sylhet, Moulvibazar, Netrokona and Kishoreganj hospitals just outside it. This lowers
  coverage near the edges and hits the one-facility snakebite case hardest. Extending the area (with a
  facility buffer) is the main improvement to make before relying on these numbers.
- The capability table is an assumption. So is treating "Sunamganj General Hospital" as the district
  hospital.
- Facilities are assumed open and reachable in the flood, and hospital capacity is not modelled.

Files: `results/e3_coverage.csv`, `e3_flood_effect.csv`, `e3_facility_levels.csv` (with each facility's
nearest-qualifying catchment), `e3_upazila_within_target.csv`, and `docs/img/e3_emergency_types.png`.
