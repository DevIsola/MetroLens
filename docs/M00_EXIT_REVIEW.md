# UrbanGauge — M00 discovery exit review (pending maintainer/PR acceptance)

**State:** Review package, **not** evidence that M00 is merged or done. The M00 feature branch remains `feat/M00-product-discovery`; M01 remains not started.

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
4. M00 completion requires a maintainer-reviewed pull request merged to `main` and an actual merge SHA and acceptance timestamp. `docs/roadmap-status.json` must remain `in_progress` until those facts exist.

## Review commands (no network, no deployment)

```powershell
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
python scripts/review_m00_naming.py
python scripts/validate_m00_architecture.py
python scripts/review_m00_exit.py
```

Expected exit report: `discovery_evidence_ready_for_manual_exit_review`, `repository_rename_verified: true`, `publication_approved: false`, `rent_to_income_ratio: null`, `m00_marked_done: false`.

After these pass, inspect the M00 feature branch diff, open a PR targeting `main`, and review approval/merge evidence. Do not turn on CI on push, Pages publishing, schedules or any raw-data publication. The repository rename **alone** does not authorize a GitHub Pages base-path change or a domain purchase.
