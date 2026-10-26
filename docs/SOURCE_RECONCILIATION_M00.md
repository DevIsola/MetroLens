# M00 — Vancouver rental/income technical evidence reconciliation

**Status:** Source-specific evidence reviewed; cross-source affordability comparison **not approved**. Review date: 2026-10-26.

This is a discovery checkpoint after the local machine successfully ran the official-source probes and extraction tools. See [`evidence-vancouver-m00.json`](evidence-vancouver-m00.json) for the **small human-reviewed benchmark**. That JSON contains publisher SHA-256 fingerprints and selected observations transcribed from the locally executed extractors, not copied raw publisher data. It is **not** a production feed, audit signature, or official certification. Re-running the CLI checks these reported observations against both source files currently stored in the gitignored probe directory. A source change must be re-reviewed; do not overwrite the benchmark merely to make a failing check pass.

## Accepted as source-specific technical evidence

| Source | Scope | Reviewed identifiers | Observations | Source hash |
| --- | --- | --- | --- | --- |
| Statistics Canada 2021 Census, [98-10-0058-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810005801) | All private households, Vancouver CMA | `2021S0503933`, coordinate `5381.1.1`, CMA code `933` | 1,043,315 households in 2021; 2020 median total income CAD 90,000; median after-tax income CAD 79,500 (2020 dollars) | `f29f937b97c18a227a25c8cc32fe361fc5d251f0aab41699c0713a4b8f3d3a81` |
| CMHC 2025 [Rental Market Survey](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables) Vancouver workbook | Surveyed purpose-built private rental apartments, Vancouver CMA | `Table 1.1.2`, row `36`, 2021 Census geography vintage | October 2024 and 2025 average monthly rents for five bedroom categories; two-bedroom rent CAD 2,314 / CAD 2,363, respectively; all 10 quality flags `a` = Excellent | `2fda7bea9ad42787c1820dd4d60f11091ff2455c4eec1732b14acc97660c3258` |

The income extractor scanned the complete CSV and skipped exactly two *trailing* blank records, preserving the no-duplicate-CMA-record check. These are data-integrity observations from the user's locally audited files; `source_evidence_reconciled` is only a technical state, not a licence or metric approval.

## Explicit comparability blockers

1. **Reference years:** The annual income values refer to **2020** (2021 Census survey), while rental values refer to **October 2024 and October 2025**. Do not align by publication year, substitute ingestion dates, or extrapolate 2020 income.
2. **Population and measures:** The income figure is the **median among all private households**; the CMHC figure is the **mean rent of surveyed private purpose-built rental apartment units**. It is not rent actually paid by the income sample, or an observed household-level burden. Even same-year figures would require a carefully labelled aggregate comparison and independent review.
3. **Geography:** Both sources claim a **2021 Census geographic basis**, but matching this vintage and place name does **not** establish an approved publisher-ID crosswalk. Census DGUID is present; CMHC workbook labels the CMA but has not provided a DGUID in the reviewed extract.
4. **Rights and disclosures:** Statistics Canada's [Open Licence](https://www.statcan.gc.ca/en/terms-conditions/open-licence) and the [CMHC data licence](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/cmhc-licence-agreement-use-of-data) need explicit approval of attribution and intended publication. No third-party files are redistributed or committed.

The script hardcodes the decision **not** to calculate or publish a rent-to-income number even if both files match their respective expected values.

## Additional income source candidates — discovery, not substitutes

Official Statistics Canada [Table 11-10-0190-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001) (Canadian Income Survey) reports *annual* market, total and after-tax income by **economic family type** and CMA through 2024. [Table 11-10-0191-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019101) offers related income-source statistics; [Table 11-10-0237-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110023701) reports economic-family distributions for selected CMAs. These are **not** the same universe as all private households, and reported 2024 income is **not** 2025 income. Table availability for Vancouver, suppression symbols, 2021 geography comparability and survey methods must be inspected in a future opt-in source probe before selecting an indicator.

**MVP fallback:** Publish rent and income as separately labelled historical indicators with their own reference periods and source metadata; defer a rent-to-income ratio until compatible underlying observations and reviewed methodology are available. This is a proposal, **not** an approved M00 scope change.

## Reproduce offline — no download or deployment

```powershell
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
python scripts/reconcile_vancouver_evidence.py
# Optional: save small source-evidence status report to Downloads
python scripts/reconcile_vancouver_evidence.py > "C:\Users\hello\Downloads\MetroLens_M00_Vancouver_Reconciliation.json"
```

Expected successful status: `source_evidence_reconciled` with `metric_comparability_approved=false`, `publication_approved=false`, and `rent_to_income_ratio=null`. If either publisher file is unavailable, changed, suppressed, or fails extraction, status is `blocked` with nonzero exit status and **no ratio**. Raw source files remain under `pipeline/data/raw/m00-source-probes/` (gitignored). The script does not create any production output, modify source manifests, access the network, or change workflow/release settings.

## Request for next user evidence

Attach **only** the small reconciliation JSON. Include any error JSON if blocked. If the report is successful, the next task is to inspect a *specific real 2024 CMA income source extract* to determine whether it can support a distinct, properly labelled comparison; do not collect and forward the entire Census archive or CMHC workbooks.
