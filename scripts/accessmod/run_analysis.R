# Run one AccessMod analysis from a replay config and export every output.
# Usage (from /app): Rscript /scripts/run_analysis.R <replay_config.json> <export_dir>
source("global.R")
config$language <- "en"
amTranslateSetSavedLanguage(config$language)

args <- commandArgs(trailingOnly = TRUE)
exportDir <- args[2]
dir.create(exportDir, recursive = TRUE, showWarnings = FALSE)

started <- Sys.time()
dirs <- amAnalysisReplayExec(
  args[1],
  exportDirectory = exportDir,
  formatVectorOut = "gpkg",
  formatRasterOut = "tiff"
)
print(dirs)
cat(sprintf("ANALYSIS DONE config=%s seconds=%.1f\n", basename(args[1]), as.numeric(difftime(Sys.time(), started, units = "secs"))))
