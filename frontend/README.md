# UrbanGauge frontend boundary

Reserved for the **future Next.js App Router + React + strict TypeScript** static-export frontend, to be introduced with pinned toolchains and lockfiles in M01-T02/T03.

No UI runtime or public dataset is installed by M01-T01. Future pages may read only validated, explicitly approved, versioned JSON shards; raw CSV/XLSX publisher files, Parquet intermediates, and DuckDB never ship to browsers.

The approved light/dark responsive design, source-specific indicator disclosures, planned interactive ECharts graphs and MapLibre maps remain M05/M06/M08 obligations. There is **no** permission to publish the reviewed Vancouver samples yet.

## M01-T03: dependency-pinned scaffold

The M01-T01 notes above describe the *earlier*, documentation-only boundary. M01-T03 adds an actual Next.js App Router and React source scaffold under `app/`, without any published dataset or server/API route. See `docs/M01_T03_APPLICATION_SCAFFOLD.md` for the required lockfile-resolution and local static build checks. Design tokens, bilingual routing, charts and maps remain later milestones. No UI runtime backend or public dataset service is enabled.
