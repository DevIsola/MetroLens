"""Offline Vancouver-CMA fixture, not a redistributed CMHC workbook."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import extract_cmhc_cma_rents as rents
import probe_official_sources as probe

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'

# These 10 values were reported from the user's 2025 worksheet review;
# the workbook constructed here is entirely synthetic and test-only.
VANCOUVER = {
    'B': '1575', 'C': 'a', 'D': '1667', 'E': 'a',
    'F': '1769', 'G': 'a', 'H': '1806', 'I': 'a',
    'J': '2314', 'K': 'a', 'L': '2363', 'M': 'a',
    'N': '2942', 'O': 'a', 'P': '3009', 'Q': 'a',
    'R': '1924', 'S': 'a', 'T': '1963', 'U': 'a',
}


def write_fixture(path: Path, *, changes=None, duplicate_cma=False,
                  include_sheet=True, heading=None, footnote=None, legend=None):
    changes = changes or {}
    sheet_rows = {
        3: {'A': heading if heading is not None else rents.TITLE},
        6: {'B': 'Studio', 'F': '1 Bedroom', 'J': '2 Bedroom',
            'N': '3 Bedroom +', 'R': 'Total'},
        7: {'A': 'Zone', 'B': 'Oct-24', 'D': 'Oct-25', 'F': 'Oct-24', 'H': 'Oct-25',
            'J': 'Oct-24', 'L': 'Oct-25', 'N': 'Oct-24', 'P': 'Oct-25',
            'R': 'Oct-24', 'T': 'Oct-25'},
        8: {'A': 'City of Vancouver (Zones 1-10)', **VANCOUVER},
        9: {'A': 'Vancouver CMA', **VANCOUVER},
        10: {'A': footnote if footnote is not None else
             '2025 and 2024 data are based on the 2021 census geographic definitions.'},
        11: {'A': 'Quality Indicators:'},
        12: {'A': legend if legend is not None else
             'a — Excellent  b — Very Good  c — Good  d — Poor (use with caution)'},
        13: {'A': '** — Data suppressed'},
        14: {'A': 'Source: Rental Market Survey (CMHC)'},
    }
    if duplicate_cma:
        sheet_rows[15] = {'A': 'Vancouver CMA', **VANCOUVER}
    for cell, value in changes.items():
        col = ''.join(c for c in cell if c.isalpha())
        row = int(''.join(c for c in cell if c.isdigit()))
        if value is None:
            sheet_rows[row].pop(col, None)
        else:
            sheet_rows.setdefault(row, {})[col] = value

    worksheet = ET.Element(f'{{{NS}}}worksheet')
    sheet_data = ET.SubElement(worksheet, f'{{{NS}}}sheetData')
    for row_id, values in sorted(sheet_rows.items()):
        row = ET.SubElement(sheet_data, f'{{{NS}}}row', r=str(row_id))
        for col, raw in values.items():
            addr = f'{col}{row_id}'
            numeric = raw.isascii() and raw.isdigit() and col != 'A'
            cell = ET.SubElement(row, f'{{{NS}}}c', r=addr, **({} if numeric else {'t': 'inlineStr'}))
            if numeric:
                ET.SubElement(cell, f'{{{NS}}}v').text = raw
            else:
                ET.SubElement(ET.SubElement(cell, f'{{{NS}}}is'), f'{{{NS}}}t').text = raw

    wb = ET.Element(f'{{{NS}}}workbook', {f'xmlns:r': REL})
    sheets = ET.SubElement(wb, f'{{{NS}}}sheets')
    ET.SubElement(sheets, f'{{{NS}}}sheet', name=rents.SHEET if include_sheet else 'Unknown',
                  sheetId='1', **{f'{{{REL}}}id': 'rId3'})
    relationship = ET.Element(f'{{{PKG_REL}}}Relationships')
    ET.SubElement(relationship, f'{{{PKG_REL}}}Relationship', Id='rId3',
                  Type=REL + '/worksheet', Target='worksheets/sheet1.xml')
    with ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('xl/workbook.xml', ET.tostring(wb))
        z.writestr('xl/_rels/workbook.xml.rels', ET.tostring(relationship))
        z.writestr('xl/worksheets/sheet1.xml', ET.tostring(worksheet))


class CMHCRentTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.path = self.root / probe.SOURCES[rents.SOURCE]['filename']

    def make(self, **kwargs):
        write_fixture(self.path, **kwargs)
        manifest = probe.build_manifest(rents.SOURCE, self.path)
        (self.root / (rents.SOURCE + '-manifest.json')).write_text(json.dumps(manifest), encoding='utf-8')

    def test_extracts_cma_not_city_and_retains_provenance(self):
        self.make()
        result = rents.extract_verified(self.root)
        self.assertEqual(result['status'], 'extracted_for_review')
        self.assertEqual(result['source_row'], 9)
        self.assertEqual(len(result['records']), 10)
        self.assertEqual(result['source_sha256'], probe.inspect_file(self.path, rents.SOURCE)['sha256'])
        two = [r for r in result['records'] if r['bedroom_type'] == 'two_bedroom']
        self.assertEqual([(r['reference_period'], r['value_cad_per_month'], r['quality_code'], r['cell'])
                         for r in two], [('2024-10', 2314, 'a', 'J9'), ('2025-10', 2363, 'a', 'L9')])
        all_units = [r for r in result['records'] if r['bedroom_type'] == 'all_bedrooms']
        self.assertEqual([r['value_cad_per_month'] for r in all_units], [1924, 1963])
        self.assertFalse(result['publication_approved'])
        self.assertFalse(result['metric_comparability_approved'])
        self.assertEqual(result['geographic_vintage'], '2021_census_definitions')

    def test_missing_manifest_blocks(self):
        self.assertEqual(rents.extract_verified(self.root)['status'], 'blocked')

    def test_mismatched_source_checksum_blocks(self):
        self.make()
        with self.path.open('ab') as f:
            f.write(b'not original')
        self.assertEqual(rents.extract_verified(self.root)['status'], 'blocked')

    def test_missing_sheet_rejected(self):
        self.make(include_sheet=False)
        with self.assertRaisesRegex(rents.RentExtractionError, 'worksheet'):
            rents.extract_verified(self.root)

    def test_bad_heading_rejected(self):
        self.make(heading='1.1.2 Vacancy Rate - Vancouver CMA')
        with self.assertRaisesRegex(rents.RentExtractionError, 'heading'):
            rents.extract_verified(self.root)

    def test_missing_cma_rejected(self):
        self.make(changes={'A9': 'Vancouver Island'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'one Vancouver CMA'):
            rents.extract_verified(self.root)

    def test_duplicate_cma_rejected(self):
        self.make(duplicate_cma=True)
        with self.assertRaisesRegex(rents.RentExtractionError, 'one Vancouver CMA'):
            rents.extract_verified(self.root)

    def test_changed_year_header_rejected(self):
        self.make(changes={'L7': 'Oct-23'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'Year labels'):
            rents.extract_verified(self.root)

    def test_wrong_bedroom_header_rejected(self):
        self.make(changes={'J6': 'All Rents'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'Bedroom heading'):
            rents.extract_verified(self.root)

    def test_missing_geography_footnote_rejected(self):
        self.make(footnote='Unknown geography vintage')
        with self.assertRaisesRegex(rents.RentExtractionError, '2021 Census'):
            rents.extract_verified(self.root)

    def test_missing_legend_rejected(self):
        self.make(legend='something else')
        with self.assertRaisesRegex(rents.RentExtractionError, 'Quality legend'):
            rents.extract_verified(self.root)

    def test_numeric_with_missing_quality_rejected(self):
        self.make(changes={'M9': ''})
        with self.assertRaisesRegex(rents.RentExtractionError, 'quality code'):
            rents.extract_verified(self.root)

    def test_suppressed_observation_is_null(self):
        self.make(changes={'L9': '**', 'M9': ''})
        two_2025 = next(r for r in rents.extract_verified(self.root)['records']
                        if r['bedroom_type'] == 'two_bedroom' and r['reference_period'] == '2025-10')
        self.assertIsNone(two_2025['value_cad_per_month'])
        self.assertEqual(two_2025['status'], 'suppressed')

    def test_suppressed_observation_with_quality_rejected(self):
        self.make(changes={'L9': '**'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'Suppressed'):
            rents.extract_verified(self.root)

    def test_poor_quality_is_explicit_caution(self):
        self.make(changes={'M9': 'd'})
        two = next(r for r in rents.extract_verified(self.root)['records']
                   if r['bedroom_type'] == 'two_bedroom' and r['reference_period'] == '2025-10')
        self.assertEqual(two['status'], 'use_with_caution')
        self.assertEqual(two['quality_description'], 'Poor (use with caution)')

    def test_invalid_quality_rejected(self):
        self.make(changes={'M9': 'e'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'quality code'):
            rents.extract_verified(self.root)

    def test_bad_amount_rejected(self):
        self.make(changes={'L9': '=ABC'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'Invalid rent'):
            rents.extract_verified(self.root)

    def test_zero_rejected(self):
        self.make(changes={'L9': '0'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'positive'):
            rents.extract_verified(self.root)

    def test_decimal_and_comma_are_supported(self):
        self.make(changes={'L9': '2,363.50'})
        two = next(r for r in rents.extract_verified(self.root)['records']
                   if r['bedroom_type'] == 'two_bedroom' and r['reference_period'] == '2025-10')
        self.assertEqual(two['value_cad_per_month'], 2363.5)

    def test_does_not_accept_wrong_cma_label(self):
        self.make(changes={'A9': 'City of Vancouver', 'A8': 'Vancouver CMA—East'})
        with self.assertRaisesRegex(rents.RentExtractionError, 'one Vancouver CMA'):
            rents.extract_verified(self.root)


if __name__ == '__main__':
    unittest.main()
