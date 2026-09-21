# Results

Real numbers per phase. Everything here rests on public data and labeled assumptions, and is
not for real emergencies. All numbers are for the current analysis area (extended in Phase E3b);
`docs/data-gaps.md` and each phase's caveats say where they should not be trusted.

**Analysis area:** (90.60, 24.05, 92.00, 25.20), a 100 m UTM 46N grid of 1,401 x 1,255 cells with
17,216,776 people (WorldPop 2020, cells outside the official upazila polygons removed), 76
upazilas of Sunamganj, Sylhet, Moulvibazar, Habiganj, Netrokona, Kishoreganj and neighbours, and
131 health facilities of which 62 are private or unclassified.

## Phase E1: dry-season baseline (AccessMod)

Travel to the nearest facility of any level, anisotropic, knight move, with the dry speed table in
`config/speeds.csv` (all speeds are assumptions).

| Reach a facility within | People | Share |
|---|---|---|
| 30 min | 12,015,772 | 69.8% |
| 60 min | 16,195,879 | 94.1% |
| 120 min | 16,818,162 | 97.7% |
| 240 min | 16,922,594 | 98.3% |
| No route within 300 min | 290,606 | 1.69% |

Mean travel time over reachable cells: 39.1 min. Map: `docs/img/e1_dry_travel_time.png`. Files:
`results/e1_coverage_dry.csv`, `e1_catchments_dry.csv`, `e1_referral_nearest_by_time_dry.csv`.

Caveats: "any facility" includes community clinics and unverified private facilities; land cover is a
single 2021 snapshot, so dry-season haor water is approximate.

## Phase E2: flood scenario (AccessMod)

**Flood layers.** Newly flooded land from Sentinel-1 (VV backscatter, Otsu threshold, before
2026-06-19), same method as the earlier flood mapping in this project family.

| Date | Orbit | Share of the area observed | Flooded share of land |
|---|---|---|---|
| 2026-07-08 (main) | 41, same as the "before" scene | 72.8% | 4.8% |
| 2026-07-13 | 114 | 33.9% | 2.0% |

2026-07-08 is the main layer because it shares the orbit of the "before" scene and covers the most.
**Neither date covers the whole area**: on 07-08, 6.2 million people (36%) live in cells with no flood
observation, and on 07-13 it is 12.6 million (73%). Unobserved cells are treated as not flooded, so
the flood effect is understated there. Validation of the mapping method against the earlier
2026-07-13 flood layer inside the original small box (done on the smaller area): 4.2% flooded here vs
4.1% there, IoU 0.75.

**Flood scenario.** Flooded land cells and submerged road pieces become one class at 2 km/h (boat or
wading, slower than dry walking); open water stays impassable in both seasons, so the difference
isolates the flood. All speeds are assumptions in `config/speeds.csv`.

| Within | Dry | Flood 07-08 | Flood 07-13 (partial) |
|---|---|---|---|
| 30 min | 69.8% | 67.0% | 69.2% |
| 60 min | 94.1% | 93.1% | 93.5% |
| 120 min | 97.7% | 97.5% | 97.6% |
| No route within 300 min | 1.69% | 1.69% | 1.69% |

**Flood 2026-07-08 impact:** mean travel time 39.1 to 41.5 min; 381,632 people gain at least 15 min;
nobody gains 60 min or more; 162,413 people are pushed from within 60 min to beyond it; nobody loses
every route; 517,850 people get a different nearest facility.

**Largest upazila effects (people pushed beyond 60 min, 07-08):** Nasirnagar 22,715, Bahubal 20,063,
Moulvibazar Sadar 16,663, Sreemangal 15,471, Chunarughat 12,703, Kamalganj 11,679, Lakhai 10,773 (all
in the south-east, where the 07-08 scene observed the flood). In Sunamganj, Derai has 3,522. Shalla, the
top priority in the earlier road-network study, changes very little: mean 22.0 to 22.3 min, 44 people
pushed beyond 60.

**Referral, 115 clinics to hospital-type destinations:** only 2 clinics are slower in the flood
(by 1 and 2 min) and none is re-routed. 64 clinics show a different nearest destination at exactly the
same travel time, which is a tie between neighbouring hospitals, not a re-route.

**Check against the earlier road-network study (same flood date, 8 upazilas):**

| Measure | Rank agreement (Spearman) | Totals, earlier vs here |
|---|---|---|
| People in flooded areas | 0.90 | 20,904 vs 44,283 |
| People within 500 m of lost or flooded road | 0.76 | 87,902 vs 195,290 |

The ranking agrees; totals here are about 2 times larger. Causes: whole 100 m cells count as flooded
when half their pixels are, the earlier polygons were cleaned and simplified, and the earlier study
counted roads that lost connectivity while this one counts flooded road pieces. A travel-time measure
("pushed beyond 60 min") agrees weakly and inconsistently with the earlier road-loss measure
(Spearman 0.10 for 07-08 and 0.68 for 07-13, 8 upazilas), because it also uses facilities outside the
original box and lets people walk off-road.

**Caveats**
- Sentinel-1 "newly flooded" misses land already wet on the "before" date, so haor flooding is
  understated, and the flood layer covers only part of the area (above).
- The two flood dates give different local results, so the flood date is a large uncertainty (Phase E7).
- Off-road walking at 3 km/h anywhere softens the effect of road cuts (also for Phase E7).
- Facilities are assumed open and reachable during the flood; nothing models boat availability.

Files: `results/e2_coverage.csv`, `e2_flood_impact.csv`, `e2_upazila_change.csv`,
`e2_referral_change.csv`, `e2_validation_vs_earlier_study.csv`, map `docs/img/e2_dry_vs_flood.png`.

## Phase E3: emergency types and the capability model

**Facility levels.** The 131 facilities are classified from OSM names with keyword rules
(`config/facility_rules.csv`, including exclusion of laboratories, diagnostic centres, eye hospitals
and veterinary features) and 7 manual overrides (`config/facility_overrides.csv`), then mapped to
emergencies through the assumption table `config/capabilities.csv` (also in `docs/capabilities.md`):
13 community clinics, 6 union health and family welfare centres, 37 Upazila Health Complexes, 5 district
hospitals (Sunamganj General, Habiganj General, Moulvibazar Sadar, Netrokona Sadar and the Kishoreganj
general hospital), 8 medical college hospitals (two of them appear twice in OSM) and 62 private or
unclassified facilities. District hospital status for Sunamganj, Habiganj and Kishoreganj rests on
overrides that read the OSM names; see the list in `results/e3_facility_levels.csv`.

**Target times (sources in `config/emergencies.csv`):** 120 min for childbirth complication (WHO
2-hour emergency obstetric care access indicator), snakebite (2 hours is the usual maximum ideal time
to antivenom in accessibility studies) and injury or drowning (Lancet Commission on Global Surgery,
2 hours to essential surgical care); 60 min for minor illness (common primary-care convention). These
are population access standards, not clinical time limits. The sources were checked through search
summaries, not read in full.

**People within the target time (17.2 million people):**

| Emergency | Qualifying facilities | Target | Dry | Flood 07-08 | Flood 07-13 (partial) |
|---|---|---|---|---|---|
| Childbirth complication | 50 | 120 min | 97.6% | 97.4% | 97.5% |
| Snakebite | 50 | 120 min | 97.6% | 97.4% | 97.5% |
| Injury or drowning | 50 | 120 min | 97.6% | 97.4% | 97.5% |
| Minor illness | 131 | 60 min | 94.1% | 93.1% | 93.5% |
| Snakebite, antivenom only at district and medical college hospitals | 13 | 120 min | 94.3% | 93.0% | 93.7% |

**What this shows**
- Under the current assumption table, childbirth, snakebite and injury or drowning qualify the same 50
  facilities (37 Upazila Health Complexes, 5 district and 8 medical college hospitals), so their results
  are identical. They would differ only if a source shows some health complexes lack emergency obstetric
  care, antivenom or surgery, which public OSM data cannot show.
- The antivenom assumption matters less than it did in the small area: if only hospitals of district
  level or above stock antivenom, 2-hour coverage is 94.3% instead of 97.6%. It matters a lot locally:
  Austagram 7.0%, Mithamain 0.7%, Itna 28.1% and Khaliajuri 32.8% under the strict case.
- The flood effect for the 50-facility emergencies: 27,321 people pushed beyond 2 hours, a
  population-weighted 1.7 extra minutes. Under the strict antivenom case 229,969 people are pushed beyond
  2 hours and 898 lose every route.
- Lowest childbirth coverage among sizeable upazilas (dry, 2 hours): Austagram 70.9% (67.3% in the flood),
  Itna 76.2%, Mithamain 78.6%, Khaliajuri 85.3%. These are in the south-west haor edge, near the edge of
  the analysis area.

**Caveats**
- Private and unclassified facilities (62) qualify only for minor illness. Private multi-specialty
  hospitals in Sylhet and Kishoreganj may in fact handle childbirth, surgery or snakebite, so the
  public-sector view is conservative for people who can pay.
- The capability table is an assumption, as are the district hospital overrides.
- Facilities beyond the edge of the area are still not modelled (upazilas near the south-west edge are
  the most affected), and OSM may be missing government facilities.
- Facilities are assumed open and reachable in the flood, and hospital capacity is not modelled.

Files: `results/e3_coverage.csv`, `e3_flood_effect.csv`, `e3_facility_levels.csv` (with each facility's
nearest-qualifying catchment), `e3_upazila_within_target.csv`, and `docs/img/e3_emergency_types.png`.

## Phase E3b: extending the area, and checking the population layer

**Why.** The first version used a smaller box (90.95, 24.4, 91.75, 25.2) with 35 facilities, only one of
them a district hospital. Hospitals just outside it (Habiganj, Sylhet, Moulvibazar, Netrokona,
Kishoreganj) could not be used, which lowered coverage near the edges. The box now reaches west to 90.60,
east to 92.00 and south to 24.05.

**What changed (smaller box, 35 facilities, 5.08 million people, versus now):**

| Measure | Smaller box | Extended area |
|---|---|---|
| Any facility within 60 min, dry | 87.5% | 94.1% |
| Childbirth, 2 hours, dry | 94.3% | 97.6% |
| Snakebite with district-level antivenom only, 2 hours, dry | 56.1% | 94.3% |
| Flood 07-08: any facility within 60 min | 86.0% | 93.1% |

**Two errors found and fixed while extending.** A first version of the duplicate filter removed any
facility within 150 m of another, which dropped Habiganj General Hospital (about 100 m from Habiganj
Medical College), and diagnostic centres removed real hospitals before being excluded themselves. The
filter now classifies first and merges only same or similar names, or an unnamed node beside a named one.
Also, an earlier correction removed two "PHC" features on the border line that lie in no upazila polygon.

**Population layer (WorldPop 2020, constrained, 100 m) against the 2022 census, per upazila.** Matched
70 of the 76 upazilas (the census table uses an older P-code format for some):

| Measure | Result |
|---|---|
| WorldPop / census, median | 1.02 |
| Middle half of upazilas | 0.97 to 1.08 |
| Within ±10% of the census | 45 of 70 |
| Within ±25% of the census | 63 of 70 |
| Rank agreement (Spearman) | 0.89 |
| Range | 0.28 (Balaganj) to 1.69 (Fenchuganj) |

Cities and haor upazilas are under-counted (Sylhet Sadar 0.51, Habiganj Sadar 0.60, Dharmapasha 0.65,
Dowarabazar 0.76); some rural upazilas are over-counted (Kapasia 1.58). Rescaling every upazila to its
census total adds 5.0% people to the grid and moves the coverage numbers by at most 0.4 points:

| Measure | WorldPop | Rescaled to census |
|---|---|---|
| Any facility within 60 min, dry | 94.1% | 94.3% |
| Any facility within 60 min, flood 07-08 | 93.1% | 93.5% |
| Childbirth, 2 hours, dry | 97.6% | 97.6% |
| Snakebite, district-level only, 2 hours, dry | 94.3% | 94.7% |

This only tests the totals per upazila, not where people live inside one, which matters most for travel
time and cannot be tested without household or building data. Individual 100 m cells are far less reliable
than upazila totals, so results should be quoted for upazilas or larger areas.

Files: `results/population_vs_census.csv`, `results/population_sensitivity.csv`.
