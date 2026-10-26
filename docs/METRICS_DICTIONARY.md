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
