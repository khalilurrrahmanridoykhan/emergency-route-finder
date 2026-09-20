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
