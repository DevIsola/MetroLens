# Canada Affordability & Opportunity Observatory

**Project codename:** MetroLens (not an approved public brand).

A proposed bilingual, static-first Canadian affordability data observatory. This repository starts with feasibility research and engineering governance before introducing ingestion, verified metrics, or a public dashboard. **No production data or analytical conclusions have been published.**

## Current scope

- Milestone M00: source discovery, candidate Canadian Census Metropolitan Areas (CMAs), rent/income compatibility, and architecture decisions.
- Canonical contract: [`docs/NORTHSTAR_MASTER_ROADMAP.md`](docs/NORTHSTAR_MASTER_ROADMAP.md), v0.2.0.
- Visual reference: [`docs/design/theme-preview-v0.2.0.html`](docs/design/theme-preview-v0.2.0.html). Figures in that preview are fictional.
- Proposed analytics: official Statistics Canada, CMHC, and Bank of Canada data, with source licensing and coverage verified before ingestion.

## Local validation (no cloud runners)

Requires Python 3.11+ and Git. M00 tools use only the Python standard library.

```sh
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
```

For a roadmap-status change, edit `docs/roadmap-status.json` and run `python scripts/sync_roadmap.py --write`, then rerun validation. Milestones cannot be marked `done` without merged PR and acceptance evidence.

## Branch, commit, and deployment policy

- Milestone branches: `feat/M00-product-discovery`, `feat/M01-engineering-foundation`, etc.
- Small atomic commits: `docs(M00-T01): ...`, `test(M00-T01): ...`, `ci(M00): ...`.
- Run local tests before **every** push; push to the current milestone branch, not directly to `main`.
- Open one PR for the milestone, updating it with each increment; merge only after review and demonstrated acceptance.
- Workflows intentionally have `workflow_dispatch` only. Ordinary commits, branch pushes, PR updates, and merges do **not** start Actions. **Bootstrap exception:** GitHub only exposes `workflow_dispatch` once the workflow file exists on the default branch; validate the first M00 PR locally, then manually run the workflow on later milestone checkpoints once the initial branch is merged.
- Pages publishing is an explicitly confirmed, manually dispatched action from `main` **only**. No deployment is expected before frontend static export and contracts are ready (M01/M05). No ETL schedule is enabled (M09 will introduce one under an ADR).
- Choose **GitHub Actions** in repository Settings → Pages → Build and deployment → Source. **Do not** select branch publishing, which would circumvent the release gate. Protect the `github-pages` environment to allow deployments from `main` only.

See [`docs/RELEASE_POLICY.md`](docs/RELEASE_POLICY.md) for release/rollback rules and setup instructions.

## Planned implementation order

M00 discovery → M01 developer foundation → M02 ingestion → M03 normalization → M04 verified marts/static contract → M05 overview/site publication → M06 explorer → M07 scenarios → M08 storytelling → M09 controlled ETL schedule → M10 observability → M11 public release.

> Source compatibility, actual data coverage, licenses, commit hashes, issue/PR IDs, and production deployments must be recorded from real evidence, never assumed.

## M00-T02 source reconnaissance (opt-in, offline by default)

```sh
python scripts/probe_official_sources.py --source boc-overnight          # Preview URL, no network
python scripts/probe_official_sources.py --source boc-overnight --fetch  # Explicit bounded fetch
```

Additional sources: `statcan-income`, `cmhc-vancouver`, `cmhc-toronto`.
See [`docs/SOURCE_VALIDATION_M00_T02.md`](docs/SOURCE_VALIDATION_M00_T02.md) for URLs, CLI examples, licence requirements and **unresolved** source-data acceptance gates. Successful probes write only to gitignored `pipeline/data/raw/`; source-format tests are synthetic and are **not** evidence that publisher files were actually downloaded or semantically comparable. Normal pushes still trigger **no** CI, Pages or scheduled ETL.

## Audit locally downloaded publisher evidence (M00-T02)

After successfully fetching official samples, run the zero-network audit:

```sh
python scripts/audit_source_probes.py
```

It revalidates original files and their manifests, and reports missing/invalid evidence without authorizing an affordability calculation. Exit codes: `0` = all selected **structural** checks pass; `1` = incomplete evidence; `2` = invalid evidence. The source files and reports remain gitignored. Refer to [`docs/SOURCE_VALIDATION_M00_T02.md`](docs/SOURCE_VALIDATION_M00_T02.md) for interpretation and limitations.

## Assess rent/income comparability (M00-T03, review only)

```sh
python scripts/assess_metric_compatibility.py
```

The command reports why the existing 2020-income/2025-rent discovery samples are **blocked**. No affordability value is calculated or published. The output never authorizes data promotion; even complete metadata requires independent methodology review. See [`docs/COMPARABILITY_REVIEW_M00_T03.md`](docs/COMPARABILITY_REVIEW_M00_T03.md). GitHub Actions, Pages and ETL schedules are unchanged.

## Preview actual publisher rows for manual source review (M00-T02)

After local `--fetch` source probes succeed, use the **offline-only**, bounded inspector:

```sh
python scripts/review_source_rows.py --source statcan-income --region Vancouver --limit 5 --max-scan 200000
python scripts/review_source_rows.py --source cmhc-vancouver  # List sheet names
python scripts/review_source_rows.py --source cmhc-vancouver --sheet '1.1.1'  # Example; use real sheet name
```

This previews raw Census values with `Symbol` fields and selected CMHC worksheet cells **only if the source manifest/file audit passes**. It does not match rent to income, approve source licensing, or write public datasets. Full instructions and explicit limitations are in [`docs/SOURCE_ROW_REVIEW_M00_T02.md`](docs/SOURCE_ROW_REVIEW_M00_T02.md). Keep review reports in gitignored `pipeline/data/raw/`.

## M00-T02 Vancouver CMA rental extraction (review only)

After auditing the downloaded CMHC Vancouver workbook, run `python scripts/extract_cmhc_cma_rents.py`. It checks the exact `Table 1.1.2` headers, reads the `Vancouver CMA` total rather than city/zone subtotals, preserves 2024/2025 observations for each apartment type with source reliability flags, and fails on missing/suppressed/changed source evidence. **This is not a production dataset or an approved rent/income join.** See [`docs/CMHC_VANCOUVER_CMA_REVIEW_M00_T02.md`](docs/CMHC_VANCOUVER_CMA_REVIEW_M00_T02.md).

## M00-T02 exact Vancouver CMA Census income (review only)

Following a passing local StatCan source-file audit, run
`python scripts/extract_statcan_cma_income.py` to extract the unique Vancouver CMA
**all-household** observation for 2020 median total/after-tax income and the 2021
household count. Preserve original Census dimension codes, quality symbols,
periods and ZIP checksum. This **does not** align 2020 income to 2024/2025 rent,
permit cross-source ratios or authorize publishing. See
[`docs/STATCAN_VANCOUVER_CMA_REVIEW_M00_T02.md`](docs/STATCAN_VANCOUVER_CMA_REVIEW_M00_T02.md).

### Windows Census extraction: unexpected final CSV record

If the audited Census income ZIP passes `review_source_rows.py` but an earlier extractor raised `Malformed Census CSV row 484870`, update to the M00-T02 trailing-record fix. It only ignores fully blank **terminal** records and preserves duplicate and nonblank-row guards. From the repository root, re-run `python scripts/extract_statcan_cma_income.py`. Send the full report, including `trailing_blank_rows_skipped`, or the new field-count diagnostic if extraction still fails. Do not edit or re-download a verified publisher file just to address the parser issue. See `docs/SOURCE_VALIDATION_M00_T02.md`.

## M00 local evidence reconciliation (read-only)

With both previously verified publisher files in the gitignored source-probe directory, run:

```powershell
python scripts/reconcile_vancouver_evidence.py
```

This validates reviewed Vancouver 2020 income and 2024/2025 rent observations against their pinned file hashes. It **does not** calculate or authorize a rent-to-income ratio. See [`docs/SOURCE_RECONCILIATION_M00.md`](docs/SOURCE_RECONCILIATION_M00.md).
