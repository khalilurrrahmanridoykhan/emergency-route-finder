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

## 3. Flood layer covers only the original box

The 2026-07-13 flood extent was mapped for the original box only. In a wider analysis
area, flooding outside the box is unmapped and would be treated as "no flood", which
understates flood-season travel times near the edge.

## 4. Missing AccessMod inputs

Land cover, a DEM and a river/water layer are not in the repo yet (Phase E1). Candidate
public sources: ESA WorldCover, SRTM or Copernicus DEM, OSM water features.

## Proposed decision (to confirm in Phase E1)

- Use the **wider box for facilities and roads**, so district and upazila hospitals outside
  the original box are candidate destinations.
- Keep the **original box** as the area with mapped flooding, and state plainly that the
  flood scenario is only valid there. Optionally extend the Sentinel-1 flood mapping to the
  wider box in Phase E2 using the `geohealth-risk-mapping` Phase H5 method.
- Use the **DGHS facility registry**, if usable, to fill missing Derai and Shalla
  facilities and to replace name-based level guesses. Otherwise keep OSM names and label
  the limitation.
