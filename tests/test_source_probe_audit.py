"""Offline evidence checks. Synthetic archives are not official publisher data."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_official_probes import make_boc, make_cmhc, make_statcan

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
import sys
sys.path.insert(0, str(SCRIPTS))
import audit_source_probes as audit
import probe_official_sources as probe


class ProbeAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raw_dir = Path(self.temp.name)

    def seed(self, key):
        filename = probe.SOURCES[key]['filename']
        path = self.raw_dir / filename
        if key.startswith('statcan'):
            make_statcan(path)
        elif key.startswith('cmhc'):
            make_cmhc(path)
        else:
            make_boc(path)
        manifest = probe.build_manifest(key, path)
        manifest_file = self.raw_dir / f'{key}-manifest.json'
        manifest_file.write_text(json.dumps(manifest), encoding='utf-8')
        return path, manifest_file, manifest

    def test_missing_manifest_is_not_success(self):
        self.assertEqual(audit.audit_source('statcan-income', self.raw_dir)['status'], 'missing_manifest')

    def test_boc_verified_is_not_approved_for_join(self):
        path, _, manifest = self.seed('boc-overnight')
        record = audit.audit_source('boc-overnight', self.raw_dir)
        self.assertEqual(record['status'], 'file_verified')
        self.assertEqual(record['sha256'], manifest['sha256'])
        self.assertEqual(record['file_bytes'], path.stat().st_size)
        self.assertFalse(record['comparison_approved'])

    def test_wide_census_and_cmhc_containers_verified(self):
        for key in ('statcan-income', 'cmhc-vancouver', 'cmhc-toronto'):
            with self.subTest(key=key):
                self.seed(key)
                self.assertEqual(audit.audit_source(key, self.raw_dir)['status'], 'file_verified')

    def test_report_all_verified_still_not_comparable(self):
        for key, spec in probe.SOURCES.items():
            if not spec.get('optional_discovery'):
                self.seed(key)
        report = audit.build_report(self.raw_dir)
        self.assertTrue(report['all_files_verified'])
        self.assertEqual(len(report['sources']), 4)
        self.assertFalse(report['metric_comparability_approved'])

    def test_partial_missing_evidence_has_status(self):
        self.seed('statcan-income')
        report = audit.build_report(self.raw_dir)
        self.assertFalse(report['all_files_verified'])
        self.assertEqual(sum(item['status'] == 'missing_manifest' for item in report['sources']), 3)

    def test_changed_file_is_invalid(self):
        path, _, _ = self.seed('boc-overnight')
        data = json.loads(path.read_text())
        data['observations'][0]['V39079']['v'] = '9.99'
        path.write_text(json.dumps(data), encoding='utf-8')
        record = audit.audit_source('boc-overnight', self.raw_dir)
        self.assertEqual(record['status'], 'invalid')
        self.assertIn('sha256', record['reason'])

    def test_changed_inspection_is_invalid(self):
        _, file, manifest = self.seed('statcan-income')
        manifest['inspection']['measure_column_indices']['median_total_income_2020'] = 0
        file.write_text(json.dumps(manifest), encoding='utf-8')
        record = audit.audit_source('statcan-income', self.raw_dir)
        self.assertEqual(record['status'], 'invalid')
        self.assertIn('inspection', record['reason'])

    def test_modified_origin_cannot_be_approved(self):
        _, file, manifest = self.seed('cmhc-toronto')
        manifest['official_url'] = 'https://example.com/publisher.xlsx'
        file.write_text(json.dumps(manifest), encoding='utf-8')
        self.assertEqual(audit.audit_source('cmhc-toronto', self.raw_dir)['status'], 'invalid')

    def test_prod_ready_true_is_rejected(self):
        _, file, manifest = self.seed('cmhc-vancouver')
        manifest['production_ready'] = True
        file.write_text(json.dumps(manifest), encoding='utf-8')
        self.assertEqual(audit.audit_source('cmhc-vancouver', self.raw_dir)['status'], 'invalid')

    def test_missing_original_is_manifest_only(self):
        path, _, _ = self.seed('boc-overnight')
        path.unlink()
        self.assertEqual(audit.audit_source('boc-overnight', self.raw_dir)['status'], 'manifest_only')

    def test_rejects_traversal_and_windows_separators(self):
        for filename in ('../outside.json', '..\\outside.json', '/etc/passwd'):
            with self.subTest(filename=filename):
                _, file, manifest = self.seed('boc-overnight')
                manifest['local_file_name'] = filename
                file.write_text(json.dumps(manifest), encoding='utf-8')
                self.assertEqual(audit.audit_source('boc-overnight', self.raw_dir)['status'], 'invalid')

    def test_rejects_symlinked_source_without_os_privileges(self):
        """Always exercise the audit guard, even if Windows forbids symlinks."""
        path, _, _ = self.seed('statcan-income')
        # Only the source file appears to be a symlink. In particular, the
        # manifest must still appear regular so we reach the source guard.
        with mock.patch.object(
            Path, 'is_symlink', autospec=True,
            side_effect=lambda candidate: candidate == path,
        ):
            record = audit.audit_source('statcan-income', self.raw_dir)
        self.assertEqual(record['status'], 'invalid')
        self.assertIn('symlink', record['reason'])

    def test_rejects_real_symlinked_source_when_supported(self):
        """Integration check: Windows can require Developer Mode or privilege."""
        path, _, _ = self.seed('statcan-income')
        other = self.raw_dir / 'elsewhere.bin'
        path.rename(other)
        try:
            path.symlink_to(other)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                self.skipTest('Windows symlink creation requires additional privileges')
            raise
        record = audit.audit_source('statcan-income', self.raw_dir)
        self.assertEqual(record['status'], 'invalid')
        self.assertIn('symlink', record['reason'])

    def test_invalid_json_manifest_does_not_crash(self):
        self.seed('boc-overnight')
        (self.raw_dir / 'boc-overnight-manifest.json').write_text('{not-json', encoding='utf-8')
        self.assertEqual(audit.audit_source('boc-overnight', self.raw_dir)['status'], 'invalid')

    def test_boolean_file_bytes_is_rejected(self):
        _, file, manifest = self.seed('boc-overnight')
        manifest['file_bytes'] = True
        file.write_text(json.dumps(manifest), encoding='utf-8')
        self.assertEqual(audit.audit_source('boc-overnight', self.raw_dir)['status'], 'invalid')

    def test_cli_exit_codes(self):
        self.assertEqual(audit.main(['--raw-dir', str(self.raw_dir), '--source', 'boc-overnight']), 1)
        self.seed('boc-overnight')
        self.assertEqual(audit.main(['--raw-dir', str(self.raw_dir), '--source', 'boc-overnight']), 0)


if __name__ == '__main__':
    unittest.main()
