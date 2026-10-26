"""M00-T03 comparison policy: eligibility for review is not publication."""

from contextlib import redirect_stdout
import io
import json
import unittest

from scripts.validate_source_samples import load_and_validate
from scripts.assess_metric_compatibility import assess_pair, main


class MetricComparabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = load_and_validate()
        cls.rent = next(r for r in rows if r['region_id'] == 'vancouver' and r['metric_id'] == 'average_turnover_2br_rent')
        cls.income = next(r for r in rows if r['region_id'] == 'vancouver' and r['metric_id'] == 'median_total_household_income')

    def eligible_pair(self):
        rent = {**self.rent, 'reference_period': '2020-10', 'quality_flag': 'observed', 'source_geo_code': 'CMHC-933'}
        income = {**self.income, 'quality_flag': 'observed'}
        evidence = {
            'geography_crosswalk': {'status': 'reviewed', 'region_id': 'vancouver',
                                    'rent_geo_code': 'CMHC-933', 'income_geo_code': '2021S0503933',
                                    'boundary_vintage': '2021', 'evidence_url': 'https://example.org/geo'},
            'period_alignment': {'status': 'reviewed', 'method': 'same_calendar_year',
                                 'evidence_url': 'https://example.org/period'},
            'population_interpretation': {'status': 'reviewed',
                                          'methodology_note': 'Mean turnover rent compared to median household income; not a household burden estimate',
                                          'evidence_url': 'https://example.org/methodology'},
            'reuse_terms': {'status': 'reviewed',
                            'statcan_terms_url': 'https://example.org/statcan',
                            'cmhc_terms_url': 'https://example.org/cmhc'},
        }
        return rent, income, evidence

    def test_real_samples_block_mismatched_year(self):
        result = assess_pair(self.rent, self.income)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('reference_year_mismatch', result['blockers'])
        self.assertIn('geography_crosswalk_not_reviewed', result['evidence_gaps'])
        self.assertFalse(result['approved_for_publication'])
        self.assertIsNone(result['computed_value'])

    def test_same_year_without_evidence_not_review_ready(self):
        rent, income, _ = self.eligible_pair()
        result = assess_pair(rent, income)
        self.assertEqual(result['status'], 'needs_evidence')
        self.assertEqual(result['blockers'], [])
        self.assertIn('population_interpretation_not_reviewed', result['evidence_gaps'])

    def test_complete_synthetic_metadata_requires_independent_review(self):
        rent, income, evidence = self.eligible_pair()
        result = assess_pair(rent, income, evidence=evidence)
        self.assertEqual(result['status'], 'ready_for_methodology_review')
        self.assertEqual(result['evidence_gaps'], [])
        self.assertTrue(result['methodology_review_required'])
        self.assertFalse(result['approved_for_publication'])
        self.assertIsNone(result['computed_value'])

    def test_geo_code_must_match_row_even_with_reviewed_status(self):
        rent, income, evidence = self.eligible_pair()
        evidence['geography_crosswalk']['rent_geo_code'] = 'other-region'
        self.assertIn('geography_crosswalk_not_reviewed', assess_pair(rent, income, evidence=evidence)['evidence_gaps'])

    def test_unverified_geocode_rejected_even_if_reviewed(self):
        rent, income, evidence = self.eligible_pair()
        rent['source_geo_code'] = 'unverified'
        evidence['geography_crosswalk']['rent_geo_code'] = 'unverified'
        self.assertIn('geography_crosswalk_not_reviewed', assess_pair(rent, income, evidence=evidence)['evidence_gaps'])

    def test_http_evidence_rejected(self):
        rent, income, evidence = self.eligible_pair()
        evidence['reuse_terms']['cmhc_terms_url'] = 'http://example.org/cmhc'
        self.assertIn('reuse_terms_not_reviewed', assess_pair(rent, income, evidence=evidence)['evidence_gaps'])

    def test_population_definition_cannot_silently_change(self):
        rent, income, evidence = self.eligible_pair()
        rent['segment'] = 'asking_rent'
        self.assertIn('population_definition_mismatch', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_income_median_cannot_silently_become_mean(self):
        rent, income, evidence = self.eligible_pair()
        income['statistic'] = 'mean'
        self.assertIn('statistic_mismatch', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_wrong_source_role_rejected(self):
        rent, income, evidence = self.eligible_pair()
        income['source_id'] = 'boc_v39079'
        self.assertIn('source_role_mismatch', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_wrong_publisher_host_requires_provenance(self):
        rent, income, evidence = self.eligible_pair()
        rent['source_url'] = 'https://example.org/rent'
        self.assertIn('source_provenance_missing', assess_pair(rent, income, evidence=evidence)['evidence_gaps'])

    def test_bad_unit_rejected(self):
        rent, income, evidence = self.eligible_pair()
        income['unit'] = 'CAD_per_month'
        self.assertIn('unit_mismatch', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_quality_suppressed_rejected(self):
        rent, income, evidence = self.eligible_pair()
        income['quality_flag'] = 'suppressed'
        self.assertIn('quality_flags_not_verified', assess_pair(rent, income, evidence=evidence)['evidence_gaps'])

    def test_nonfinite_value_rejected(self):
        rent, income, evidence = self.eligible_pair()
        rent['value'] = 'NaN'
        self.assertIn('invalid_or_missing_value', assess_pair(rent, income, evidence=evidence)['blockers'])
        rent['value'] = 0
        self.assertIn('invalid_or_missing_value', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_invalid_calendar_period_rejected(self):
        rent, income, evidence = self.eligible_pair()
        rent['reference_period'] = '2020-13'
        self.assertIn('invalid_period_format', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_different_regions_rejected(self):
        rent, income, evidence = self.eligible_pair()
        income['region_id'] = 'toronto'
        self.assertIn('region_mismatch', assess_pair(rent, income, evidence=evidence)['blockers'])

    def test_missing_evidence_not_considered_approved(self):
        rent, income, evidence = self.eligible_pair()
        evidence['population_interpretation']['status'] = 'pending'
        self.assertEqual(assess_pair(rent, income, evidence=evidence)['status'], 'needs_evidence')

    def test_cli_discovery_samples_outputs_no_value(self):
        with io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(main([]), 0)
            report = json.loads(output.getvalue())
        self.assertEqual(len(report['comparisons']), 2)
        self.assertTrue(all(c['status'] == 'blocked' and c['computed_value'] is None
                            and not c['approved_for_publication'] for c in report['comparisons']))


if __name__ == '__main__':
    unittest.main()
