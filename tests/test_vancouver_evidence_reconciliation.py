"""Guard technical review evidence without licensing an income-rent join."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reconcile_vancouver_evidence import (EVIDENCE, ReconciliationError, build_report,
                                           main, reconcile)

E = json.loads(EVIDENCE.read_text(encoding='utf-8'))


def inputs():
    income = {
        'status': 'extracted_for_review', 'file_audit_status': 'file_verified',
        'source_id': E['income']['source_id'], 'source_sha256': E['income']['sha256'],
        'geography_crosswalk_approved': False, 'metric_comparability_approved': False,
        'publication_approved': False, 'production_ready': False,
        'dguid': '2021S0503933', 'coordinate': '5381.1.1', 'cma_code_2021': '933',
        'population_universe': 'all_private_households',
        'geographic_vintage': '2021_census_definitions', 'income_reference_year': 2020,
        'household_size': 'Total - Households by household size',
        'household_type': 'Total – Household type including census family structure',
        'observations': [
            {'metric_id': mid, 'value': val, 'reference_period': year,
             'unit': unit, 'measure_type': typ, 'source_symbol': None, 'status': 'observed'}
            for mid, year, unit, typ, val in (
                ('household_count', '2021', 'households', 'count', 1043315),
                ('median_total_household_income', '2020', 'CAD_per_year', 'median', 90000),
                ('median_after_tax_household_income', '2020', 'CAD_per_year', 'median', 79500),
            )
        ],
    }
    rents = []
    for room in ('studio', 'one_bedroom', 'two_bedroom', 'three_plus_bedroom', 'all_bedrooms'):
        for year in ('2024-10', '2025-10'):
            amount = {('two_bedroom', '2024-10'): 2314, ('two_bedroom', '2025-10'): 2363}.get((room, year), 1500)
            rents.append({'bedroom_type': room, 'reference_period': year,
                          'metric_id': 'cmhc_average_private_apartment_rent',
                          'quality_code': 'a', 'status': 'observed', 'value_cad_per_month': amount})
    rent = {
        'status': 'extracted_for_review', 'file_audit_status': 'file_verified',
        'source_id': E['rent']['source_id'], 'source_sha256': E['rent']['sha256'],
        'geography_crosswalk_approved': False, 'metric_comparability_approved': False,
        'publication_approved': False, 'production_ready': False,
        'sheet': 'Table 1.1.2', 'source_row': 36, 'geography_label': 'Vancouver CMA',
        'geographic_vintage': '2021_census_definitions',
        'rental_universe': 'private_purpose_built_rental_apartments',
        'rent_measure': 'average_of_surveyed_units_not_turnover_or_asking_rent',
        'records': rents,
    }
    return income, rent


class ReconcileTests(unittest.TestCase):
    def test_matches_reviewed_evidence_without_authorizing_join(self):
        report = reconcile(*inputs(), E)
        self.assertEqual(report['status'], 'source_evidence_reconciled')
        self.assertEqual(report['source_evidence']['rent']['metric_count'], 10)
        self.assertEqual(report['source_evidence']['income']['metric_count'], 3)
        self.assertFalse(report['reference_periods_aligned'])
        self.assertFalse(report['geographic_identifier_crosswalk_verified'])
        self.assertFalse(report['statistical_populations_comparable'])
        self.assertFalse(report['metric_comparability_approved'])
        self.assertFalse(report['publication_approved'])
        self.assertFalse(report['production_ready'])
        self.assertIsNone(report['rent_to_income_ratio'])
        self.assertEqual(len(report['remaining_gates']), 4)

    def assert_rejected(self, index, key, value):
        sources = list(inputs())
        sources[index][key] = value
        with self.assertRaises(ReconciliationError):
            reconcile(*sources, E)

    def test_block_missing_source_file(self):
        self.assert_rejected(0, 'status', 'blocked')

    def test_block_missing_rent_source(self):
        self.assert_rejected(1, 'file_audit_status', 'manifest_only')

    def test_hash_change_requires_review(self):
        self.assert_rejected(0, 'source_sha256', '0' * 64)

    def test_rent_hash_change_requires_review(self):
        self.assert_rejected(1, 'source_sha256', '1' * 64)

    def test_mismatched_census_geography_is_blocked(self):
        self.assert_rejected(0, 'dguid', '2021S0503999')

    def test_mismatched_rent_vintage_is_blocked(self):
        self.assert_rejected(1, 'geographic_vintage', '2016_census_definitions')

    def test_wrong_income_population_is_blocked(self):
        self.assert_rejected(0, 'household_type', 'Census-family households')

    def test_wrong_rent_population_is_blocked(self):
        self.assert_rejected(1, 'rent_measure', 'asking_rent')

    def test_review_benchmark_cannot_authorize_publication(self):
        altered = copy.deepcopy(E)
        altered['approved_for_publication'] = True
        with self.assertRaises(ReconciliationError):
            reconcile(*inputs(), altered)

    def test_publisher_output_cannot_self_approve(self):
        self.assert_rejected(1, 'publication_approved', True)

    def test_changed_2020_income_is_blocked(self):
        income, rent = inputs()
        income['observations'][1]['value'] = 92000
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_income_suppression_blocked(self):
        income, rent = inputs()
        income['observations'][1]['source_symbol'] = 'x'
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_duplicate_income_metric_blocked(self):
        income, rent = inputs()
        income['observations'][2] = income['observations'][1].copy()
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_duplicate_rent_period_blocked(self):
        income, rent = inputs()
        rent['records'][1] = rent['records'][0].copy()
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_suppressed_rent_blocked(self):
        income, rent = inputs()
        rent['records'][5]['status'] = 'suppressed'
        rent['records'][5]['value_cad_per_month'] = None
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_changed_two_bedroom_benchmark_blocked(self):
        income, rent = inputs()
        rent['records'][5]['value_cad_per_month'] = 2380
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_changed_period_is_blocked(self):
        income, rent = inputs()
        income['observations'][1]['reference_period'] = '2025'
        with self.assertRaises(ReconciliationError):
            reconcile(income, rent, E)

    def test_build_report_uses_existing_extractors(self):
        income, rent = inputs()
        with patch('reconcile_vancouver_evidence.extract_income', return_value=income), \
             patch('reconcile_vancouver_evidence.extract_rent', return_value=rent):
            report = build_report(Path('/tmp/m00-no-network-fixtures'))
        self.assertEqual(report['status'], 'source_evidence_reconciled')

    def test_cli_fail_closed_without_raw_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('sys.stderr') as stderr:
                code = main(['--raw-dir', directory])
        self.assertEqual(code, 2)
        text = ''.join(str(args[0]) for args, _ in stderr.write.call_args_list)
        self.assertIn('"status": "blocked"', text)
        self.assertIn('"rent_to_income_ratio": null', text)


if __name__ == '__main__':
    unittest.main()
