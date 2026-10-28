# UrbanGauge — M01-T04 repository governance (proposal / local contract)

**Status:** Repository files prepared and locally checkable. **No claim** that GitHub branch rules, labels, issue forms on the default branch, or required hosted checks are already installed. M01 is `in_progress`. This increment does **not** approve publication or an automated CI/deployment trigger.

## What this increment changes

- Add issue-form templates in `.github/ISSUE_TEMPLATE/` for reproducible bugs, scoped milestone tasks, and publisher-specific source reviews.
- Retain the existing pull-request template; strengthen its validation and publication decision checklist.
- Document contribution workflow, review evidence and manual governance procedures in `CONTRIBUTING.md`.
- Add `scripts/validate_m01_governance.py` and tests to detect removal of review templates, premature publication authorizations, or automatic Actions triggers.
- Record that no GitHub administrator settings are changed by a committed file or by running the validator.

## Suggested GitHub issue labels (maintainer creates manually, if desired)

| Label | Purpose |
| --- | --- |
| `type:bug` | Reproducible defects |
| `type:feature` | Planned engineering/product work |
| `type:source-review` | Official-source evidence, licensing and provenance |
| `priority:P0` / `priority:P1` / `priority:P2` | Scope/urgency as assigned by maintainer |
| `milestone:M01` / `milestone:M02` | Milestone grouping; do not equate with completion |
| `blocked:source-permission` | Publisher reuse or redistribution unknown |
| `blocked:comparability` | Cross-source statistical definitions are not compatible |

Templates do **not** auto-assign labels because their existence is not verified. To use labels, create and review them under the repository's Issues → Labels interface; log which were actually created. Do not claim they exist merely because this table is committed.

## Proposed ruleset for `main` — manual administrator decision

At repository **Settings → Rules → Rulesets**, review availability and branch protections with the repository owner. Consider a rule for `main` requiring pull requests before merging and blocking force pushes and deletion. Select appropriate reviewer approval requirements only if the repository has people who can actually review; do not strand a sole maintainer. Apply only after a separate explicit settings review and verify the repository's actual UI/API state.

**Do not enable 'Require status checks to pass' yet.** The repository's verification workflow is `workflow_dispatch`-only, and GitHub Actions checks from manually dispatched workflows generally do **not** satisfy PR required-status-check rules. Enabling a required but unsatisfiable check can block every merge. A future separately approved CI-provider plan can resolve that without silently enabling GitHub Actions on `push` or `pull_request`.

The repository's two committed GitHub Actions workflows must remain `workflow_dispatch`-only; scheduled ETL, push/PR CI and automatic release stay disabled. The existing Pages workflow remains a manual legacy pathway, not an authorization to deploy. Any future change of hosting to Cloudflare requires a separate decision and implementation milestone.

## Review checklist for a PR

1. Check milestone/task IDs, source definitions if involved, and evidence from a reproducible local test or build run.
2. Verify `python -m unittest discover -s tests -v`, roadmap synchronization, new governance validator, applicable pnpm/uv checks, and the real `frontend/out` static build if UI changed.
3. Confirm no raw publisher downloads or secrets are committed, no joins/ratios from incompatible sources are presented, and any static export is approved separately.
4. Review diff and rollback, then merge manually. Record actual PR number/merge SHA before updating a milestone to `done`.
5. Keep unproven required-status-check rules **off**. User review and local evidence are the current acceptance mechanism.

## Completion distinction

This increment establishes **repository-file governance**, not GitHub-hosted ruleset enforcement. M01-T04 administrator-side labels/ruleset availability and any manually chosen settings remain **pending maintainer review**. The project milestone M01 must remain `in_progress` until the full M01 exit gate is met.

References:
- GitHub issue forms: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
- GitHub required-status-check constraints: https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks
- GitHub rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
