# Canada Affordability & Opportunity Observatory

**Project codename:** MetroLens (not an approved public brand).

A proposed bilingual, static-first Canadian affordability data observatory. This repository starts with feasibility research and engineering governance before introducing ingestion, verified metrics, or a public dashboard. **No production data or analytical conclusions have been published.**

## Current scope

- Milestone M00: source discovery, candidate Canadian Census Metropolitan Areas (CMAs), rent/income compatibility, and architecture decisions.
- Canonical contract: [`docs/NORTHSTAR_MASTER_ROADMAP.md`](docs/NORTHSTAR_MASTER_ROADMAP.md), v0.2.0.
- Visual reference: [`docs/design/theme-preview-v0.2.0.html`](docs/design/theme-preview-v0.2.0.html). Figures in that preview are fictional.
- Proposed analytics: official Statistics Canada, CMHC, and Bank of Canada data, with source licensing and coverage verified before ingestion.

## Local validation (no cloud runners)

Requires Python 3.11+ and Git. M00 tools use only the Python standard library.

```sh
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
```

For a roadmap-status change, edit `docs/roadmap-status.json` and run `python scripts/sync_roadmap.py --write`, then rerun validation. Milestones cannot be marked `done` without merged PR and acceptance evidence.

## Branch, commit, and deployment policy

- Milestone branches: `feat/M00-product-discovery`, `feat/M01-engineering-foundation`, etc.
- Small atomic commits: `docs(M00-T01): ...`, `test(M00-T01): ...`, `ci(M00): ...`.
- Run local tests before **every** push; push to the current milestone branch, not directly to `main`.
- Open one PR for the milestone, updating it with each increment; merge only after review and demonstrated acceptance.
- Workflows intentionally have `workflow_dispatch` only. Ordinary commits, branch pushes, PR updates, and merges do **not** start Actions. **Bootstrap exception:** GitHub only exposes `workflow_dispatch` once the workflow file exists on the default branch; validate the first M00 PR locally, then manually run the workflow on later milestone checkpoints once the initial branch is merged.
- Pages publishing is an explicitly confirmed, manually dispatched action from `main` **only**. No deployment is expected before frontend static export and contracts are ready (M01/M05). No ETL schedule is enabled (M09 will introduce one under an ADR).
- Choose **GitHub Actions** in repository Settings → Pages → Build and deployment → Source. **Do not** select branch publishing, which would circumvent the release gate. Protect the `github-pages` environment to allow deployments from `main` only.

See [`docs/RELEASE_POLICY.md`](docs/RELEASE_POLICY.md) for release/rollback rules and setup instructions.

## Planned implementation order

M00 discovery → M01 developer foundation → M02 ingestion → M03 normalization → M04 verified marts/static contract → M05 overview/site publication → M06 explorer → M07 scenarios → M08 storytelling → M09 controlled ETL schedule → M10 observability → M11 public release.

> Source compatibility, actual data coverage, licenses, commit hashes, issue/PR IDs, and production deployments must be recorded from real evidence, never assumed.
