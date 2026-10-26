# ADR-0001 — Static distribution and manual release control

- **Status:** proposed (M00-T05; not yet reviewed/accepted)
- **Date:** 2026-10-26
- **Related roadmap:** M00-T05; M01-T07; M04; M05; M09

## Context

The proposed observatory uses official Canadian datasets whose periods, update rates and geographic definitions vary. React/Next.js static export provides public navigation without a paid application server. During initial discovery and UI development, rebuilding and deploying on every commit consumes CI budget without improving published data correctness. Later ETL must not publish incomplete or incompatible data.

## Decision proposed

1. Keep one Git milestone branch per phase; commit small independently testable changes and push to the branch; merge after review.
2. During M00–M08, only manually dispatched GitHub Actions workflows are configured. Verify locally before each push and request a manual Actions verification at milestones. No `push`, `pull_request`, `schedule`, `release`, or tag-driven deploy triggers.
3. Pages publishes via a manually dispatched workflow **only from `main` and only after `confirm_release: true`**. It must build a Next.js static export with locked dependencies and validate available contracts before uploading. Deployment is not usable until M01/M05 prerequisites exist; it fails closed on missing build inputs.
4. Configure repository Pages source as **GitHub Actions**, not branch publishing. Protect the `github-pages` environment to accept `main` only when repository plan allows it. These settings must be applied in GitHub; files cannot enforce remote settings alone.
5. Production data is batch-transformed into versioned JSON; no per-request server backend. M04–M05 introduce validated dataset contracts; M09 may add carefully gated scheduler and change detection via an accepted follow-up ADR.
6. A failed validation/build does not deploy; the previously deployed site remains the public version.

## Alternatives considered

- **Deploy on every push/PR:** good feedback frequency but avoidable runner usage and risk of partial-data publication.
- **Publish from `main` branch folder:** simple but GitHub Pages can rebuild on every push to the publishing branch, bypassing manual release policy.
- **Cloudflare/Vercel:** potentially useful later, but would introduce another host and release path before the data contracts and deployment budgets are known.
- **No GitHub Actions at all:** saves runners but loses a repeatable release gate when the site is ready.

## Consequences and explicit limitations

- Developers run tests locally; manual-only CI does **not** provide an automatic required check for every PR. GitHub exposes `workflow_dispatch` only after the workflow exists on the default branch; the first M00 PR is therefore validated locally. M01 will revisit targeted PR verification if needed to support branch protection.
- Human release choice decouples integration from production. Major merged milestones may be published; partial merges need not be.
- Manual releases can become stale; later observable source freshness and a controlled ETL schedule will address this.
- Free-tier billing is plan- and usage-dependent. This policy reduces unnecessary Actions activity but is not a zero-cost guarantee.
- Changing Pages settings, environment protection, or older repository workflows remains an administrator operation. This ADR cannot claim those have been changed remotely.

## Acceptance record

Pending architecture review and an actual milestone PR. No PR number, merged SHA, or production success should be fabricated.
