# ADR-0004 — Manual verification and docs-as-code

- **Status:** accepted for M01-T05 engineering implementation; not production or publication approval
- **Date:** 2026-10-28
- **Related roadmap:** M01-T04, M01-T05, M01-T06, M01-T07
- **Affected files:** `.github/workflows/verify.yml`, `scripts/sync_roadmap.py`, `scripts/validate_m01_docs.py`, `docs/adr/README.md`, `CHANGELOG.md`

## Context

M00 discovery is complete and M01 has an installed Next.js static scaffold. Local verification passes, but checks must be reproducible, documentation drift must fail, and publisher data must remain unpublished. The maintainer has explicitly prohibited GitHub Actions running on pushes, pull requests, or schedules. A manual `workflow_dispatch` is allowed as a human-started check. A manually run check is not a continuously produced required PR check.

## Decision

1. The canonical roadmap remains `docs/NORTHSTAR_MASTER_ROADMAP.md`, with generated status synchronized from `docs/roadmap-status.json` by `scripts/sync_roadmap.py --check`. **CI only checks; it does not rewrite or commit documentation.**
2. Maintain a human-readable `CHANGELOG.md` and an ADR index. Add `scripts/validate_m01_docs.py` to fail closed on roadmap drift, missing ADR/changelog links, unexpected automatic workflow triggers, or relaxation of source-publication controls.
3. Extend `.github/workflows/verify.yml` with manually dispatched Python regressions, roadmap and docs-as-code checks, pinned pnpm/Node dependencies, TypeScript validation, and a **build-only** static-export smoke test. Workflow permission is `contents: read`; it does not upload, deploy or publish the resulting site.
4. Leave `.github/workflows/pages.yml` unchanged and manual-only. **No** required status-check branch rules are installed by this increment. Before any future release, the publisher gates and manual release authorization must be reviewed independently.
5. Report local checks as local evidence; report a hosted verification as passed only after observing an actual workflow run on the reviewed ref. The existence of a YAML file or green local test is not a hosted-run claim.

## Alternatives and consequences

- Automatically run CI on every push/PR: rejected because it contradicts the current maintainer policy.
- Configure a required hosted status check without an automatic producer: rejected as a risk of blocking merges indefinitely.
- Skip hosted build reproducibility entirely: rejected; a **manually invoked**, read-only verification workflow allows periodic milestone acceptance testing.

This decision improves evidence discipline without changing the offline source pipeline, public output permissions, Pages deployment configuration or metric comparability. Dependency upgrades and security automation remain separate reviewed work (M01-T06 onward).

## Acceptance

Run `python scripts/validate_m01_docs.py`, `python scripts/sync_roadmap.py --check`, Python unit tests, a frozen pnpm install, frontend typecheck, and frontend build locally. When workflow is available on the relevant GitHub default branch, optionally dispatch the verify workflow manually and record the actual run URL and SHA. **Do not** mark M01 done from this ADR alone.
