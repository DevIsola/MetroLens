#!/usr/bin/env python3
"""M00 discovery: reconcile two reviewed CIS Vancouver observations (not rent burden).

A source-specific, full-file extraction. Never re-label economic families and
unattached persons as private households or automatically approve a rent join.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys
from zipfile import BadZipFile, ZipFile

from audit_source_probes import audit_source
from probe_official_sources import RAW_DIR, SOURCES, ProbeError, inspect_statcan_standard_zip
from review_cis_income_candidate import FAMILY_CANDIDATE, INCOME_CANDIDATE, SOURCE

# Reviewed on 2026-10-26 from a local, publisher-file-verified probe and its
# complete sample report. Changes in upstream file bytes require a fresh review.
REVIEWED_SHA256 = '03677bae1fd1cc412c6563c0b33251d2eb4cf3837712ee7c92aa87d7bec782e4'
CMA_DGUID = '2021S0503933'
CMA_LABEL = 'Vancouver, British Columbia'
SERIES_COORDINATE = '21.12.1'
SERIES_VECTOR = 'v96416811'
REVIEWED_VALUES = {'2023': 77700, '2024': 78900}
MAX_CSV_ROWS = 2_000_000


class CISExtractionError(ValueError):
    """Missing, contradictory or unreviewed publisher source evidence."""


def _is_requested_row(row: dict[str, str]) -> bool:
    return (row['REF_DATE'].strip() in REVIEWED_VALUES and
            row['GEO'].strip().casefold() == CMA_LABEL.casefold() and
            row['Income concept'].strip() == INCOME_CANDIDATE and
            row['Economic family type'].strip() == FAMILY_CANDIDATE)


def _validate_observation(row: dict[str, str]) -> dict:
    year = row['REF_DATE'].strip()
    exact = {
        'DGUID': CMA_DGUID,
        'COORDINATE': SERIES_COORDINATE,
        'VECTOR': SERIES_VECTOR,
        'UOM': '2024 constant dollars',
        'UOM_ID': '455',
        'SCALAR_FACTOR': 'units',
        'SCALAR_ID': '0',
        'STATUS': 'A',
        'SYMBOL': '',
        'TERMINATED': '',
    }
    for field, value in exact.items():
        if row[field].strip() != value:
            raise CISExtractionError(f'{year} candidate: unexpected {field}; independent source review required')
    raw = row['VALUE'].strip()
    if not re.fullmatch(r'[1-9][0-9]*', raw):
        raise CISExtractionError(f'{year} candidate: missing, suppressed, or invalid income value')
    value = int(raw)
    if value != REVIEWED_VALUES[year]:
        raise CISExtractionError(f'{year} candidate: value differs from reviewed source sample')
    return {
        'metric_id': 'cis_median_after_tax_income_economic_family_unit',
        'reference_period': year,
        'value': value,
        'unit': 'CAD_2024_constant_per_year',
        'measure_type': 'median',
        'statistical_population': 'economic_families_and_persons_not_in_economic_families',
        'source_status_code': row['STATUS'],
        'quality_interpretation': 'acceptable_or_better_in_statcan_standard_symbols',
        'source_symbol': None,
        'source_terminated': None,
        'source_unit_id': row['UOM_ID'],
        'source_scalar_id': row['SCALAR_ID'],
        'source_decimals': row['DECIMALS'],
        'source_coordinate': row['COORDINATE'],
        'source_vector': row['VECTOR'],
        'status': 'observed_candidate_only',
        'approved_for_affordability_join': False,
    }


def extract_rows(path: Path) -> dict:
    inspection = inspect_statcan_standard_zip(path)
    header = inspection['columns']
    observed = {}
    scanned = blanks = 0
    with ZipFile(path) as archive, archive.open(inspection['csv_member']) as raw:
        with io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as source:
            reader = csv.reader(source)
            if next(reader, None) != header:
                raise CISExtractionError('CIS source header differs from validated header')
            for fields in reader:
                scanned += 1
                if scanned > MAX_CSV_ROWS:
                    raise CISExtractionError('CIS row count exceeds bounded full scan')
                if not fields or all(not value.strip() for value in fields):
                    blanks += 1
                    continue
                if blanks:
                    raise CISExtractionError('Nonblank CIS data follow trailing blank rows')
                if len(fields) != len(header):
                    raise CISExtractionError(f'Malformed CIS CSV row {scanned}: expected {len(header)} fields, got {len(fields)}')
                row = dict(zip(header, fields))
                if _is_requested_row(row):
                    year = row['REF_DATE'].strip()
                    if year in observed:
                        raise CISExtractionError(f'Duplicate reviewed candidate for {year}')
                    observed[year] = _validate_observation(row)
    if set(observed) != set(REVIEWED_VALUES):
        raise CISExtractionError('Missing reviewed Vancouver economic-family candidate year(s): ' +
                                 ', '.join(sorted(set(REVIEWED_VALUES) - set(observed))))
    return {
        'geography_label': CMA_LABEL,
        'dguid': CMA_DGUID,
        'geographic_vintage': '2021_census_definitions',
        'income_concept': INCOME_CANDIDATE,
        'economic_family_type': FAMILY_CANDIDATE,
        'price_basis': '2024_constant_dollars',
        'observations': [observed[year] for year in sorted(observed)],
        'source_csv_member': inspection['csv_member'],
        'data_rows_scanned': scanned - blanks,
        'trailing_blank_rows_skipped': blanks,
        'full_source_scanned': True,
    }


def extract_verified(raw_dir: Path = RAW_DIR, *, reviewed_sha256: str = REVIEWED_SHA256) -> dict:
    audited = audit_source(SOURCE, raw_dir)
    base = {
        'schema_version': 1, 'milestone': 'M00-T02', 'source': SOURCE,
        'source_id': SOURCES[SOURCE]['source_id'],
        'official_source_url': SOURCES[SOURCE]['url'],
        'file_audit_status': audited['status'],
        'candidate_only': True,
        'census_private_households_equivalent': False,
        'statistical_populations_comparable': False,
        'geography_crosswalk_approved': False,
        'reference_periods_aligned': False,
        'metric_comparability_approved': False,
        'publication_approved': False,
        'production_ready': False,
        'rent_to_income_ratio': None,
    }
    if audited['status'] != 'file_verified':
        return {**base, 'status': 'blocked', 'reason': audited['reason']}
    if audited['sha256'] != reviewed_sha256:
        return {**base, 'status': 'blocked', 'reason': 'CIS publisher file differs from independently reviewed SHA-256'}
    manifest = json.loads((raw_dir / f'{SOURCE}-manifest.json').read_text(encoding='utf-8'))
    body = extract_rows(raw_dir / manifest['local_file_name'])
    if audit_source(SOURCE, raw_dir) != audited:
        raise CISExtractionError('Publisher source or manifest changed during full extraction')
    return {
        **base, 'status': 'candidate_extracted_for_review',
        'source_sha256': audited['sha256'], **body,
        'remaining_gates': [
            'CIS economic-family estimates are not Census private-household medians',
            '2024 income and October 2025 rent refer to different periods',
            'Matching DGUID alone does not approve CMHC source geography crosswalk',
            'Review source notes, reuse attribution and meaningful separate-indicator design',
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    args = parser.parse_args(argv)
    try:
        report = extract_verified(args.raw_dir)
    except (CISExtractionError, ProbeError, BadZipFile, OSError, ValueError,
            KeyError, UnicodeError, csv.Error, EOFError, TypeError) as exc:
        print(json.dumps({'status': 'invalid', 'reason': str(exc),
                          'metric_comparability_approved': False,
                          'publication_approved': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'candidate_extracted_for_review' else 1


if __name__ == '__main__':
    raise SystemExit(main())
