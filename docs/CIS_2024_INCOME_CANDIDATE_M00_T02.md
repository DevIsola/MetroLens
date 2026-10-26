# M00-T02 — Canadian Income Survey 2024 CMA income candidate

**Discovery status:** candidate only; **no rent/income join or publication approval**. Date reviewed: 2026-10-26.

## Official evidence and decision

Statistics Canada [Table 11-10-0190-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001), *Market income, government transfers, total income, income tax and after-tax income by economic family type*, is **annual**, includes **census metropolitan areas**, and was updated with the **2024** Canadian Income Survey (CIS) release on **2026-04-29**. Data from 2018–2023 were revised in that release to incorporate updated 2021 Census information; do not compare against previously downloaded vintages without a revision note. See [The Daily: Canadian Income Survey, 2024](https://www150.statcan.gc.ca/n1/daily-quotidien/260429/dq260429a-eng.htm).

The candidate is **not a substitute for** our verified **2020 median annual income of all private households**, derived from 2021 Census Table `98-10-0058-01`. CIS units are **economic families and persons not in an economic family**, while the Census measure describes **private households**. Even if both are labelled Vancouver and both use a particular Census vintage, the source geography and statistical populations must be reconciled, not assumed identical. A 2024 income observation is **not** temporally aligned with **October 2025 rent**; comparison with October 2024 rent remains a separate *methodological* question because an annual mean/median economic-family income and a monthly mean apartment rent refer to different universes and summary statistics. No ratio may be published or calculated from this candidate.

Statistics Canada's [Full Table Download CSV specification](https://www.statcan.gc.ca/en/developers/csv/user-guide) defines the non-Census **long-form** layout, including `VALUE`, `STATUS`, `SYMBOL`, `VECTOR`, and `COORDINATE`. Unlike the 2021 Census transposed table, **this candidate uses the non-Census layout**. It is downloaded as a ZIP with its separate metadata CSV. The exact downloaded row values, `DGUID`, data status flags, currency/constant-dollar basis, series revisions, and population/geography join evidence have **not** been examined in this development environment. Re-use of selected derivatives remains subject to Statistics Canada's [Open Licence](https://www.statcan.gc.ca/en/terms-conditions/open-licence) and correct attribution.

## Reproducible workstation procedure (no scheduled ETL)

Run from the existing MetroLens repository after patch installation:

```powershell
# Optional: show pinned Statistics Canada URL, without downloading
python scripts/probe_official_sources.py --source statcan-cis-income

# Explicit, bounded one-time download; only under gitignored pipeline/data/raw/
python scripts/probe_official_sources.py --source statcan-cis-income --fetch --max-mib 150

# Verify unchanged bytes and long CSV header against the generated manifest
python scripts/audit_source_probes.py --source statcan-cis-income

# Review actual Vancouver-related 2023/2024 candidate rows and source flags
python scripts/review_cis_income_candidate.py --limit 12 --max-scan 2000000
```

- **Probe expected:** `PASS: container/schema validated; no metric joins approved`, then a manifest under `pipeline/data/raw/m00-source-probes/statcan-cis-income-manifest.json`. Download host is pinned to the official Statistics Canada HTTPS host. `--max-mib` bounds the response; increase to at most 250 only if the actual archive requires it and the origin has been confirmed.
- **Audit expected:** `sources[0].status=file_verified` and a real SHA-256; otherwise stop and share the JSON. The legacy `--source all` audit deliberately checks only the original four sources until this optional candidate is selected.
- **Review expected:** `status=candidate_rows_sampled` if it finds exact `Median after-tax income` / `Economic families and persons not in an economic family` rows for a Vancouver-labelled geography and years 2023–2024. It may return `no_exact_candidate_in_scan` if field/member names differ or the requested rows are absent. In either case, share the complete report, including `candidate_geography_labels`, `candidate_income_concepts_seen`, `candidate_economic_family_types_seen`, `sampled_rows`, `scan_cap_reached` and `sha256` if present. Do not override a missing or flagged value.
- **Review statuses:** `candidate_rows_sampled` is **not** approved data. Every result deliberately contains `candidate_observation_usable=false`, `geography_crosswalk_approved=false`, `reference_periods_aligned=false`, `statistical_populations_comparable=false`, `publication_approved=false`, and `rent_to_income_ratio=null`.

When a sample is empty or invalid, share the complete JSON or error and stop. The reviewer reads only the previously audited file; no network call is made by the review command. Publisher ZIP bytes and manifests are gitignored; do not upload or commit the entire source ZIP.

## What must be decided after real-file inspection

1. Which **exact** `GEO`, `DGUID`, `Economic family type`, `Income concept`, `REF_DATE`, unit and scalar members are returned for Vancouver and how do those geographies relate to CMHC 2021-CMA definitions?
2. Which 2023 and 2024 estimates are reported as observed, suppressed, provisional or low-quality according to the publisher metadata and CIS methods? Are those observations statistically defensible for CMA-level comparisons?
3. Does MetroLens offer the CIS measure as a **separate economic-family indicator**, restricted to its own statistical population, or select a different source for **annual private-household** income before designing an affordability index?
4. Is the MVP more credible as side-by-side labelled income and rent history instead of a combined ratio? Record this decision in M00-T03 metrics documentation and (if semantics change) an ADR.

**Not changed:** `main`, manual-only GitHub Actions / Pages, scheduled ETL, raw-data redistribution, and M00 acceptance status.
