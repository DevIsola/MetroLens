# M01 — Engineering foundation pre-merge review

**State:** PRE-MERGE REVIEW ONLY. Do not set M01 to `done` or create acceptance/merge SHA evidence before merging a reviewed PR. This document does not authorize public data export, hosted deployment or automatic GitHub Actions.

**Branch under review:** `feat/M01-engineering-foundation`, targeting `main` in `DevIsola/UrbanGauge`.

## Implementation evidence matrix

| Task | Concrete implementation | Evidence / state |
| --- | --- | --- |
| M01-T01 | Repository structure, onboarding, fail-closed workspace activation | Implemented; M00 remains accepted |
| M01-T02 | Node 24.22.1, pnpm 10.34.9, Python 3.13, uv 0.10.0 and lockfiles | Local install and contract checks reported passing |
| M01-T03 | Next 16.4.3, strict TypeScript, source provenance contract | Local production build and typecheck reported passing |
| M01-T04 | PR template, GitHub issue forms, CONTRIBUTING and governance contract | File-side complete; labels/rulesets/admin options not installed or verified |
| M01-T05 | ADRs, changelog, generated roadmap verification, manual CI with frontend build | Local checks passed; hosted workflow run unverified |
| M01-T06 | Offline security hygiene, least-privilege workflow contract, manual dependency-review guide | File-side complete; Dependabot, hosted secret scanning and advisory audit not verified |
| M01-T07 | Static export, real `/methodology/` route, /UrbanGauge/ HTTP/assets smoke | Subpath smoke passed; **root-path smoke must be rerun using `--base-path=`** |

The maintainer reported **375 Python tests passing (one expected skip)**, successful Next.js production builds and type checking, and the `/UrbanGauge/` loopback HTTP smoke with 4 retrieved assets. These are human-provided local results, not independently observed by this pre-merge reviewer. The root-path HTTP check did not run because the original PowerShell empty argument was omitted. Rerun it and retain the terminal output before completing review.

## Open decisions — do not silently declare complete

1. **Licence (M01-T01):** No repository source-code licence has been selected; this is a roadmap item. Select one or explicitly authorize deferral before closing the milestone. Neither an open-source licence nor publisher redistribution rights can be assumed.
2. **Lint quality gates (M01-T02):** Strict TypeScript, Python regressions, toolchain validation and a production build exist. Ruff and ESLint lint tasks were not installed. Decide whether to implement them in a final M01 hardening increment or record a reviewed deferral.
3. **GitHub administrator settings (M01-T04/T06):** Branch rules, labels, Dependabot and hosted secret scanning have not been verified or activated by repository files. Required PR status checks must not be configured without a compatible producer, given manual-only CI. A reviewed deferral is possible for optional controls, not a claim that they exist.
4. **Locale routes (M01-T07):** The methodology route is implemented; EN/PT-BR product routing is planned in M05. Accept deferral or require more implementation here.
5. **Hosted verification:** `.github/workflows/verify.yml` is manually dispatched only and is not asserted to have run on a hosted runner. Local results are evidence, but not hosted check results.
6. **Hosting:** Existing Pages release job is manual/confirmation-gated and remains **unauthorized for invocation**. Cloudflare hosting decisions belong to a separately approved plan.

## Final offline pre-merge checks (PowerShell)

```powershell
# Fix the prior empty-argument problem; this rebuild is ROOT path only.
Remove-Item Env:NEXT_PUBLIC_BASE_PATH -ErrorAction SilentlyContinue
pnpm.cmd --dir frontend build
if ($LASTEXITCODE -ne 0) { throw 'Root static build failed' }
python scripts/validate_m01_static_export.py --smoke --base-path=
if ($LASTEXITCODE -ne 0) { throw 'Root HTTP smoke failed' }

python scripts/review_m01_exit.py
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
python scripts/validate_m01_security.py
pnpm.cmd install --frozen-lockfile --ignore-scripts
pnpm.cmd --dir frontend typecheck
py -3.14 -m uv --version  # Project .venv Python 3.13 need not include uv.
```

The pre-merge validator confirms repository **files and safeguards**, not any hosted GitHub settings, running deployments, browser accessibility audit, or newly performed dynamic smoke test. It intentionally reports `pr_merged: false` and `requires_maintainer_review: true`.

## Review and merge sequence

1. Resolve or explicitly record the open M01 roadmap exceptions. Attach the two local smoke reports and a passing test log in PR description or review comments.
2. Push the pre-merge review increment. Open **one** M01 PR targeting `main` and review the entire diff from the accepted M00 main baseline; do not merge automatically.
3. If the reviewer accepts the listed deferrals and implementation, merge manually. Note the real PR number, merge SHA, exact UTC time and accepted evidence. No Pages/Cloudflare publish is implied.
4. **Only after merge**, prepare a separate documentation closeout change to set M01 to `done` in `docs/roadmap-status.json` and regenerate the roadmap table. Existing M01 validators assume `in_progress` and will need a carefully scoped lifecycle adjustment first, as happened for M00. Do not fabricate a merge SHA or rerun the M01 activator.
5. M02 source work begins only after the reviewed M01 closeout, with publisher and statistical-comparability gates still closed.
