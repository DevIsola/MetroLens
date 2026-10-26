# M00-T02 — Official source sampling and reuse assessment

**Reviewed:** 2026-10-26 · **State:** partial discovery evidence, **not** machine-readable ingestion acceptance. All values in [`samples/official-page-observations.csv`](samples/official-page-observations.csv) were **manually transcribed from official publisher HTML**, not parsed from source CSV, API, or Excel payloads. Do not use this fixture in production or to calculate an affordability ratio.

## 1. Statistics Canada — household income

- **Confirmed machine-readable table identifier:** [Table 98-10-0058-01 — Household income statistics by household type: Census metropolitan areas, tracted census agglomerations and census tracts](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810005801). This is an *occasional* 2021 Census table, released 2022-07-13, with a private-household universe. The publisher offers a full-table Census CSV ZIP. Its **2021 Census transposed (wide)** record layout, unlike non-Census long-form CSV, uses one column per household income measure and a separate adjacent `Symbol` column for each measure; it does **not** have a generic `VALUE` field. See the [Statistics Canada Full Table Download (CSV) User Guide](https://www.statcan.gc.ca/en/developers/csv/user-guide). Actual downloaded bytes, CMA observation rows, and their checksums have not been independently examined or archived as evidence in this repository.
- **Actual sample observations:** [Vancouver CMA 2021 Census Profile](https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/page.cfm?DGUIDlist=2021A00055915055%2C2021A00055915046%2C2021A00055915051%2C2021S0503933%2C2021A00055915043&GENDERlist=1&HEADERlist=0&Lang=E&STATISTIClist=1&SearchText=Vancouver) reports **CAD 90,000 median total household income in 2020**; [Toronto CMA profile](https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/page.cfm?DGUIDlist=2021S0503535&GENDERlist=1&HEADERlist=0&Lang=E&STATISTIClist=1&SearchText=toronto&wbdisable=true) reports **CAD 97,000** for the same indicator and period. These are **Census Profile HTML** observations; they have **not yet been reconciled against rows from Table 98-10-0058-01**. Do not mark table data as downloaded based on these samples.
- **Universe/definition:** median *total* annual income among private households; includes households of multiple sizes and housing tenures. This is not median income specifically for renters or for 2-bedroom apartment tenants, and it refers to calendar-year 2020 despite the 2021 Census release.
- **Permission:** [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/terms-conditions/open-licence) permits reuse and redistribution of covered material (including adapted works) with prescribed attribution; third-party material is excluded. Use the licence's specific attribution form and never imply endorsement.
- **Outstanding:** export a small verified CSV subset; inspect geography identifiers, income-statistic codes, quality flags, reference years, schema/hash, and potential stable year-by-year source needed for future annual trends.

## 2. CMHC — rental market

- **Source:** [2025 Rental Market Survey data tables](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables), published **2025-12-11**, are offered as Excel workbooks and contain average rents, vacancies, turnover and universe counts. **Workbook download, specific sheet/table identifiers, column labels, and file hashes are pending.**
- **Actual sample observations:** [2025 Rental Market Report, Figure 1](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres) gives **CAD 2,696 for Vancouver** and **CAD 2,547 for Toronto** in **October 2025**, each an **average monthly turnover-unit rent for a two-bedroom purpose-built rental apartment**. This figure is HTML/transcribed; it is not an Excel-sheet extraction.
- **Measure semantics:** average turnover rent concerns units whose tenant changed; it is **not** average rent across all occupied units, **not** posted asking rent, and **not** condominium rent. CMHC identifies reliability/suppression indicators in rental tables; treat suppressed/not statistically reliable data as unavailable. The official 2025 report describes the purpose-built rental market as privately initiated rental apartments with three or more units; geographic boundary vintage and survey universe must still be checked at workbook level.
- **Permission:** [CMHC Licence Agreement for the Use of Data](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/cmhc-licence-agreement-use-of-data) grants specified reproduction and redistribution rights with source attribution, subject to any additional limitations communicated by CMHC. Website [general terms](https://www.cmhc-schl.gc.ca/about-us/terms-conditions) are more restrictive; confirm which agreement governs the selected export and required notice before mirroring source files. Until checked, link to publisher and store only this small attributed observation sample; do **not** redistribute original Excel files in Git.
- **Outstanding:** obtain workbook(s) for selected CMA(s); record workbook/sheet/table names, column structure, dates, flags, hash, and 2021-CMA crosswalk, including any boundary vintage differences.

## 3. Bank of Canada — macroeconomic context

- **Source:** [Valet API documentation](https://www.bankofcanada.ca/valet-api-how-to/) and [official interest-rate lookup](https://www.bankofcanada.ca/rates/interest-rates/canadian-interest-rates/). Confirmed series `V39079` is **Target for the overnight rate**, daily / business-day series. Endpoint contract: `https://www.bankofcanada.ca/valet/observations/V39079/json?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` (exact live payload/schema **not inspected in this step**). No API key is required; rate-limit and cache according to the publisher guidance.
- **Actual sample observation:** [Bank of Canada lookup, 2026-10-22](https://www.bankofcanada.ca/rates/interest-rates/canadian-interest-rates/?dF=2026-10-15&dT=2026-10-22&lP=lookup_canadian_interest.php) reports **2.25%**. This is a *historical sample date*, not a live rate or a housing cost estimate; never join it directly to a single CMA household record.
- **Permission:** [Bank of Canada terms](https://www.bankofcanada.ca/terms/) generally permit reuse with accurate source attribution and change disclosure, subject to exclusions for third-party material and logos; no excessive polling or bypassing API limits.
- **Outstanding:** fetch a bounded live Valet response, record returned `seriesDetail` and observation shape, confirm frequency/revisions, checksum an archived sample, and establish if the macro context justifies publication.

## Cross-source comparability decision

**Status: BLOCKED for rent-to-income calculation.** The observed income samples refer to **2020** while current rent examples refer to **October 2025**. Even if both samples shared a year, a broad median of all households divided against an average of turnover-only two-bedroom units would be a descriptive *population-mismatched indicator*, **not** measured household rent burden. A matching CMA name alone cannot prove the geographic boundaries are identical. Reconcile both units, temporal alignment, statistic/segment, geography and aggregation before computing a ratio; otherwise show `insufficient comparable data`.

The small sample fixture exists only to test provenance, schema controls and detection of unsupported joins. No new ETL, hosted dataset, scheduling, or Pages changes are authorized by this task.

## Remaining acceptance evidence (M00-T02)

1. Obtain **actual CSV** data for StatsCan table `98-10-0058-01`, including row/column codes, reference vintage, extraction date and SHA-256.
2. Obtain **actual CMHC Excel** workbook(s), record download URL, edition, sheet/table, relevant cells and SHA-256. Verify geographic definitions and survey populations.
3. Obtain **actual bounded Valet JSON** response for `V39079`, document metadata and SHA-256.
4. Verify coverage and alignment using real raw columns across at least two candidate CMAs and document formal reuse/attribution notices for each exported data product.
5. Make an explicit go/no-go decision for a metric pair, with negative test cases. Preserve `M00=in_progress` until the whole M00 acceptance gate is met.

## Increment 2 — reproducible machine-readable source probes (2026-10-26)

**Status: locally implemented and tested, network retrieval NOT completed in this execution environment.** The execution environment cannot resolve publisher hosts to download CSV/JSON/XLSX bytes, so there are **no genuine raw-download hashes or inspected live data rows** to report. Test archives/JSON are synthetically constructed in memory strictly to exercise the format validators; they are not actual StatCan, CMHC, or Valet samples.

A no-dependency, **opt-in** discovery program is now available at `scripts/probe_official_sources.py`. Its default action is URL preview without network I/O. It only makes a request with `--fetch` for a named, pinned official source, enforces HTTPS and the expected publisher host, caps downloads, validates the basic file/container schema, emits `sha256` plus byte size and inspection metadata, and labels every manifest `production_ready: false`, `semantic_comparability_verified: false`. Files are stored only under gitignored `pipeline/data/raw/m00-source-probes/`.

| CLI `--source` | Pinned publisher download/endpoint | What is verified after an actual download | Still requires human inspection |
| --- | --- | --- | --- |
| `statcan-income` | [StatCan full-table CSV ZIP route](https://www150.statcan.gc.ca/n1/en/tbl/csv/98100058-eng.zip) | ZIP valid, CSV member labeled `98100058`; 2021 Census **wide** columns including `REF_DATE`, `GEO`, `DGUID`, `Coordinate`, household-type/size dimensions, 2021 household count, 2020 median total/after-tax income, and adjacent `Symbol` columns; SHA-256 | Actual CMA rows and codes, household category selection, suppression status, geographic vintage and equivalence, income reference year, actual downloaded bytes; entire cube may exceed default 80 MiB cap |
| `cmhc-vancouver` | [Vancouver 2025 RMS XLSX](https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-data-tables/rental-market/rental-market-report-data-tables/2025/rmr-vancouver-2025-en.xlsx?rev=9c12f2db-c0c8-4d06-83e1-cc3e06da8d36) | Valid XLSX workbook container and worksheet list; SHA-256 | Header rows, cell references, numeric tables, reliability flags, CMA boundary vintage |
| `cmhc-toronto` | [Toronto 2025 RMS XLSX](https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-data-tables/rental-market/rental-market-report-data-tables/2025/rmr-toronto-2025-en.xlsx?rev=f107330e-4620-4462-9027-8c6ff1522f1a) | Same XLSX container check and SHA-256 | Same unresolved checks as Vancouver, in particular survey geography vs. 2021 CMA |
| `boc-overnight` | [Valet V39079 bounded JSON](https://www.bankofcanada.ca/valet/observations/V39079/json?start_date=2026-10-19&end_date=2026-10-22) | Expected series ID, dated numeric observations in fixed 2026-10-19 through 2026-10-22 window, no duplicate/out-of-range dates; SHA-256 | Publication/revision methodology, application as national context rather than CMA input |

The direct CMHC XLSX URLs were recovered from the official **2025 Rental Market Report** 'download Excel' links on 2026-10-26, not guessed from filenames. Statistics Canada's official table page confirms the CSV download option but the *entire-table ZIP endpoint* used by the CLI remains a **conventional candidate URL**, not evidence that its download currently succeeds. On a connected workstation, validate that candidate endpoint before assuming its availability.

### Reproducible local run (no CI, no hosting)

```sh
# Preview all official source URLs without network requests:
python scripts/probe_official_sources.py --source statcan-income
python scripts/probe_official_sources.py --source cmhc-vancouver
python scripts/probe_official_sources.py --source cmhc-toronto
python scripts/probe_official_sources.py --source boc-overnight

# One deliberate, bounded download per command (run locally with internet):
python scripts/probe_official_sources.py --source boc-overnight --fetch
python scripts/probe_official_sources.py --source cmhc-vancouver --fetch
python scripts/probe_official_sources.py --source cmhc-toronto --fetch
python scripts/probe_official_sources.py --source statcan-income --fetch

# Large StatCan ZIP, ONLY if verified to need more space and within project budget:
python scripts/probe_official_sources.py --source statcan-income --fetch --max-mib 250

# Alternatively, inspect a manually downloaded publisher file without network:
python scripts/probe_official_sources.py --source cmhc-vancouver --input /path/to/publisher-file.xlsx

python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --check
```

A successful `--fetch` creates a small JSON manifest in the ignored raw directory with **actual** retrieval-time SHA and format metadata; it does **not** create a production CSV, confirm a semantic definition, or establish compatibility between 2020 income and 2025 rents. No source data or generated raw manifests are committed. Record the applicable Statistics Canada Open Licence attribution and CMHC's required reproduction/value-added notice *before* distributing derived tables; official terms are linked in sections 1–2 above.

**Next gate (still M00-T02):** run each probe with publisher access, review real worksheet/cube values and source geography identifiers, capture evidence without committing large binaries, and resolve (or narrow) the income–rent comparison before selecting any analytics mart. ETL scheduling remains deferred to M09.

## Increment 3 — fix Census CSV schema detection (M00-T02)

The previous `statcan-income` probe mistakenly expected the standard non-Census long-form columns `REF_DATE`, `GEO`, `VALUE`. Statistics Canada's official [Full Table Download (CSV) User Guide](https://www.statcan.gc.ca/en/developers/csv/user-guide) explicitly documents that **2021 Census of Population tables (`98-XXXX-XX`) transpose the final dimension into multiple columns** with paired `Symbol` columns. The user observed this exact layout when running `--fetch` for table `98-10-0058-01` on 2026-10-26. This was a **probe validator bug**, not evidence of a corrupted StatCan download.

The probe now validates the Census-specific `REF_DATE`, `GEO`, `DGUID`, household size/type, and `Coordinate` dimensions, identifies the columns for `Number of households (2021)`, `Median household total income (2020)`, and `Median household after-tax income (2020)`, and checks a `Symbol` field immediately follows each transposed measure. It retains every original column (including repeated `Symbol` headers), reports positional indices, and explicitly labels the income year **2020** rather than **2021**. Regression tests cover this format and fail for a generic `VALUE` schema, missing measures, missing symbols, and invalid dimensions.

Re-run the same explicit fetch:

```sh
python scripts/probe_official_sources.py --source statcan-income --fetch
```

Or inspect a source ZIP already saved outside this repository:

```sh
python scripts/probe_official_sources.py --source statcan-income --input /path/to/98100058-eng.zip
```

A successful result confirms **only file/container/header structure** and writes a manifest under gitignored `pipeline/data/raw/m00-source-probes/`. It does **not** establish valid CMA rows, data comparability, dataset licensing of individual derived files, or a rent-to-income ratio. Note that the prior failed `--fetch` discards its temporary download; re-download unless you separately saved a publisher ZIP.

## Increment 4 — offline provenance audit of downloaded files (M00-T02)

Once the four `--fetch` commands succeed on a network-enabled workstation, run:

```sh
python scripts/audit_source_probes.py
# Optional: audit one source at a time
python scripts/audit_source_probes.py --source statcan-income
```

This check makes **no network calls**. It reads the ignored `pipeline/data/raw/m00-source-probes/<source>-manifest.json` and the corresponding downloaded file, recomputes its SHA-256 and byte size, reruns the source-format validation, and compares those results with the recorded inspection metadata. A manifest is accepted only for a known pinned publisher URL and source ID, with `production_ready: false` and `semantic_comparability_verified: false`. Source paths are restricted to simple filenames (no traversal or symlinked files). The JSON report contains only limited source metadata and checksums, **not observations or source-file contents**.

| Status | Interpretation | Next action |
| --- | --- | --- |
| `file_verified` | Manifest and local original bytes match and the structural probe passes | Examine real rows/worksheets, geographic definitions, licensing and alignment |
| `missing_manifest` | No successful probe manifest for the selected source | Run `probe_official_sources.py --source ... --fetch` |
| `manifest_only` | Manifest exists but original file is not in the probe directory | With `--input` the original may have stayed elsewhere; rerun `--fetch`, or place the *same* verified file under its original basename in the ignored raw directory |
| `invalid` | Corrupt, altered or untrusted manifest/file, or schema mismatch | Review the source, repeat the publisher probe; do not promote the output |

Exit code **0** means all requested source files pass the *local structural/byte-consistency* check; **1** means incomplete evidence; **2** means at least one invalid artifact. Example of writing the small report in the ignored raw directory:

```sh
python scripts/audit_source_probes.py > pipeline/data/raw/m00-source-probes/evidence-audit.json
```

Because the publisher files and manifests remain on your workstation, **passing the audit is not independently verifiable by another developer until they reproduce the download**. The recorded hash proves only consistency between a local file and its local manifest; it is not a publisher-provided authenticity attestation. It does not check row semantics, suppression, the exact CMHC CMA crosswalk, compatible reference periods, matching household populations, or source-data redistribution permission. `metric_comparability_approved` is always `false`. **Do not calculate rent-to-income ratios from the 2020 Census-income and 2025 CMHC-rent examples.**

The next substantive M00 gate is a manual, cited field/worksheet review of the real files and evidence of compatible rent/income concepts, followed by the M00-T03 approved metric contract. A successful structural audit alone does not complete M00-T02 or unlock M01/M02.
