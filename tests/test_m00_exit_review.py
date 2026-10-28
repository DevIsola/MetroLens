"""M00 exit gate: actual PR merge accepted; publication still forbidden."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from review_m00_exit import ExitReviewError, review


class ExitReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = review()

    def test_post_merge_completion_is_not_publication(self):
        report = self.result
        self.assertEqual(report["status"], "discovery_accepted_post_merge")
        self.assertTrue(report["repository_rename_verified"])
        self.assertFalse(report["publication_approved"])
        self.assertTrue(report["m00_marked_done"])
        self.assertEqual(report["m01_started"], json.loads((ROOT / "docs/roadmap-status.json").read_text(encoding="utf-8"))["milestones"][1]["status"] != "not_started")
        self.assertIsNone(report["rent_to_income_ratio"])

    def test_renamed_repo_must_have_exact_slug_evidence(self):
        naming = json.loads((ROOT / "docs/branding/m00_t06_name_review.json").read_text())
        self.assertEqual(naming["repository_migration"]["new_repository"], "DevIsola/UrbanGauge")
        self.assertEqual(naming["repository_migration"]["status"], "verified_completed")
        self.assertFalse(naming["trademark_clearance_verified"])

    def test_roadmap_records_actual_github_merge(self):
        roadmap = json.loads((ROOT / "docs/roadmap-status.json").read_text())
        self.assertEqual(roadmap["milestones"][0]["status"], "done")
        self.assertEqual(roadmap["milestones"][0]["prs"], ["https://github.com/DevIsola/UrbanGauge/pull/1"])
        self.assertEqual(roadmap["milestones"][0]["merged_commit"], "87e9d035dfbc841c0282ec35da7a3d29707f7ff1")
        self.assertEqual(roadmap["milestones"][0]["accepted_at"], "2026-10-27T23:05:21Z")
        self.assertEqual(self.result["m01_started"], roadmap["milestones"][1]["status"] != "not_started")

    def test_missing_evidence_directory_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            with self.assertRaises(ExitReviewError):
                review(root=Path(dirname))


if __name__ == "__main__":
    unittest.main()
