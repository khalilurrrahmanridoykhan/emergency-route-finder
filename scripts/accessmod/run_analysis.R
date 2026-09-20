# Run AccessMod analyses from replay configs and export every output.
# Usage (from /app): Rscript /scripts/run_analysis.R <export_base_dir> <replay_config.json> [more configs...]
# Each config exports to <export_base_dir>/<config name without "replay_" and ".json">.
source("global.R")
config$language <- "en"
amTranslateSetSavedLanguage(config$language)

args <- commandArgs(trailingOnly = TRUE)
exportBase <- args[1]

for (conf in args[-1]) {
  name <- sub("^replay_", "", sub("\\.json$", "", basename(conf)))
  exportDir <- file.path(exportBase, name)
  dir.create(exportDir, recursive = TRUE, showWarnings = FALSE)
  started <- Sys.time()
  ok <- tryCatch({
    amAnalysisReplayExec(
      conf,
      exportDirectory = exportDir,
      formatVectorOut = "gpkg",
      formatRasterOut = "tiff"
    )
    TRUE
  }, error = function(e) {
    cat(sprintf("ERROR %s: %s\n", name, conditionMessage(e)))
    FALSE
  })
  if (ok) {
    cat(sprintf("ANALYSIS DONE %s seconds=%.1f\n", name, as.numeric(difftime(Sys.time(), started, units = "secs"))))
  }
}
