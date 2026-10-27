#!/usr/bin/env python3
"""Extract one exact, audited 2021 Census Vancouver CMA income row (review only).

No network I/O, published datasets, ETL, or CMHC income/rent joins.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile, BadZipFile

from audit_source_probes import audit_source
from probe_official_sources import RAW_DIR, SOURCES, ProbeError, inspect_statcan_zip

SOURCE = 'statcan-income'
DGUID = '2021S0503933'
CMA_LABEL = 'Vancouver (CMA) 933, B.C.'
COORDINATE = '5381.1.1'
HOUSEHOLD_SIZE = 'Total - Households by household size'
HOUSEHOLD_TYPE = 'Total – Household type including census family structure'
MEASURES = {
    'household_count_2021': ('households', '2021', 'household_count'),
    'median_total_income_2020': ('CAD_per_year', '2020', 'median_total_household_income'),
    'median_after_tax_income_2020': ('CAD_per_year', '2020', 'median_after_tax_household_income'),
}
MAX_CENSUS_ROWS = 2_000_000


class IncomeExtractionError(ValueError):
    """The Census row violates the manually reviewed source contract."""


def _normalize(value: str) -> str:
    return ' '.join(value.replace('\u2013', '-').replace('\u2014', '-').split()).casefold()


def _observation(raw: str, symbol: str, key: str, column: str, index: int) -> dict:
    unit, period, metric_id = MEASURES[key]
    value = raw.strip()
    flag = symbol.strip()
    base = {
        'metric_id': metric_id, 'source_measure_id': key, 'reference_period': period,
        'unit': unit, 'measure_type': 'count' if unit == 'households' else 'median',
        'source_column': column, 'source_column_index': index,
        'source_symbol_column_index': index + 1, 'source_symbol': flag or None,
    }
    # Any nonempty publisher symbol is treated as unavailable until its meaning
    # is independently reviewed. Never transform source suppression to zero.
    if flag:
        if value not in ('', '..', '...', 'x', 'F'):
            raise IncomeExtractionError(f'Flagged measure {key} has unexpected numeric/content value')
        return {**base, 'value': None, 'status': 'source_flagged_not_usable'}
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)', value):
        raise IncomeExtractionError(f'Missing or invalid unflagged value for {key}')
    number = int(value.replace(',', ''))
    if number <= 0:
        raise IncomeExtractionError(f'Nonpositive source value for {key}')
    return {**base, 'value': number, 'status': 'observed'}


def extract_census(path: Path) -> dict:
    info = inspect_statcan_zip(path)
    expected_columns = info['columns']
    positions = info['measure_column_indices']
    col_index = {name: i for i, name in enumerate(expected_columns) if name in ('REF_DATE', 'GEO', 'DGUID', 'Coordinate', 'Household size (7)')}
    type_indices = [i for i, name in enumerate(expected_columns)
                    if _normalize(name).startswith('household type including census family structure')]
    if len(type_indices) != 1 or len(col_index) != 5:
        raise IncomeExtractionError('Required source dimension positions are missing or ambiguous')
    found = None
    scanned = 0
    trailing_blank_rows = 0
    with ZipFile(path) as archive, archive.open(info['csv_member']) as binary:
        with io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as text:
            reader = csv.reader(text)
            if next(reader, None) != expected_columns:
                raise IncomeExtractionError('Census CSV header changed after structural verification')
            for values in reader:
                scanned += 1
                if scanned > MAX_CENSUS_ROWS:
                    raise IncomeExtractionError('Census row scan exceeded discovery bound')
                # Some full-table CSVs can contain empty records after the
                # last data row. Only skip records with *no populated fields*.
                # Keep scanning to EOF so an empty record in the middle cannot
                # hide a later, malformed, or duplicate CMA observation.
                if not values or all(not value.strip() for value in values):
                    trailing_blank_rows += 1
                    continue
                if trailing_blank_rows:
                    raise IncomeExtractionError(
                        f'Nonempty Census record {scanned} after '
                        f'{trailing_blank_rows} blank record(s); blank rows are only allowed at EOF'
                    )
                if len(values) != len(expected_columns):
                    raise IncomeExtractionError(
                        f'Malformed Census CSV row {scanned}: '
                        f'expected {len(expected_columns)} fields, found {len(values)}; '
                        'nonblank records cannot be skipped'
                    )
                if values[col_index['DGUID']].strip() != DGUID:
                    continue
                size = values[col_index['Household size (7)']]
                category = values[type_indices[0]]
                if _normalize(size) != _normalize(HOUSEHOLD_SIZE) or _normalize(category) != _normalize(HOUSEHOLD_TYPE):
                    continue
                if found is not None:
                    raise IncomeExtractionError('Duplicate Vancouver CMA all-household aggregate')
                geo = values[col_index['GEO']].strip()
                coordinate = values[col_index['Coordinate']].strip()
                ref_date = values[col_index['REF_DATE']].strip()
                if _normalize(geo) != _normalize(CMA_LABEL) or coordinate != COORDINATE or ref_date != '2021':
                    raise IncomeExtractionError('Exact CMA label, Census coordinate, or Census reference year mismatch')
                observations = []
                for key in MEASURES:
                    i = positions[key]
                    if expected_columns[i + 1].strip() != 'Symbol':
                        raise IncomeExtractionError(f'Missing adjacent source Symbol for {key}')
                    observations.append(_observation(values[i], values[i + 1], key, expected_columns[i], i))
                found = {
                    'census_reference_year': 2021, 'income_reference_year': 2020,
                    'geography_label': geo, 'dguid': DGUID, 'cma_code_2021': '933',
                    'coordinate': coordinate, 'household_size': size, 'household_type': category,
                    'geographic_vintage': '2021_census_definitions',
                    'population_universe': 'all_private_households',
                    'observations': observations,
                }
    if found is None:
        raise IncomeExtractionError('Vancouver CMA all-household aggregate not found')
    return {
        **found,
        'scanned_rows': scanned,
        'data_rows_scanned': scanned - trailing_blank_rows,
        'trailing_blank_rows_skipped': trailing_blank_rows,
        'source_csv_member': info['csv_member'],
    }


def extract_verified(raw_dir: Path = RAW_DIR) -> dict:
    audit = audit_source(SOURCE, raw_dir)
    base = {
        'schema_version': 1, 'milestone': 'M00-T02', 'source': SOURCE,
        'source_id': SOURCES[SOURCE]['source_id'],
        'official_source_url': SOURCES[SOURCE]['url'],
        'file_audit_status': audit['status'],
        'data_provenance_level': 'locally_audited_source_file',
        'geography_crosswalk_approved': False, 'metric_comparability_approved': False,
        'publication_approved': False, 'production_ready': False,
    }
    if audit['status'] != 'file_verified':
        return {**base, 'status': 'blocked', 'reason': audit['reason']}
    manifest = json.loads((raw_dir / f'{SOURCE}-manifest.json').read_text(encoding='utf-8'))
    detail = extract_census(raw_dir / manifest['local_file_name'])
    if audit_source(SOURCE, raw_dir)['status'] != 'file_verified':
        raise IncomeExtractionError('Source or manifest changed during extraction')
    return {**base, 'status': 'extracted_for_review', 'source_sha256': audit['sha256'], **detail}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    args = parser.parse_args(argv)
    try:
        report = extract_verified(args.raw_dir)
    except (IncomeExtractionError, ProbeError, BadZipFile, OSError, ValueError,
            KeyError, UnicodeError, csv.Error, EOFError) as exc:
        print(json.dumps({'status': 'invalid', 'reason': str(exc),
                          'publication_approved': False, 'metric_comparability_approved': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'extracted_for_review' else 1


if __name__ == '__main__':
    raise SystemExit(main())
