# M00 — data source and geography feasibility catalog

**State:** Discovery catalog, **not an approved production catalog**. Updated 2026-10-26. Scope: `M00-T01` and partial official HTML source sampling in `M00-T02`. See [`SOURCE_VALIDATION_M00_T02.md`](SOURCE_VALIDATION_M00_T02.md) and [`samples/official-page-observations.csv`](samples/official-page-observations.csv). No raw CSV/XLSX/API sample has been downloaded or accepted.

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
| Statistics Canada | [Web Data Service](https://www.statcan.gc.ca/en/developers/wds) | Income series (exact household definition **not selected**) | WDS API / table CSV | CMA household-income table `98-10-0058-01` identified; 2020 median total household income verified in Census Profile HTML (Toronto/Vancouver); CSV/schema pending; licence reviewed |
| CMHC | [Rental Market Survey data tables](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables) | Average rent, vacancy, universe counts | Workbook/Excel | 2025 report shows average 2-bedroom *turnover* rent for Vancouver/Toronto, October 2025; workbook/sheets/geo vintage pending; CMHC data licence reviewed |
| Bank of Canada | [Valet API documentation](https://www.bankofcanada.ca/valet-api-how-to/) | Interest rates, macro context | API/JSON | `V39079` target for overnight rate verified from official lookup (2026-10-22 sample); Valet JSON payload/schema uninspected; national context only |

Five **manually transcribed official-page observations** are checked in strictly as a discovery/test fixture, **not** source extracts or production data. No CSV/XLSX/Valet API payload has yet been ingested. The 2020 income and 2025 rent observations are **not directly comparable**; geography boundaries and statistical populations also remain unverified. Never present an affordability percentage from these samples.

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

An opt-in, bounded publisher-format probe exists at [`scripts/probe_official_sources.py`](../scripts/probe_official_sources.py), with independent synthetic-schema tests in `tests/test_official_probes.py`. It records SHA-256, raw byte length, date of inspection, and partial format evidence into **gitignored raw-data manifests** on successful retrieval. Direct 2025 CMHC Vancouver and Toronto XLSX links are now cataloged in [`SOURCE_VALIDATION_M00_T02.md`](SOURCE_VALIDATION_M00_T02.md), alongside Bank of Canada V39079 and a *not-yet-downloaded* Statistics Canada full-table CSV ZIP candidate.

**Do not interpret a successful format probe as published-source semantic acceptance.** Neither genuine Excel tables nor real StatCan or Valet payloads were downloadable in the current execution environment. Geography crosswalk, raw column definitions, licence notices and aligned rental-income population/period comparisons remain unverified. Milestone M00 stays `in_progress` and **no affordability ratio is authorized**.
