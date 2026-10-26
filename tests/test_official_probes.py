"""Hermetic synthetic-format contracts; these are NOT publisher extracts."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'probe_official_sources.py'
spec = importlib.util.spec_from_file_location('official_probe', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

XLSX_XML = (b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b'<sheets><sheet name="1.1.1" sheetId="1"/></sheets></workbook>')


def make_statcan(path, *, columns='REF_DATE,GEO,VALUE'):
    with ZipFile(path, 'w') as z:
        z.writestr('98100058.csv', columns + '\n2021,"Vancouver",100\n')


def make_cmhc(path, *, names_xml=XLSX_XML):
    with ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('xl/workbook.xml', names_xml)


def make_boc(path, *, rows=None):
    payload = {'seriesDetail': {'V39079': {'label': 'Target for the overnight rate'}},
               'observations': rows if rows is not None else [
                   {'d': '2026-10-19', 'V39079': {'v': '2.25'}},
                   {'d': '2026-10-20', 'V39079': {'v': '2.25'}}]}
    path.write_text(json.dumps(payload), encoding='utf-8')


class OfficialProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'synthetic.bin'

    def test_synthetic_statcan_csv_zip_schema(self):
        make_statcan(self.path)
        report = probe.inspect_file(self.path, 'statcan-income')
        self.assertEqual(report['inspection']['columns'], ['REF_DATE', 'GEO', 'VALUE'])
        self.assertEqual(len(report['sha256']), 64)
        self.assertFalse(report['semantic_comparability_verified'])

    def test_statcan_rejects_bad_header(self):
        make_statcan(self.path, columns='REF_DATE,GEO,INCORRECT')
        with self.assertRaisesRegex(probe.ProbeError, 'expected columns'):
            probe.inspect_file(self.path, 'statcan-income')

    def test_statcan_rejects_foreign_dataset_member(self):
        with ZipFile(self.path, 'w') as z:
            z.writestr('12345678.csv', 'REF_DATE,GEO,VALUE\n')
        with self.assertRaisesRegex(probe.ProbeError, '98100058'):
            probe.inspect_file(self.path, 'statcan-income')

    def test_cmhc_workbook_sheet_inspection(self):
        make_cmhc(self.path)
        report = probe.inspect_file(self.path, 'cmhc-vancouver')
        self.assertEqual(report['inspection']['worksheet_names'], ['1.1.1'])
        self.assertFalse(report['inspection']['table_cells_verified'])
        self.assertFalse(report['inspection']['geography_crosswalk_verified'])

    def test_cmhc_requires_workbook_xml(self):
        with ZipFile(self.path, 'w') as z:
            z.writestr('unrelated.txt', 'not a workbook')
        with self.assertRaisesRegex(probe.ProbeError, 'not an XLSX'):
            probe.inspect_file(self.path, 'cmhc-toronto')

    def test_cmhc_rejects_duplicate_sheet_names(self):
        xml = XLSX_XML.replace(b'</sheets>', b'<sheet name="1.1.1" sheetId="2"/></sheets>')
        make_cmhc(self.path, names_xml=xml)
        with self.assertRaisesRegex(probe.ProbeError, 'uniquely named'):
            probe.inspect_file(self.path, 'cmhc-vancouver')

    def test_boc_date_and_numerical_schema(self):
        make_boc(self.path)
        report = probe.inspect_file(self.path, 'boc-overnight')
        self.assertEqual(report['inspection']['observation_count'], 2)
        self.assertFalse(report['inspection']['approved_for_affordability_join'])

    def test_boc_rejects_other_series(self):
        make_boc(self.path)
        data = json.loads(self.path.read_text())
        data['seriesDetail'] = {'WRONG': {}}
        self.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(probe.ProbeError, 'V39079 metadata'):
            probe.inspect_file(self.path, 'boc-overnight')

    def test_boc_rejects_missing_dates(self):
        make_boc(self.path, rows=[{'d': '2026-10-19'}])
        with self.assertRaisesRegex(probe.ProbeError, 'Invalid date'):
            probe.inspect_file(self.path, 'boc-overnight')

    def test_boc_rejects_out_of_range_date(self):
        make_boc(self.path, rows=[{'d': '2026-10-23', 'V39079': {'v': '2.25'}}])
        with self.assertRaisesRegex(probe.ProbeError, 'outside requested'):
            probe.inspect_file(self.path, 'boc-overnight')

    def test_boc_rejects_nonfinite_rate(self):
        make_boc(self.path, rows=[{'d': '2026-10-20', 'V39079': {'v': 'NaN'}}])
        with self.assertRaisesRegex(probe.ProbeError, 'Invalid date'):
            probe.inspect_file(self.path, 'boc-overnight')

    def test_boc_rejects_duplicate_observations(self):
        make_boc(self.path, rows=[{'d': '2026-10-20', 'V39079': {'v': '2.25'}}] * 2)
        with self.assertRaisesRegex(probe.ProbeError, 'uniquely dated'):
            probe.inspect_file(self.path, 'boc-overnight')

    def test_dry_run_makes_no_network_call_or_manifest(self):
        self.assertEqual(probe.main(['--source', 'boc-overnight']), 0)

    def test_manifest_explicitly_rejects_production_status(self):
        make_boc(self.path)
        manifest = probe.build_manifest('boc-overnight', self.path)
        self.assertEqual(manifest['verification_scope'], 'container_and_schema_only')
        self.assertFalse(manifest['production_ready'])
        self.assertIn('inspected_at_utc', manifest)


if __name__ == '__main__':
    unittest.main()
