# M00-T02 — Bounded review of actual source rows and CMHC worksheets

**Status: discovery-only.** This is a local read-only evidence review, not a production parser, a geographic crosswalk, or proof of statistical comparability. It does not fetch data, publish a dashboard, commit raw files, or generate rent-to-income figures. Run it only after the publisher probes and their manifests exist locally.

## Workstation commands (PowerShell)

```powershell
python scripts/audit_source_probes.py

# Inspect income source rows by *candidate label*; numbers and Symbol flags are unmodified text.
python scripts/review_source_rows.py --source statcan-income --region Vancouver --limit 5 --max-scan 200000
python scripts/review_source_rows.py --source statcan-income --region Toronto --limit 5 --max-scan 200000

# First list worksheet titles, then select an EXACT workbook sheet title from the result.
python scripts/review_source_rows.py --source cmhc-vancouver
python scripts/review_source_rows.py --source cmhc-vancouver --sheet '1.1.1' --limit 8
python scripts/review_source_rows.py --source cmhc-toronto

# V39079 is background macroeconomic data, not CMA-level rent/income evidence.
python scripts/review_source_rows.py --source boc-overnight
```

`'1.1.1'` is **only an example of an exact worksheet name**. Use the names reported by your actual workbook; do not treat this number as an approved CMHC table identifier. A sheet title listing is more reliable than guessing worksheet position.

To save a small review report while keeping publisher values out of the tracked repository:

```powershell
python scripts/review_source_rows.py --source statcan-income --region Vancouver --limit 5 --max-scan 200000 > pipeline/data/raw/m00-source-probes/review-statcan-vancouver.json
```

## Audit gate and result contract

The command calls the existing offline `audit_source_probes.py` for exactly the source selected. It prints `status: blocked` and returns exit code **1** if the hash/format manifest is unavailable, missing its original publisher file, or invalid. It prints `status: sampled` with a verified local SHA-256 and limited sample when the file and manifest match, returning **0**. An incorrect sheet, malformed cell, or unexpected workbook structure returns **2**, `status: invalid`. No status authorizes a metric or publication.

Every successful response has `sampling_only: true`, `all_rows_reviewed: false`, `geography_crosswalk_approved: false`, `metric_comparability_approved: false`, and `publication_approved: false`.

For Census table `98-10-0058-01`, the script scans up to `--max-scan` records (100,000 by default; maximum 2,000,000), emits up to `--limit` matching rows (5 by default; maximum 12), and retains `GEO`, `DGUID`, household size/type, original transposed income measure labels, raw values, and their **adjacent `Symbol` flags**. It **does not** infer a 2025 income observation from the 2021 Census: the household income reference year remains **2020**. A matching `GEO` label is a search heuristic, not proof of CMA DGUID equivalence with CMHC. A result with no rows might mean the bounded scan did not reach that geography, not that a CMA has no income data.

For CMHC, listing worksheets does not read rent cells. When a specific worksheet is requested, the tool streams only a small number of its initial populated rows and the first 16 cells per row, with values truncated to 160 characters. It handles standard XLSX shared strings, inline strings and cached numeric values, but **not** spreadsheet formatting, merged-cell interpretation, formulas without cached results, or year/series disambiguation. A large shared-string dictionary (>32 MiB) and oversized worksheet (>256 MiB uncompressed) fail closed. Review the workbook legend, geography names/codes, year, rental stock/turnover universe, bedroom count, unit, and any suppressed cells manually before selecting a statistic.

## Human review checklist

1. Verify the full Census `DGUID` and the 2021 geographic vintage behind each `GEO`; narrow the correct household-size/type slice and reject rows with nonempty suppression/quality symbols unless source methodology says otherwise.
2. Identify **exact** CMHC sheet title, heading/series label, bedroom composition, average-vs-median measure, survey year, CMA coverage, and suppressed/not-applicable symbols. Determine whether the published sheet supports an authoritative source geo code or requires a documented name/boundary crosswalk.
3. Record the selected IDs, exact official source links, geographic-vintage and population alignment rationale, reference dates, units, attribution and license in `docs/DATA_CATALOG.md` and `docs/METRICS_DICTIONARY.md` after independent review.
4. If compatible income/rent definitions cannot be proven, publish **side-by-side indicators** at M05 instead of a fabricated universal ratio. `assess_metric_compatibility.py` must remain non-authorizing.

All automated tests in this increment use **synthetic** CSV/XLSX fixtures. Actual workbook interpretation and source licensing remain pending M00 acceptance; `M00` remains `in_progress`. GitHub Pages, Actions triggers, and scheduled ETL are unchanged.
