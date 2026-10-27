"""Acceptance-negative tests: samples cannot silently become affordability claims."""

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.validate_source_samples import SAMPLE_PATH, assess_rent_income_join, load_and_validate


class OfficialSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_and_validate()
        cls.income = next(r for r in cls.records if r['region_id'] == 'vancouver' and r['metric_id'] == 'median_total_household_income')
        cls.rent = next(r for r in cls.records if r['region_id'] == 'vancouver' and r['metric_id'] == 'average_turnover_2br_rent')

    def test_five_real_manual_observations_and_sources(self):
        self.assertEqual(len(self.records), 5)
        self.assertEqual({r['source_id'] for r in self.records}, {'statcan_census2021_profile', 'cmhc_rms2025_report', 'boc_v39079'})
        self.assertEqual(self.income['value'], '90000')
        self.assertEqual(self.rent['value'], '2696')

    def test_actual_samples_block_period_mismatch(self):
        self.assertEqual(assess_rent_income_join(self.rent, self.income), (False, 'period_mismatch'))

    def test_even_same_year_does_not_clear_unverified_geography(self):
        income = {**self.income, 'reference_period': '2025'}
        self.assertEqual(assess_rent_income_join(self.rent, income), (False, 'geography_unverified'))

    def test_even_same_year_and_verified_geo_population_is_mismatched(self):
        income = {**self.income, 'reference_period': '2025'}
        self.assertEqual(assess_rent_income_join(self.rent, income, geography_verified=True), (False, 'population_statistic_mismatch'))

    def test_different_region_is_never_a_valid_join(self):
        income = {**self.income, 'region_id': 'toronto', 'reference_period': '2025'}
        self.assertEqual(assess_rent_income_join(self.rent, income), (False, 'region_mismatch'))

    def test_incorrect_unit_rejected(self):
        with SAMPLE_PATH.open(newline='', encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
        rows[0]['unit'] = 'CAD_per_month'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sample.csv'
            with path.open('w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, 'semantics'):
                load_and_validate(path)

    def test_duplicate_record_rejected(self):
        with SAMPLE_PATH.open(newline='', encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
        rows.append(dict(rows[0]))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sample.csv'
            with path.open('w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                load_and_validate(path)


if __name__ == '__main__':
    unittest.main()
