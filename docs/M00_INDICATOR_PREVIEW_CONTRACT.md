# M00-T03 — Vancouver local indicator-preview contract

**Status:** Technical demonstration only, *not a public dataset or approved KPI*. **Date:** 2026-10-26. ADR: [proposed 0002](adr/ADR-0002-unjoined-indicators.md).

## Objective

Enable M00-T04 design/wireframe exploration using **two unjoined, source-specific indicators** that preserve actual publisher periods, units, populations, source quality symbols, and source fingerprints. The preview is intentionally **not** a household affordability index and does not claim to quantify typical renter burden.

1. **Rent:** CMHC 2025 RMS Vancouver workbook, Table 1.1.2, *Private Apartment Average Rents* (not turnover rent and not rent of vacant units/asking rent), Vancouver CMA row 36. Five bedroom categories, October 2024/2025; monthly CAD mean weighted across surveyed occupied and vacant apartments; CMHC quality indicator `a` (Excellent); value and reliability cell addresses retained. Note that these are rent *levels*, not CMHC's composition-controlled published percent-change estimates.
2. **Income:** Statistics Canada CIS Table 11-10-0190-01, annual median after-tax income, **economic families and persons not in an economic family**, years 2023/2024 in **2024 constant CAD**. Source `DGUID=2021S0503933`, vector `v96416811`, coordinate `21.12.1`, status `A` (StatsCan *acceptable or better*). This differs from 2020 **private-household** Census income (another source available separately).

**Semantic caution:** CMHC average rent estimates include vacant as well as occupied apartments; they are not purely existing-tenant rents. The CIS income estimates are not incomes for these apartments' renters. No income or rent share of disposable income can be inferred.

## Local run — no network or persisted output

```powershell
python scripts/preview_vancouver_indicators.py
```

The command reads the existing three source files from `pipeline/data/raw/m00-source-probes/`. It re-executes full-file audited extractors and the existing Census/CMHC reconciliation, then validates the exact independently reviewed CIS candidate. It writes the **JSON to stdout only**. Raw files remain ignored. To save the output from PowerShell to Downloads, use `> "C:\Users\hello\Downloads\MetroLens_M00_Indicator_Preview.json"`; PowerShell may encode redirected output as UTF-16, which is readable with an appropriate editor/JSON reader. For a guaranteed UTF-8 file use: `python scripts/preview_vancouver_indicators.py | Out-File -Encoding utf8 "C:\Users\hello\Downloads\MetroLens_M00_Indicator_Preview.json"`.

Expected:

- `status=indicator_preview_for_review`; `mode=local_nonpublic_discovery_preview`.
- `series` has **2** entries; one with **10** rent points (five bedroom classes × two October periods), one with **2** CIS income points (2023/2024).
- Full publisher links, SHA-256, source cell/vector, and quality flags appear in each series.
- `blocked_metrics[0].metric_id=rent_to_income_pct`, `value=null`, explanatory blocker codes.
- All comparability/publication/production flags remain **false**, and `rent_to_income_ratio=null`.

A `blocked` report is **not** a request to bypass source validation. Send the entire JSON error instead. No download is required if all three local audits remain `file_verified`.

## UX acceptance criteria (M00-T04 input, not a finished design)

- Separate cards/charts rather than a shared time axis for the two populations, with meaningful mobile display and accessible source/quality explanations.
- Rent card: bedroom selector and October survey month, *private purpose-built apartment weighted mean (including vacant units)* label; do not call it newly advertised price.
- Income card: annual median, after-tax, economic families/unattached persons, **2024 constant dollars**; do not label it median income *per renter household*.
- Show geographic region with "2021 Census CMA definitions" and visible status that the CMHC crosswalk has not been formally approved.
- Do not show a fake affordability index, `rent_to_income_pct`, aggregate rent-income gap, synchronized change rates, or an automatic numeric percentage trend not supported by the source's methodology.
- Visible official-source links and source-quality markers; explain data age vs. release date instead of treating current extraction date as observation date.
- This JSON remains non-public and not under version control as a generated dataset. Presentation design is pending maintainer review, external attribution/reuse acceptance and eventual M04/M05 export validation.

## Remaining M00 gates

1. Confirm CMHC's Vancouver CMA geographic ID and boundary equivalence to StatsCan's 2021 Census DGUID with documented primary-source evidence, or explicitly limit geographic comparability claims.
2. Review statistical population pairing and period alignment independently if a **new** ratio is proposed; otherwise formalize separate-indicator-only MVP scope through ADR acceptance.
3. Review source-specific publishing requirements: Statistics Canada table DOI/citation and open licence; CMHC copyright/attribution and reuse constraints; applicable source quality/sample-size methodology notes.
4. Approve wireframes, accessibility/disclosure copy, and a cautious editorial narrative before M00 acceptance.

References: [CMHC RMS methodology](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-research/surveys/methods/methodology-rental-market-survey); [StatsCan Table 11-10-0190-01 and notes](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001); [CIS 2024 release](https://www150.statcan.gc.ca/n1/daily-quotidien/260429/dq260429a-eng.htm).
