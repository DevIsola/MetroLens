# Security and responsible disclosure

UrbanGauge is an early-stage public research repository. Its frontend is not a public production data service, and source-data publication has **not** been approved.

## Reporting a security concern

Do **not** post secrets, access tokens, exploitable credentials, or private source data in a public GitHub issue. Contact the repository maintainer through a private channel you already trust. GitHub private vulnerability reporting may be used **only if the maintainer has enabled and verified it**; its availability is not claimed by this file. If no private channel is available, request a safe contact method without disclosing exploit details or secrets.

Include affected component, version/commit, reproduction outline without private data, impact, and a mitigation proposal. Do not include real tokens or unapproved publisher files.

## Scope and current guarantees

- M01 repository security gates cover checked-in files and workflow configuration; they do **not** prove hosted GitHub settings or the absence of all vulnerabilities.
- GitHub Actions workflows are **manual-only** (`workflow_dispatch`). Do not create `push`, `pull_request`, `schedule`, or `workflow_run` triggers.
- `.github/dependabot.yml` is intentionally absent. Automated dependency PRs or alerts are not claimed as configured. Review any future enablement separately.
- The verification workflow has read-only repository permissions. The existing legacy Pages workflow has write permissions only in its human-confirmed deployment job; **deployment is not authorized by M01**.
- Secrets, `.env` files, private keys, raw publisher archives, local databases and unreviewed exported data must not be committed or published.
- External dependency advisories require a *separate manually initiated, network-backed audit*. Passing the offline check is not a vulnerability-free claim.

See `docs/M01_T06_SECURITY_AND_DEPENDENCIES.md` and ADR-0005 for the reviewer checklist and audit procedures.
