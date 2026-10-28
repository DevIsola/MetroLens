# UrbanGauge Python pipeline boundary

Reserved for an **offline, reproducible Python pipeline**, with uv/toolchain decisions in M01-T02 and source ingestion introduced in M02.

- `pipeline/data/raw/`: original publisher files, private manifests and local audit outputs; **Git-ignored, never browser served**.
- Later phases: Bronze manifests, Silver Parquet, DuckDB/dbt Gold and *only after approval* versioned JSON exports.
- Preserve source ID, geographic vintage, reference period, statistical unit, quality/suppression fields, publisher URLs and SHA-256 fingerprints across each transformation.
- No live HTTP ingestion, scheduled ETL, automated release, or inferred rent-to-income score is enabled here.

## M01-T03: private Python contract module

`src/urbangauge_pipeline/contracts.py` introduces a standard-library-only, immutable publisher reference record. It stores source/provenance *metadata*, never source values or a joined KPI. It is not an installed distribution, ingestion client, scheduler, database, or publishing pipeline. No live HTTP ingestion is introduced.
