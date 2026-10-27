# M00-T04 — Maintainer review decision

- **Decision date:** 2026-10-26
- **Evidence:** Maintainer's explicit acceptance in the MetroLens implementation conversation, following successful local regression tests and real-data wireframe rendering. This is a **human review record**, not a GitHub PR, release or publication approval.
- **Verification supplied:** 235 unit tests passing with one expected Windows symlink skip; roadmap synchronization passed; `render_m00_wireframes.py` returned `local_wireframes_created` with light/dark and desktop/mobile options, 10 rental observations, 2 income observations, null rent-to-income ratio and no publication clearance.

## Accepted decisions

1. **MVP metric scope (ADR-0002): ACCEPTED.** Two source-specific, separately labelled rent and income series; no aggregate rent-to-income ratio, burden percentage, composite score, or invented comparability.
2. **Visual and responsive baseline: ACCEPTED.** The M00-T04 coral/charcoal light/dark direction, paired desktop/mobile wireframe, bedroom control, source and quality disclosures, and explicitly unavailable comparison state are accepted as a *design direction*, not as a production accessibility certification.
3. **Editorial story concepts: ACCEPTED.** The stories about CMHC apartment rent definitions and CIS economic-family income definitions may proceed to research/editorial production in M08. Individual claims, exact chart choices and publication remain subject to evidence checks and editorial review.

## Explicit maintainer enhancement request

> Include more interactive maps and graphs in future phases.

Translate that into trackable acceptance requirements rather than expanding the M00 static discovery preview:

- **M05:** responsive, interactive ECharts visuals for the independently labelled rent and income series; focus/keyboard-operable selection, hover/focus detail, source/quality disclosure and accessible data-table equivalents. No same-axis or combined affordability chart implying comparability.
- **M06:** MapLibre-powered explorer with zoom/pan, region selection, legend, URL-persisted filters, and linked chart updates; source-verified simplified CMA boundary geometry, geography-vintage and licensing evidence, keyboard alternatives and graceful fallback. If the geographic crosswalk is not approved, a region is not coloured with unsupported source values.
- **M08:** richer story-led chart interactions (selectable series, annotated source-specific timelines, small multiples) that retain periods, units and methodological limits; do not animate or combine incompatible aggregates as though they represent household burden.
- **Performance:** lazy-load mapping and graphing libraries on pages that require them, do not ship raw Parquet to browsers, and prefer static self-hosted geodata over paid or key-requiring map tiles in the free-tier MVP. Establish actual byte/performance budgets once M05/M06 exist.

## Non-approvals and follow-up

No publisher reuse licence, CMHC/Statistics Canada source-geography crosswalk, statistical population join, reference-period alignment, metric comparability or public release was approved in this review. Keep all such gates false. Record M00-T04 design acceptance in roadmap notes while M00 remains `in_progress`; ADR-0001 pipeline architecture (M00-T05), naming (M00-T06) and remaining source/publication gates are still outstanding.
