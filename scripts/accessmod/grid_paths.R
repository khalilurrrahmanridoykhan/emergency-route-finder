# Phase E6: primary-only paths for the web map's precomputed query grid.
#
# Same technique as Phase E4 (scripts/accessmod/e4_paths.R): rerun r.walk.accessmod for a
# movement-direction raster (verified there to reproduce AccessMod's own published rasters
# exactly), then trace one complete path per point with GRASS r.drain. This variant skips the
# backup-facility phase (a static site shows the primary route; the backup and a full record are
# still available per point via `make route`) so a much larger set of points is affordable: every
# grid point x every real emergency type, both seasons.
#
# Usage (from /app): Rscript /scripts/grid_paths.R <tasks.csv> <qualifying_cats.json> <out_dir>
source("global.R")
config$language <- "en"
amTranslateSetSavedLanguage(config$language)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
tasksFile <- args[1]
catsFile <- args[2]
outDir <- args[3]
dir.create(outDir, recursive = TRUE, showWarnings = FALSE)

PROJECT <- "e1dry"
SEASONS <- c("dry", "flood0708")
qualifyingCats <- fromJSON(catsFile)
tasks <- read.csv(tasksFile, stringsAsFactors = FALSE)

amGrassNS(location = PROJECT, mapset = PROJECT, {
  results <- list()
  resultRow <- 1

  whatAt <- function(rasterMap, x, y) {
    # r.what returns "east|north|<label, blank here>|value" with "*" for null cells.
    line <- execGRASS("r.what", map = rasterMap, coordinates = c(x, y), intern = TRUE)
    value <- strsplit(line, "\\|")[[1]][4]
    if (is.na(value) || value == "*") NA_real_ else as.numeric(value)
  }

  # Rebuild r.walk.accessmod's direction field for one (season, emergency) combination.
  # elevation/friction/flags exactly match amTravelTimeAnalysis() (see docs/accessmod-notes.md).
  buildDirection <- function(season, emergency, cats, tag) {
    vSel <- sprintf("vSel__%s", tag)
    execGRASS("v.extract",
      input = sprintf("vFacility__%s", PROJECT), cats = paste(cats, collapse = ","),
      output = vSel, flags = "overwrite"
    )
    rOut <- sprintf("rWalkRaw__%s", tag)
    rDir <- sprintf("rWalkDir__%s", tag)
    rNear <- sprintf("rWalkNear__%s", tag)
    execGRASS("r.walk.accessmod",
      elevation = "rDem__dem@PERMANENT",
      friction = sprintf("rSpeed__%s_%s", season, emergency),
      start_points = vSel,
      output = rOut, outdir = rDir, nearest = rNear,
      flags = c("overwrite", "s", "t", "k")
    )
    list(dir = rDir, near = rNear)
  }

  drainPath <- function(costRaster, dirRaster, x, y, pathId) {
    rOut <- "rDrainTmp"
    vOut <- sprintf("vDrain__%s", pathId)
    ok <- tryCatch({
      execGRASS("r.drain",
        input = costRaster, direction = dirRaster, output = rOut, drain = vOut,
        start_coordinates = c(x, y), flags = c("overwrite", "d")
      )
      TRUE
    }, error = function(e) FALSE)
    if (!ok) {
      return(NA_character_)
    }
    outFile <- file.path(outDir, sprintf("path_%s.geojson", pathId))
    execGRASS("v.out.ogr", input = vOut, output = outFile, format = "GeoJSON", flags = "overwrite")
    execGRASS("g.remove", type = "vector", name = vOut, flags = "f")
    basename(outFile)
  }

  record <- function(taskId, gridId, season, facilityCat, minutes, pathFile) {
    results[[resultRow]] <<- data.frame(
      id = taskId, grid_id = gridId, season = season, facility_cat = facilityCat,
      minutes = minutes, path_file = ifelse(is.na(pathFile), "", pathFile)
    )
    resultRow <<- resultRow + 1
  }

  # One direction raster per (season, emergency) -- shared by every grid point with that emergency.
  combos <- unique(tasks[, "emergency_id", drop = FALSE])
  primaryDirs <- list()
  for (season in SEASONS) {
    for (emergency in combos$emergency_id) {
      key <- paste(season, emergency)
      tag <- sprintf("primary_%s_%s", season, emergency)
      primaryDirs[[key]] <- buildDirection(season, emergency, qualifyingCats[[emergency]], tag)
      cat(sprintf("PRIMARY DIRECTION %s\n", key))
    }
  }

  for (i in seq_len(nrow(tasks))) {
    t <- tasks[i, ]
    for (season in SEASONS) {
      travelMap <- sprintf("rTravelTime__%s_%s", season, t$emergency_id)
      nearMap <- sprintf("rNearest__%s_%s", season, t$emergency_id)
      minutes <- whatAt(travelMap, t$x, t$y)
      facCat <- whatAt(nearMap, t$x, t$y)
      pathFile <- NA_character_
      if (!is.na(minutes) && !is.na(facCat)) {
        dirRaster <- primaryDirs[[paste(season, t$emergency_id)]]$dir
        pathFile <- drainPath(travelMap, dirRaster, t$x, t$y, sprintf("%d_%s", t$id, season))
      }
      record(t$id, t$grid_id, season, facCat, minutes, pathFile)
    }
    if (i %% 50 == 0) {
      cat(sprintf("TASK %d of %d done\n", i, nrow(tasks)))
    }
  }

  out <- do.call(rbind, results)
  write.csv(out, file.path(outDir, "tasks_result.csv"), row.names = FALSE)
  cat(sprintf("E6 GRID DONE rows=%d\n", nrow(out)))
})
