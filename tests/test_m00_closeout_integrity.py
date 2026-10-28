"""Regression gates for the verified M00 discovery merge record."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
from scripts.sync_roadmap import StatusValidationError, validate_status
from scripts.review_m00_exit import review

ROOT = Path(__file__).resolve().parent.parent

class M00CloseoutIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "docs/roadmap-status.json").read_text(encoding="utf-8"))

    def test_merged_pr_and_sha_are_real_recorded_evidence(self):
        a = self.data["milestones"][0]
        self.assertEqual(a["prs"], ["https://github.com/DevIsola/UrbanGauge/pull/1"])
        self.assertEqual(a["merged_commit"], "87e9d035dfbc841c0282ec35da7a3d29707f7ff1")
        self.assertEqual(a["accepted_at"], "2026-10-27T23:05:21Z")

    def test_absent_merge_sha_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["milestones"][0]["merged_commit"] = None
        with self.assertRaises(StatusValidationError):
            validate_status(bad)

    def test_absent_pr_evidence_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["milestones"][0]["prs"] = []
        with self.assertRaises(StatusValidationError):
            validate_status(bad)

    def test_completed_discovery_does_not_approve_publication(self):
        report = review()
        self.assertTrue(report["m00_marked_done"])
        self.assertFalse(report["publication_approved"])
        self.assertIsNone(report["rent_to_income_ratio"])
        self.assertFalse(report["automatic_deployment_enabled"])
        self.assertEqual(report["m01_started"], self.data["milestones"][1]["status"] != "not_started")

if __name__ == "__main__":
    unittest.main()
