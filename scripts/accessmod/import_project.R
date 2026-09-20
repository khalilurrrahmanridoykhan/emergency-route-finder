# Create an AccessMod project from prepared inputs, headless, inside the AccessMod container.
# Usage (from /app): Rscript /scripts/import_project.R <project_name> <input_dir>
source("global.R")
config$language <- "en"
amTranslateSetSavedLanguage(config$language)

args <- commandArgs(trailingOnly = TRUE)
project <- args[1]
inDir <- args[2]

# The upload functions delete their input files, so always hand them a temporary copy.
tmpCopy <- function(pattern) {
  files <- list.files(inDir, pattern = pattern, full.names = TRUE)
  tmpDir <- file.path(tempdir(), amRandomName())
  dir.create(tmpDir)
  copies <- file.path(tmpDir, basename(files))
  file.copy(files, copies)
  copies
}

started <- Sys.time()
amGrassNS(location = "demo", mapset = "demo", {
  demFile <- tmpCopy("^dem\\.tif$")
  newDem <- data.frame(
    datapath = demFile, name = basename(demFile),
    size = file.info(demFile)$size, stringsAsFactors = FALSE
  )
  amProjectCreateFromDem(newDem, project)
  stopifnot(amIsValidLocation(project))

  lc <- tmpCopy("^landcover_merged\\.tif$")
  lcName <- paste0("rLandCoverMerged", config$sepClass, project)
  amUploadRaster(config, lc, lcName, lc, "rLandCoverMerged", "import")
  stopifnot(amRastExists(lcName))

  pop <- tmpCopy("^population\\.tif$")
  popName <- paste0("rPopulation", config$sepClass, project)
  amUploadRaster(config, pop, popName, pop, "rPopulation", "import")
  stopifnot(amRastExists(popName))

  fac <- tmpCopy("^facilities\\.(shp|dbf|shx|prj)$")
  facName <- paste0("vFacility", config$sepClass, project)
  amUploadVector(fac[grepl("\\.shp$", fac)], facName, fac, "import")
  stopifnot(amVectExists(facName))

  print(amMapMeta()$grid)
  print(execGRASS("v.db.select", map = facName, intern = TRUE))
})
cat(sprintf("IMPORT DONE project=%s seconds=%.1f\n", project, as.numeric(difftime(Sys.time(), started, units = "secs"))))
