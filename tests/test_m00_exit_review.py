"""M00 exit gate: evidence ready for review is not merged acceptance."""
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

    def test_review_is_not_publication_or_completion(self):
        report = self.result
        self.assertEqual(report["status"], "discovery_evidence_ready_for_manual_exit_review")
        self.assertTrue(report["repository_rename_verified"])
        self.assertFalse(report["publication_approved"])
        self.assertFalse(report["m00_marked_done"])
        self.assertFalse(report["m01_started"])
        self.assertIsNone(report["rent_to_income_ratio"])

    def test_renamed_repo_must_have_exact_slug_evidence(self):
        naming = json.loads((ROOT / "docs/branding/m00_t06_name_review.json").read_text())
        self.assertEqual(naming["repository_migration"]["new_repository"], "DevIsola/UrbanGauge")
        self.assertEqual(naming["repository_migration"]["status"], "verified_completed")
        self.assertFalse(naming["trademark_clearance_verified"])

    def test_roadmap_has_no_fabricated_merge(self):
        roadmap = json.loads((ROOT / "docs/roadmap-status.json").read_text())
        self.assertEqual(roadmap["milestones"][0]["status"], "in_progress")
        self.assertIsNone(roadmap["milestones"][0]["merged_commit"])
        self.assertIsNone(roadmap["milestones"][0]["accepted_at"])
        self.assertEqual(roadmap["milestones"][1]["status"], "not_started")

    def test_missing_evidence_directory_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            with self.assertRaises(ExitReviewError):
                review(root=Path(dirname))


if __name__ == "__main__":
    unittest.main()
