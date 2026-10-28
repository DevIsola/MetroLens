# M01-T07 — Local static export and project subpath validation

**Scope:** Verify an unpublished Next.js static build at both `/` and `/UrbanGauge/`. No GitHub Pages release, Cloudflare deployment, workflow scheduling, public dataset or application server is started.

The new `/methodology/` route is an actual statically exported deep link. Its copy states the research's publication and statistical-comparability restrictions without embedding source-derived observations. Next's `<Link>` prefixes internal links at build time, and `trailingSlash: true` ensures `methodology/index.html` can be served by ordinary directory-based static hosts.

## Commands on Windows PowerShell

From the repository root, with Node 24.22.1, pnpm 10.34.9 and all packages installed:

```powershell
python scripts/validate_m01_static_export.py
pnpm.cmd install --frozen-lockfile --ignore-scripts

# 1. Default root-path export, only local files.
Remove-Item Env:NEXT_PUBLIC_BASE_PATH -ErrorAction SilentlyContinue
pnpm.cmd --dir frontend typegen
pnpm.cmd --dir frontend typecheck
pnpm.cmd --dir frontend build
python scripts/validate_m01_static_export.py --smoke --base-path=

# 2. Independent project-path export, still only local files.
$env:NEXT_PUBLIC_BASE_PATH = '/UrbanGauge'
try {
    pnpm.cmd --dir frontend build
    if ($LASTEXITCODE -ne 0) { throw 'Prefixed build failed' }
    python scripts/validate_m01_static_export.py --smoke --base-path /UrbanGauge
    if ($LASTEXITCODE -ne 0) { throw 'Local HTTP smoke failed' }
} finally {
    Remove-Item Env:NEXT_PUBLIC_BASE_PATH -ErrorAction SilentlyContinue
}

python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
git diff --check
git status -sb
```

On Windows PowerShell, pass the root-path argument as `--base-path=` (one token). Passing `--base-path ""` may result in an omitted argument. Always rebuild without `NEXT_PUBLIC_BASE_PATH` before the root smoke.

`--smoke` serves `frontend/out/` on an ephemeral **127.0.0.1-only** port, requests the homepage and direct methodology deep link, checks that absolute URLs keep the correct subpath, and retrieves up to four actual Next.js static assets. It shuts the server down after the checks and makes no internet requests. It does **not** assert production hosting/CDN behavior, a hosted GitHub Actions run, or an independently reviewed source-data release.

You may also inspect the **local development page** with `pnpm.cmd --dir frontend dev` at <http://localhost:3000/>. It is a different process from the production-export smoke test. After finishing the prefixed build, unset `NEXT_PUBLIC_BASE_PATH` before running the root development server.

## Manual workflow and hosting distinction

`.github/workflows/verify.yml` stays `workflow_dispatch`-only with `contents: read`. Its build now runs with `NEXT_PUBLIC_BASE_PATH: /UrbanGauge` and performs the same local HTTP smoke on the resulting artifact; it never uploads or deploys the site. Existing `.github/workflows/pages.yml` remains unchanged and must **not** be dispatched for this milestone. A future hosting decision may use Cloudflare instead; that requires separate approval, build-path review and tests.

## Publication and data safeguards

M00 is done, M01 remains in progress. No public source-derived exports, CMHC/StatCan crosswalk, income/rent join, inferred affordability ratio, automated CI/ETL or website deployment is authorized. M01-T07 is an engineering acceptance increment, not permission to publish a website.
