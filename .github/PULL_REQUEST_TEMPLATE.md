## Milestone / task IDs

<!-- Example: M01 / M01-T04. Link real GitHub Issues when created. -->

## Scope and why

<!-- Describe one reviewable increment, the user/engineering outcome, and what is explicitly out of scope. -->

## Changes

## Evidence / checks

- [ ] Full local Python suite run (`python -m unittest discover -s tests -v`)
- [ ] Roadmap synchronized (`python scripts/sync_roadmap.py --check`)
- [ ] Relevant contract validators run (workspace/toolchains/frontend/governance as applicable)
- [ ] Frozen package installation and actual typecheck/build passed when frontend dependencies changed
- [ ] Source definitions, publisher terms, licence decisions and incompatible-input cases reviewed when metrics/data changed
- [ ] Responsive/keyboard checks and screenshots attached when user-facing UI changed
- [ ] No secrets, unapproved publisher datasets, invented data, or binary source archives committed
- [ ] Any manual GitHub Actions execution is described as optional evidence, **not** an automatically required PR check

## Source / methodology / release restrictions

<!-- State what is and is not approved for reuse, statistical comparability, client JSON export, and publication. -->

- [ ] No new unapproved rent-to-income join, aggregate burden, or misleading cross-source comparison
- [ ] No Pages/Cloudflare/public-data deployment with this PR (default)
- [ ] No new push/PR/scheduled GitHub Actions triggers

## Documentation impact

<!-- Files updated or "none" with a reason. Never mark a milestone done before real merge and acceptance evidence. -->

## Reviewer decision / Risks / rollback

<!-- Record manual review, reproduction notes, and rollback steps. Any later release needs separate human confirmation. -->
