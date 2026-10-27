"""Offline synthetic Canadian Income Survey samples, never official observations."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile

from test_source_probe_audit import SCRIPTS
import sys
sys.path.insert(0, str(SCRIPTS))
import audit_source_probes as audit
import probe_official_sources as probe
import review_cis_income_candidate as cis

HEADER = [
    'REF_DATE', 'GEO', 'DGUID', 'Income concept', 'Economic family type',
    'UOM', 'UOM_ID', 'SCALAR_FACTOR', 'SCALAR_ID', 'VECTOR', 'COORDINATE',
    'VALUE', 'STATUS', 'SYMBOL', 'TERMINATED', 'DECIMALS',
]


def sample_row(year='2024', geo='Vancouver, British Columbia',
               concept='Median after-tax income', family=cis.FAMILY_CANDIDATE,
               value='74800', status='B', dguid='2021S0503933'):
    return [year, geo, dguid, concept, family, '2024 constant dollars', '81',
            'units', '0', 'v1234', '1.2.3', value, status, '', '', '0']


def make_cis(path: Path, rows=None, header=None, metadata=True):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(HEADER if header is None else header)
    for row in rows if rows is not None else [sample_row()]:
        writer.writerow(row)
    with ZipFile(path, 'w') as archive:
        archive.writestr('11100190.csv', output.getvalue())
        if metadata:
            archive.writestr('11100190_MetaData.csv', 'Cube Title,Product Id\nSynthetic candidate,11100190\n')


class CISReviewTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / '11100190-eng.zip'

    def seed(self, **kwargs):
        make_cis(self.path, **kwargs)
        manifest = probe.build_manifest(cis.SOURCE, self.path)
        (self.dir / f'{cis.SOURCE}-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        return manifest

    def test_source_pinned_to_official_host_and_correct_format(self):
        source = probe.SOURCES[cis.SOURCE]
        self.assertTrue(source['url'].startswith('https://www150.statcan.gc.ca/'))
        self.assertEqual(source['source_id'], 'statcan_11100190')
        self.assertEqual(source['format'], 'statcan_standard_zip')
        self.assertTrue(source['optional_discovery'])

    def test_accepts_standard_long_csv_and_metadata(self):
        self.seed()
        info = probe.inspect_statcan_standard_zip(self.path)
        self.assertEqual(info['layout'], 'standard_statcan_long_form')
        self.assertFalse(info['source_rows_verified'])
        self.assertEqual(audit.audit_source(cis.SOURCE, self.dir)['status'], 'file_verified')

    def test_rejects_missing_metadata(self):
        make_cis(self.path, metadata=False)
        with self.assertRaises(probe.ProbeError):
            probe.inspect_statcan_standard_zip(self.path)

    def test_rejects_missing_standard_fields(self):
        make_cis(self.path, header=[h for h in HEADER if h != 'STATUS'])
        with self.assertRaisesRegex(probe.ProbeError, 'STATUS'):
            probe.inspect_statcan_standard_zip(self.path)

    def test_rejects_duplicate_headers(self):
        make_cis(self.path, header=HEADER + ['VALUE'])
        with self.assertRaisesRegex(probe.ProbeError, 'duplicate'):
            probe.inspect_statcan_standard_zip(self.path)

    def test_exact_2023_2024_candidate_rows(self):
        self.seed(rows=[sample_row('2023', value='70000'), sample_row('2024')])
        result = cis.build_review(self.dir)
        self.assertEqual(result['status'], 'candidate_rows_sampled')
        self.assertEqual([r['ref_date'] for r in result['sampled_rows']], ['2023', '2024'])
        self.assertFalse(result['metric_comparability_approved'])
        self.assertFalse(result['publication_approved'])
        self.assertFalse(result['statistical_populations_comparable'])
        self.assertIsNone(result['rent_to_income_ratio'])
        self.assertTrue(all(not r['candidate_observation_usable'] for r in result['sampled_rows']))

    def test_keeps_status_and_units_as_unreviewed_raw_fields(self):
        self.seed(rows=[sample_row(status='F', value='')])
        result = cis.build_review(self.dir)['sampled_rows'][0]
        self.assertEqual(result['status_code'], 'F')
        self.assertEqual(result['raw_value'], '')
        self.assertEqual(result['unit'], '2024 constant dollars')
        self.assertFalse(result['candidate_observation_usable'])

    def test_excludes_wrong_year_income_and_family(self):
        self.seed(rows=[sample_row('2022'), sample_row(concept='Mean after-tax income'),
                        sample_row(family='Economic families'), sample_row(geo='Toronto, Ontario'),
                        sample_row('2024', value='77777')])
        result = cis.build_review(self.dir)
        self.assertEqual(len(result['sampled_rows']), 1)
        self.assertEqual(result['sampled_rows'][0]['raw_value'], '77777')

    def test_does_not_confuse_city_with_cma_approval(self):
        self.seed(rows=[sample_row(geo='Vancouver, British Columbia', dguid='other')])
        result = cis.build_review(self.dir)
        self.assertEqual(result['sampled_rows'][0]['dguid'], 'other')
        self.assertFalse(result['geography_crosswalk_approved'])

    def test_no_exact_sample_is_explicit(self):
        self.seed(rows=[sample_row(concept='Median total income')])
        result = cis.build_review(self.dir)
        self.assertEqual(result['status'], 'no_exact_candidate_in_scan')
        self.assertIn('Median total income', result['candidate_income_concepts_seen'])

    def test_malformed_nonblank_row_fails_closed(self):
        self.seed(rows=[sample_row()[:-2]])
        with self.assertRaisesRegex(cis.CandidateReviewError, 'expected 16 fields'):
            cis.build_review(self.dir)

    def test_trailing_blank_rows_allowed_but_nonblank_after_rejected(self):
        self.seed(rows=[sample_row(), [], []])
        result = cis.inspect_candidates(self.path, limit=3)
        self.assertEqual(result['blank_records_skipped'], 2)
        make_cis(self.path, rows=[[], sample_row()])
        with self.assertRaisesRegex(cis.CandidateReviewError, 'Nonblank'):
            cis.inspect_candidates(self.path)

    def test_limits_fail_closed(self):
        self.seed()
        for lim in (0, 21, True):
            with self.subTest(lim=lim):
                with self.assertRaises(cis.CandidateReviewError):
                    cis.inspect_candidates(self.path, limit=lim)
        with self.assertRaises(cis.CandidateReviewError):
            cis.inspect_candidates(self.path, max_scan=2_000_001)

    def test_scan_cap_and_sample_cap(self):
        self.seed(rows=[sample_row('2023'), sample_row('2024')])
        self.assertTrue(cis.inspect_candidates(self.path, limit=1)['sample_limit_reached'])
        result = cis.inspect_candidates(self.path, max_scan=1)
        self.assertTrue(result['scan_cap_reached'])
        self.assertEqual(len(result['sampled_rows']), 1)

    def test_missing_manifest_blocks(self):
        result = cis.build_review(self.dir)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['file_audit_status'], 'missing_manifest')

    def test_corrupted_bytes_cannot_pass_audit(self):
        self.seed()
        with self.path.open('ab') as out:
            out.write(b'tamper')
        result = cis.build_review(self.dir)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['file_audit_status'], 'invalid')

    def test_existing_audit_all_ignores_optional_candidate(self):
        self.seed()
        report = audit.build_report(self.dir)
        self.assertEqual(len(report['sources']), 4)
        self.assertNotIn(cis.SOURCE, [entry['source'] for entry in report['sources']])
        self.assertEqual(audit.audit_source(cis.SOURCE, self.dir)['status'], 'file_verified')

    def test_review_sample_limit_cannot_claim_full_data(self):
        self.seed(rows=[sample_row('2023'), sample_row('2024'), sample_row('2024')])
        result = cis.build_review(self.dir, limit=2)
        self.assertTrue(result['sample_limit_reached'])
        self.assertFalse(result['publication_approved'])

    def test_real_network_is_not_used_by_review(self):
        self.seed()
        with mock.patch.object(probe, 'urlopen', side_effect=AssertionError('network disallowed')):
            result = cis.build_review(self.dir)
        self.assertEqual(result['status'], 'candidate_rows_sampled')


if __name__ == '__main__':
    unittest.main()
