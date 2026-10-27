# UrbanGauge — M00 discovery accepted, PR #1 merged

**State:** M00 discovery approved by the maintainer and merged in [PR #1](https://github.com/DevIsola/UrbanGauge/pull/1) at 2026-10-27T23:05:21Z. Verified merge commit: `87e9d035dfbc841c0282ec35da7a3d29707f7ff1`. This closes discovery planning, **not** data publication; M01 remains not started.

## Scope accepted for planning

- **M00-T01:** Eight initial 2021-Census CMA candidates and source geography identifiers.
- **M00-T02:** Locally audited, reproducible Vancouver CMA source observations: 2020 Census private-household income, 2024/2025 CMHC private apartment rents, and a separately labelled 2023/2024 CIS economic-family income candidate. Source fingerprints, exact dimensions, quality flags and non-public provenance are recorded.
- **M00-T03:** Fail-closed comparability gate and source-specific unjoined indicator preview; no household affordability ratio or approved cross-source statistical join.
- **M00-T04:** Maintainer accepted paired light/dark desktop/mobile UX direction, separate-series scope (ADR-0002) and two editorial story concepts. More ECharts interaction in M05/M08 and MapLibre map exploration in M06 are requirements, not yet built.
- **M00-T05:** Maintainer accepted ADR-0001 for planning: original sources ignored by Git, future offline Parquet/DuckDB transforms, approved-only versioned JSON browser exports, manual-only GitHub Actions. No automated deploy or ETL is activated.
- **M00-T06:** UrbanGauge approved as project name; GitHub repository renamed from `DevIsola/MetroLens` to `DevIsola/UrbanGauge` and local Git remote validated on 2026-10-27. Historical planning names, canonical roadmap path and original source IDs remain unchanged. No domain/trademark clearance claim.

## Unresolved restrictions (do not silently approve)

1. CMHC publisher CMA crosswalk and source-geography comparison require independently reviewed evidence.
2. Rent and income populations, reference periods and mean-versus-median aggregation do not support a household rent burden calculation.
3. Source-specific attribution, redistribution and publishing permissions must be reviewed before public export.
4. M00 discovery was accepted/merged in PR #1, and the real merge SHA and accepted timestamp are now recorded. Separate publisher-reuse, geographic-comparability and production-publication restrictions remain unresolved.

## Review commands (no network, no deployment)

```powershell
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
python scripts/review_m00_naming.py
python scripts/validate_m00_architecture.py
python scripts/review_m00_exit.py
```

Expected exit report: `discovery_accepted_post_merge`, `repository_rename_verified: true`, `publication_approved: false`, `rent_to_income_ratio: null`, `m00_marked_done: true`, `m01_started: false`.

After local validation, merge the post-merge bookkeeping closeout by PR and only then start `feat/M01-engineering-foundation` from updated `main`. Do not turn on CI on push, Pages publishing, schedules or any raw-data publication. The repository rename **alone** does not authorize a GitHub Pages base-path change or a domain purchase.
