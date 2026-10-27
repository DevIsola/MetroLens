#!/usr/bin/env python3
"""Offline evidence audit for M00 discovery probes; never approves analytics joins.

Reopens local publisher files, recomputes hashes and revalidates their probe
schema. A passing result is evidence of local file consistency, not source
identity attestation, statistical comparability, or production readiness.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from probe_official_sources import ProbeError, RAW_DIR, SOURCES, inspect_file

MAX_MANIFEST_BYTES = 1_048_576


def _validate_manifest(source: str, manifest: object) -> dict:
    if not isinstance(manifest, dict):
        raise ValueError('Manifest root must be an object')
    expected = SOURCES[source]
    fields = {
        'manifest_schema_version': 1,
        'verification_scope': 'container_and_schema_only',
        'source_id': expected['source_id'],
        'publisher': expected['publisher'],
        'official_url': expected['url'],
        'landing_page': expected['reference'],
        'format': expected['format'],
        'schema_inspected': True,
        'production_ready': False,
        'semantic_comparability_verified': False,
    }
    for field, value in fields.items():
        if type(manifest.get(field)) is not type(value) or manifest[field] != value:
            raise ValueError(f'Invalid manifest field: {field}')
    filename = manifest.get('local_file_name')
    if (not isinstance(filename, str) or not filename or filename in {'.', '..'}
            or '/' in filename or '\\' in filename or Path(filename).name != filename):
        raise ValueError('Unsafe local_file_name in manifest')
    if not isinstance(manifest.get('inspection'), dict):
        raise ValueError('Missing source inspection metadata')
    timestamp = manifest.get('inspected_at_utc')
    try:
        instant = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError) as error:
        raise ValueError('Invalid inspection timestamp') from error
    if instant.tzinfo is None or instant.utcoffset().total_seconds() != 0:
        raise ValueError('Inspection timestamp must be UTC with an explicit offset')
    digest = manifest.get('sha256')
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Missing or malformed SHA-256 checksum')
    size = manifest.get('file_bytes')
    if type(size) is not int or size <= 0:
        raise ValueError('Invalid source file byte count')
    return manifest


def audit_source(source: str, raw_dir: Path = RAW_DIR) -> dict:
    """Audit one pinned source, returning an explicit evidence state."""
    if source not in SOURCES:
        raise ValueError(f'Unknown source key: {source}')
    base = {'source': source, 'source_id': SOURCES[source]['source_id'],
            'comparison_approved': False}
    manifest_path = raw_dir / f'{source}-manifest.json'
    if not manifest_path.is_file():
        return {**base, 'status': 'missing_manifest', 'reason': 'Run the opt-in publisher probe first'}
    try:
        if manifest_path.is_symlink() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError('Manifest must be a regular JSON file under 1 MiB')
        manifest = _validate_manifest(source, json.loads(manifest_path.read_text(encoding='utf-8')))
        filename = manifest['local_file_name']
        source_path = raw_dir / filename
        if not source_path.exists():
            return {**base, 'status': 'manifest_only',
                    'reason': 'Original file not in probe directory; a --input file may be stored elsewhere'}
        if source_path.is_symlink() or not source_path.is_file():
            raise ValueError('Source file must be a regular file, not a symlink')
        # Also re-inspect file contents; checking only the self-reported manifest
        # hash would allow silently corrupt or replaced source bytes.
        observed = inspect_file(source_path, source)
        for field in ('sha256', 'file_bytes', 'format', 'schema_inspected',
                      'semantic_comparability_verified', 'inspection'):
            if manifest[field] != observed[field]:
                raise ValueError(f'File no longer matches manifest: {field}')
        return {**base, 'status': 'file_verified', 'sha256': observed['sha256'],
                'file_bytes': observed['file_bytes'],
                'reason': 'Byte consistency and container/schema checks only; statistical joins remain unverified'}
    except (OSError, UnicodeError, ValueError, ProbeError, TypeError, KeyError) as error:
        return {**base, 'status': 'invalid', 'reason': str(error)}


def build_report(raw_dir: Path = RAW_DIR, selected: tuple[str, ...] | None = None) -> dict:
    sources = selected if selected is not None else tuple(
        key for key, spec in SOURCES.items() if not spec.get('optional_discovery')
    )
    results = [audit_source(name, raw_dir) for name in sources]
    return {
        'report_schema_version': 1,
        'milestone': 'M00-T02',
        'sources': results,
        'all_files_verified': bool(results) and all(r['status'] == 'file_verified' for r in results),
        'metric_comparability_approved': False,
        'remaining_review_gates': [
            'Inspect actual income and rental observations and suppression flags',
            'Document compatible source geography IDs and CMA boundary vintages',
            'Align income/rent reference periods and statistical populations',
            'Approve publisher attribution and reuse obligations for derived products',
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=('all', *SOURCES), default='all')
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR,
                        help='Directory holding locally downloaded files and manifests (default gitignored raw/)')
    args = parser.parse_args(argv)
    selection = None if args.source == 'all' else (args.source,)
    report = build_report(args.raw_dir, selection)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if any(result['status'] == 'invalid' for result in report['sources']):
        return 2
    return 0 if report['all_files_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
