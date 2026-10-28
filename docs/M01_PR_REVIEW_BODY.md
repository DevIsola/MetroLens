# M01 — Engineering foundation (pre-merge PR draft)

## Milestone / task IDs

M01 / M01-T01 through M01-T07. Base: `main`; head: `feat/M01-engineering-foundation`.

## Scope

Establish a reproducible static-first UrbanGauge engineering foundation without publishing any source-derived data or activating automatic GitHub workflows.

## Included

- Node 24.22.1, pnpm 10.34.9, Python 3.13 and uv 0.10.0 version/lock contracts.
- Next.js 16.4.3/React 19.3.1 static App Router and strict TypeScript; modular Python provenance contract.
- Offline project policy, security and governance regression suite; issue/PR templates and contributor guidance.
- Documentation-as-code, ADRs/changelog and read-only, manual-only verification workflow.
- Local root/subpath static-export smoke, methodology deep link and asset/URL checks.

## Reproducible checks and evidence

- 375 Python tests reported passed before this pre-merge increment; one Windows skip. Re-run after applying this increment.
- Type generation, TypeScript typecheck and Next.js static build passed on Windows.
- `/UrbanGauge/` and `/UrbanGauge/methodology/` served via 127.0.0.1; four static assets verified.
- Root-path smoke to be rerun with `--base-path=`; attach actual output.
- `python scripts/review_m01_exit.py`, roadmap sync and security validation to be rerun before review.

## Decisions still needed

Review `docs/M01_PREMERGE_REVIEW.md`: source-code licence, missing Ruff/ESLint lint tasks, unconfigured rulesets/labels/Dependabot/hosted security, future EN/PT-BR routes, and whether local verification suffices without hosted CI. Record explicit acceptances/deferrals before merging.

## Restrictions

No automatic `push`, `pull_request` or `schedule` workflow triggers. No Pages/Cloudflare publication, public data export, publisher licence clearance, CMHC/Statistics Canada crosswalk or rent-to-income join is approved by this PR.

## Rollback and acceptance

Review the complete M00→M01 file diff and make a manual merge decision. Roll back through a revert PR if needed; never directly rewrite M00 accepted evidence. Complete M01's roadmap status **after merge only**, using the real PR merge SHA and UTC acceptance timestamp.
