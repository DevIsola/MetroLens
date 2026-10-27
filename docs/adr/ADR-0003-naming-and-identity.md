# ADR-0003 — Product naming and identity decision (M00-T06)

- **Current status (2026-10-27):** UrbanGauge accepted as project name; GitHub repository renamed and independently verified. **No domain/trademark/publication clearance is implied.** Earlier exploratory findings below are retained as dated history.
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
| **UrbanGauge** | Public data instrumentation and clear visual comparisons | May underrepresent nonurban coverage; exact-name urban-indicator research and related software-publisher uses | Historical UrbanGauge research system (2007–2009); UrbanGauge Studio game-publisher attribution (2020); .com premium-marketplace listing. Not legally cleared |
| **Living Ledger** | Civic accountability and source traceability | Similar name used by existing home-inventory and retirement-planning software | Existing examples: https://livingledger.net/ and https://www.livingledger.com/ ; no legal conclusion |
| **MetroLens** | Metropolitan exploration and interactive spatial data | Existing independent `Metro Lens` services; transportation/real estate use is a relevant proximity signal | https://metrolens.fyi/developers/ ; https://metrolens--prototype.vercel.app/about ; https://www.metro-lens.com/ ; no legal conclusion |
| **Civic Ledger** | Public-good data, transparency | Could imply official government affiliation | No reliable clearance conclusion; trademark/domains/apps unverified |

These observed products **are not evidence of trademark infringement or domain unavailability for all variants**. The quick web preflight is not comprehensive. Conversely, no easily surfaced web result is **not proof of availability**. Do not purchase a domain or switch branding on this basis alone.

### Provisional editorial recommendation

Review **UrbanGauge** and **CityMargin** first for brand fit; retain **MetroLens** as the working codename until selection. CityMargin was the v0.2.0 roadmap's preliminary recommendation; however its association with a calculated financial margin could overpromise the MVP's *separate rent and income indicators*. UrbanGauge may therefore better represent the initially approved scope, but its name and domains require independent checks. These are subjective positioning arguments, not rankings of actual legal availability.

Use descriptive, non-governmental metadata such as **“Independent Canadian housing, income and opportunity data”**; never impersonate Statistics Canada, CMHC, a public agency or a trademark owner. Evaluate pronunciation and reading in EN and PT-BR with the chosen name.

## Maintainer preference recorded — 2026-10-26

The maintainer has chosen **UrbanGauge** as the **preferred candidate**, not an authorization to use it as a public brand. The selected public name remains null in the review contract until clearance evidence and a final maintainer decision are recorded.

Additional public-web preflight evidence specifically for UrbanGauge:

- A 2007–2009 project titled **“UrbanGauge: A real-time indicator system for urban design decision making”** appears in a researcher's profile at https://uosarch.ac.kr/uosarch_people/%ED%99%A9%EC%9D%80/ . The prior use is **closely related in subject matter** to our proposed geographic indicators and visualizations. This is not proof of continuing use or of trademark rights.
- Australia's public classification record for *Word Play: City Edition* (2020) identifies **UrbanGauge Studio** as developer/publisher: https://www.classification.gov.au/titles/word-play-city-edition . The publisher identity may be unrelated to our proposed field of use but requires consideration.
- A marketplace page advertises **UrbanGauge.com** for **US$2,695**, observed October 26, 2026: https://www.brandzilla.io/name/UrbanGauge.com . This is a third-party asking price subject to change, **not registry availability** or an offer the project has accepted. No budget is approved for this purchase.

**Risk:** discoverability and potential confusion, especially given the historical urban-indicators project. Neither no visible CIPO matches in web search nor the domain marketplace listing constitutes trademark clearance. We have **not** completed an official CIPO results review, an official .ca registry lookup, social/app-store inventories or legal risk assessment. If the exact-name historical use is concerning, consider a more distinctive name before committing design assets.

## Additional checks before any commercial/hosted brand or domain commitment (superseded for repository-only naming)

1. Search the **Canadian Intellectual Property Office (CIPO)** database for exact, variant, plural and phonetically similar names, considering the relevant goods/services classes; record dated results. Official search guidance: https://www.ised-isde.canada.ca/site/canadian-intellectual-property-office/en/trademarks/basic-search and https://ised-isde.canada.ca/cipo/trademark-search/ . This project has **not** completed that formal search.
2. Check relevant foreign marks via official WIPO search at https://branddb.wipo.int/ if serving other jurisdictions. Seek professional advice if branding/legal risk is material.
3. Check `.ca`, `.com` and key social identifiers **using registrar/RDAP and actual search screens** (record provider, date, cost/renewals); a DNS response, a parked page, or a generic web search is not enough to prove availability.
4. Review existing GitHub projects, browser/web search, Google Play and Apple App Store; record links and assess audience/industry proximity, rather than equating all identical terms with conflict.
5. Maintainer explicitly selects a candidate or submits a new name, then independently approves the reference-migration plan in `M00_T06_MIGRATION_PLAN.md`. Until that point, do not rename the GitHub repository, domain, README, image assets or historical paths.

## Prior decision state — superseded by repository-scope approval below

- **Preferred candidate:** UrbanGauge (maintainer, 2026-10-26).
- **Selected public name:** _not selected; pending clearance and final maintainer approval_.
- **Domain/trademark status:** _not verified_.
- **Brand logo, navigation label, app metadata:** _not authorized for renaming_.
- **Output of M00-T06:** reviewed name + evidence + maintainer approval + migration plan. The user can also **defer** naming; in that case, M00-T06 remains open, and M01 can only be considered under explicit risk acceptance and temporary codename metadata.

This ADR does not change the already approved separate-indicator methodology or visual identity direction, and it does not authorize a production release.

## Verified repository migration — 2026-10-27

Following the maintainer's explicit request, GitHub now resolves the public repository as [`DevIsola/UrbanGauge`](https://github.com/DevIsola/UrbanGauge). The maintainer updated the local `origin`, fetched successfully, confirmed `feat/M00-product-discovery` tracking and reported `Everything up-to-date`. This verifies only the GitHub slug migration, not GitHub Pages, public domain ownership, licensed dataset reuse, legal clearance, or public brand availability. Source IDs, canonical roadmap filename and historical evidence remain unchanged.

## Maintainer decision — public research repository scope (2026-10-26)

**Decision: Accepted for project naming.** The maintainer explicitly clarified that the project is a public **research repository**, not a currently operated service or app, and confirmed **UrbanGauge** as its name after receiving the observed public-use research. For that defined scope, the maintainer accepts the practical discoverability/confusion risk and elects not to treat domain acquisition, official trademark clearance, or app-store searches as prerequisites for progressing with M00/M01 development.

This decision is **not a finding of trademark clearance**, does not create exclusive rights, and is not a legal conclusion that a public repository can never conflict with someone else's trademark. Reevaluate before converting the repository into a commercial service, offering a hosted branded product, purchasing a domain, or asserting exclusivity. The earlier collision evidence remains preserved above.

**Scope and execution:**

- Selected project name: **UrbanGauge**; approved for the README and future documentation as a public repository project label.
- The existing GitHub repository **`DevIsola/MetroLens` remains unchanged**. Renaming the remote, altering GitHub Pages paths, adding DNS, modifying existing URL references or publishing a hosted service requires a separately requested migration.
- Historical `MetroLens` and `Northstar` references stay where needed for canonical links, citations and audit provenance. Do not bulk replace earlier source-acceptance records.
- Branding for an app/service, trademark/domain clearance, source reuse approvals, data joins, scheduled ETL and production deployment remain **unapproved**.
- M00-T06 naming-choice gate is met **for repository scope only**. M00 milestone acceptance still requires an independent check of the separate-indicator scope, source evidence, and PR/merge documentation before marking M00 `done`.

The machine-readable contract `m00_t06_name_review.json` records the distinction between selected project label and unverified legal/domain status.
