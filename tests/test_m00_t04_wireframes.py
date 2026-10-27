"""Offline M00-T04 paired-wireframe artifact must preserve source and safety gates."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from preview_vancouver_indicators import assemble_preview
from render_m00_wireframes import WireframeError, prepare_data, render_html, main, SOURCE_CELLS
from test_vancouver_indicator_preview import fixture, E


def report():
    result = assemble_preview(*fixture(), E)
    # Original M00-T03 test fixtures use synthetic rent figures. This wireframe
    # gate targets the actual, manually reviewed Vancouver CMA values instead.
    observed = {
        ('all_bedrooms', '2024-10'): 1924, ('all_bedrooms', '2025-10'): 1963,
        ('one_bedroom', '2024-10'): 1769, ('one_bedroom', '2025-10'): 1806,
        ('studio', '2024-10'): 1575, ('studio', '2025-10'): 1667,
        ('three_plus_bedroom', '2024-10'): 2942, ('three_plus_bedroom', '2025-10'): 3009,
        ('two_bedroom', '2024-10'): 2314, ('two_bedroom', '2025-10'): 2363,
    }
    for point in result['series'][0]['observations']:
        key = (point['bedroom_type'], point['reference_period'])
        point['value'] = observed[key]
        point['source_cell'], point['source_quality_cell'] = SOURCE_CELLS[key]
    return result


class M00T04WireframeTests(unittest.TestCase):
    def test_preserves_two_unjoined_series_and_quality(self):
        result = prepare_data(report())
        self.assertFalse(result['cross_source_comparison_allowed'])
        self.assertEqual(len(result['rent']), 10)
        self.assertEqual(len(result['income']), 2)
        self.assertEqual(result['income'][1]['value'], 78900)
        self.assertEqual(result['income'][1]['quality'], 'A')
        self.assertIn('cmhc-schl.gc.ca', result['source_links']['rent'])

    def test_reviewed_two_bedroom_values_are_not_confused_with_all_bedrooms(self):
        rent = prepare_data(report())['rent']
        two = [x['value'] for x in rent if x['bedroom_type'] == 'two_bedroom']
        all_units = [x['value'] for x in rent if x['bedroom_type'] == 'all_bedrooms']
        self.assertEqual(two, [2314, 2363])
        self.assertEqual(all_units, [1924, 1963])

    def test_html_is_standalone_and_has_paired_accessible_controls(self):
        html = render_html(report())
        for fragment in ('<!doctype html>', '<meta charset="utf-8">', 'Desktop pair',
                         'Mobile pair (390 px)', 'Light theme concept', 'Dark theme concept',
                         'for="bedrooms-light"', 'for="bedrooms-dark"',
                         'aria-pressed', 'aria-live="polite"',
                         'Affordability ratio unavailable', 'Source quality',
                         '2024 constant dollars', 'weighted mean',
                         '2021 Census geographic definitions', '2024-10', '2025-10'):
            self.assertIn(fragment, html)
        self.assertNotIn('/*__M00_DATA_JSON__*/', html)
        self.assertNotIn('rent_to_income_pct', html)
        self.assertNotIn('rent_to_income_ratio', html)
        self.assertNotIn('income_yoy_pct', html)
        self.assertNotIn('rent_yoy_pct', html)

    def test_output_html_contains_verified_values_only_as_json(self):
        html = render_html(report())
        self.assertIn('"value":2363', html)
        self.assertIn('"value":78900', html)
        self.assertIn('"cross_source_comparison_allowed":false', html)
        self.assertNotIn('1043315', html)

    def test_html_json_string_escapes_inline_script_breakout(self):
        sample = 'before</script>after'
        html = render_html(report(), 'const DATA=/*__M00_DATA_JSON__*/;')
        self.assertIn('"region":"Vancouver CMA"', html)
        self.assertNotIn(sample, html)

    def test_duplicate_placeholder_fails(self):
        with self.assertRaises(WireframeError):
            render_html(report(), '/*__M00_DATA_JSON__*/ /*__M00_DATA_JSON__*/')

    def test_missing_placeholder_fails(self):
        with self.assertRaises(WireframeError):
            render_html(report(), '<html></html>')

    def test_cli_without_verified_source_files_fails_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output.html'
            with patch('render_m00_wireframes.build_report', side_effect=WireframeError('No audited files')):
                self.assertEqual(main(['--output', str(out)]), 2)
            self.assertFalse(out.exists())

    def test_cli_writes_utf8_html_only_for_valid_data(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output.html'
            with patch('render_m00_wireframes.build_report', return_value=report()):
                self.assertEqual(main(['--output', str(out)]), 0)
            html = out.read_text(encoding='utf-8')
            self.assertIn('What do the numbers actually measure?', html)
            self.assertIn('2024 constant dollars', html)
            self.assertNotIn('ù', html)

    def mutate(self, key, value):
        broken = copy.deepcopy(report())
        broken[key] = value
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_production_approval_rejected(self):
        self.mutate('production_ready', True)

    def test_publication_approval_rejected(self):
        self.mutate('publication_approved', True)

    def test_fake_reconciled_false_rejected(self):
        self.mutate('source_specific_evidence_reconciled', False)

    def test_nonnull_ratio_rejected(self):
        self.mutate('rent_to_income_ratio', 31)

    def test_missing_blocked_reasons_rejected(self):
        broken = copy.deepcopy(report())
        broken['blocked_metrics'][0]['reason_codes'] = []
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_wrong_income_population_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][1]['statistical_unit'] = 'private_household'
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_wrong_rent_quality_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][0]['observations'][0]['quality_code'] = 'd'
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_missing_cis_point_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][1]['observations'].pop()
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_duplicate_rent_point_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][0]['observations'][-1] = broken['series'][0]['observations'][0]
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_spoofed_publisher_url_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][0]['official_source_url'] = 'https://bad.example/?cmhc-schl.gc.ca/'
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_wrong_source_cell_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][0]['observations'][0]['source_cell'] = 'J36'
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_rejects_output_inside_tracked_docs(self):
        path = ROOT / 'docs' / 'do-not-create-wireframe.html'
        with patch('render_m00_wireframes.build_report', return_value=report()):
            self.assertEqual(main(['--output', str(path)]), 2)
        self.assertFalse(path.exists())

    def test_missing_secure_source_url_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][0]['official_source_url'] = 'http://example.com'
        with self.assertRaises(WireframeError):
            prepare_data(broken)

    def test_hash_change_rejected(self):
        broken = copy.deepcopy(report())
        broken['series'][1]['source_sha256'] = '0'*64
        with self.assertRaises(WireframeError):
            prepare_data(broken)


if __name__ == '__main__':
    unittest.main()
