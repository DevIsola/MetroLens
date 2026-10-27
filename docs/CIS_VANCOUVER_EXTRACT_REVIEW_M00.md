# M00-T02 — Reviewed Vancouver CIS candidate observations (2023–2024)

**Status:** Source-specific *candidate extraction* implementation, not production acceptance. Evidence furnished in the workstation reviewer JSON on 2026-10-26. The original downloaded publisher bytes are **not** in this Git repository or the implementation sandbox.

## Reviewed observed source sample

- Statistics Canada [Table 11-10-0190-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110019001), Canadian Income Survey, annual; full table CSV archive `11100190-eng.zip`.
- Local `audit_source_probes.py --source statcan-cis-income` returned `file_verified`, file size **3,264,030 bytes**, SHA-256 `03677bae1fd1cc412c6563c0b33251d2eb4cf3837712ee7c92aa87d7bec782e4`.
- Geography: `Vancouver, British Columbia`, source `DGUID` **`2021S0503933`**; **this identifier does not independently authorize** a CMHC crosswalk.
- Income concept: **Median after-tax income**, economic-family type **Economic families and persons not in an economic family**. **NOT** the Census median income of all private households.
- Original vector `v96416811`, coordinate `21.12.1`, unit `2024 constant dollars`, UOM_ID `455`, scalar `units` (`SCALAR_ID=0`). Source status `A`; `SYMBOL` and `TERMINATED` empty in both reported rows.

| Reference year | Value (2024 constant CAD/year) | Status | Source type |
| --- | ---: | --- | --- |
| 2023 | 77,700 | A | Median after-tax income, economic-family units plus unattached persons |
| 2024 | 78,900 | A | Identical source series/population and constant-dollar basis |

The user-provided reviewer reported `253680` records scanned, **two** matching samples, and no scan cap reached. These numbers describe the **reported local sample review**, not an independently reproduced complete extraction in this development environment.

The [Statistics Canada standard table symbols guide](https://www.statcan.gc.ca/en/concepts/definitions/guide-symbol) describes data-quality symbols `A`–`D` as *acceptable or better*. The individual table's quality footnotes, confidence intervals and any precision cautions must still be reviewed before analytic use. Never apply CMHC's `a` quality legend to a CIS `A` status solely because the letters match. The [full-table CSV user guide](https://www.statcan.gc.ca/en/developers/csv/user-guide) distinguishes `STATUS` from `SYMBOL`, and makes clear that table metadata/footnotes must be retained.

## Implementation

New `scripts/extract_cis_cma_income.py` is a read-only, no-network, no-production-output extractor. It runs the normal local source manifest audit, additionally requires the **specific reviewed file SHA-256**, and scans the entire standard-form CSV. It checks the exact geography, DGUID, income concept, economic-family type, years, vector, coordinate, measurement units, quality/status flags, and the two pinned values. Duplicate matches, altered input values, nonblank malformed records, missing observations and file changes fail closed. A different Statistics Canada revision requires **review and an updated fixture**, not silent acceptance.

The returned `status=candidate_extracted_for_review` is a **technical sample-verification status only**. All `publication_approved`, `production_ready`, `metric_comparability_approved` and population equivalence flags remain **false**, and `rent_to_income_ratio=null`.

## Workstation validation handoff

From the existing feature branch after applying the Git patch and passing local tests:

```powershell
python scripts/audit_source_probes.py --source statcan-cis-income
python scripts/extract_cis_cma_income.py
```

Success means `candidate_extracted_for_review`, source SHA exactly as above, DGUID `2021S0503933`, **two** observations (2023 `77700`, 2024 `78900`), `full_source_scanned=true`, and all approval flags `false`. The original archive does not need re-downloading if it still audits as `file_verified`.

Send the **complete extractor JSON** and the final test summary. A `blocked` or `invalid` output requires the full error JSON; do not change the source data to bypass a mismatch. Raw ZIP and manifests remain ignored by Git.

## Remaining product decision

**Do not compute a rent-to-income ratio.** A Census *private household* income of 2020 is not a CIS economic-family/unattached-person income of 2024; neither automatically measures the income of households actually paying CMHC's sampled purpose-built apartment rents. Even the matched geography and same calendar **2024** leave the different populations, rent sampling unit, median-vs-mean aggregation, rental survey date vs full income year, and source geography definitions to resolve. October 2025 rents are not a 2024 observation. A safer initial product design is separate, clearly labelled trend tiles; the final choice requires M00 methodology sign-off and licence attribution review.

All GitHub workflows remain manually dispatched only. No ETL schedule, GitHub Pages publication, or raw dataset redistribution is introduced.
