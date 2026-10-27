# M00-T06 — Controlled naming migration (repository rename completed)

**Status:** UrbanGauge accepted as the **public repository project label** on 2026-10-26. The GitHub repository was renamed from `DevIsola/MetroLens` to `DevIsola/UrbanGauge` and its local remote validated on 2026-10-27. No domain, trademark, historical source identifier, deployment configuration, or publication approval was changed.

## Inventory and dependencies

Use `python scripts/review_m00_naming.py` to obtain a bounded, read-only inventory of **tracked** references to `MetroLens`, `Northstar`, and the Canada Affordability Observatory descriptor. The inventory includes historic planning docs and source evidence; **not all references should be mechanically replaced**.

| Surface | Action *after* identity approval | Preservation requirement |
| --- | --- | --- |
| Product-facing copy and README | New public name and bilingual EN/PT-BR descriptor in UI titles, intro, metadata, alt text, footer | Do not alter official source names or citations |
| Package/project metadata | New app ID, package names and any icon/favicons only after M01 metadata planning | Freeze dependency versions and lockfiles during rename |
| GitHub repository and Pages base path | Separate explicit owner authorization; update static `NEXT_PUBLIC_BASE_PATH` and test all routes | Preserve clone URLs/redirects where possible; verify GitHub redirect behavior, backlinks, Actions and Pages |
| Existing roadmap paths | Keep `docs/NORTHSTAR_MASTER_ROADMAP.md` canonical unless separately authorized | Preserve historical links; add navigation/aliases rather than breaking backlinks |
| ADRs, audits and past evidence | Annotate superseded codename where useful; never bulk rewrite immutable acceptance records or source fingerprints | Commit history, source checksums and dated evidence remain unchanged |
| Branding/SEO and maps | Review EN/PT-BR copy, responsive icon, Open Graph metadata, social handles and map attribution | No impression of public agency endorsement; maps still require source licence clearance |
| Local tool scripts and reports | Change human-facing labels only after executable compatibility tests | Keep source IDs, stable `region_id` and audited hash values unchanged |

## Remaining application/brand migration sequence — future milestones

1. **Repository rename completed**: `DevIsola/MetroLens` → `DevIsola/UrbanGauge` on 2026-10-27; verify local `origin` and preserve historical links. A future domain or hosted/commercial brand rollout still requires separate approval and relevant legal/registry review.
2. Produce a searchable before/after inventory; split user-facing strings from historical file names, source identifiers and links.
3. Prepare reversible changes on a fresh feature branch, with tests asserting existing `region_id`, source IDs, CSV/Excel cell provenance, audit hashes, and page base-path behavior.
4. Confirm both EN/PT-BR copy, responsive/logo sizes, contrast, accessible labels, social metadata, license attributions and permalink preservation.
5. Run local tests, static export and link check. Hold all deployment buttons until maintainer explicitly authorizes a separate release.
6. If the repo name or domain changes, verify remotes, README badge links, GitHub Pages project path, external links and rollback path **before** any public publication.

**Explicit stop:** project naming does not authorize remote repository rename, domain purchase, trademark-availability claims, hosted public-service rollout or publication of unapproved data. M00/M01 must not fabricate trademark clearance or production status. Do not enable push CI, scheduled ETL or deploy hooks while changing names.
