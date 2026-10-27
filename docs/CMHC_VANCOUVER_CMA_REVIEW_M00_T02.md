# M00-T02 — Vancouver CMA average rent extraction review

**Decision:** CMA rent worksheet structure and values were **reported by the user** from the CMHC 2025 Rental Market Survey on 2026-10-26. Automated extraction from the user's original file has **not** been run inside this repository session. `M00` remains `in_progress`; **no affordability ratio, production mart, or publication is approved**.

## Source and selected observation

- Official publisher: **Canada Mortgage and Housing Corporation (CMHC)**, 2025 Rental Market Survey, [Vancouver workbook](https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-data-tables/rental-market/rental-market-report-data-tables/2025/rmr-vancouver-2025-en.xlsx?rev=9c12f2db-c0c8-4d06-83e1-cc3e06da8d36).
- Excel worksheet: **`Table 1.1.2`**, heading: `1.1.2 Private Apartment Average Rents ($), by Zone and Bedroom Type - Vancouver CMA`.
- Row label: **`Vancouver CMA`** (not `City of Vancouver (Zones 1-10)`, individual survey zones or `West End/Downtown`).
- Survey periods: **October 2024** and **October 2025**. Both years use **2021 Census geographic definitions**, per the workbook's footnote. This is *evidence of matching reference vintage*, **not yet an independently verified geography-ID crosswalk** to Statistics Canada table `98-10-0058-01`.
- Source-reported local provenance: the user's prior row-review output returned `file_verified` and SHA-256 `2fda7bea9ad42787c1820dd4d60f11091ff2455c4eec1732b14acc97660c3258`. This hash has **not been independently reproduced** here.

| Apartment category | Oct 2024 (CAD/month) | Oct 2025 (CAD/month) | Source quality (both periods) | Source columns: 2024 value / flag; 2025 value / flag |
| --- | ---: | ---: | --- | --- |
| Studio | 1,575 | 1,667 | `a` / `a` | `B/C`; `D/E` |
| 1 bedroom | 1,769 | 1,806 | `a` / `a` | `F/G`; `H/I` |
| 2 bedrooms | 2,314 | 2,363 | `a` / `a` | `J/K`; `L/M` |
| 3+ bedrooms | 2,942 | 3,009 | `a` / `a` | `N/O`; `P/Q` |
| All apartment bedroom counts | 1,924 | 1,963 | `a` / `a` | `R/S`; `T/U` |

**Measure:** CMHC average surveyed private purpose-built apartment rent, by bedroom type, in CAD/month; **not** turnover rent for newly changed tenants, condominium rent, or advertised asking rent. Do not silently compare this measure with the 2025 2-bedroom *turnover* rent sample of CAD 2,696.

## Published reliability legend (source-reported)

- `a` — Excellent
- `b` — Very Good
- `c` — Good
- `d` — Poor (use with caution)
- `**` — Data suppressed, must be represented as `null`, never zero

The extractor records the quality code and cell address adjacent to **each** observation. Unknown codes, missing quality for a numerical value, duplicate CMA totals, unexpected years/categories, or missing geographic or quality footnotes block extraction. A `d` observation is explicitly marked `use_with_caution`; `**` becomes a null suppressed record. It does **not** calculate change percentages or infer household rent burden.

## Run on the real, audited workbook (PowerShell)

From the MetroLens repository root, after the Vancouver CMHC probe succeeds:

```powershell
python scripts/audit_source_probes.py --source cmhc-vancouver
python scripts/extract_cmhc_cma_rents.py
```

To keep a review report in the **gitignored** local source folder:

```powershell
python scripts/extract_cmhc_cma_rents.py > pipeline/data/raw/m00-source-probes/vancouver-cma-rent-review.json
```

Expected JSON: `status: extracted_for_review`; `sheet: Table 1.1.2`; `geography_label: Vancouver CMA`; `source_row` (real Excel row index); `records` (five apartment categories × two reference periods), `source_sha256`, quality codes, exact addresses, and explicit approval gates all `false`. The extractor checks the file audit **before and after** sampling; it never downloads data or writes derived records itself. Its input must be the **identical** file in the ignored source directory referenced by the existing verified manifest. When the source file is absent or its checksum differs, the extractor blocks; it does not use values transcribed in this document as a fallback.

## Remaining M00 acceptance gates

1. Run the extractor on the original workbook and review JSON output against the row above. Verify 2021-CMA code/DGUID crosswalk with the Census source and document population boundaries.
2. Review actual Statistics Canada 2020 household-income rows and available **time-aligned** 2024/2025 household-income alternatives. A 2020 household median cannot be paired with 2025 average rent as a burden indicator.
3. Preserve differences between average survey rent, turnover rent, asking rent and household population concepts; obtain publication/reuse notice approval under the applicable CMHC data licence.
4. Introduce an explicit `M00-T03` methodology decision for any safe display-only or derived measure. Do not advance `M00` to done before the separate review/PR acceptance gate.

No GitHub Actions schedules, GitHub Pages deployments or ETL jobs are modified by this increment.
