# Metrics dictionary — discovery draft v0.1

**Milestone:** M00-T03. **Status:** draft, pending real series compatibility checks. No values have been computed or published.

## Required semantics

| Metric ID | Meaning / formula | Unit | Preconditions | Null handling |
| --- | --- | --- | --- | --- |
| `rent_to_income_pct` | `monthly_rent * 12 / annual_household_income * 100` | Percent (%) of annual **household** income | Same geography/boundary basis and aligned reference periods; rent class and income definition explicitly recorded; income greater than 0 | `null` with explicit reason if input missing, suppressed, mismatched, or denominator nonpositive |
| `rent_yoy_pct` | `(rent_t / rent_t_minus_1 - 1) * 100` | Percent (%) | Same rent survey universe/bedroom or unit type, geographies and comparable periods; prior rent greater than 0 | `null` with reason on break/non-comparability |
| `income_yoy_pct` | `(income_t / income_t_minus_1 - 1) * 100` | Percent (%) | Same income concept and comparable geography/reference periods; prior income greater than 0 | `null` with reason on break/non-comparability |
| `rent_income_gap_pp` | `rent_yoy_pct - income_yoy_pct` | Percentage points (pp) | Both YoY components valid and defined for comparable window/geography | `null` if either component is unavailable |
| `vacancy_rate_pct` | Source-supplied CMHC vacancy rate | Percent (%) | Source method, survey universe, and applicable period retained; never infer a value from counts without approved formula | Source quality semantics and suppression retained |
| `reference_freshness` | `reference_period`, `published_at`, `retrieved_at`, `generated_at` displayed **separately** | Date/period | All timestamps timezone explicit; no use of ingestion date as observation date | Missing field flagged without substituting today's date |

## Why these measures are not interchangeable

- The rent series must distinguish asking rent for newly advertised units from survey measures of occupied/purpose-built units. Average and median measures cannot be silently merged.
- Household, individual, before-tax, after-tax and median/mean income concepts are different. The initial ratio formula assumes annual **household** income; other bases require a separately named metric and clear explanatory UI.
- Annual observations must not be joined to monthly time series using nearest dates without an explicit, reviewed period alignment method.
- Each value must preserve source and lineage (`source_id`, `source_url`, `reference_period`, `retrieved_at`, `schema_version`, and related provenance attributes), along with release SHA when published.
- A source-reported `missing`, `suppressed`, `not_applicable`, or `not_published` flag must not be collapsed into zero.
- If a metric is not comparable across two CMAs, show **insufficient comparable data** rather than a computed value.

## Data contract to finalize before implementation

| Field | Provisional type | Validation constraint |
| --- | --- | --- |
| `region_id` | string | Maps to official geography with version, may not rely only on display name |
| `source_geo_code` | string | Preserve leading zeros; source-specific, not assumed equal across publishers |
| `metric_id` | string | Registry-defined; do not infer from source column heading |
| `reference_period` | date or explicit period string | Periodicity specified, not a processing timestamp |
| `periodicity` | enum | `monthly`, `quarterly`, `annual`, or documented source-specific frequency |
| `value` | number or null | Reject NaN/Infinity; do not impute suppressed values |
| `unit` | string | Explicit CAD/month, CAD/year, %, pp, etc. |
| `measure_type` | string | `mean` versus `median`, rent class or household basis as needed |
| `quality_flag` | enum/string | Source-specific quality flags retained and documented |
| `source_id` | string | Points to a real catalog entry with official URL |

Before marking this task complete, select real tables, use example observations to prove the formulas, and test at least one negative case (invalid/mismatched inputs). See the master roadmap §1.3 and §2.1 for definition and quality requirements.

## M00-T03 executable discovery gate (2026-10-26)

The first policy check is implemented in [`scripts/assess_metric_compatibility.py`](../scripts/assess_metric_compatibility.py), with the review contract documented in [`COMPARABILITY_REVIEW_M00_T03.md`](COMPARABILITY_REVIEW_M00_T03.md). It checks the proposed **annualized mean turnover two-bedroom rent versus median total household income** pairing against strict source roles, units, periods, geography identifiers, quality flags, and required methodology evidence. These are distinct aggregated statistics, **not** observed household-level rent burdens.

`blocked`, `needs_evidence` and `ready_for_methodology_review` are **triage states, not production approvals**. All outputs explicitly retain `approved_for_publication: false` and `computed_value: null`. The manually transcribed 2020 income / 2025 rent examples remain blocked. A numeric formula must not be applied to these observations. See the separate review contract for data and licensing acceptance work.

## M00 real-source Vancouver technical reconciliation (2026-10-26)

The locally verified CMHC Vancouver 2024/2025 average rent and StatsCan 2021 Census/2020 all-household median income selections are now recorded in [`SOURCE_RECONCILIATION_M00.md`](SOURCE_RECONCILIATION_M00.md). The reproducible check is `python scripts/reconcile_vancouver_evidence.py` and requires the same audited files already present on the workstation. It compares source hashes, exact source rows, dimensions, periods and quality flags to manually reviewed evidence.

**Decision:** technical source evidence may reconcile, but `rent_to_income_pct` stays **unavailable** because reference years, statistical populations and publisher geographic identifiers have not been reconciled. Never translate `source_evidence_reconciled` into `approved_for_publication`. A later 2024 income candidate such as CIS Table `11-10-0190-01` differs in population and is not an automatic replacement for Census private-household median income.

## M00-T03 — Proposed separately labelled indicator contract (2026-10-26)

The read-only tool [`scripts/preview_vancouver_indicators.py`](../scripts/preview_vancouver_indicators.py) prepares **two separate candidate series for local design review**; it does **not** implement or authorize a metric join:

| Indicator ID | Source | Units / statistical unit | Display period | Quality metadata |
| --- | --- | --- | --- | --- |
| `cmhc_average_private_apartment_rent` | CMHC RMS Table 1.1.2, Vancouver CMA row 36 | Weighted **mean** CAD/month for privately initiated, purpose-built rental apartment units (vacant and occupied sample) | October 2024 and October 2025, separated by bedroom type | Original CMHC `a` = Excellent, separate cell reference |
| `cis_median_after_tax_income_economic_family_unit` | Statistics Canada CIS Table 11-10-0190-01, series `v96416811` | **Median** CAD/year in **2024 constant dollars**, economic families and persons not in economic families | Annual 2023 and 2024 | Original StatsCan status `A` = Acceptable or better, vector/coordinate |

**Display rules:** show the entire source name, collection date/reference year, population, currency basis, and quality indicator. The source values are **not** incomes of the units in CMHC's surveyed rentals. Do not place both series on one shared axis, convert an income figure to hypothetical monthly spending power, show a rent burden/affordability score, or compute a combined rent-income YoY gap. Same Vancouver DGUID on the two StatsCan inputs and the CMHC 2021 boundary-vintage footnote do **not** establish an approved cross-publisher geography crosswalk. Keep all computed cross-source fields `null` with named blockers.

CMHC's [Rental Market Survey methodology](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-research/surveys/methods/methodology-rental-market-survey) describes its average rent as a weighted average across vacant and occupied units; it is not the published composition-controlled percentage change in average rent. Statistics Canada's [CIS table notes](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001) describe economic families and unattached persons. The proposed UX baseline is recorded in [`M00_INDICATOR_PREVIEW_CONTRACT.md`](M00_INDICATOR_PREVIEW_CONTRACT.md) and proposed ADR-0002; release and licensing acceptance remain outstanding.
