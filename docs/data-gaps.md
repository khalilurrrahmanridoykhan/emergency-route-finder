# Data gaps found in Phase E0

Findings from inventorying the inputs. Counts by facility level are a rough keyword match
on OSM names, not a verified classification; the real classifier comes in Phase E3.

## 1. No district-level hospital inside the original area

The original analysis box `(91.15, 24.5, 91.5, 24.8)` holds 13 OSM health facilities:

| Level (rough, by name) | Count |
|---|---|
| Community clinic | 9 |
| Union health and family welfare centre | 2 |
| Upazila Health Complex | 2 (Ajmiriganj, Baniachong) |
| District / general hospital | 0 |

For childbirth complication, snakebite and injury or drowning, the only qualifying
destinations under the assumption table are 2 Upazila Health Complexes. The Derai and
Shalla upazila health complexes do not appear in the OSM extract at all, which is most
likely an OSM mapping gap rather than a missing facility.

## 2. Higher-level facilities exist just outside the box

A wider OSM query, box `(90.95, 24.4, 91.75, 25.2)`, returned 47 hospital, clinic or
doctors features. By name this includes about 13 distinct Upazila Health Complexes (one
appears twice as two nodes) and **Sunamganj General Hospital at (91.411, 25.065)**, north
of the original box. `Khaled General Hospital` is probably private and its capabilities are
unknown.

## 3. Flood layer covered only the original box (resolved in Phase E2)

The 2026-07-13 flood extent was mapped for the original box only. Phase E2 mapped the flood
for the wider area from Sentinel-1 on 2026-07-08 (98% of the area observed). The 2026-07-13
scene still misses the east, so results built on it understate flooding there.

## 4. Missing AccessMod inputs (resolved in Phase E1)

Land cover (ESA WorldCover 2021) and a DEM (Copernicus GLO-30) are now fetched by
`scripts/fetch_inputs.py`. Water is the WorldCover water class, one 2021 snapshot.

## 5. Higher-level facilities just outside the wider box (found in Phase E3)

Only one district-level hospital (Sunamganj General Hospital) lies inside the wider box. The Habiganj
district hospital sits just south of it, and the Sylhet, Moulvibazar, Netrokona and Kishoreganj
hospitals just outside its other edges. Travel to them is not modelled, which lowers coverage near
the edges and matters most for emergencies that need a district hospital. Fix: extend the grid
with a facility buffer (roads, land cover, DEM, population and flood mapping all follow).

## Decision taken in Phase E1

- Use the **wider box for facilities and roads**, so district and upazila hospitals outside
  the original box are candidate destinations.
- Keep the **original box** as the area with mapped flooding, and state plainly that the
  flood scenario is only valid there. Optionally extend the Sentinel-1 flood mapping to the
  wider box in Phase E2 using the `geohealth-risk-mapping` Phase H5 method.
- Applied in E1: analysis grid is the wider box (largest UTM rectangle inside it), cells and
  facilities outside Bangladesh are masked out (some OSM "PHC" features near the Meghalaya
  border are in India), and 2 facilities on water cells were moved to the nearest passable cell.
- Still open: use the **DGHS facility registry**, if usable, to fill missing Derai and Shalla
  facilities and to replace name-based level guesses. Otherwise keep OSM names and label
  the limitation.
