# UrbanGauge — Local development (M01-T01)

## Prerequisites and branch policy

- Windows PowerShell, Git and Python **3.11 or newer** for current M00/M01-T01 standard-library checks. `Node.js`, `pnpm` and `uv` version selection/installation are deferred to M01-T02, where versions and lockfiles will be pinned together.
- Clone `https://github.com/DevIsola/UrbanGauge.git` or continue with the existing local checkout. Existing directory name is unimportant.
- Develop on `feat/M01-engineering-foundation` based on `main`; never commit directly to `main`. Run local validations before each push.
- GitHub Actions verification and Pages publication are manually dispatched only. A push must not trigger CI, ETL, or deployment.

```powershell
git switch main
git pull --ff-only origin main
git switch feat/M01-engineering-foundation

python --version
python scripts/activate_m01.py --check
python scripts/activate_m01.py --apply
python scripts/validate_m01_workspace.py
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
git diff --check
git status -sb
```

The activation command changes only `docs/roadmap-status.json` and the **generated milestone table** in `docs/NORTHSTAR_MASTER_ROADMAP.md`. `--check` performs a dry run and does not alter files. The activation refuses non-M01 branches and invalid M00 acceptance evidence. After successful validation, commit those two generated changes together with the M01-T01 files.

## Source and output safety

Official publisher inputs must stay under the ignored `pipeline/data/raw/` tree. Do not commit large raw ZIP/XLSX/CSV downloads, local extraction reports, secrets, `.env` files or made-up output datasets. Store provenance and licence decisions in the documented review process; review explicit publication gates before any public JSON export.

Current source inspection and data previews are local-only, with independent rent and income series. **Do not compute or publish an affordability ratio** from the reviewed Vancouver rent/income samples.

## Folder ownership

- `docs/`: decisions, methods, contract, and onboarding.
- `scripts/`, `tests/`: repository contracts and the retained M00 safety suite.
- `pipeline/`: eventual validated data processing, never an HTTP server or frontend database.
- `frontend/`: eventual statically exported browser application, never direct access to the ignored source downloads.

If the user-facing M00 README references old MetroLens/Northstar paths, preserve historical citations rather than bulk-renaming audited evidence.
