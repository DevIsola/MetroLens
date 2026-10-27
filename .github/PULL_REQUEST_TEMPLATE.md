## Milestone / task IDs

<!-- Example: M00 / M00-T01, M00-T03. Link real GitHub Issues when created. -->

## Scope and why

<!-- Describe one milestone increment; include relevant source citations/official IDs for data changes. -->

## Changes

## Evidence / checks

- [ ] Local tests run (`python -m unittest discover -s tests -v` for M00)
- [ ] Roadmap synchronized (`python scripts/sync_roadmap.py --check`)
- [ ] Manual cloud CI run, when workflow is available on default branch
- [ ] If changing metrics, official definitions and incompatible-input cases validated
- [ ] If changing UI, screenshots and keyboard/mobile checks attached
- [ ] No secrets, invalid/mock production data, or unnecessary binary datasets committed

## Documentation impact

<!-- Files updated or "none" with a reason. Never mark milestones done without post-merge SHA and acceptance evidence. -->

## Release decision

- [ ] No Pages publication with this PR (default)
- [ ] Approved major milestone: manual release **after merge** to main (requires separate human confirmation)

## Risks / rollback

<!-- How to safely revert. -->
