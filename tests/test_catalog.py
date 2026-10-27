"""Verify provenance boundaries of the deliberately narrow M00 candidate scope."""

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CMASelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "docs" / "cma-candidates.csv").open(newline="", encoding="utf-8") as f:
            cls.records = list(csv.DictReader(f))

    def test_five_to_ten_candidates(self):
        self.assertGreaterEqual(len(self.records), 5)
        self.assertLessEqual(len(self.records), 10)

    def test_unique_ids_and_codes(self):
        self.assertEqual(len({v["region_id"] for v in self.records}), len(self.records))
        self.assertEqual(len({v["cma_code_2021"] for v in self.records}), len(self.records))
        for row in self.records:
            self.assertRegex(row["cma_code_2021"], r"^\d{3}$")

    def test_official_2021_codes_not_city_codes(self):
        # 2021-based codes checked against the Statistics Canada T1FF reference.
        expected = {
            "halifax": "205", "montreal": "462", "toronto": "535",
            "winnipeg": "602", "calgary": "825", "edmonton": "835",
            "vancouver": "933", "victoria": "935",
        }
        self.assertEqual(
            {v["region_id"]: v["cma_code_2021"] for v in self.records}, expected
        )

    def test_unverified_cmhc_matches_are_explicit(self):
        for row in self.records:
            self.assertEqual(row["cmhc_geography_match"], "pending")
            self.assertEqual(row["scope_status"], "candidate")


if __name__ == "__main__":
    unittest.main()
