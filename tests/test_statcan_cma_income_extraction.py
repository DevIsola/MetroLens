"""Synthetic-only Statistics Canada Census income extraction acceptance tests."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import extract_statcan_cma_income as income
import probe_official_sources as probe

HEADER = [
    'REF_DATE', 'GEO', 'DGUID', 'Household size (7)',
    'Household type including census family structure  (11)', 'Coordinate',
    'Household income statistics (6):Number of households (2021)[1]', 'Symbol',
    'Household income statistics (6):Number of households (2016)[2]', 'Symbol',
    'Household income statistics (6):Median household total income (2020) (2020 constant dollars)[3]', 'Symbol',
    'Household income statistics (6):Median household total income (2015) (2020 constant dollars)[4]', 'Symbol',
    'Household income statistics (6):Median household after-tax income (2020) (2020 constant dollars)[5]', 'Symbol',
    'Household income statistics (6):Median household after-tax income (2015) (2020 constant dollars)[6]', 'Symbol',
]
BASE = [
    '2021', 'Vancouver (CMA) 933, B.C.', '2021S0503933',
    'Total - Households by household size',
    'Total – Household type including census family structure', '5381.1.1',
    '1043315', '', '1000000', '', '90000', '', '87000', '', '79500', '', '72000', '',
]


def make_zip(path: Path, *, rows=None, header=None):
    content = io.StringIO(newline='')
    writer = csv.writer(content)
    writer.writerow(header if header is not None else HEADER)
    writer.writerows([BASE] if rows is None else rows)
    with ZipFile(path, 'w') as archive:
        archive.writestr('98100058.csv', content.getvalue())


class CensusIncomeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.path = self.folder / probe.SOURCES[income.SOURCE]['filename']

    def prepare(self, **kwargs):
        make_zip(self.path, **kwargs)
        manifest = probe.build_manifest(income.SOURCE, self.path)
        (self.folder / f'{income.SOURCE}-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')

    def test_exact_cma_and_all_households_with_original_values(self):
        narrow = BASE.copy()
        narrow[4], narrow[5], narrow[10] = 'Census-family households', '5381.1.2', '117000'
        toronto = BASE.copy()
        toronto[1:3] = ['Toronto (CMA) 535, Ont.', '2021S0503535']
        self.prepare(rows=[toronto, narrow, BASE])
        report = income.extract_verified(self.folder)
        self.assertEqual(report['status'], 'extracted_for_review')
        self.assertEqual(report['dguid'], '2021S0503933')
        self.assertEqual(report['coordinate'], '5381.1.1')
        self.assertEqual(report['geography_label'], 'Vancouver (CMA) 933, B.C.')
        self.assertEqual(report['scanned_rows'], 3)
        self.assertEqual([(x['value'], x['reference_period']) for x in report['observations']],
                         [(1043315, '2021'), (90000, '2020'), (79500, '2020')])
        self.assertTrue(all(x['status'] == 'observed' and x['source_symbol'] is None
                            for x in report['observations']))
        self.assertEqual(report['source_sha256'], probe.inspect_file(self.path, income.SOURCE)['sha256'])
        for gate in ('production_ready', 'publication_approved', 'geography_crosswalk_approved', 'metric_comparability_approved'):
            self.assertFalse(report[gate])

    def test_missing_manifest_blocks(self):
        self.assertEqual(income.extract_verified(self.folder)['status'], 'blocked')

    def test_changed_file_blocks(self):
        self.prepare()
        self.path.write_bytes(self.path.read_bytes() + b'other')
        self.assertEqual(income.extract_verified(self.folder)['status'], 'blocked')

    def test_non_default_input_basename_uses_manifest(self):
        self.path = self.folder / 'publisher-census-export.zip'
        self.prepare()
        self.assertEqual(income.extract_verified(self.folder)['status'], 'extracted_for_review')

    def test_unknown_cma_rejected(self):
        row = BASE.copy()
        row[2] = '2021S0503935'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'not found'):
            income.extract_verified(self.folder)

    def test_wrong_cma_label_rejected(self):
        row = BASE.copy()
        row[1] = 'City of Vancouver'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'label'):
            income.extract_verified(self.folder)

    def test_wrong_coordinate_rejected(self):
        row = BASE.copy()
        row[5] = '5381.9.9'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'coordinate'):
            income.extract_verified(self.folder)

    def test_wrong_census_year_rejected(self):
        row = BASE.copy()
        row[0] = '2020'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'year'):
            income.extract_verified(self.folder)

    def test_household_subgroup_does_not_replace_total(self):
        row = BASE.copy()
        row[3] = '1 person'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'not found'):
            income.extract_verified(self.folder)

    def test_household_type_subgroup_does_not_replace_total(self):
        row = BASE.copy()
        row[4] = 'Census-family households'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'not found'):
            income.extract_verified(self.folder)

    def test_duplicate_exact_total_rejected(self):
        self.prepare(rows=[BASE, BASE])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'Duplicate'):
            income.extract_verified(self.folder)

    def test_missing_income_rejected(self):
        row = BASE.copy()
        row[10] = ''
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'Missing'):
            income.extract_verified(self.folder)

    def test_zero_income_rejected(self):
        row = BASE.copy()
        row[10] = '0'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'Nonpositive'):
            income.extract_verified(self.folder)

    def test_flagged_income_not_usable(self):
        row = BASE.copy()
        row[10], row[11] = '', 'x'
        self.prepare(rows=[row])
        measure = income.extract_verified(self.folder)['observations'][1]
        self.assertEqual(measure['status'], 'source_flagged_not_usable')
        self.assertIsNone(measure['value'])
        self.assertEqual(measure['source_symbol'], 'x')

    def test_flagged_numeric_income_rejected(self):
        row = BASE.copy()
        row[11] = 'x'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'Flagged'):
            income.extract_verified(self.folder)

    def test_bad_row_width_rejected(self):
        self.prepare(rows=[BASE[:-1]])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'Malformed'):
            income.extract_verified(self.folder)

    def test_trailing_blank_csv_records_are_ignored_only_at_eof(self):
        # CSV readers can expose physical empty lines as zero-field records.
        # Both physical blanks and a quoted/whitespace blank field are safe
        # to ignore, but only if no subsequent data records appear.
        for suffix in ([''], ['   '], []):
            with self.subTest(suffix=suffix):
                self.prepare(rows=[BASE, [], suffix, [''] * len(HEADER)])
                report = income.extract_verified(self.folder)
                self.assertEqual(report['status'], 'extracted_for_review')
                self.assertEqual(report['data_rows_scanned'], 1)
                self.assertEqual(report['trailing_blank_rows_skipped'], 3)
                self.assertEqual(report['scanned_rows'], 4)
                self.assertEqual(report['observations'][1]['value'], 90000)

    def test_blank_record_inside_csv_is_not_silently_ignored(self):
        self.prepare(rows=[BASE, [], BASE])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'blank rows are only allowed at EOF'):
            income.extract_verified(self.folder)

    def test_nonempty_row_after_blank_fails_even_if_other_cma(self):
        other = BASE.copy()
        other[1:3] = ['Toronto (CMA) 535, Ont.', '2021S0503535']
        self.prepare(rows=[BASE, [''], other])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'Nonempty Census record 3'):
            income.extract_verified(self.folder)

    def test_nonempty_malformed_trailer_remains_invalid_with_field_count(self):
        self.prepare(rows=[BASE, ['Source', 'Statistics Canada']])
        with self.assertRaisesRegex(income.IncomeExtractionError, r'expected 18 fields, found 2'):
            income.extract_verified(self.folder)

    def test_empty_only_file_still_rejects_missing_aggregate(self):
        self.prepare(rows=[[], ['']])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'aggregate not found'):
            income.extract_verified(self.folder)

    def test_non_digit_amount_rejected(self):
        row = BASE.copy()
        row[10] = '90,0?0'
        self.prepare(rows=[row])
        with self.assertRaisesRegex(income.IncomeExtractionError, 'invalid'):
            income.extract_verified(self.folder)

    def test_bom_header_supported(self):
        self.prepare()
        with ZipFile(self.path, 'r') as archive:
            csv_bytes = archive.read('98100058.csv')
        with ZipFile(self.path, 'w') as archive:
            archive.writestr('98100058.csv', b'\xef\xbb\xbf' + csv_bytes)
        manifest = probe.build_manifest(income.SOURCE, self.path)
        (self.folder / f'{income.SOURCE}-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        self.assertEqual(income.extract_verified(self.folder)['status'], 'extracted_for_review')

    def test_changed_file_mid_scan_rejected(self):
        self.prepare()
        real_audit = income.audit_source
        with patch.object(income, 'audit_source', side_effect=[real_audit(income.SOURCE, self.folder), {'status': 'invalid'}]):
            with self.assertRaisesRegex(income.IncomeExtractionError, 'changed'):
                income.extract_verified(self.folder)

    def test_cli_blocked_without_raw_file(self):
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            status = income.main(['--raw-dir', str(self.folder)])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(out.getvalue())['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
