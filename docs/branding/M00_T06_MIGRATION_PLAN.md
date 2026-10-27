# M00-T06 — Controlled naming migration plan (not executed)

**Status:** UrbanGauge accepted as the **public repository project label** on 2026-10-26, with known use/collision signals acknowledged. The README project title changes in this increment; the GitHub repository slug, domain, historical paths, deployment configuration and publisher evidence do **not** change. Trademark/domain clearance has not been established.

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

## Controlled remote/application migration sequence — later increment only

1. The maintainer has selected UrbanGauge for repository naming and acknowledged known collision signals. **Before any remote rename or commercial/hosted product rollout**, record the exact requested migration scope and additional domain/trademark checks appropriate to that scope.
2. Produce a searchable before/after inventory; split user-facing strings from historical file names, source identifiers and links.
3. Prepare reversible changes on a fresh feature branch, with tests asserting existing `region_id`, source IDs, CSV/Excel cell provenance, audit hashes, and page base-path behavior.
4. Confirm both EN/PT-BR copy, responsive/logo sizes, contrast, accessible labels, social metadata, license attributions and permalink preservation.
5. Run local tests, static export and link check. Hold all deployment buttons until maintainer explicitly authorizes a separate release.
6. If the repo name or domain changes, verify remotes, README badge links, GitHub Pages project path, external links and rollback path **before** any public publication.

**Explicit stop:** project naming does not authorize remote repository rename, domain purchase, trademark-availability claims, hosted public-service rollout or publication of unapproved data. M00/M01 must not fabricate trademark clearance or production status. Do not enable push CI, scheduled ETL or deploy hooks while changing names.
