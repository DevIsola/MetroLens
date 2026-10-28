# UrbanGauge — M01-T02 reproducible toolchains (2026-10-27)

**Scope:** reproducible, **dependency-free** package-manager bootstrap. This is not M01-T03's Next.js application, a completed frontend build, or an approved publication pipeline.

| Tool | Declared version | Reason |
| --- | --- | --- |
| Node.js | **24.22.1** | October 2026 LTS security release; pinned in `.node-version` |
| pnpm | **10.34.9** | Conservative supported line; pinned in root `package.json` `packageManager` |
| Python | **3.13.x** | Minor-version lock through `.python-version`, `requires-python`, and `uv.lock`; allow compatible security patches |
| uv | **0.10.0** | Enforced by `[tool.uv].required-version` and used to generate `uv.lock` |

## Windows PowerShell setup — from the repository root

1. Verify `python --version`, `node --version`, `npm.cmd --version`, `pnpm.cmd --version` (when installed), and `uv --version` (when installed). Existing Python tests only need Python; the pinned Node/pnpm/uv run commands need their corresponding tools.
2. Install Node 24.22.1 for your architecture from <https://nodejs.org/en/download/archive/v24.22.1> if `node --version` differs. Open a **new** PowerShell session afterward.
3. If needed, install pnpm 10.34.9 with `npm.cmd install --global pnpm@10.34.9` and verify `pnpm.cmd --version` returns `10.34.9`. Use `pnpm.cmd` explicitly in Windows PowerShell to avoid execution-policy errors from `.ps1` shims. Do not run `pnpm self-update` or install global project dependencies.
4. Install uv **0.10.0** using an official installer or `python -m pip install --user uv==0.10.0` (if pip is installed); start a new shell and confirm `uv --version` reports `0.10.0`.
5. Run these **locked, no-script** checks after the versions match:

```powershell
node --version
pnpm.cmd --version
python --version
uv --version
python scripts/validate_m01_toolchains.py
uv lock --check --offline
uv sync --locked --offline
pnpm.cmd install --frozen-lockfile --ignore-scripts
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
```

`uv sync` creates an ignored `.venv/` and pnpm can create an ignored `node_modules/`; no packages are declared yet. Do **not** commit those local folders. `pnpm-lock.yaml` is initially a no-dependency schema-v9 lockfile and must pass the actual **pnpm v10** frozen installer on your workstation before calling the pnpm side operationally verified. This package was generated in an offline environment without an accessible pnpm executable; its structure and schema are checked locally, but the actual pnpm CLI validation remains a workstation acceptance gate.

## Scripts and scope

- Root `package.json` includes `check:toolchains`, `check:roadmap`, and `test:python` for existing checks. It intentionally contains no `build`, `lint`, `typecheck`, or dependency imports yet. Do not use an empty/no-op command as evidence of an application build.
- `pnpm-workspace.yaml` reserves `frontend/` for the later Next.js workspace package.
- Root `pyproject.toml` represents the **virtual, non-installable** Python pipeline environment; existing standard-library scripts remain in `scripts/` and source downloads stay gitignored. No Python third-party runtime dependencies are introduced.
- Use `uv lock --check --offline` to verify sync without changing the lock; change dependencies later only through a reviewed increment that updates and commits the corresponding lockfile.
- Do not enable GitHub push/PR CI, Pages deployment, scheduled ETL, or public source-data exports during toolchain setup.
- Do not compute a cross-source rent-to-income ratio from the reviewed M00 samples.

## Later M01 increments

M01-T03 will add an actual Next.js app and its packages under `frontend/`, strict TypeScript, and corresponding pnpm lockfile changes; M01-T04–T06 will build out quality/security workflows under separate review; M01-T07 will demonstrate a local static export under the `UrbanGauge` Pages base path without deploying.

**Official reference:** <https://nodejs.org/en/download/archive/v24.22.1>, <https://pnpm.io>, <https://docs.astral.sh/uv/concepts/projects/sync/>.
