#!/usr/bin/env python3
"""Offline, audited sample of 2023/2024 Canadian Income Survey CMA records.

Discovery only: economic families and persons not in economic families are NOT
private households, and 2024 income is NOT a same-period 2025 rent measure.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

from audit_source_probes import audit_source
from probe_official_sources import RAW_DIR, ProbeError, SOURCES, inspect_statcan_standard_zip

SOURCE = 'statcan-cis-income'
REVIEW_YEARS = ('2023', '2024')
FAMILY_CANDIDATE = 'Economic families and persons not in an economic family'
INCOME_CANDIDATE = 'Median after-tax income'
MAX_LIMIT = 20
MAX_SCAN = 2_000_000
GEO_MATCH = re.compile(r'^Vancouver(?:\s*\(CMA\))?(?:\s*,|\s*$)', re.IGNORECASE)


class CandidateReviewError(ValueError):
    """Untrusted source records or an unsupported schema were encountered."""


def _candidate(row: dict) -> bool:
    return (row['REF_DATE'] in REVIEW_YEARS and
            bool(GEO_MATCH.match(row['GEO'].strip())) and
            row['Income concept'].strip().casefold() == INCOME_CANDIDATE.casefold() and
            row['Economic family type'].strip().casefold() == FAMILY_CANDIDATE.casefold())


def inspect_candidates(path: Path, *, limit: int = 12, max_scan: int = MAX_SCAN) -> dict:
    """Read a bounded subset without trusting labels as official CMA crosswalks."""
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise CandidateReviewError('limit must be 1 to 20')
    if type(max_scan) is not int or not 1 <= max_scan <= MAX_SCAN:
        raise CandidateReviewError('max_scan must be 1 to 2000000')
    inspection = inspect_statcan_standard_zip(path)
    header = inspection['columns']
    hits = []
    scanned = 0
    blanks = 0
    geo_candidates = set()
    concepts = set()
    family_types = set()
    with ZipFile(path) as archive, archive.open(inspection['csv_member']) as binary:
        with io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as stream:
            reader = csv.reader(stream)
            if next(reader, None) != header:
                raise CandidateReviewError('CIS header changed during inspection')
            for fields in reader:
                scanned += 1
                if not fields or all(not cell.strip() for cell in fields):
                    blanks += 1
                    if scanned >= max_scan:
                        break
                    continue
                if blanks:
                    raise CandidateReviewError('Nonblank row follows blank CSV record')
                if len(fields) != len(header):
                    raise CandidateReviewError(f'Malformed CIS row {scanned}: expected {len(header)} fields, got {len(fields)}')
                row = dict(zip(header, fields))
                if GEO_MATCH.match(row['GEO'].strip()):
                    if len(geo_candidates) < 12:
                        geo_candidates.add(row['GEO'][:160])
                    if row['REF_DATE'] in REVIEW_YEARS:
                        if len(concepts) < 18:
                            concepts.add(row['Income concept'][:160])
                        if len(family_types) < 18:
                            family_types.add(row['Economic family type'][:160])
                if _candidate(row):
                    hits.append({
                        'ref_date': row['REF_DATE'], 'geo': row['GEO'],
                        'dguid': row['DGUID'], 'income_concept': row['Income concept'],
                        'economic_family_type': row['Economic family type'],
                        'unit': row['UOM'], 'unit_id': row['UOM_ID'],
                        'scalar_factor': row['SCALAR_FACTOR'], 'scalar_id': row['SCALAR_ID'],
                        'raw_value': row['VALUE'], 'status_code': row['STATUS'],
                        'symbol': row['SYMBOL'], 'terminated': row['TERMINATED'],
                        'coordinate': row['COORDINATE'], 'vector': row['VECTOR'],
                        'candidate_observation_usable': False,
                    })
                    if len(hits) >= limit:
                        break
                if scanned >= max_scan:
                    break
    return {
        'status': 'candidate_rows_sampled' if hits else 'no_exact_candidate_in_scan',
        'candidate_geography_labels': sorted(geo_candidates),
        'candidate_income_concepts_seen': sorted(concepts),
        'candidate_economic_family_types_seen': sorted(family_types),
        'sampled_rows': hits, 'matching_rows_seen': len(hits),
        'scanned_rows': scanned, 'blank_records_skipped': blanks,
        'scan_cap_reached': scanned >= max_scan,
        'sample_limit_reached': len(hits) >= limit,
    }


def build_review(raw_dir: Path, *, limit: int = 12, max_scan: int = MAX_SCAN) -> dict:
    base = {
        'schema_version': 1, 'milestone': 'M00-T02', 'source': SOURCE,
        'source_id': SOURCES[SOURCE]['source_id'],
        'candidate_only': True, 'census_private_households_equivalent': False,
        'geography_crosswalk_approved': False, 'reference_periods_aligned': False,
        'statistical_populations_comparable': False, 'metric_comparability_approved': False,
        'publication_approved': False, 'production_ready': False, 'rent_to_income_ratio': None,
        'review_warning': ('Canadian Income Survey economic-family units are not Census private households; '
                           '2024 annual estimates cannot be treated as 2025 rents. '
                           'Confirm quality symbols, DGUID vintage and constant-dollar basis.'),
    }
    audit = audit_source(SOURCE, raw_dir)
    if audit['status'] != 'file_verified':
        return {**base, 'status': 'blocked', 'file_audit_status': audit['status'],
                'reason': audit['reason']}
    manifest_path = raw_dir / f'{SOURCE}-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    path = raw_dir / manifest['local_file_name']
    result = inspect_candidates(path, limit=limit, max_scan=max_scan)
    if audit_source(SOURCE, raw_dir)['status'] != 'file_verified':
        raise CandidateReviewError('CIS file changed during sample review')
    return {**base, 'file_audit_status': 'file_verified', 'sha256': audit['sha256'], **result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    parser.add_argument('--limit', type=int, default=12)
    parser.add_argument('--max-scan', type=int, default=MAX_SCAN)
    args = parser.parse_args(argv)
    try:
        result = build_review(args.raw_dir, limit=args.limit, max_scan=args.max_scan)
    except (CandidateReviewError, ProbeError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'invalid', 'reason': str(error),
                          'metric_comparability_approved': False,
                          'publication_approved': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['status'] == 'candidate_rows_sampled' else 1


if __name__ == '__main__':
    raise SystemExit(main())
