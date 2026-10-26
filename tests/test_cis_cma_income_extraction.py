"""Independent synthetic tests; never imply source-publisher row acceptance."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from test_cis_income_candidate import make_cis, sample_row, HEADER
from test_source_probe_audit import SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import extract_cis_cma_income as extractor
import probe_official_sources as probe


def reviewed(year: str, **changes):
    fields = sample_row(year, value=str(extractor.REVIEWED_VALUES[year]), status='A')
    modifications = {
        'UOM_ID': '455', 'COORDINATE': '21.12.1',
        'VECTOR': 'v96416811',
    }
    modifications.update(changes)
    for name, value in modifications.items():
        fields[HEADER.index(name)] = value
    return fields


class CISExtractorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.path = self.folder / '11100190-eng.zip'

    def seed(self, rows=None):
        make_cis(self.path, rows=rows if rows is not None else [reviewed('2023'), reviewed('2024')])
        manifest = probe.build_manifest(extractor.SOURCE, self.path)
        (self.folder / f'{extractor.SOURCE}-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        return manifest

    def test_full_scan_preserves_evidence_and_2024_price_basis(self):
        self.seed(rows=[reviewed('2024'), sample_row('2022', value='67000'), reviewed('2023')])
        result = extractor.extract_rows(self.path)
        self.assertEqual(result['data_rows_scanned'], 3)
        self.assertEqual(result['dguid'], '2021S0503933')
        self.assertEqual([x['value'] for x in result['observations']], [77700, 78900])
        self.assertEqual([x['reference_period'] for x in result['observations']], ['2023', '2024'])
        self.assertEqual([x['source_coordinate'] for x in result['observations']], ['21.12.1'] * 2)
        self.assertTrue(result['full_source_scanned'])
        self.assertEqual(result['price_basis'], '2024_constant_dollars')
        self.assertTrue(all(x['status'] == 'observed_candidate_only' for x in result['observations']))
        self.assertTrue(all(not x['approved_for_affordability_join'] for x in result['observations']))

    def test_audit_and_hash_gate_allow_exact_reviewed_version_only(self):
        manifest = self.seed()
        report = extractor.extract_verified(self.folder, reviewed_sha256=manifest['sha256'])
        self.assertEqual(report['status'], 'candidate_extracted_for_review')
        self.assertFalse(report['metric_comparability_approved'])
        self.assertFalse(report['publication_approved'])
        self.assertFalse(report['census_private_households_equivalent'])
        self.assertIsNone(report['rent_to_income_ratio'])
        self.assertEqual(report['source_sha256'], manifest['sha256'])

    def test_expected_official_sha_pinned(self):
        self.assertEqual(extractor.REVIEWED_SHA256, '03677bae1fd1cc412c6563c0b33251d2eb4cf3837712ee7c92aa87d7bec782e4')
        self.seed()
        self.assertEqual(extractor.extract_verified(self.folder)['status'], 'blocked')

    def test_missing_source_manifest_blocks(self):
        report = extractor.extract_verified(self.folder)
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['file_audit_status'], 'missing_manifest')

    def test_corrupted_source_does_not_extract(self):
        manifest = self.seed()
        self.path.write_bytes(self.path.read_bytes() + b'tampered')
        self.assertEqual(extractor.extract_verified(self.folder, reviewed_sha256=manifest['sha256'])['status'], 'blocked')

    def test_non_cma_subgroup_not_an_aggregate(self):
        self.seed(rows=[reviewed('2023', GEO='Toronto, Ontario'), reviewed('2024')])
        with self.assertRaisesRegex(extractor.CISExtractionError, 'Missing reviewed.*2023'):
            extractor.extract_rows(self.path)

    def test_bad_dguid_rejected(self):
        self.seed(rows=[reviewed('2023', DGUID='wrong'), reviewed('2024')])
        with self.assertRaisesRegex(extractor.CISExtractionError, 'DGUID'):
            extractor.extract_rows(self.path)

    def test_duplicate_candidate_rejected_even_late(self):
        self.seed(rows=[reviewed('2023'), reviewed('2024'), reviewed('2023')])
        with self.assertRaisesRegex(extractor.CISExtractionError, 'Duplicate'):
            extractor.extract_rows(self.path)

    def test_missing_year_rejected(self):
        self.seed(rows=[reviewed('2023')])
        with self.assertRaisesRegex(extractor.CISExtractionError, '2024'):
            extractor.extract_rows(self.path)

    def test_suppressed_or_invalid_value_rejected(self):
        for bad in ('', '0', '..', 'NaN', '77,700', '-1'):
            with self.subTest(value=bad):
                self.seed(rows=[reviewed('2023', VALUE=bad), reviewed('2024')])
                with self.assertRaisesRegex(extractor.CISExtractionError, 'income value'):
                    extractor.extract_rows(self.path)

    def test_quality_and_revision_flags_must_match_review(self):
        for field, value in [('STATUS', 'F'), ('STATUS', 'B'), ('SYMBOL', 'r'), ('TERMINATED', 't')]:
            with self.subTest(field=field, value=value):
                self.seed(rows=[reviewed('2023', **{field: value}), reviewed('2024')])
                with self.assertRaisesRegex(extractor.CISExtractionError, field):
                    extractor.extract_rows(self.path)

    def test_units_and_vector_must_match(self):
        for field, value in [('UOM', 'current dollars'), ('UOM_ID', '99'),
                             ('SCALAR_FACTOR', 'thousands'), ('VECTOR', 'v1'),
                             ('COORDINATE', '21.11.1')]:
            with self.subTest(field=field):
                self.seed(rows=[reviewed('2023', **{field: value}), reviewed('2024')])
                with self.assertRaisesRegex(extractor.CISExtractionError, field):
                    extractor.extract_rows(self.path)

    def test_change_in_observation_requires_new_review(self):
        self.seed(rows=[reviewed('2023', VALUE='77701'), reviewed('2024')])
        with self.assertRaisesRegex(extractor.CISExtractionError, 'differs from reviewed'):
            extractor.extract_rows(self.path)

    def test_trailing_blank_records_handled_but_nonblank_after_rejected(self):
        self.seed(rows=[reviewed('2023'), reviewed('2024'), [], []])
        self.assertEqual(extractor.extract_rows(self.path)['trailing_blank_rows_skipped'], 2)
        self.seed(rows=[reviewed('2023'), [], reviewed('2024')])
        with self.assertRaisesRegex(extractor.CISExtractionError, 'Nonblank'):
            extractor.extract_rows(self.path)

    def test_malformed_width_never_ignored(self):
        self.seed(rows=[reviewed('2023'), reviewed('2024')[:-2]])
        with self.assertRaisesRegex(extractor.CISExtractionError, 'expected 16'):
            extractor.extract_rows(self.path)

    def test_full_source_limit_fails_closed(self):
        self.seed(rows=[reviewed('2023'), reviewed('2024'), sample_row('2022')])
        with mock.patch.object(extractor, 'MAX_CSV_ROWS', 2):
            with self.assertRaisesRegex(extractor.CISExtractionError, 'bounded full scan'):
                extractor.extract_rows(self.path)

    def test_source_change_mid_extraction_rejected(self):
        manifest = self.seed()
        with mock.patch.object(extractor, 'audit_source', side_effect=[
            {'status': 'file_verified', 'sha256': manifest['sha256']},
            {'status': 'invalid', 'reason': 'Changed'},
        ]):
            with self.assertRaisesRegex(extractor.CISExtractionError, 'changed'):
                extractor.extract_verified(self.folder, reviewed_sha256=manifest['sha256'])


if __name__ == '__main__':
    unittest.main()
