# UrbanGauge — M01-T03 static application and pipeline scaffold

**Status:** Implementation and local acceptance pending. This is a source-code scaffold, not an approved public product, hosted app or production dataset. M00 is accepted; M01 remains `in_progress`.

## Scope and reproducibility

- `frontend/`: Next.js **16.4.3** App Router, React/React DOM **19.3.1**, TypeScript **5.9.3** in strict/no-emit mode. `output: "export"` and `trailingSlash: true` support static hosting, with an optional build-time `NEXT_PUBLIC_BASE_PATH` (for example `/UrbanGauge`). No API endpoints, server actions, default image optimizer or dynamically rendered routes.
- `frontend/app/`: one English research landing page and a minimal responsive layout. The geometric graph is explicitly illustrative and contains **no metrics**. This is a scaffold, not the complete M05 design or localization milestone.
- `pipeline/src/urbangauge_pipeline/`: Python 3.13 stdlib-only immutable `SourceReference` provenance contract. No downloaded publisher bytes, raw statistics, cross-source calculation or HTTP ingestion.
- Existing design direction remains charcoal/coral/light canvas. User-facing data cards, charts, EN/PT-BR routes, map interactions and editorial content belong to M05/M06/M08 after source and geography publication review.
- `.github/workflows/` remains manual-only. Static build artifacts are ignored; **do not publish GitHub Pages** in M01-T03.

## Lockfile generation — required on the developer workstation

This implementation was authored without npm registry access. It intentionally includes **exact dependency pins** and **does not ship a fabricated pnpm lockfile**. After applying the patch, the existing lockfile remains the previous dependency-free M01-T02 revision and is expected to fail the new scaffold validator until regenerated. Resolve dependency versions using the pinned pnpm 10.34.9 on your workstation:

```powershell
# First verify Node 24.22.1 is active in the shell via fnm.
node --version
pnpm.cmd --version

# Requires npm registry access. Updates the EXISTING pnpm-lock.yaml.
pnpm.cmd install --lockfile-only --ignore-scripts
pnpm.cmd install --frozen-lockfile

# Generate framework types and type-check; no background processes.
pnpm.cmd --dir frontend typegen
pnpm.cmd --dir frontend typecheck
pnpm.cmd --dir frontend build

python scripts/validate_m01_frontend.py
python scripts/validate_m01_toolchains.py
python scripts/validate_m01_workspace.py
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
```

If `pnpm install` fails, stop and report the exact error **without** replacing exact pins with `latest` or deleting the lockfile. Commit the **actual** generated `pnpm-lock.yaml` once the production build and tests pass. Subsequent installs must use `--frozen-lockfile`. Do not commit `node_modules`, `.next`, `frontend/out`, generated `next-env.d.ts`, or other local build artifacts.

## Static-export smoke verification (M01-T03 baseline; M01-T07 expands this)

With the default empty base path, the production build must generate a nonempty `frontend/out/index.html` and have no dynamic/API routes. For an independent GitHub Pages project-path build:

```powershell
$env:NEXT_PUBLIC_BASE_PATH = '/UrbanGauge'
pnpm.cmd --dir frontend build
Remove-Item Env:NEXT_PUBLIC_BASE_PATH
Test-Path frontend/out/index.html
```

The project-path build **does not deploy** anything and must not be interpreted as publication approval. The browser path prefix is baked into a specific build and needs rebuilding to change; future deep-link and accessible navigation smoke tests are M01-T07 acceptance criteria.

## Non-approvals

No publisher reuse or redistribution approval; no CMHC/Statistics Canada crosswalk; no aligned household-rent burden calculation; no source-data export; no automatic GitHub workflows; no Pages release; no paid infrastructure. Retain all M00 source fingerprints and historical roadmap paths.
