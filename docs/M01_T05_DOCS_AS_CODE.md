# M01-T05 — Documentation-as-code and manual verification

**Scope:** Add a changelog, ADR index, M01-specific ADR and a validator that couples reviewable documentation to the canonical roadmap; extend a manually dispatched verification workflow with real frontend checks.

## Local acceptance (Windows PowerShell)

```powershell
python scripts/sync_roadmap.py --check
python scripts/validate_m01_docs.py
python -m unittest discover -s tests -v
pnpm.cmd install --frozen-lockfile --ignore-scripts
pnpm.cmd --dir frontend typegen
pnpm.cmd --dir frontend typecheck
pnpm.cmd --dir frontend build
Test-Path .\frontend\out\index.html
git diff --check
```

The last test should print `True`. `validate_m01_docs.py` checks source contracts **offline**, not hosted workflow execution. An actual manually dispatched GitHub Actions run is a separate reviewer choice and can only be claimed with its URL and tested commit SHA.

## Review and release constraints

- `verify.yml` remains **workflow_dispatch only**, and it has no `pages: write` or `id-token: write` permission, deployment job, Pages upload or automatic event.
- `pages.yml` is **unchanged** by M01-T05; it still requires an explicit manual confirmation on `main` and remains subject to independent release gates. Do not dispatch it for M01 acceptance.
- `M00` stays `done`, `M01` stays `in_progress`; publication/affordability/geographic-crosswalk gates stay closed.
- The changelog is engineering-only and must not imply a public website, approved source data, or a released data product.

## Future work

M01-T06 will audit token permissions and security posture without enabling automatic Actions. M01-T07 will validate a local static export under the intended subpath and deep links, without publishing it. A future governance decision is needed if the maintainer later authorizes automatically produced checks or required PR statuses.
