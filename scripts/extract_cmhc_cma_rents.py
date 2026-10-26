#!/usr/bin/env python3
"""Extract audited CMHC Vancouver CMA Table 1.1.2 average rents for M00 review.

Offline discovery only: the output is neither a production data mart nor a
rent-to-income comparison. Publisher files remain within ignored raw storage.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from audit_source_probes import audit_source
from probe_official_sources import RAW_DIR, SOURCES, ProbeError
from review_source_rows import (_NS, _workbook_sheets, _shared_strings, _cell_text,
                                ReviewError)

SOURCE = 'cmhc-vancouver'
SHEET = 'Table 1.1.2'
AREA = 'Vancouver CMA'
TITLE = '1.1.2 Private Apartment Average Rents ($), by Zone and Bedroom Type - Vancouver CMA'
MAX_WORKSHEET_BYTES = 256 * 1024 * 1024
MAX_ROWS = 10000
# Source workbook positions, with adjacent source-reliability codes.
BEDROOM_COLUMNS = (
    ('studio', 'Studio', 'B', 'C', 'D', 'E'),
    ('one_bedroom', '1 Bedroom', 'F', 'G', 'H', 'I'),
    ('two_bedroom', '2 Bedroom', 'J', 'K', 'L', 'M'),
    ('three_plus_bedroom', '3 Bedroom +', 'N', 'O', 'P', 'Q'),
    ('all_bedrooms', 'Total', 'R', 'S', 'T', 'U'),
)
QUALITY = {'a': 'Excellent', 'b': 'Very Good', 'c': 'Good', 'd': 'Poor (use with caution)'}
YEAR_COLUMNS = ((2024, 'Oct-24', 0, 1), (2025, 'Oct-25', 2, 3))


class RentExtractionError(ValueError):
    """CMHC sheet does not meet the reviewed discovery extraction contract."""


def _normalize(value: str) -> str:
    return ' '.join(value.split()).casefold()


def _reference_cells(archive: ZipFile, sheet_member: str) -> dict[str, str]:
    """Read addressed cells; prevent ambiguous duplicate references and huge sheets."""
    info = archive.getinfo(sheet_member)
    if info.file_size > MAX_WORKSHEET_BYTES:
        raise RentExtractionError('Worksheet exceeds bounded extraction limit')
    shared = _shared_strings(archive)
    cells = {}
    seen_rows = 0
    with archive.open(info) as data:
        for _, row in ET.iterparse(data, events=('end',)):
            if row.tag != f'{{{_NS}}}row':
                continue
            seen_rows += 1
            if seen_rows > MAX_ROWS:
                raise RentExtractionError('Worksheet exceeds bounded row limit')
            for cell in row.findall(f'{{{_NS}}}c'):
                ref = cell.get('r', '')
                if not re.fullmatch(r'[A-Z]{1,3}[1-9]\d{0,6}', ref):
                    raise RentExtractionError('Invalid Excel cell reference')
                if ref in cells:
                    raise RentExtractionError(f'Duplicate Excel cell reference: {ref}')
                cells[ref] = _cell_text(cell, shared).strip()
            row.clear()
    return cells


def _parse_rent(raw: str, quality: str, *, ref: str) -> dict:
    if raw == '**':
        if quality:
            raise RentExtractionError(f'Suppressed value {ref} unexpectedly carries quality code')
        return {'value_cad_per_month': None, 'quality_code': None,
                'quality_description': None, 'status': 'suppressed', 'cell': ref}
    if quality.casefold() not in QUALITY:
        raise RentExtractionError(f'Unknown/missing quality code for {ref}: {quality!r}')
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?', raw):
        raise RentExtractionError(f'Invalid rent amount in {ref}: {raw!r}')
    try:
        number = Decimal(raw.replace(',', ''))
    except InvalidOperation as exc:
        raise RentExtractionError(f'Invalid numeric rent in {ref}') from exc
    if not number.is_finite() or number <= 0:
        raise RentExtractionError(f'Rent must be positive in {ref}')
    return {
        'value_cad_per_month': int(number) if number == number.to_integral_value() else float(number),
        'quality_code': quality.casefold(), 'quality_description': QUALITY[quality.casefold()],
        'status': 'use_with_caution' if quality.casefold() == 'd' else 'observed',
        'cell': ref,
    }


def extract_table(path: Path) -> dict:
    with ZipFile(path) as archive:
        sheets = _workbook_sheets(archive)
        if SHEET not in sheets:
            raise RentExtractionError(f'Missing required exact worksheet: {SHEET}')
        cells = _reference_cells(archive, sheets[SHEET])
    if _normalize(cells.get('A3', '')) != _normalize(TITLE):
        raise RentExtractionError('Unexpected Table 1.1.2 heading or geography')
    if _normalize(cells.get('A7', '')) != 'zone':
        raise RentExtractionError('Unexpected geography column header')
    for _, expected, y24, _, y25, _ in BEDROOM_COLUMNS:
        if _normalize(cells.get(f'{y24}6', '')) != _normalize(expected):
            raise RentExtractionError(f'Bedroom heading mismatch in {y24}6')
        if cells.get(f'{y24}7') != 'Oct-24' or cells.get(f'{y25}7') != 'Oct-25':
            raise RentExtractionError(f'Year labels mismatch for {expected}')
    # Verify the exact aggregate rather than city, zone, or household section.
    aggregate_rows = sorted({int(match.group(1)) for ref, value in cells.items()
                             if (match := re.fullmatch(r'A(\d+)', ref)) and _normalize(value) == _normalize(AREA)})
    if len(aggregate_rows) != 1:
        raise RentExtractionError('Expected exactly one Vancouver CMA aggregate row')
    row_num = aggregate_rows[0]
    if row_num < 8:
        raise RentExtractionError('CMA row cannot be part of the table header')
    # The geographic vintage and quality legend are present in the publisher
    # worksheet; do not silently infer them merely from the workbook year.
    text = _normalize(' '.join(cells.values()))
    if '2025 and 2024 data are based on the 2021 census geographic definitions' not in text:
        raise RentExtractionError('2021 Census geographic-definition footnote not found')
    if 'data suppressed' not in text or 'quality indicators' not in text:
        raise RentExtractionError('Quality/suppression legend missing')
    # Both the letter and the meaning must appear; no unknown flags admitted.
    for label in QUALITY.values():
        if _normalize(label) not in text:
            raise RentExtractionError(f'Quality legend missing: {label}')
    records = []
    for key, _heading, y24, flag24, y25, flag25 in BEDROOM_COLUMNS:
        for year, _month, val_col, flag_col in (
                (2024, 'Oct-24', y24, flag24), (2025, 'Oct-25', y25, flag25)):
            ref = f'{val_col}{row_num}'
            observation = _parse_rent(cells.get(ref, ''), cells.get(f'{flag_col}{row_num}', ''), ref=ref)
            records.append({'bedroom_type': key, 'reference_period': f'{year}-10',
                            'metric_id': 'cmhc_average_private_apartment_rent',
                            'quality_cell': f'{flag_col}{row_num}', **observation})
    return {'sheet': SHEET, 'source_table': '1.1.2', 'source_row': row_num,
            'geography_label': AREA, 'geographic_vintage': '2021_census_definitions',
            'rental_universe': 'private_purpose_built_rental_apartments',
            'rent_measure': 'average_of_surveyed_units_not_turnover_or_asking_rent',
            'records': records}


def extract_verified(raw_dir: Path = RAW_DIR) -> dict:
    audit = audit_source(SOURCE, raw_dir)
    result = {'schema_version': 1, 'milestone': 'M00-T02', 'source': SOURCE,
              'source_id': SOURCES[SOURCE]['source_id'],
              'official_source_url': SOURCES[SOURCE]['url'],
              'file_audit_status': audit['status'],
              'data_provenance_level': 'locally_audited_source_file',
              'metric_comparability_approved': False, 'geography_crosswalk_approved': False,
              'publication_approved': False, 'production_ready': False}
    if audit['status'] != 'file_verified':
        return {**result, 'status': 'blocked', 'reason': audit['reason']}
    manifest = json.loads((raw_dir / f'{SOURCE}-manifest.json').read_text(encoding='utf-8'))
    source_path = raw_dir / manifest['local_file_name']
    detail = extract_table(source_path)
    if audit_source(SOURCE, raw_dir)['status'] != 'file_verified':
        raise RentExtractionError('Source or manifest changed during extraction')
    return {**result, 'status': 'extracted_for_review', 'source_sha256': audit['sha256'], **detail}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    args = parser.parse_args(argv)
    try:
        result = extract_verified(args.raw_dir)
    except (RentExtractionError, ReviewError, ProbeError, OSError, ValueError,
            ET.ParseError, KeyError) as error:
        print(json.dumps({'status': 'invalid', 'reason': str(error),
                          'metric_comparability_approved': False,
                          'publication_approved': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['status'] == 'extracted_for_review' else 1


if __name__ == '__main__':
    raise SystemExit(main())
