# Contributing to UrbanGauge

UrbanGauge is a public **research repository**, not a public data service. The repository is visible on GitHub, but an open-source licence has not yet been selected; visibility does not grant reuse permission for repository code or third-party source datasets.

## Work in reviewable increments

1. Check the canonical roadmap in `docs/NORTHSTAR_MASTER_ROADMAP.md` and its machine-readable `docs/roadmap-status.json` before selecting an `Mxx-Tyy` task.
2. Branch from the latest `main`; use `feat/Mxx-...`, `fix/...`, or `docs/...` names. For the currently active M01 milestone, use `feat/M01-engineering-foundation`.
3. Open an issue using the bug, engineering-task, or official-source form. Link relevant issue IDs in the pull request where available.
4. Keep pull requests scoped, document acceptance commands, and provide the actual output and commit SHA. Use `.github/PULL_REQUEST_TEMPLATE.md`; never claim an offline contract validator proves a production build or deployment.
5. Request maintainer review before merge. Record milestone completion only after approved review, a real merged PR, and an actual merge SHA.

## Local verification

Run commands appropriate to changed files, including:

```powershell
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
python scripts/validate_m01_workspace.py
python scripts/validate_m01_toolchains.py
python scripts/validate_m01_frontend.py
python scripts/validate_m01_governance.py
pnpm.cmd --dir frontend typecheck
pnpm.cmd --dir frontend build
pnpm.cmd install --frozen-lockfile
python -m uv lock --check --offline
```

A command should be executed only once the corresponding runtime is installed and the relevant milestone files exist. Do not merge if required local checks fail. Do not enable automated push, pull-request, or schedule triggers to make a check pass.

## Protect research provenance

- Never commit secrets, publisher ZIP/CSV/XLSX originals, private provenance, local database files, personal information, or unapproved derived metrics.
- Document publisher identifiers, statistical units, reference periods, geography vintages, quality flags, licence/reuse evidence and source fingerprints when a source is reviewed.
- Keep rent and income observations independently labelled unless a separate, documented methodology and publisher crosswalk are approved. Do not infer a renter-affordability ratio from incompatible populations or mean/median aggregations.
- Browser assets can contain only explicitly approved, versioned exports. No public export or deployment is authorized by the M01 foundation work.

## GitHub governance

GitHub Actions verification and deployment are currently **manual-only** (`workflow_dispatch`). A local test run must be recorded as local evidence, not a required hosted check. No repository ruleset or label installation is performed by the governance-file change. See `docs/M01_T04_REPOSITORY_GOVERNANCE.md` for suggested manual admin settings and why an unproduced required status check must not be enabled.
