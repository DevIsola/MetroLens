# M00 — data source and geography feasibility catalog

**State:** Initial discovery, **not an approved production catalog**. Updated 2026-10-26. Scope: `M00-T01` with source-discovery groundwork for `M00-T02`.

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
| Statistics Canada | [Web Data Service](https://www.statcan.gc.ca/en/developers/wds) | Income series (exact household definition **not selected**) | WDS API / table CSV | API exists; candidate table ID, definition, vintage, frequency, license, and extracts pending |
| CMHC | [Rental Market Survey data tables](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables) | Average rent, vacancy, universe counts | Workbook/Excel | 2025 survey edition exists (published Dec 11, 2025); exact tables/sheets/field semantics and coverage pending |
| Bank of Canada | [Valet API documentation](https://www.bankofcanada.ca/valet-api-how-to/) | Interest rates, macro context | API/JSON | API documented; series selection, applicability and temporal alignment pending |

No data have yet been ingested into this repository. Do not assume that current publications share period, rent class, survey population, or geographic boundary definitions. **Do not invent source table IDs.**

## Required catalog row (M00-T02)

Each selected dataset must document the following before an ingestion adapter is implemented:

- Source name, publisher, canonical URL, dataset/table/series ID, official license and attribution, redistribution/cache permission.
- Reference period vs. publication date vs. retrieval timestamp, cadence, availability range and revision behavior.
- Geography ID, boundary vintage, coverage universe, sample/suppression flags, and geographic crosswalk evidence.
- Metric definition, unit, periodicity, income/rent population (e.g., households vs. individuals; purpose-built rent vs. asking rent), and method of aggregate calculation.
- Reproducible downloaded fixture and schema, integrity checksum, interpretation risks, join constraints, and selected fallback behavior.

## Feasibility acceptance gate

`M00` is **not done** until at least one rental measure and one income measure are demonstrably comparable for a useful sample, with real source identifiers, sample extracts, evidence, and documented limitations. If no compatible intersection exists, revise the scope before any affordability statistic is released. Avoid claiming feasibility based solely on code or on published source landing pages.
