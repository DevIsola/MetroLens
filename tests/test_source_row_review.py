"""Hermetic source-row reconnaissance fixtures: no official data or network calls."""

import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parent / 'tests'))
import probe_official_sources as probe
import review_source_rows as review
from test_official_probes import CENSUS_HEADER, make_boc


def make_income_file(path, *, bad_row=False):
    text = io.StringIO(newline='')
    writer = csv.writer(text)
    writer.writerow(CENSUS_HEADER)
    def row(city, dguid, income, symbol=''):
        return ['2021', city, dguid, 'Total - Household size', 'Total - Household type', '1.2',
                '100', '', '120', '', income, symbol, '50000', '', '61000', '', '42000', '']
    writer.writerow(row('Ottawa (CMA)', '2021S0503505', '94000'))
    writer.writerow(row('Vancouver (CMA)', '2021S0503933', '99000', 'x'))
    writer.writerow(row('Vancouver (CMA)', '2021S0503933', '95000'))
    if bad_row:
        writer.writerow(['2021', 'Vancouver (CMA)'])
    with ZipFile(path, 'w') as archive:
        archive.writestr('98100058.csv', text.getvalue())


def make_xlsx(path, *, relationship='worksheets/sheet1.xml', malformed_shared=False):
    wb = ('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="1.1.1" sheetId="1" r:id="rId7"/></sheets></workbook>')
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{relationship}"/>'
            '</Relationships>')
    sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>Header B</t></is></c></row>'
             '<row r="2"><c r="A2"><v>2400</v></c><c r="B2" t="s"><v>1</v></c></row></sheetData></worksheet>')
    strings = ('<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
               '<si><t>Unit mix</t></si>' + ('' if malformed_shared else '<si><t>Vancouver</t></si>') + '</sst>')
    with ZipFile(path, 'w') as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('xl/workbook.xml', wb)
        archive.writestr('xl/_rels/workbook.xml.rels', rels)
        archive.writestr('xl/worksheets/sheet1.xml', sheet)
        archive.writestr('xl/sharedStrings.xml', strings)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def seed(self, source, maker, **kwargs):
        path = self.root / probe.SOURCES[source]['filename']
        maker(path, **kwargs)
        manifest = probe.build_manifest(source, path)
        (self.root / f'{source}-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        return path

    def view(self, source, **kwargs):
        return review.build_review(source, self.root, region='Vancouver', sheet=None, limit=5, max_scan=100,
                                 **kwargs)

    def test_missing_manifest_blocks_without_fabricating_rows(self):
        result = self.view('statcan-income')
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['publication_approved'])
        self.assertEqual(result['sha256'], None)

    def test_census_rows_preserve_symbol_and_period(self):
        self.seed('statcan-income', make_income_file)
        report = self.view('statcan-income')
        self.assertEqual(report['status'], 'sampled')
        self.assertEqual(report['scanned_rows'], 3)
        self.assertEqual(report['matching_rows_seen'], 2)
        self.assertEqual(report['income_reference_year'], 2020)
        self.assertEqual(report['rows'][0]['dguid'], '2021S0503933')
        self.assertEqual(report['rows'][0]['measures']['median_total_income_2020']['symbol'], 'x')
        self.assertFalse(report['geography_crosswalk_approved'])
        self.assertFalse(report['metric_comparability_approved'])

    def test_census_respects_scan_cap_and_region_choice(self):
        path = self.seed('statcan-income', make_income_file)
        report = review.build_review('statcan-income', self.root, region='Halifax', sheet=None, limit=2, max_scan=1)
        self.assertEqual(report['rows'], [])
        self.assertTrue(report['scan_cap_reached'])
        self.assertEqual(report['scanned_rows'], 1)
        self.assertTrue(path.exists())

    def test_census_broken_row_fails_closed(self):
        path = self.root / probe.SOURCES['statcan-income']['filename']
        make_income_file(path, bad_row=True)
        with self.assertRaisesRegex(review.ReviewError, 'inconsistent column count'):
            review.review_census(path, region='Vancouver', limit=5, max_scan=100)

    def test_census_rejects_unknown_cma_label(self):
        path = self.root / 'data.zip'
        make_income_file(path)
        with self.assertRaisesRegex(review.ReviewError, 'candidate CMA'):
            review.review_census(path, region='Ottawa', limit=5, max_scan=100)

    def test_workbook_inventories_sheets_without_guessing_columns(self):
        self.seed('cmhc-vancouver', make_xlsx)
        report = self.view('cmhc-vancouver')
        self.assertEqual(report['worksheet_names'], ['1.1.1'])
        self.assertEqual(report['rows'], [])
        self.assertIsNone(report['selected_worksheet'])

    def test_workbook_previews_shared_and_inline_strings(self):
        self.seed('cmhc-toronto', make_xlsx)
        report = review.build_review('cmhc-toronto', self.root, region='Vancouver', sheet='1.1.1', limit=5, max_scan=100)
        self.assertEqual(report['rows'][0]['cells'][0]['display'], 'Unit mix')
        self.assertEqual(report['rows'][0]['cells'][1]['display'], 'Header B')
        self.assertEqual(report['rows'][1]['cells'][0]['display'], '2400')
        self.assertEqual(report['rows'][1]['cells'][1]['display'], 'Vancouver')
        self.assertFalse(report['publication_approved'])

    def test_unknown_sheet_rejected(self):
        self.seed('cmhc-vancouver', make_xlsx)
        with self.assertRaisesRegex(review.ReviewError, 'Unknown worksheet'):
            review.build_review('cmhc-vancouver', self.root, region='Vancouver', sheet='1.1.2', limit=5, max_scan=100)

    def test_workbook_rejects_unsafe_relationship(self):
        path = self.root / 'bad.xlsx'
        make_xlsx(path, relationship='../evil.xml')
        with self.assertRaisesRegex(review.ReviewError, 'unsafe'):
            review.review_cmhc(path, sheet='1.1.1', limit=5)

    def test_workbook_rejects_bad_shared_string_reference(self):
        path = self.root / 'bad.xlsx'
        make_xlsx(path, malformed_shared=True)
        with self.assertRaisesRegex(review.ReviewError, 'shared-string'):
            review.review_cmhc(path, sheet='1.1.1', limit=5)

    def test_workbook_rejects_missing_relationship_file(self):
        path = self.root / 'bad.xlsx'
        with ZipFile(path, 'w') as archive:
            archive.writestr('xl/workbook.xml', '<workbook/>')
        with self.assertRaisesRegex(review.ReviewError, 'missing required XML'):
            review.review_cmhc(path, sheet=None, limit=5)

    def test_original_filename_comes_from_audited_manifest(self):
        original = self.seed('cmhc-vancouver', make_xlsx)
        renamed = self.root / 'cmhc-downloaded-copy.xlsx'
        original.rename(renamed)
        manifest_path = self.root / 'cmhc-vancouver-manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['local_file_name'] = renamed.name
        manifest_path.write_text(json.dumps(manifest))
        report = self.view('cmhc-vancouver')
        self.assertEqual(report['status'], 'sampled')
        self.assertEqual(report['worksheet_names'], ['1.1.1'])

    def test_modified_bytes_are_not_trusted_even_with_old_manifest(self):
        path = self.seed('statcan-income', make_income_file)
        path.write_bytes(path.read_bytes() + b'\n')
        self.assertEqual(self.view('statcan-income')['status'], 'blocked')

    def test_boc_never_reports_regional_metrics(self):
        self.seed('boc-overnight', make_boc)
        report = self.view('boc-overnight')
        self.assertEqual(report['status'], 'sampled')
        self.assertIn('macro', report['review_warning'])
        self.assertFalse(report['metric_comparability_approved'])

    def test_input_limits_must_be_bounded(self):
        with self.assertRaisesRegex(review.ReviewError, 'limits'):
            review.build_review('statcan-income', self.root, region='Vancouver', sheet=None, limit=13, max_scan=100)
        with self.assertRaisesRegex(review.ReviewError, 'limits'):
            review.build_review('statcan-income', self.root, region='Vancouver', sheet=None, limit=2, max_scan=3000000)


if __name__ == '__main__':
    unittest.main()
