# UrbanGauge — M01 Engineering Foundation (increment T01)

**Status:** M01-T01 in progress after M00 acceptance and the merged bookkeeping closeout PR; this increment is **not** M01 completion.

## Scope and architecture boundaries

- `frontend/` — future Next.js App Router, React, strict TypeScript static-export application (M01-T02/T03/T07). Currently documentation only. Browser assets will consume *approved, versioned JSON*, never raw publisher files or local Parquet.
- `pipeline/` — future Python uv-managed pipelines and source-specific validation (M01-T02/T03; M02 onward). Original downloaded files and manifests stay Git-ignored and never enter static-export directories.
- `scripts/` — cross-cutting validation and roadmap maintenance. Existing M00 programs remain usable and source identifiers/checksums remain unchanged.
- `tests/` — Python standard-library regression suite for legacy M00 and new repository contracts; future frontend test tooling is introduced only with its runtime and lockfile.
- `docs/` — canonical planning ADRs, source methodologies, decision evidence and developer onboarding. Historical filename `NORTHSTAR_MASTER_ROADMAP.md` is retained to avoid breaking links.
- `.github/workflows/` — both verification and Pages release are `workflow_dispatch` only. No `push`, `pull_request`, `schedule`, or publish trigger is approved in this increment.

## M01-T01 deliverables and explicit omissions

- Deliver: these module ownership READMEs, Windows-friendly setup instructions, `.editorconfig`, a fail-closed workspace validator and local-only M01 roadmap activation.
- Defer to M01-T02: runtime version pinning, pnpm workspace, Node/pnpm and uv lockfiles, language linters and strict TypeScript configuration. Do not invent dependency-version evidence.
- Defer to M01-T03: actual Next.js frontend and Python package creation, module imports and integration tests.
- Defer to M01-T04–T06: branch-rule/permission reviews and additional security scanners. Do not silently enable Actions on pushes or PRs.
- Defer to M01-T07: a reproducible static export and `basePath` smoke test. Do not deploy Pages.
- Licence: **undecided**. A publicly visible GitHub repository does not, by itself, specify an open-source licence. Select a licence explicitly before adding a `LICENSE` file or reuse assertions.

## Carry-forward restrictions from M00

1. CMHC/Statistics Canada CMA crosswalk is not approved.
2. Mean apartment rent cannot be divided by unmatched CIS economic-family median income to claim renter burden or affordability.
3. Publisher reuse/redistribution/attribution must be reviewed before public data export.
4. ADR-0001 remains accepted **for planning**, not activated for production; publication and scheduling gates remain false.
5. M05/M06/M08 must deliver richer accessible interactive ECharts/MapLibre charts and maps as accepted in M00-T04, subject to data and geospatial licensing gates.

## Checkpoint

Run `python scripts/activate_m01.py --apply` once on `feat/M01-engineering-foundation`, then run `python scripts/validate_m01_workspace.py`, the full Python regression suite, and roadmap synchronization check. Record a normal local commit and push only after these pass. Do not mark M01 `done` before its own acceptance and merge evidence.
