#!/usr/bin/env python3
"""Bounded, audited preview of publisher rows for M00 discovery only.

Not an ETL parser, extraction guarantee, semantic approval, or metric engine.
Does not contact a network or persist publisher rows to the repository.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import posixpath
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from audit_source_probes import audit_source
from probe_official_sources import RAW_DIR, SOURCES, ProbeError, inspect_statcan_zip

_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_PKG_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
_MAX_XML_BYTES = 32 * 1024 * 1024
_MAX_FIELD_CHARS = 160
_MAX_ROWS = 12
_MAX_COLS = 16
_CMA_NAMES = ('Vancouver', 'Victoria', 'Calgary', 'Edmonton', 'Winnipeg', 'Toronto', 'Montréal', 'Halifax')


class ReviewError(ValueError):
    """Evidence is incomplete or publisher rows could not be safely previewed."""


def _clip(value: object) -> str:
    txt = str(value) if value is not None else ''
    return txt[:_MAX_FIELD_CHARS] + ('…' if len(txt) > _MAX_FIELD_CHARS else '')


def _json_base(source: str, audit: dict) -> dict:
    return {
        'review_schema_version': 1,
        'milestone': 'M00-T02',
        'source': source,
        'source_id': SOURCES[source]['source_id'],
        'file_audit_status': audit['status'],
        'sha256': audit.get('sha256'),
        'sampling_only': True,
        'all_rows_reviewed': False,
        'geography_crosswalk_approved': False,
        'metric_comparability_approved': False,
        'publication_approved': False,
    }


def review_census(path: Path, *, region: str, limit: int, max_scan: int) -> dict:
    """Scan bounded Census records for geographic label; preserve symbol semantics."""
    if region not in _CMA_NAMES:
        raise ReviewError('Region must be one of the candidate CMA names')
    info = inspect_statcan_zip(path)
    member = info['csv_member']
    wanted = info['measure_column_indices']
    rows: list[dict] = []
    scanned = 0
    matching = 0
    with ZipFile(path) as archive:
        with archive.open(member) as raw:
            with io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as src:
                reader = csv.reader(src)
                header = next(reader, None)
                if header != info['columns']:
                    raise ReviewError('CSV header changed since structural inspection')
                positions = {key: header.index(key) for key in ('REF_DATE', 'GEO', 'DGUID', 'Coordinate', 'Household size (7)')}
                type_index = next(i for i, value in enumerate(header) if value.startswith('Household type including census family structure'))
                for values in reader:
                    scanned += 1
                    if len(values) != len(header):
                        raise ReviewError(f'CSV row {scanned} has inconsistent column count')
                    geo = values[positions['GEO']]
                    # Only a candidate label match. CMA/boundary verification remains manual.
                    if region.casefold() not in geo.casefold():
                        if scanned >= max_scan:
                            break
                        continue
                    matching += 1
                    measures = {}
                    for key, ix in wanted.items():
                        measures[key] = {
                            'raw_value': _clip(values[ix]),
                            'symbol': _clip(values[ix + 1]),
                            'source_column': _clip(header[ix]),
                        }
                    rows.append({
                        'ref_date': _clip(values[positions['REF_DATE']]),
                        'geo_label': _clip(geo),
                        'dguid': _clip(values[positions['DGUID']]),
                        'coordinate': _clip(values[positions['Coordinate']]),
                        'household_size': _clip(values[positions['Household size (7)']]),
                        'household_type': _clip(values[type_index]),
                        'measures': measures,
                    })
                    if matching >= limit or scanned >= max_scan:
                        break
    return {
        'dataset_layout': info['layout'],
        'candidate_region': region,
        'census_reference_year': info['census_reference_year'],
        'income_reference_year': info['income_reference_year'],
        'scanned_rows': scanned,
        'matching_rows_seen': matching,
        'scan_cap_reached': scanned >= max_scan,
        'sample_limit_reached': len(rows) >= limit,
        'rows': rows,
        'review_warning': 'Geography selected by label only. Inspect DGUID, all-household dimensions, suppression flags and source geography vintage before any join.',
    }


def _zip_entry(archive: ZipFile, member: str, *, limit: int = _MAX_XML_BYTES) -> bytes:
    try:
        info = archive.getinfo(member)
    except KeyError as exc:
        raise ReviewError(f'Workbook missing required XML: {member}') from exc
    if info.file_size > limit:
        raise ReviewError(f'XML member too large for bounded preview: {member}')
    with archive.open(info) as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ReviewError(f'XML member exceeded size limit: {member}')
    return data


def _workbook_sheets(archive: ZipFile) -> dict[str, str]:
    root = ET.fromstring(_zip_entry(archive, 'xl/workbook.xml', limit=2_000_000))
    relroot = ET.fromstring(_zip_entry(archive, 'xl/_rels/workbook.xml.rels', limit=2_000_000))
    rels = {}
    for item in relroot.findall(f'{{{_PKG_REL}}}Relationship'):
        if item.get('Type', '').endswith('/worksheet') and item.get('TargetMode') != 'External':
            target = item.get('Target', '')
            path = (target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl', target)))
            if not path.startswith('xl/worksheets/') or '..' in path.split('/'):
                raise ReviewError('Invalid or unsafe workbook worksheet relationship')
            rels[item.get('Id')] = path
    sheets = {}
    for item in root.findall(f'.//{{{_NS}}}sheet'):
        name, rid = item.get('name'), item.get(f'{{{_REL}}}id')
        if not isinstance(name, str) or not name or rid not in rels or name in sheets:
            raise ReviewError('Workbook sheet name or relationship missing/duplicated')
        sheets[name] = rels[rid]
    if not sheets:
        raise ReviewError('No linked worksheets available for review')
    return sheets


def _shared_strings(archive: ZipFile) -> list[str]:
    if 'xl/sharedStrings.xml' not in archive.namelist():
        return []
    root = ET.fromstring(_zip_entry(archive, 'xl/sharedStrings.xml'))
    return [''.join(part.text or '' for part in item.iter(f'{{{_NS}}}t'))
            for item in root.findall(f'{{{_NS}}}si')]


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    kind = cell.get('t')
    if kind == 'inlineStr':
        return ''.join(element.text or '' for element in cell.iter(f'{{{_NS}}}t'))
    value = cell.find(f'{{{_NS}}}v')
    raw = value.text if value is not None and value.text is not None else ''
    if kind == 's':
        if not re.fullmatch(r'\d+', raw) or int(raw) >= len(shared):
            raise ReviewError('Invalid shared-string reference')
        return shared[int(raw)]
    if kind == 'b':
        return 'TRUE' if raw == '1' else 'FALSE'
    return raw


def review_cmhc(path: Path, *, sheet: str | None, limit: int) -> dict:
    """Limited visible cell sample. Does NOT infer CMHC table semantics."""
    with ZipFile(path) as archive:
        sheets = _workbook_sheets(archive)
        available = list(sheets)
        if sheet is None:
            return {'worksheet_names': available, 'selected_worksheet': None, 'rows': [],
                    'review_warning': 'Select a worksheet by exact name with --sheet; no rent series has been identified.'}
        if sheet not in sheets:
            raise ReviewError('Unknown worksheet; choose an exact name from worksheet_names')
        # Large survey workbooks are common: stream just the first N rows rather
        # than decoding the entire worksheet XML. Shared strings are separately
        # bounded and inspected above; source files stay outside Git.
        shared = _shared_strings(archive)
        member = sheets[sheet]
        info = archive.getinfo(member)
        if info.file_size > 256 * 1024 * 1024:
            raise ReviewError('Worksheet exceeds 256 MiB discovery inspection bound')
        rows = []
        with archive.open(info) as data:
            for event, element in ET.iterparse(data, events=('end',)):
                if element.tag != f'{{{_NS}}}row':
                    continue
                entry = []
                for cell in element.findall(f'{{{_NS}}}c')[:_MAX_COLS]:
                    entry.append({'cell': _clip(cell.get('r', '')),
                                  'display': _clip(_cell_text(cell, shared))})
                if entry:
                    rows.append({'source_row_number': element.get('r'), 'cells': entry})
                element.clear()
                if len(rows) >= limit:
                    break
        return {'worksheet_names': available, 'selected_worksheet': sheet,
                'displayed_rows': len(rows), 'displayed_columns_cap': _MAX_COLS,
                'rows': rows,
                'review_warning': 'Unformatted cell values only; formulas may not have cached values. Review table heading, population, geography, column units and suppression legend manually.'}


def build_review(source: str, raw_dir: Path, *, region: str, sheet: str | None, limit: int, max_scan: int) -> dict:
    if source not in SOURCES:
        raise ReviewError('Unknown source')
    if not 1 <= limit <= _MAX_ROWS or not 1 <= max_scan <= 2_000_000:
        raise ReviewError('Row/sample limits outside permitted range')
    audit = audit_source(source, raw_dir)
    result = _json_base(source, audit)
    if audit['status'] != 'file_verified':
        return {**result, 'status': 'blocked', 'reason': audit['reason']}
    # Use the exact audited manifest filename, not an assumed default basename.
    # A --input probe may legitimately use a different local source filename.
    manifest = json.loads((raw_dir / f'{source}-manifest.json').read_text(encoding='utf-8'))
    source_path = raw_dir / manifest['local_file_name']
    if source == 'statcan-income':
        body = review_census(source_path, region=region, limit=limit, max_scan=max_scan)
    elif source.startswith('cmhc-'):
        body = review_cmhc(source_path, sheet=sheet, limit=limit)
    else:
        # Rate dates and counts are already in the Valet source manifest.
        body = {'review_warning': 'V39079 is macroeconomic context, not a regional rent/income series. See the inspected source manifest.'}
    # Reject local file changes between the initial audit and the preview.
    if audit_source(source, raw_dir)['status'] != 'file_verified':
        raise ReviewError('Publisher file changed while sampling; rerun the audit')
    return {**result, 'status': 'sampled', **body}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, choices=tuple(SOURCES))
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    parser.add_argument('--region', choices=_CMA_NAMES, default='Vancouver')
    parser.add_argument('--sheet', help='CMHC worksheet title (exact match; run without first to list sheets)')
    parser.add_argument('--limit', type=int, default=5, help=f'Maximum printed rows (1–{_MAX_ROWS})')
    parser.add_argument('--max-scan', type=int, default=100_000, help='Max CSV records inspected (1–2000000)')
    args = parser.parse_args(argv)
    try:
        report = build_review(args.source, args.raw_dir, region=args.region, sheet=args.sheet,
                              limit=args.limit, max_scan=args.max_scan)
    except (ReviewError, ProbeError, OSError, ET.ParseError, ValueError) as error:
        print(json.dumps({'milestone': 'M00-T02', 'source': args.source, 'status': 'invalid',
                          'reason': str(error), 'metric_comparability_approved': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'sampled' else 1


if __name__ == '__main__':
    raise SystemExit(main())
