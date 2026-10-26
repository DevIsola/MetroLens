#!/usr/bin/env python3
"""Opt-in M00 official-source download and format/provenance probe (not ETL).

All fetched files and manifests live beneath gitignored pipeline/data/raw/. A
successful probe demonstrates valid container/schema shape, NOT metric alignment.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / 'pipeline' / 'data' / 'raw' / 'm00-source-probes'
DEFAULT_LIMIT = 80 * 1024 * 1024
SOURCES = {
    'statcan-income': {
        'publisher': 'Statistics Canada',
        'source_id': 'statcan_98100058',
        'format': 'statcan_zip',
        'filename': '98100058-eng.zip',
        # Official entire-table CSV ZIP route. Size/availability is not guaranteed.
        'url': 'https://www150.statcan.gc.ca/n1/en/tbl/csv/98100058-eng.zip',
        'reference': 'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810005801',
    },
    'cmhc-vancouver': {
        'publisher': 'Canada Mortgage and Housing Corporation',
        'source_id': 'cmhc_rms_2025_vancouver',
        'format': 'xlsx',
        'filename': 'rmr-vancouver-2025-en.xlsx',
        'url': 'https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-data-tables/rental-market/rental-market-report-data-tables/2025/rmr-vancouver-2025-en.xlsx?rev=9c12f2db-c0c8-4d06-83e1-cc3e06da8d36',
        'reference': 'https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres',
    },
    'cmhc-toronto': {
        'publisher': 'Canada Mortgage and Housing Corporation',
        'source_id': 'cmhc_rms_2025_toronto',
        'format': 'xlsx',
        'filename': 'rmr-toronto-2025-en.xlsx',
        'url': 'https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-data-tables/rental-market/rental-market-report-data-tables/2025/rmr-toronto-2025-en.xlsx?rev=f107330e-4620-4462-9027-8c6ff1522f1a',
        'reference': 'https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres',
    },
    'boc-overnight': {
        'publisher': 'Bank of Canada',
        'source_id': 'boc_V39079',
        'format': 'valet_json',
        'filename': 'V39079_2026-10-19_2026-10-22.json',
        'url': 'https://www.bankofcanada.ca/valet/observations/V39079/json?start_date=2026-10-19&end_date=2026-10-22',
        'reference': 'https://www.bankofcanada.ca/valet-api-how-to/',
    },
}


class ProbeError(ValueError):
    """A download or machine-readable source violated the discovery contract."""


def inspect_statcan_zip(path: Path) -> dict:
    try:
        with ZipFile(path) as archive:
            files = [m for m in archive.infolist() if not m.is_dir()]
            csv_files = [m for m in files if m.filename.endswith('.csv') and '98100058' in Path(m.filename).name]
            if not csv_files:
                raise ProbeError('Statistics Canada archive has no 98100058 CSV member')
            member = sorted(csv_files, key=lambda x: x.file_size, reverse=True)[0]
            with archive.open(member) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', errors='replace', newline='') as reader:
                header = next(csv.reader(reader), [])
            if not {'REF_DATE', 'GEO', 'VALUE'}.issubset(header):
                raise ProbeError(f'Statistics Canada CSV missing expected columns: {header[:20]}')
            return {'csv_member': member.filename, 'columns': header,
                    'uncompressed_csv_bytes': member.file_size, 'source_rows_verified': False}
    except (BadZipFile, EOFError) as error:
        raise ProbeError('Statistics Canada file is not a valid CSV ZIP') from error


def inspect_cmhc_xlsx(path: Path) -> dict:
    try:
        with ZipFile(path) as archive:
            if 'xl/workbook.xml' not in archive.namelist() or '[Content_Types].xml' not in archive.namelist():
                raise ProbeError('CMHC response is not an XLSX workbook')
            workbook = archive.getinfo('xl/workbook.xml')
            if workbook.file_size > 2_000_000:
                raise ProbeError('Workbook metadata exceeds safe size limit')
            root = ElementTree.fromstring(archive.read(workbook))
            sheets = [e.attrib['name'] for e in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
            if not sheets or len(set(sheets)) != len(sheets):
                raise ProbeError('CMHC workbook must contain uniquely named worksheets')
            return {'worksheet_names': sheets, 'worksheet_count': len(sheets),
                    'table_cells_verified': False, 'geography_crosswalk_verified': False}
    except (BadZipFile, ElementTree.ParseError) as error:
        raise ProbeError('Invalid CMHC Excel package or workbook XML') from error


def inspect_boc_json(path: Path) -> dict:
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ProbeError('Bounded Valet JSON cannot exceed 5 MiB')
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, UnicodeError) as error:
        raise ProbeError('Bank of Canada response is not valid JSON') from error
    if not isinstance(data, dict) or not isinstance(data.get('seriesDetail'), dict) or 'V39079' not in data['seriesDetail']:
        raise ProbeError('Expected V39079 metadata in seriesDetail')
    entries = data.get('observations')
    if not isinstance(entries, list) or not entries:
        raise ProbeError('Missing bounded V39079 observations')
    dates = []
    for row in entries:
        try:
            date = datetime.strptime(row['d'], '%Y-%m-%d').date()
            number = float(row['V39079']['v'])
            if not math.isfinite(number) or number < -20 or number > 100:
                raise ValueError('Value outside plausible policy-rate bounds')
        except (KeyError, TypeError, ValueError) as error:
            raise ProbeError('Invalid date or numerical value in V39079 observations') from error
        if not ('2026-10-19' <= str(date) <= '2026-10-22'):
            raise ProbeError('Valet data outside requested bounded window')
        dates.append(str(date))
    if dates != sorted(set(dates)):
        raise ProbeError('Valet observations are not uniquely dated and ordered')
    return {'series': 'V39079', 'observed_dates': dates, 'observation_count': len(dates),
            'unit': 'percent', 'geography': 'Canada', 'approved_for_affordability_join': False}


def inspect_file(path: Path, source: str) -> dict:
    if not path.is_file():
        raise ProbeError(f'Input file not found: {path}')
    if path.stat().st_size == 0:
        raise ProbeError('Empty source payload')
    fmt = SOURCES[source]['format']
    details = {
        'statcan_zip': inspect_statcan_zip,
        'xlsx': inspect_cmhc_xlsx,
        'valet_json': inspect_boc_json,
    }[fmt](path)
    digest = hashlib.sha256()
    with path.open('rb') as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'sha256': digest.hexdigest(), 'file_bytes': path.stat().st_size,
            'format': fmt, 'inspection': details, 'schema_inspected': True,
            'semantic_comparability_verified': False}


def fetch_to_file(source: str, dest: Path, limit: int = DEFAULT_LIMIT) -> None:
    """Single bounded HTTPS request; never retain a partial/invalid response."""
    spec = SOURCES[source]
    req = Request(spec['url'], headers={'User-Agent': 'MetroLens-M00-Discovery/0.1 (one-time manual probe)', 'Accept': '*/*'})
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with urlopen(req, timeout=30) as response, tempfile.NamedTemporaryFile('wb', dir=dest.parent, delete=False) as out:
            tmp_path = Path(out.name)
            final_url = urlsplit(response.geturl())
            expected_host = urlsplit(spec['url']).hostname
            if final_url.scheme != 'https' or final_url.hostname != expected_host:
                raise ProbeError('Source redirected away from the pinned official HTTPS host')
            length = response.headers.get('Content-Length')
            if length is not None and int(length) > limit:
                raise ProbeError('Advertised source exceeds the explicit download cap')
            count = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > limit:
                    raise ProbeError(f'Payload exceeded limit of {limit} bytes; request a larger explicit cap')
                out.write(chunk)
        inspect_file(tmp_path, source)
        tmp_path.replace(dest)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def build_manifest(source: str, path: Path) -> dict:
    spec = SOURCES[source]
    return {
        'manifest_schema_version': 1,
        'verification_scope': 'container_and_schema_only',
        'source_id': spec['source_id'], 'publisher': spec['publisher'],
        'official_url': spec['url'], 'landing_page': spec['reference'],
        'inspected_at_utc': datetime.now(timezone.utc).isoformat(),
        'local_file_name': path.name,
        **inspect_file(path, source),
        'production_ready': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=tuple(SOURCES), required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--fetch', action='store_true', help='Opt in to one bounded official network request')
    action.add_argument('--input', type=Path, help='Inspect an already downloaded official file without network')
    parser.add_argument('--max-mib', type=int, default=80, help='Download size cap, default 80 MiB')
    args = parser.parse_args(argv)
    spec = SOURCES[args.source]
    if args.max_mib < 1 or args.max_mib > 250:
        parser.error('--max-mib must be between 1 and 250')
    if not args.fetch and args.input is None:
        print(json.dumps({'source_id': spec['source_id'], 'source_url': spec['url'],
                          'action': 'dry_run_only; specify --fetch or --input to inspect'}, indent=2))
        return 0
    path = args.input if args.input is not None else RAW_DIR / spec['filename']
    try:
        if args.input is not None and path.stat().st_size > args.max_mib * 1024 * 1024:
            raise ProbeError('Local file exceeds the explicit input size cap')
        if args.fetch:
            fetch_to_file(args.source, path, args.max_mib * 1024 * 1024)
        manifest = build_manifest(args.source, path)
        # Report location is always gitignored; never put manifests in source docs.
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        result = RAW_DIR / f'{args.source}-manifest.json'
        result.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'PASS: container/schema validated; no metric joins approved; manifest: {result}')
        return 0
    except (OSError, ProbeError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
