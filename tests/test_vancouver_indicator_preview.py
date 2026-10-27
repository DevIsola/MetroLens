"""M00-T03 unjoined Vancouver indicator preview must fail closed."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from preview_vancouver_indicators import (IndicatorPreviewError, assemble_preview,
                                           build_report, main)
from reconcile_vancouver_evidence import EVIDENCE, ReconciliationError
from probe_official_sources import SOURCES
from test_vancouver_evidence_reconciliation import inputs

E = json.loads(EVIDENCE.read_text(encoding='utf-8'))


def fixture():
    census, rent = inputs()
    rent['official_source_url'] = SOURCES['cmhc-vancouver']['url']
    for r in rent['records']:
        r['quality_description'] = 'Excellent'
        r['cell'] = 'J36'
        r['quality_cell'] = 'K36'
    cis = {
        'status': 'candidate_extracted_for_review',
        'file_audit_status': 'file_verified',
        'source_id': 'statcan_11100190',
        'official_source_url': SOURCES['statcan-cis-income']['url'],
        'source_sha256': '03677bae1fd1cc412c6563c0b33251d2eb4cf3837712ee7c92aa87d7bec782e4',
        'geography_label': 'Vancouver, British Columbia',
        'dguid': '2021S0503933',
        'geographic_vintage': '2021_census_definitions',
        'income_concept': 'Median after-tax income',
        'economic_family_type': 'Economic families and persons not in an economic family',
        'price_basis': '2024_constant_dollars',
        'full_source_scanned': True,
        'candidate_only': True,
        'census_private_households_equivalent': False,
        'statistical_populations_comparable': False,
        'geography_crosswalk_approved': False,
        'reference_periods_aligned': False,
        'metric_comparability_approved': False,
        'publication_approved': False,
        'production_ready': False,
        'rent_to_income_ratio': None,
        'observations': [
            {'metric_id': 'cis_median_after_tax_income_economic_family_unit',
             'reference_period': year, 'value': value,
             'unit': 'CAD_2024_constant_per_year', 'measure_type': 'median',
             'statistical_population': 'economic_families_and_persons_not_in_economic_families',
             'source_status_code': 'A', 'status': 'observed_candidate_only',
             'approved_for_affordability_join': False,
             'source_symbol': None, 'source_terminated': None,
             'source_vector': 'v96416811', 'source_coordinate': '21.12.1'}
            for year, value in (('2023', 77700), ('2024', 78900))],
    }
    return census, cis, rent


class IndicatorPreviewTests(unittest.TestCase):
    def test_outputs_separate_units_without_cross_source_calculation(self):
        report = assemble_preview(*fixture(), E)
        self.assertEqual(report['status'], 'indicator_preview_for_review')
        self.assertEqual(len(report['series']), 2)
        self.assertEqual(report['series'][0]['measure_type'], 'weighted_mean')
        self.assertEqual(report['series'][1]['measure_type'], 'median')
        self.assertEqual(report['series'][0]['unit'], 'CAD_per_month')
        self.assertEqual(report['series'][1]['unit'], 'CAD_2024_constant_per_year')
        self.assertEqual(len(report['series'][0]['observations']), 10)
        self.assertEqual(len(report['series'][1]['observations']), 2)
        self.assertEqual(report['series'][1]['observations'][1]['value'], 78900)
        self.assertIsNone(report['rent_to_income_ratio'])
        self.assertEqual(report['blocked_metrics'][0]['metric_id'], 'rent_to_income_pct')
        self.assertIsNone(report['blocked_metrics'][0]['value'])
        for key in ('production_ready', 'publication_approved',
                    'metric_comparability_approved', 'geography_crosswalk_approved',
                    'reference_periods_aligned_for_join', 'statistical_populations_comparable_for_join'):
            self.assertIs(report[key], False)
        self.assertNotIn('income_yoy_pct', report)
        self.assertNotIn('rent_yoy_pct', report)

    def mutate(self, origin: str, field: str, replacement):
        census, cis, rent = copy.deepcopy(fixture())
        obj = {'census': census, 'cis': cis, 'rent': rent}[origin]
        obj[field] = replacement
        with self.assertRaises((IndicatorPreviewError, ReconciliationError)):
            assemble_preview(census, cis, rent, E)

    def test_missing_cis_file_is_rejected(self):
        self.mutate('cis', 'status', 'blocked')

    def test_cis_hash_mismatch_is_rejected(self):
        self.mutate('cis', 'source_sha256', 'e' * 64)

    def test_unverified_publisher_url_is_rejected(self):
        self.mutate('cis', 'official_source_url', 'https://example.org/cis.zip')

    def test_cis_geography_mismatch_is_rejected(self):
        self.mutate('cis', 'dguid', '2021S0503999')

    def test_cis_population_swap_is_rejected(self):
        self.mutate('cis', 'economic_family_type', 'Private households')

    def test_cis_income_measure_swap_is_rejected(self):
        self.mutate('cis', 'income_concept', 'Median total income')

    def test_cis_price_basis_swap_is_rejected(self):
        self.mutate('cis', 'price_basis', 'current_dollars')

    def test_cis_incomplete_scan_is_rejected(self):
        self.mutate('cis', 'full_source_scanned', False)

    def test_cis_publication_claim_is_rejected(self):
        self.mutate('cis', 'publication_approved', True)

    def test_cis_population_equivalence_claim_is_rejected(self):
        self.mutate('cis', 'census_private_households_equivalent', True)

    def test_cis_injected_ratio_is_rejected(self):
        self.mutate('cis', 'rent_to_income_ratio', 32.5)

    def test_legacy_census_reconciliation_still_applies(self):
        self.mutate('census', 'dguid', 'fake')

    def test_legacy_cmhc_reconciliation_still_applies(self):
        self.mutate('rent', 'source_sha256', '0' * 64)

    def test_cis_missing_or_duplicate_period_is_rejected(self):
        for replacement in ([fixture()[1]['observations'][0]],
                            [fixture()[1]['observations'][0]] * 2):
            census, cis, rent = fixture()
            cis['observations'] = replacement
            with self.assertRaises(IndicatorPreviewError):
                assemble_preview(census, cis, rent, E)

    def test_cis_source_status_not_acceptable_rejected(self):
        census, cis, rent = fixture()
        cis['observations'][0]['source_status_code'] = 'F'
        with self.assertRaises(IndicatorPreviewError):
            assemble_preview(census, cis, rent, E)

    def test_cis_hidden_suppression_is_rejected(self):
        census, cis, rent = fixture()
        cis['observations'][0]['source_symbol'] = 'x'
        with self.assertRaises(IndicatorPreviewError):
            assemble_preview(census, cis, rent, E)

    def test_cis_value_changed_rejected(self):
        census, cis, rent = fixture()
        cis['observations'][1]['value'] = 79000
        with self.assertRaises(IndicatorPreviewError):
            assemble_preview(census, cis, rent, E)

    def test_rent_quality_description_mismatch_rejected(self):
        census, cis, rent = fixture()
        rent['records'][0]['quality_description'] = 'Poor'
        with self.assertRaises(IndicatorPreviewError):
            assemble_preview(census, cis, rent, E)

    def test_rent_missing_cells_rejected(self):
        census, cis, rent = fixture()
        rent['records'][0].pop('cell')
        with self.assertRaises(IndicatorPreviewError):
            assemble_preview(census, cis, rent, E)

    def test_build_report_calls_all_verified_extractors(self):
        census, cis, rent = fixture()
        with patch('preview_vancouver_indicators.extract_census', return_value=census), \
             patch('preview_vancouver_indicators.extract_rent', return_value=rent), \
             patch('preview_vancouver_indicators.extract_cis', return_value=cis):
            with tempfile.TemporaryDirectory() as td:
                result = build_report(Path(td))
            self.assertEqual(result['status'], 'indicator_preview_for_review')

    def test_cli_errors_are_blocked_and_never_authorize_publication(self):
        with patch('preview_vancouver_indicators.build_report', side_effect=IndicatorPreviewError('missing source')):
            from io import StringIO
            from contextlib import redirect_stderr
            output = StringIO()
            with redirect_stderr(output):
                rc = main([])
            self.assertEqual(rc, 2)
            report = json.loads(output.getvalue())
            self.assertEqual(report['status'], 'blocked')
            self.assertFalse(report['publication_approved'])
            self.assertIsNone(report['rent_to_income_ratio'])

    def test_missing_real_file_returns_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises((ReconciliationError, IndicatorPreviewError)):
                build_report(Path(td))


if __name__ == '__main__':
    unittest.main()
