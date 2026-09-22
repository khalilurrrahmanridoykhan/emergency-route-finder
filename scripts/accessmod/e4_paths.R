# Phase E4: complete least-cost paths for synthetic emergency points, primary and backup facility.
#
# AccessMod's own referral analysis exports path lines, but when several destinations share an
# origin in one run, shared route segments are deduplicated (see docs/accessmod-notes.md). This
# script instead reruns r.walk.accessmod itself (the same module, same flags, same inputs
# AccessMod's accessibility() uses -- verified to reproduce its published travel times and
# nearest-facility rasters exactly) to get a movement-direction raster, then traces one complete
# path per point with GRASS r.drain.
#
# Usage (from /app): Rscript /scripts/e4_paths.R <points.csv> <qualifying_cats.json> <out_dir>
source("global.R")
config$language <- "en"
amTranslateSetSavedLanguage(config$language)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
pointsFile <- args[1]
catsFile <- args[2]
outDir <- args[3]
dir.create(outDir, recursive = TRUE, showWarnings = FALSE)

PROJECT <- "e1dry"
SEASONS <- c("dry", "flood0708")
qualifyingCats <- fromJSON(catsFile)
points <- read.csv(pointsFile, stringsAsFactors = FALSE)

amGrassNS(location = PROJECT, mapset = PROJECT, {
  results <- list()
  resultRow <- 1

  whatAt <- function(rasterMap, x, y) {
    # r.what returns "east|north|<label, blank here>|value" with "*" for null cells.
    line <- execGRASS("r.what", map = rasterMap, coordinates = c(x, y), intern = TRUE)
    value <- strsplit(line, "\\|")[[1]][4]
    if (is.na(value) || value == "*") NA_real_ else as.numeric(value)
  }

  # Rebuild r.walk.accessmod's direction field for one (season, emergency, cats) combination.
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

  record <- function(pointId, season, kind, facilityCat, minutes, pathFile) {
    results[[resultRow]] <<- data.frame(
      id = pointId, season = season, kind = kind, facility_cat = facilityCat,
      minutes = minutes, path_file = ifelse(is.na(pathFile), "", pathFile)
    )
    resultRow <<- resultRow + 1
  }

  # --- Primary: one direction raster per (season, emergency) actually needed, shared by all points ---
  combos <- unique(points[, "emergency_id", drop = FALSE])
  primaryDirs <- list()
  for (season in SEASONS) {
    for (emergency in combos$emergency_id) {
      key <- paste(season, emergency)
      tag <- sprintf("primary_%s_%s", season, emergency)
      primaryDirs[[key]] <- buildDirection(season, emergency, qualifyingCats[[emergency]], tag)
      cat(sprintf("PRIMARY DIRECTION %s\n", key))
    }
  }

  for (i in seq_len(nrow(points))) {
    p <- points[i, ]
    for (season in SEASONS) {
      travelMap <- sprintf("rTravelTime__%s_%s", season, p$emergency_id)
      nearMap <- sprintf("rNearest__%s_%s", season, p$emergency_id)
      minutes <- whatAt(travelMap, p$x, p$y)
      facCat <- whatAt(nearMap, p$x, p$y)
      pathFile <- NA_character_
      if (!is.na(minutes) && !is.na(facCat)) {
        dirRaster <- primaryDirs[[paste(season, p$emergency_id)]]$dir
        pathFile <- drainPath(travelMap, dirRaster, p$x, p$y, sprintf("%d_%s_primary", p$id, season))
      }
      record(p$id, season, "primary", facCat, minutes, pathFile)
      cat(sprintf("POINT %d %s primary minutes=%s cat=%s\n", p$id, season, minutes, facCat))
    }
  }

  # --- Backup: one direction raster per (season, emergency, excluded facility) group actually needed ---
  primary <- do.call(rbind, results)
  primary <- primary[primary$kind == "primary" & !is.na(primary$facility_cat), ]
  primary <- merge(primary, points[, c("id", "emergency_id")], by = "id")
  groups <- unique(primary[, c("season", "emergency_id", "facility_cat")])

  backupDirs <- list()
  for (g in seq_len(nrow(groups))) {
    season <- groups$season[g]
    emergency <- groups$emergency_id[g]
    excludeCat <- groups$facility_cat[g]
    cats <- setdiff(qualifyingCats[[emergency]], excludeCat)
    key <- paste(season, emergency, excludeCat)
    if (length(cats) == 0) {
      backupDirs[[key]] <- NULL
      next
    }
    tag <- sprintf("backup_%s_%s_%d", season, emergency, excludeCat)
    built <- buildDirection(season, emergency, cats, tag)
    rMin <- sprintf("rBackupMin__%s", tag)
    execGRASS("r.mapcalc",
      expression = sprintf("%s = ceil(rWalkRaw__%s / 60.0)", rMin, tag), flags = "overwrite"
    )
    backupDirs[[key]] <- list(dir = built$dir, near = built$near, minRaster = rMin)
    cat(sprintf("BACKUP DIRECTION %s (excluding cat %d)\n", key, excludeCat))
  }

  for (i in seq_len(nrow(primary))) {
    p <- primary[i, ]
    key <- paste(p$season, p$emergency_id, p$facility_cat)
    g <- backupDirs[[key]]
    if (is.null(g)) {
      record(p$id, p$season, "backup", NA, NA, NA)
      next
    }
    minutes <- whatAt(g$minRaster, points[points$id == p$id, "x"], points[points$id == p$id, "y"])
    facCat <- whatAt(g$near, points[points$id == p$id, "x"], points[points$id == p$id, "y"])
    pathFile <- NA_character_
    if (!is.na(minutes) && !is.na(facCat)) {
      pathFile <- drainPath(
        g$minRaster, g$dir, points[points$id == p$id, "x"], points[points$id == p$id, "y"],
        sprintf("%d_%s_backup", p$id, p$season)
      )
    }
    record(p$id, p$season, "backup", facCat, minutes, pathFile)
    cat(sprintf("POINT %d %s backup minutes=%s cat=%s\n", p$id, p$season, minutes, facCat))
  }

  out <- do.call(rbind, results)
  write.csv(out, file.path(outDir, "points_result.csv"), row.names = FALSE)
  cat(sprintf("E4 DONE rows=%d\n", nrow(out)))
})
