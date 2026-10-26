# ADR-0003 — Product naming and identity decision (M00-T06)

- **Status:** under review; **no brand selected or rename authorized**
- **Research date:** 2026-10-26
- **Decision owner:** project maintainer
- **Codename:** MetroLens; legacy planning nickname Northstar and canonical document path `docs/NORTHSTAR_MASTER_ROADMAP.md` are retained for continuity.
- **Companion review contract:** [`../branding/m00_t06_name_review.json`](../branding/m00_t06_name_review.json)
- **Migration plan:** [`../branding/M00_T06_MIGRATION_PLAN.md`](../branding/M00_T06_MIGRATION_PLAN.md)

## Why this review exists

The project is a bilingual Canadian data observatory with public statistics, interactive CMA maps, accessible charts, independent rental/income indicators and explicit methodology. The product descriptor *Canada Affordability & Opportunity Observatory* is **not** a cleared commercial brand. The master roadmap calls for naming before M01 metadata, UI titles, domains and release paths are fixed.

**Approval at M00-T05 does not approve a brand.** ADR-0001 remains accepted as an *architecture plan*; source reuse/publication, automatic deployment and statistical joins all remain disabled.

## Candidate analysis — editorial fit, not legal or domain clearance

| Candidate | Product story | Main concern | Observed independent uses / verification |
| --- | --- | --- | --- |
| **CityMargin** | Financial margin when comparing places, potential scenario tools | Sounds like profit or a *validated* rent-to-income metric, which we do not yet have | No reliable clearance conclusion; trademark/domains/apps unverified |
| **UrbanGauge** | Public data instrumentation and clear visual comparisons | May underrepresent provinces and nonurban coverage | No reliable clearance conclusion; trademark/domains/apps unverified |
| **Living Ledger** | Civic accountability and source traceability | Similar name used by existing home-inventory and retirement-planning software | Existing examples: https://livingledger.net/ and https://www.livingledger.com/ ; no legal conclusion |
| **MetroLens** | Metropolitan exploration and interactive spatial data | Existing independent `Metro Lens` services; transportation/real estate use is a relevant proximity signal | https://metrolens.fyi/developers/ ; https://metrolens--prototype.vercel.app/about ; https://www.metro-lens.com/ ; no legal conclusion |
| **Civic Ledger** | Public-good data, transparency | Could imply official government affiliation | No reliable clearance conclusion; trademark/domains/apps unverified |

These observed products **are not evidence of trademark infringement or domain unavailability for all variants**. The quick web preflight is not comprehensive. Conversely, no easily surfaced web result is **not proof of availability**. Do not purchase a domain or switch branding on this basis alone.

### Provisional editorial recommendation

Review **UrbanGauge** and **CityMargin** first for brand fit; retain **MetroLens** as the working codename until selection. CityMargin was the v0.2.0 roadmap's preliminary recommendation; however its association with a calculated financial margin could overpromise the MVP's *separate rent and income indicators*. UrbanGauge may therefore better represent the initially approved scope, but its name and domains require independent checks. These are subjective positioning arguments, not rankings of actual legal availability.

Use descriptive, non-governmental metadata such as **“Independent Canadian housing, income and opportunity data”**; never impersonate Statistics Canada, CMHC, a public agency or a trademark owner. Evaluate pronunciation and reading in EN and PT-BR with the chosen name.

## Required checks before an identity decision

1. Search the **Canadian Intellectual Property Office (CIPO)** database for exact, variant, plural and phonetically similar names, considering the relevant goods/services classes; record dated results. Official search guidance: https://www.ised-isde.canada.ca/site/canadian-intellectual-property-office/en/trademarks/basic-search and https://ised-isde.canada.ca/cipo/trademark-search/ . This project has **not** completed that formal search.
2. Check relevant foreign marks via official WIPO search at https://branddb.wipo.int/ if serving other jurisdictions. Seek professional advice if branding/legal risk is material.
3. Check `.ca`, `.com` and key social identifiers **using registrar/RDAP and actual search screens** (record provider, date, cost/renewals); a DNS response, a parked page, or a generic web search is not enough to prove availability.
4. Review existing GitHub projects, browser/web search, Google Play and Apple App Store; record links and assess audience/industry proximity, rather than equating all identical terms with conflict.
5. Maintainer explicitly selects a candidate or submits a new name, then independently approves the reference-migration plan in `M00_T06_MIGRATION_PLAN.md`. Until that point, do not rename the GitHub repository, domain, README, image assets or historical paths.

## Decision pending

- **Selected public name:** _not selected_.
- **Domain/trademark status:** _not verified_.
- **Brand logo, navigation label, app metadata:** _not authorized for renaming_.
- **Output of M00-T06:** reviewed name + evidence + maintainer approval + migration plan. The user can also **defer** naming; in that case, M00-T06 remains open, and M01 can only be considered under explicit risk acceptance and temporary codename metadata.

This ADR does not change the already approved separate-indicator methodology or visual identity direction, and it does not authorize a production release.
