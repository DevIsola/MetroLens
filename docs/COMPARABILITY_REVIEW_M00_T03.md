# M00-T03 — Rent/income comparability review gate

**Status:** Proposed, not an approved metric or production dataset. Date: 2026-10-26.

This increment implements a deliberately **non-authorizing** source-pair triage function in `scripts/assess_metric_compatibility.py`. It uses the discovery-only, manually transcribed official-page observations already documented in `docs/SOURCE_VALIDATION_M00_T02.md`; it does **not** read the raw publisher probe files, replace the M00-T02 evidence audit, transform source data, or publish an affordability number.

## Run locally

```powershell
python scripts/assess_metric_compatibility.py
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
```

The CLI prints a JSON assessment for Vancouver and Toronto. The existing sample records use **2020 median household income** (2021 Census) and **October 2025 average turnover two-bedroom rent** (CMHC). Both assessments must report `status: "blocked"` and include `reference_year_mismatch`. The source-page samples have not established CMHC CMA codes, source quality flags, reuse terms, or statistical-population comparability.

## Proposed comparison, not a generic affordability index

The triage ID `annualized_mean_turnover_2br_rent_vs_median_total_household_income` is intentionally specific. Annualizing the *mean turnover rent* and dividing by *median household income*, even if periods and CMAs eventually align, would compare **two aggregates from different statistical populations**. It would **not** be the mean or median household rent burden, nor a causal finding. No value is computed by this increment. Do not show any such ratio in the UI without a separate methodology review and accepted metric contract.

## Deterministic decision states

| Status | Meaning | Publication allowed? |
| --- | --- | --- |
| `blocked` | At least one input is fundamentally inconsistent, e.g. reference years, region, measure, segment, units, source role, or numeric value. | **No** |
| `needs_evidence` | Mechanical input definitions pass, but quality flags, publisher URLs or reviewed source metadata are missing. | **No** |
| `ready_for_methodology_review` | Mechanical conditions and *declared* review metadata are present. This is a **request for independent review**, not proof that the metadata are correct. | **No** |

All results contain `methodology_review_required: true`, `approved_for_publication: false`, and `computed_value: null`. These fields remain fixed regardless of any supplied approval status. Tests that reach `ready_for_methodology_review` use fabricated same-year records and placeholder example URLs; they are **synthetic negative/structural scenarios only**, not source evidence or approval.

The review function rejects or flags:

- mismatched region IDs and rent/income reference years; malformed annual/monthly periods;
- incorrect measure IDs, upstream publisher roles, mean/median definitions, period frequencies, statistical populations, units, non-finite or nonpositive values;
- missing source-quality evidence or `suppressed`/`missing` values (quality must be explicitly `observed`);
- absent or inconsistent CMHC/StatsCan CMA crosswalk evidence, including unknown CMHC source codes;
- missing reviewed source-date alignment and explanation of the differing rent/income populations;
- missing independently reviewed Statistics Canada and CMHC reuse/attribution documentation.

Crosswalk metadata must match the *source-specific* geographic identifiers on both records and include a boundary vintage and supporting HTTPS reference. Simply matching the city display name or marking one Boolean as `true` is insufficient. `status: reviewed` in a metadata object is a declared input, not externally authenticated approval.

## Outstanding acceptance work

1. Capture the **real** `audit_source_probes.py` report and examine actual StatsCan CSV rows and CMHC worksheet values, columns, suppression symbols and CMA identifiers. Neither the workbook header scan nor checksum alone proves these properties.
2. Locate a rental series and an **income series referring to a methodologically acceptable period**, with geography crosswalk evidence and a documented review of differences in survey universes.
3. Review source terms/attribution and choose whether the aggregate-to-aggregate comparison is meaningful; otherwise restrict the MVP to side-by-side indicators instead of an unsupported ratio.
4. Record selected source IDs, definitions, review rationale, negative cases, and decisions in `docs/DATA_CATALOG.md`, `docs/METRICS_DICTIONARY.md`, and an ADR if the definition changes.
5. After manual acceptance and merged PR evidence, create a separate numeric metric implementation and its exact reconciliation tests (M04/M07). Do **not** flip this discovery triage function into a production approval flag.

**Release policy:** no changes to `.github/workflows`, Pages, schedules, or ETL; the M00 milestone stays `in_progress`.
