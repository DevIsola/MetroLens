# ADR-0005 — Manual security and dependency governance

- **Status:** accepted for M01-T06 repository-file implementation; hosted administrator review pending
- **Date:** 2026-10-28
- **Related roadmap:** M01-T04, M01-T05, M01-T06, M01-T07, M09
- **Companion machine-readable policy:** `../architecture/m01_t06_security_policy.json`

## Context

The maintainer requires no automatically triggered GitHub Actions, scheduled data ingestion, or automatic deployment. M01-T05 added manually dispatched verification, and M01-T03 pinned a small frontend dependency graph. The repository is public, but has no selected open-source license and source-data export is not authorized. Required hosted status checks are not viable while checks are produced only on explicit manual dispatch.

## Decision

1. Retain **only** `workflow_dispatch` triggers. The verification job requires only `contents: read`; keep Pages `pages: write` and `id-token: write` isolated to its existing manual, main-only, confirmation-gated deployment job. Do not start Pages or claim publication approval.
2. Do **not** commit `.github/dependabot.yml`, add scheduled dependency checks, enable automatic dependency PRs, or assert GitHub secret scanning/private vulnerability reporting without verifying account settings and obtaining a separate maintainer decision.
3. Add an offline, deterministic security validator for workflow permissions, unapproved settings, pinned dependency manifests, tracked credential indicators, and source/publication gates. Add `SECURITY.md` with a private-reporting policy that does not invent a contact address or GitHub feature availability.
4. A vulnerability assessment of npm/Python dependencies requires separately recorded manual network-backed audit evidence. Local scans detect only a limited set of high-confidence secret patterns; never treat a clean scan as proof of absence.
5. Integrate the offline security validator into the **existing manually dispatched** verification workflow. No required check or hosted setting changes are made by a committed file.

## Alternatives rejected

- Automatic Dependabot pull requests and scheduled security workflows: not authorized under current no-automation policy.
- Claiming GitHub secret scanning is enabled because a `SECURITY.md` exists: incorrect; administrator verification is required.
- Adding mandatory PR status checks without a producer on PRs: risks making the repository unmergeable.
- Suppressing source-reuse, statistical-comparability, or export safeguards in the name of security hardening: not acceptable.

## Consequences and acceptance

M01-T06 establishes repository-file security checks and a manual review process, not a production-grade assurance or hosted security configuration. Run `python scripts/validate_m01_security.py`, existing M01 validators, the Python regression suite, frozen pnpm install, frontend typecheck/build, and optional manually initiated `pnpm audit` with explicit advisory/network caveats. M01 stays `in_progress`; no publisher data, application runtime, or automated workflow is released.
