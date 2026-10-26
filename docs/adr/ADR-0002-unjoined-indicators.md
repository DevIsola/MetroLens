# ADR-0002 — Propose separate income and rent indicators for the MVP

- **Status:** proposed; requires maintainer acceptance and documented source-use review
- **Date:** 2026-10-26
- **Related roadmap:** M00-T03, M00-T04, M00-T06; M04–M07

## Context

M00 source-specific technical verification passed on the user's workstation for:

- CMHC Vancouver CMA purpose-built apartment *mean* rent, October 2024/2025 (Table 1.1.2, worksheet row 36, quality `a`).
- Statistics Canada 2021 Census median **2020 private-household** income (Table 98-10-0058-01, DGUID `2021S0503933`).
- Statistics Canada Canadian Income Survey **2023/2024 economic-family and unattached-person** median after-tax income in **2024 constant dollars** (Table 11-10-0190-01, same StatsCan DGUID, quality `A`).

The periods, summary measures and statistical units are different. A matching CMA DGUID between Statistics Canada tables and a CMHC note that the workbook uses 2021 Census geographic definitions do not constitute an independently reviewed *cross-publisher* identifier/boundary crosswalk. CMHC's Rental Market Survey also samples rental *units*, whereas Census and CIS income statistics do not identify their tenants' incomes.

M00's acceptance criteria explicitly require changing scope when data cannot be reconciled rather than inventing an estimate.

## Proposed decision (not yet accepted)

1. For the discovery UX contract, **show separate source-specific rent and CIS income series**, each in its own card or chart, with distinct population and frequency labels, dates, units, quality badges/legends and source links. Do not create an affordability score, rent-to-income ratio, shared cross-source growth chart, or point comparison from these sources.
2. Keep the verified 2020 Census private-household income available as a *separately identified historical source* for methodology review, not as the denominator of 2024/2025 rents.
3. Treat the display as a **local non-public preview** while independent CMHC/StatsCan licence, source footnote, CMA crosswalk and publication review are pending. Future public publication requires an approved decision and export pipeline under M04–M05.
4. Revisit composite affordability indicators only when an income source and rental population/period have an explicitly reviewed pairing and metric contract. A temporal match alone is not enough.

## Alternatives

- **Annualize 2024 CMHC mean rent / divide by 2024 CIS median income:** rejected for preview because rental units and economic-family/unattached-person statistical units differ; a mean/median ratio of regional aggregates is not household rent burden.
- **Use 2020 Census all-households income as 2025 denominator:** rejected for period mismatch and census household versus sampled rental unit mismatch.
- **Show only rental values and omit income:** avoids ambiguity but hides relevant, carefully qualified evidence already verified on the user's workstation.
- **Wait for a harmonized dataset before designing any visual UX:** scientifically conservative but unnecessary for a *clearly separate* discovery preview.

## Consequences and approval gate

The local JSON contract explicitly returns `rent_to_income_ratio: null`, `publication_approved: false`, `metric_comparability_approved: false`, and `production_ready: false`. It prints no joined or inferred numeric field. This ADR **does not close M00** or update milestone status, nor does it authorize a GitHub Pages/Cloudflare deployment. Maintainer still needs to review the exact copy/design and publisher attribution, sampling limitations, and geographic definitions before approving implementation in M04/M05.

Evidence: `docs/SOURCE_RECONCILIATION_M00.md`, `docs/CIS_VANCOUVER_EXTRACT_REVIEW_M00.md`, and `docs/M00_INDICATOR_PREVIEW_CONTRACT.md`.
