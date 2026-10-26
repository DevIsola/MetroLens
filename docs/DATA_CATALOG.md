# M00 — data source and geography feasibility catalog

**State:** Discovery catalog, **not an approved production catalog**. Updated 2026-10-26. Scope: M00-T01 through partial M00-T03. The source-specific CMHC Vancouver, Census and Canadian Income Survey extracts have passed user-run local audits and full-file checks; original publisher ZIP/XLSX files remain **outside Git**. See [`SOURCE_RECONCILIATION_M00.md`](SOURCE_RECONCILIATION_M00.md), [`CIS_VANCOUVER_EXTRACT_REVIEW_M00.md`](CIS_VANCOUVER_EXTRACT_REVIEW_M00.md), and [`samples/official-page-observations.csv`](samples/official-page-observations.csv). No cross-publisher affordability metric or publication is approved.

## Candidate CMA scope

Eight candidate Census Metropolitan Areas are registered in [`cma-candidates.csv`](cma-candidates.csv). Their three-digit `cma_code_2021` identifiers were checked against an official Statistics Canada geography reference (2021 Census basis). A CMA represents a metropolitan region rather than city proper. Leading zeros must be preserved if any future CMA codes include them.

| Region | StatsCan 2021 CMA code | Provincial coverage | CMHC crosswalk |
| --- | --- | --- | --- |
| Halifax | `205` | NS | Pending verification |
| Montréal | `462` | QC | Pending verification |
| Toronto | `535` | ON | Pending verification |
| Winnipeg | `602` | MB | Pending verification |
| Calgary | `825` | AB | Pending verification |
| Edmonton | `835` | AB | Pending verification |
| Vancouver | `933` | BC | Pending verification |
| Victoria | `935` | BC | Pending verification |

**StatsCan evidence:** [Technical Reference Guide for the Preliminary Estimates from the T1 Family File (T1FF), section: CMA codes for 2021 Census](https://www150.statcan.gc.ca/n1/pub/11-26-0001/112600012025001-eng.htm). This verifies Census geographic labels/identifiers in that series, **not** dataset availability, income comparability, or CMHC crosswalk equivalence.

**Pending M00-T01 validation:** Examine geography identifiers in a specific, downloaded CMHC Rental Market Survey workbook; establish whether the reported universe and CMA boundary vintage are comparable. For any mismatched region, document a crosswalk or exclude the region. Until verified, candidates must not be presented as analytically comparable or approved for dashboards.

## Source discovery inventory

| Source | Official entry point | Potential measure | Ingestion format | Known versus pending |
| --- | --- | --- | --- | --- |
| Statistics Canada (Census) | [Table 98-10-0058-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810005801) | 2020 median annual income of all private households | Wide-format Census ZIP CSV | Vancouver CMA row, DGUID, symbols and source SHA-256 verified in workstation full-file extraction; historical 2020 income only |
| Statistics Canada (CIS) | [Table 11-10-0190-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001) | 2023/2024 median after-tax income of economic-family units and unattached persons | Long-format table ZIP CSV | Vancouver CMA DGUID and both observations verified in workstation full-file extraction; **not** private-household median income |
| CMHC | [Rental Market Survey data tables](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables) | Average private apartment rent, vacancy candidates | Workbook/Excel | Vancouver CMA 2024/2025 *all-unit average* rent in Table 1.1.2 (not turnover or asking rent), including source reliability codes and 2021 geography-vintage note, verified in workstation extraction; cross-publisher geographic identity and reuse review remain pending |
| Bank of Canada | [Valet API documentation](https://www.bankofcanada.ca/valet-api-how-to/) | Interest rates, macro context | API/JSON | `V39079` target for overnight rate verified from official lookup (2026-10-22 sample); Valet JSON payload/schema uninspected; national context only |

Five **manually transcribed official-page observations** are checked in strictly as a discovery/test fixture, **not** production data. Audited raw source archives have been downloaded **only to gitignored workstation storage**; reproducible read-only source extractors are available. The 2020 Census private-household income, 2023–2024 CIS economic-family income and 2024–2025 CMHC rental observations **cannot be combined into an approved affordability percentage**. The three independent series require correct population labels and separate-period displays.

## Required catalog row (M00-T02)

Each selected dataset must document the following before an ingestion adapter is implemented:

- Source name, publisher, canonical URL, dataset/table/series ID, official license and attribution, redistribution/cache permission.
- Reference period vs. publication date vs. retrieval timestamp, cadence, availability range and revision behavior.
- Geography ID, boundary vintage, coverage universe, sample/suppression flags, and geographic crosswalk evidence.
- Metric definition, unit, periodicity, income/rent population (e.g., households vs. individuals; purpose-built rent vs. asking rent), and method of aggregate calculation.
- Reproducible downloaded fixture and schema, integrity checksum, interpretation risks, join constraints, and selected fallback behavior.

## Feasibility acceptance gate

`M00` is **not done** until at least one rental measure and one income measure are demonstrably comparable for a useful sample, with real source identifiers, sample extracts, evidence, and documented limitations. If no compatible intersection exists, revise the scope before any affordability statistic is released. Avoid claiming feasibility based solely on code or on published source landing pages.

## Reproducible download discovery — M00-T02 follow-up (2026-10-26)

An opt-in, bounded publisher-format probe exists at [`scripts/probe_official_sources.py`](../scripts/probe_official_sources.py), with independent synthetic-schema tests in `tests/test_official_probes.py`. It records SHA-256, raw byte length, date of inspection, and partial format evidence into **gitignored raw-data manifests** on successful retrieval. Direct 2025 CMHC Vancouver and Toronto XLSX links are now cataloged in [`SOURCE_VALIDATION_M00_T02.md`](SOURCE_VALIDATION_M00_T02.md), alongside Bank of Canada V39079 and Statistics Canada full-table ZIP CSV sources now verified on the user workstation.

**Do not interpret a successful format probe as published-source semantic acceptance.** Neither genuine Excel tables nor real StatCan or Valet payloads were downloadable in the current execution environment. Geography crosswalk, raw column definitions, licence notices and aligned rental-income population/period comparisons remain unverified. Milestone M00 stays `in_progress` and **no affordability ratio is authorized**.

## Vancouver CMA rent review — M00-T02 (2026-10-26)

The user supplied, then locally verified, the Vancouver CMA aggregate and reliability legend from the **2025 CMHC Rental Market Survey, Table 1.1.2**. It reports 2-bedroom average rents of CAD 2,314 in October 2024 and CAD 2,363 in October 2025, both with `a` (Excellent) quality, and states that both use 2021 Census geographic definitions. These are **user-run locally audited, source-specific observations**, not independently audited published data products. The new local extractor `scripts/extract_cmhc_cma_rents.py` verifies a locally audited source workbook before selecting the exact CMA row and all bedroom categories. See [`CMHC_VANCOUVER_CMA_REVIEW_M00_T02.md`](CMHC_VANCOUVER_CMA_REVIEW_M00_T02.md). Temporal income alignment, cross-publisher CMA identity, reuse approval and general affordability-comparability gates remain pending.

## M00-T02 — Optional 2024 CMA income candidate (not an approved source)

[Statistics Canada Table 11-10-0190-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001), Canadian Income Survey annual data through 2024, is available for a bounded, opt-in machine-readable ZIP inspection through `statcan-cis-income` (non-Census **long CSV** layout). This source's **economic-family** population must not be substituted for 2021 Census **all private households** or silently joined to October 2025 CMHC rents. The user ran a full-file CIS extractor, checked the 2023/2024 values, source quality and SHA-256, and attached the output. The source ZIP remains absent from the implementation environment; no CMHC crosswalk or publication licence check is accepted. See [`CIS_2024_INCOME_CANDIDATE_M00_T02.md`](CIS_2024_INCOME_CANDIDATE_M00_T02.md) for execution, provenance, flags and outstanding review gates.

## M00-T03 — Non-public, unjoined display candidate (2026-10-26)

[`scripts/preview_vancouver_indicators.py`](../scripts/preview_vancouver_indicators.py) requires all three verified local source extractors, checks the existing Vancouver Census/CMHC evidence and the exact CIS candidate, and prints an explicit **non-public** two-series preview contract. It displays CMHC mean rents and CIS median incomes in separate groups, with source-specific statistical units, dates, currency basis, quality codes, source URLs and SHA-256. It returns `rent_to_income_ratio: null` and blocks derived affordability claims, year-on-year rate claims, and joining on the shared DGUID. See [`adr/ADR-0002-unjoined-indicators.md`](adr/ADR-0002-unjoined-indicators.md) (proposed, not accepted) and [`M00_INDICATOR_PREVIEW_CONTRACT.md`](M00_INDICATOR_PREVIEW_CONTRACT.md). No production-ready dataset or public release is created.
