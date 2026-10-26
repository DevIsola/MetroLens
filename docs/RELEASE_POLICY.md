# GitHub and release execution policy — proposed

Status: initial implementation contract, subject to M00-T05 ADR acceptance.

## Goal

Keep feature-branch pushes fast and cheap. Preserve an explicit human release decision until reproducible data-quality checks and validated static export exist.

## Development cadence

1. One long-lived branch **per milestone only**, not per individual task: `feat/Mnn-description` from the latest `main`. Feature branches stay short-lived within their milestone.
2. Small commits for one checkable change (code + matching tests/docs), with Conventional Commit scope `Mnn-Txx`.
3. Push each validated increment to its milestone branch. This is a developer action, not a GitHub Actions trigger.
4. Review the accumulated milestone in a PR targeting `main`; link relevant Issues when GitHub is available. Obtain required manual verification before merge.
5. Merge accepted milestone work to `main`; leave incomplete milestones `in_progress`, recording the merge SHA in the status file only when actually known.
6. Publish only when the milestone merits a public release. From the GitHub Actions tab, manually run **Publish Pages (manual milestone release)** on `main` with explicit confirmation.

## CI and deployment behavior

| Event | Quality workflow | Pages workflow | ETL |
| --- | --- | --- | --- |
| Local commit or branch push | Local tests only | Not triggered | Not triggered |
| PR creation/update | Local tests, optional manually dispatched GitHub verification | Not triggered | Not triggered |
| Merge to `main` | No automatic run; perform approved verification as part of merge process | Not triggered | Not triggered |
| Manual `workflow_dispatch` for Verify | Runs checks only | Not triggered | Not triggered |
| Manual `workflow_dispatch` for Pages on `main` with confirmation | Built-in pre-deploy gates | Builds and publishes approved static site | Not triggered |
| Future ETL schedule, M09 | To be designed | To be designed | Disabled until accepted ADR |

**Note:** Manual-only verification cannot simultaneously serve as a reliable required PR status check unless a compatible triggering mechanism is later introduced. Until then, use local validation + explicit reviewer checklist. An accepted M01 ruleset/ADR may enable limited PR CI for quality without enabling Pages deployments.

## Required repository settings (manual, not automated by this package)

- GitHub Pages: Source = **GitHub Actions**, not **Deploy from a branch**. Otherwise branch publishing can cause extra Pages workflow runs.
- Protect `main` against direct pushes when permitted by plan. Require PR review and successful checks when an appropriate automated check strategy is configured.
- Protect deployment environment `github-pages`, limiting branches to `main` where GitHub's plan/settings allow.
- Avoid schedules and release tag triggers during M00–M08.
- Review GitHub Actions usage/settings periodically; manual-only workflows minimize runner usage, but do **not** guarantee zero cost under every repository plan/billing policy.
- If importing this project into an existing repository, inspect and disable/rewrite **existing** workflows and any branch-publishing configuration separately; this package cannot modify remote repository settings.

## Publish gates (when frontend exists)

- Published commit must be on `main`, with an approved release decision.
- Static export must produce `frontend/out/` and compatible `NEXT_PUBLIC_BASE_PATH` (project sites).
- Data-quality/export schema checks must be integrated into the release build once M04 is implemented; absent gates block production-data publication.
- Failed build or failing quality validation must stop before upload/deploy. Previous successful site stays published.
- Record release commit SHA, reference period, dataset version, and data-provenance information when real outputs exist.
- No live-data claims or fictional demo metrics on production pages.

## Future ETL (M09)

Use separately controlled refresh cadence per actual source publication frequency. Detect data changes, validate schemas/metrics/license, skip release on no-change, and request/pursue a release only after tests. Record the approved workflow change via ADR. Do not introduce an unconditional daily site rebuild.
