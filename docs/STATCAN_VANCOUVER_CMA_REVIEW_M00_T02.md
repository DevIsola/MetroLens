# M00-T02 — Vancouver CMA 2021 Census household income extraction

**State:** Extraction code and synthetic regression tests verified locally; **real publisher-file extraction on the user's workstation still required**. This is discovery evidence only, not an approved production data mart or rent/income join.

## Evidence supplied by local source review (2026-10-26)

The user supplied the output of `python scripts/audit_source_probes.py --source statcan-income` and `python scripts/review_source_rows.py --source statcan-income --region Vancouver --limit 12 --max-scan 2000000`.

- Source: Statistics Canada Census Table `98-10-0058-01`, `statcan_98100058`.
- Locally audited compressed ZIP SHA-256: `f29f937b97c18a227a25c8cc32fe361fc5d251f0aab41699c0713a4b8f3d3a81`; 6,552,215 bytes. This hash is user-reported local evidence, **not a publisher cryptographic attestation**.
- 2021 Census geography: **Vancouver (CMA) 933, B.C.**; DGUID `2021S0503933`; original coordinate `5381.1.1`.
- Household size: `Total - Households by household size`.
- Household type: `Total – Household type including census family structure`.
- 2021 household count: **1,043,315**, blank adjacent symbol.
- Median annual total household income in **2020** (2020 constant dollars): **CAD 90,000**, blank adjacent symbol.
- Median annual after-tax household income in **2020** (2020 constant dollars): **CAD 79,500**, blank adjacent symbol.
- `REF_DATE` = `2021` refers to the **Census** year, not the income year. The other 11 reviewed observations represent household subgroups or sizes, not the total used here.

This observed sample is not itself sufficient to prove every row in the original publisher file; the extractor must reproduce the values on the audited local ZIP.

## Exact extractor contract

Run from the repository root:

```powershell
python scripts/audit_source_probes.py --source statcan-income
python scripts/extract_statcan_cma_income.py
```

The script uses only built-in Python modules and never fetches data. It re-audits the recorded ZIP and manifest, verifies the Census-wide transposed header, scans the CSV with bounded memory, requires exactly one row matching **the DGUID, both total-household dimensions, the geographic label, Census coordinate and reference year**, and emits three measure records with original source column positions and adjacent `Symbol` fields. It re-audits after the scan to detect file changes. It never writes production data.

Expected result for the user-reported file: `status: extracted_for_review`, `dguid: 2021S0503933`, `coordinate: 5381.1.1`, `income_reference_year: 2020`, and three observed values `1043315`, `90000`, `79500`. Source symbol text is preserved; flagged/unusable measures become `null` and cannot silently become zero.

Exit codes: `0` = an exact candidate record was extracted for review, `1` = missing/unverified file evidence, `2` = source contents invalid or ambiguous. No exit code approves the data for publication or for cross-source joins. Save the JSON report locally under gitignored `pipeline/data/raw/` if a durable record is needed; **do not add raw source ZIPs or publisher records to Git**.

## What remains blocked

1. The CMHC 2024/2025 rental workbook and this 2020 Census income table refer to different periods. No contemporaneous affordability fraction is authorized.
2. Both source products refer to a 2021 Census geographic vintage, but **source-specific coverage and the exact population-compatibility crosswalk still require review**. The rental survey covers purpose-built apartments; income covers *all* private households, not renter households only.
3. Source licensing, required CMHC notices, transformation attribution and redistribution permissions must be reviewed for the intended derived output.
4. Find a genuinely comparable 2024/2025 income series (or revise the product metric to explicitly separated contextual indicators). Do not relabel 2020 income as current.

The user-reported 2020 median total and after-tax income are useful separate **historical Census indicators** once method and reuse review is complete; they are not sample evidence that the 2024/2025 CMHC rent values are affordable or unaffordable for a typical renting household.

**No workflow, hosting, CI trigger, or ETL schedule changes. M00 stays in progress.**
