# AccessMod notes

Findings about AccessMod itself. The first section comes from reading the project's public
repository and Docker Hub metadata. **Nothing here has been verified by running AccessMod
yet.** Phase E1 replaces it with what actually happens when it runs on this area.

## Before running (read from the AccessMod repository, 2026-09-20)

- Maintained at `unige-geohealth/accessmod` (LGPL-3.0), developed by the University of
  Geneva GeoHealth group with WHO. R + Shiny on GRASS GIS 8, packaged as Docker images.
- The repo's `docker-compose.yml` runs `fredmoser/accessmod_base:5.9-c` and serves the app
  on ports 3080 and 3180. The compressed image sizes on Docker Hub are about 0.2 to 0.3 GB.
- The developer guide describes a **replay** function, `amAnalysisReplayExec("<config>.json")`,
  that reruns a saved analysis from its parameter file. This suggests runs may be scriptable
  without the UI. To be confirmed in E1.
- Outputs, barrier and land-cover import, and whether path lines can be exported are not
  yet confirmed.

## Spike questions for Phase E1

1. What does an accessibility run export (travel-time raster, nearest-facility table)?
2. What does the referral analysis export, and can it give paths or only times?
3. How are barriers and land-cover speed classes imported?
4. Can a run be replayed headless from a saved config, and what does the config contain?
5. How long does a run take on this area at the chosen resolution?
