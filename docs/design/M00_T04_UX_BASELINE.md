# M00-T04 — MetroLens UX baseline, paired local wireframes, and stories

**Status:** Visual direction, separate-indicator scope and two story concepts accepted by maintainer on 2026-10-26; **not** production-ready or publicly approved. **Date:** 2026-10-26. Related [ADR-0002](../adr/ADR-0002-unjoined-indicators.md), [M00-T03 preview contract](../M00_INDICATOR_PREVIEW_CONTRACT.md), and [master roadmap](../NORTHSTAR_MASTER_ROADMAP.md). M00-T04 delivers a review artifact; **M05 implements the production frontend**.

## Source and scope boundary

The only source-derived numerical observations in the local rendered wireframe come from the three previously verified local files: CMHC 2024/2025 Vancouver CMA purpose-built apartment mean rents (five bedroom types); Statistics Canada CIS 2023/2024 median after-tax income for economic families and unattached persons (2024 constant dollars); plus Census 2020 all-household income **only as a reconciliation gate**, **not** displayed or joined.

There is **no** approved estimate of rent burden, share of income, apartment-level household income, affordability index, inter-source growth rate, or expenditure residual. `rent_to_income_ratio` stays null. Never label the annual CIS median as *household* or *tenant* income. Never label CMHC average rent as advertised or turnover-only rent. CMHC average rent is a weighted mean across surveyed occupied/vacant purpose-built units; the source's October snapshots must not be described as a composition-adjusted rent increase. Source-specific rate calculations are intentionally absent.

M00-T04 HTML is generated only after **all three local publisher extractors and the M00 reconciliation re-run**. Source hashes and reviewed rent/income values are verified again. This means it intentionally stops for a changed official file until a source review is repeated; no override flag exists.

## Review artifact: paired dark / light / mobile / desktop

Run from repository root (no network or package install):

```powershell
python scripts/render_m00_wireframes.py
```

It prints `status: local_wireframes_created` and writes a **UTF-8** standalone HTML file at `local-previews/M00_T04_Vancouver_Paired_Wireframes.html`. Open locally in a browser; no server is required and no fetches occur. `local-previews/` is `.gitignore`d. Do not host, commit, send through public Pages or treat as publication. `--output "C:\...\custom.html"` changes the destination. The source data remain in ignored `pipeline/data/raw/` paths and are never copied into the repository.

The HTML shows original **light and dark side-by-side** using the semantic tokens of [`theme-preview-v0.2.0.html`](theme-preview-v0.2.0.html). Use the `Desktop pair` / `Mobile pair (390 px)` controls to compare both themes at both layouts. The bedroom selector updates both rent panels simultaneously; income remains separately identified. Every value has an explicit source, period, unit, population and quality label. The blocking panel is visible, not hidden behind a tooltip.

### Token roles and visual hierarchy

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| Canvas | `#F7F7F5` | `#0D0F12` | Quiet editorial background |
| Card/surface | `#FFFFFF` | `#181B20` | Independent data sections |
| Text | `#202328` | `#F5F6F7` | Primary foreground |
| Muted text | `#606773` | `#ADB3BC` | Sources, periods, limits |
| Accent | `#BC453B` | `#F46D5F` | Small editorial eyebrow, markers, links |
| Border | `#DDE0DF` | `#333840` | Cards and separation |
| Focus | `#315E9C` | `#97BEFF` | Visible keyboard focus |

**Source of design direction:** original MetroLens v0.2.0 theme concept with an editorial typographic hierarchy inspired by Taiwan Metrics. Do not copy Taiwan Metrics assets/content or claim this concept reproduces their system. Color contrast is a **design target**, not certified here; WCAG 2.2 AA testing and EN/PT-BR production localization remain M05 work.

### Frames and responsive behavior

1. **Desktop 1440:** 2 frames, one light and one dark, header/navigation concept, narrative hero, CMA definition, rent section, income section, disabled comparison, source links. The pair intentionally shows the *same* observations and selectors, not competing locations.
2. **Mobile 390:** same information order, cards stacked, full-width quality/source labels, readable keyboard-operated bedroom select; no horizontally truncated source definitions. Mobile frame is fixed to approximately 390 CSS pixels, with graceful single-column fallbacks at narrow browser widths.
3. **Light/dark parity:** no information or capability is missing in either. Browser controls update both panes for easier copy/layout acceptance. Final product may honor `system` theme and user persistence; this review intentionally shows both at once.
4. **Accessibility/interaction:** HTML labels for selection, focus-visible treatment, display values always in text (bars are redundant), reduced-motion compatibility, native links to primary-source files, mobile-first reading order. Validate keyboard navigation, screen-reader announcement and zoom at 200%/400% in M05.

### Copy and blocked states

- Preferred geography label: **Vancouver CMA · 2021 Census geographic definitions**. Do **not** claim a cross-publisher geography approval; CMHC workbook footnote and StatsCan DGUID alone are insufficient.
- Rent card: **Average purpose-built apartment rent**, with CMHC RMS population, weighted mean, surveyed vacant/occupied units, CAD per month, **October 2024 / October 2025**, bedroom filter and quality `a (Excellent)`.
- Income card: **Median after-tax income**, with **economic families and persons not in an economic family**, CAD per year in **2024 constant dollars**, **2023 / 2024**, status `A`. It is **not** a Census private-household income measure.
- Disabled composite card: **Affordability ratio unavailable.** Directly state statistical units, mean/median distinction, source geography and period review gaps; no placeholder %, color-coded improvement or fictitious KPI.
- Provenance: each source link opens the official upstream publisher, not an internal stale cache. Evidence checksums remain in the JSON/extractor contract; avoid cluttering the public-facing card with 64-character hashes.
- Preview notice: **Local non-public review**, never a cleared, licensed publication. Public release requires publisher-specific licensing/attribution review and content acceptance.

## Proposed routes (information architecture, not implemented navigation)

| Route | Purpose and current data policy | Milestone |
| --- | --- | --- |
| `/` | Static locale selection, no middleware/SSR redirect | M05 |
| `/en/`, `/pt-br/` | Editorial Overview; unjoined indicators and clear methodology limits | M05 |
| `/{locale}/explore/` | Geography and bedroom-type filters; no invalid joins or unavailable-city fabricated values | M06 |
| `/{locale}/methodology/` | Publisher methods, population definitions, dates, quality, caveats, licenses | M05 / M10 |
| `/{locale}/lab/` | Future scenario lab; not a validated household burden calculation | M07 |
| `/{locale}/stories/` | Research-backed narratives; editorial approval required | M08 |
| `/{locale}/data-status/` | Source freshness and provenance notices | M10 |

The wireframe nav is **plain, non-clickable route labels** until routes exist. No fake links or server-side dependencies.

## Two potential independently scoped stories

**Story A — What does Vancouver's average apartment rent actually capture?** Source: CMHC Table 1.1.2, Vancouver CMA, 2024/2025. Question: what are levels by bedroom type? Recommended chart: two separately labelled October bars for a chosen bedroom count and a descriptive, non-causal takeaway. Caveat: weighted mean of purpose-built apartment units, not current asking rent, not a controlled same-unit rent-change series. Official table/quality legend prominent. Do **not** assert renter cost burden.

**Story B — Whose median after-tax income is in the 2024 income survey?** Source: Statistics Canada CIS Table 11-10-0190-01, Vancouver CMA DGUID `2021S0503933`, 2023/2024, 2024 constant dollars. Question: how is the economic-family and unattached-person median defined? Recommended two-year chart and concise population explanation. Caveat: population is **not** all-private-households and does not identify CMHC renters. Do **not** derive rent share or imply the 2020 Census household median is the same series.

Both story outlines are editorial hypotheses, not approved factual interpretations or M08 deliverables. Their reproducibility, citations, sample quality, limitations and narrative revisions must be signed off later.

## UX and engineering backlog (proposed priority, not schedule)

| Priority | Future task | Acceptance evidence | Phase |
| --- | --- | --- | --- |
| P0 | Approve/refine ADR-0002 separate-indicator scope, terminology and geography disclaimer | Maintainer review and accepted ADR | M00 |
| P0 | Decide light/dark token roles, hero copy, card order, bedroom control and blocked-state prominence | Desktop/mobile paired screenshot acceptance | M00-T04 |
| P0 | Review publisher reuse notices, attribution, geographic crosswalk and boundary evidence | Recorded primary-source evidence, explicit signoff | M00 |
| P0 | Implement semantic design system and source-linked cards with data contracts | Component tests, no hidden ratio; real data manifest only once authorized | M05 |
| P0 | Build accessible EN/PT-BR routes and keyboard-resilient responsive views | Locale and zoom/axe/Playwright checks | M05 |
| P1 | Explorer city/type filters and missing-data states | No unverified location joins; appropriate null displays | M06 |
| P1 | Methodology panels with source notes, period vs publication date, quality meanings | Link and source-content audits | M05/M10 |
| P1 | Chart data tables and no-color-only encodings | WCAG 2.2 AA testing, color-blind review | M05/M06 |
| P1 | Interactive source-specific charts: keyboard access, focus tooltips, selectable series, data tables and reduced-motion alternatives | ECharts component/E2E tests, no cross-source ratio or implied comparison | M05/M08 |
| P1 | MapLibre CMA explorer with pan/zoom, linked region/chart filters, URL state, legend and accessible alternative | Approved boundary provenance, crosswalk gate, keyboard/performance/fallback tests | M06 |
| P2 | Two sourced, editorially signed-off stories | Claim/evidence audit, no implied cross-source causality | M08 |

## Review decision and interactive-visualization follow-up

**All three design decisions were accepted by the maintainer on 2026-10-26.** The request for more interactive maps and charts is captured with M05/M06/M08 deliverables and acceptance criteria in [`M00_T04_REVIEW_DECISION.md`](M00_T04_REVIEW_DECISION.md). Visual approval does **not** authorize public distribution or statistical joins. M00 remains `in_progress`; M01 remains `not_started`.
