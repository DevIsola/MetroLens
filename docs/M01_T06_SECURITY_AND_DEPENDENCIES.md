# UrbanGauge — M01-T06 security and dependency governance

**Status:** repository-file security baseline for maintainer validation; no source-data publication is authorized. M01 remains **in progress**. This document does not claim a GitHub administrator setting has been enabled or that a production website has been published.

## Boundaries and threat model

1. **Secrets in version control:** committed `.env` files, private keys, GitHub access tokens and cloud credentials may expose privileged systems. Reject tracked sensitive paths and high-confidence credential patterns. Do not claim this limited scanner replaces GitHub secret scanning or a human review.
2. **Supply-chain drift:** `pnpm-lock.yaml` and `uv.lock` should be reviewed, pinned, and installed reproducibly. Offline consistency checks do **not** identify every vulnerable transitive dependency. Audit intentionally, record its date/output and handle advisories through reviewed updates.
3. **Workflow privilege escalation:** verification is read-only. Pages retains narrowly scoped write permissions only in its existing confirmation-gated deployment job. M01 does not authorize invoking that job; any hosting migration requires separate review.
4. **Unapproved source export:** publisher reuse, CMA crosswalk and income/rent statistical join permissions remain blocked. Static frontend assets must not contain original publisher downloads, unlicensed geodata or fabricated metrics.
5. **Unattended execution:** repository workflows remain `workflow_dispatch` only; Dependabot configuration and scheduled GitHub Action checks are not committed. GitHub-wide security controls require a separate administrator decision.

## Offline Windows acceptance

From `feat/M01-engineering-foundation`:

```powershell
python scripts/validate_m01_security.py
python scripts/validate_m01_governance.py
python scripts/validate_m01_docs.py
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
python scripts/validate_m01_toolchains.py
pnpm.cmd install --frozen-lockfile --ignore-scripts
pnpm.cmd --dir frontend typecheck
pnpm.cmd --dir frontend build
git diff --check
```

The security validator uses `git ls-files` plus non-ignored working-tree files for path checks and limited high-confidence credential-pattern detection. It does not transmit repository contents or make network requests. A successful result means **the checked files passed these rules**, not that the source tree is immune to all secret leaks or supply-chain vulnerabilities.

### Optional, explicitly manual dependency audit

Run this only when network-backed package auditing is desired and permitted:

```powershell
pnpm.cmd audit --audit-level high
```

Record advisory IDs, exit status and timestamp in the PR review, and triage any findings without silently changing pinned dependencies. If the audit registry cannot be reached, record **not verified**, not **passed**. `uv lock --check --offline` validates the locked Python environment but is **not** a Python vulnerability advisory scan. Keep Dependabot automatic PRs/scheduling disabled until a separate explicit decision.

## Maintainer GitHub security review (not performed by this package)

- Inspect repository Settings → Security / Code security & analysis for available secret scanning, push protection, Dependabot alerts and private vulnerability reporting. Record actual availability and enabled state; do not assume account entitlement or activation.
- Examine repository **Settings → Rules → Rulesets** and action permissions. No status check should be marked required unless a compatible producer is configured and approved; manual-only verification is not an automatic PR check.
- Check GitHub Actions permissions and secrets. Never add powerful repository credentials or automation tokens merely to run a read-only contract check.
- Determine whether a private security-reporting channel is actually available before advertising its use; `SECURITY.md` deliberately does not invent an email address.
- Keep repo visibility, licence and redistribution decisions separate from publisher data reuse permissions. **A public repository is not the same as licensed public datasets.**

**Carry-forward:** M01-T07 must demonstrate a locally validated static export/base path; it may not activate Pages, Cloudflare, or another deployment by inference from this security review.
