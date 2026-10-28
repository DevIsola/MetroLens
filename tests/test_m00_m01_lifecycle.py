"""M00 acceptance is permanent evidence; it cannot block later M01 work."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.review_m00_exit import ExitReviewError, review

ROOT = Path(__file__).resolve().parent.parent
INPUTS = (
    "docs/branding/m00_t06_name_review.json",
    "docs/roadmap-status.json",
    "docs/architecture/static_pipeline_policy.json",
    "docs/evidence-vancouver-m00.json",
    "README.md",
    "docs/design/M00_T04_REVIEW_DECISION.md",
    "docs/architecture/M00_T05_REVIEW_DECISION.md",
    ".github/workflows/verify.yml",
    ".github/workflows/pages.yml",
)

class M00M01LifecycleTests(unittest.TestCase):
    def fixture(self, root):
        for name in INPUTS:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        status_path = root / "docs/roadmap-status.json"
        return status_path, json.loads(status_path.read_text(encoding="utf-8"))

    def test_m00_review_survives_m01_start(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = self.fixture(Path(temp))
            for state in ("not_started", "in_progress"):
                with self.subTest(m01=state):
                    data["milestones"][1]["status"] = state
                    path.write_text(json.dumps(data), encoding="utf-8")
                    outcome = review(root=Path(temp))
                    self.assertEqual(outcome["status"], "discovery_accepted_post_merge")
                    self.assertEqual(outcome["m01_started"], state != "not_started")
                    self.assertTrue(outcome["m00_marked_done"])
                    self.assertFalse(outcome["publication_approved"])
                    self.assertIsNone(outcome["rent_to_income_ratio"])

    def test_m00_cannot_be_reopened_or_approve_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, data = self.fixture(root)
            data["milestones"][1]["status"] = "in_progress"
            data["milestones"][0]["status"] = "in_progress"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ExitReviewError):
                review(root=root)
            data["milestones"][0]["status"] = "done"
            path.write_text(json.dumps(data), encoding="utf-8")
            policy_path = root / "docs/architecture/static_pipeline_policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["publication_gates"]["public_data_export_approved"] = True
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaises(ExitReviewError):
                review(root=root)

if __name__ == "__main__":
    unittest.main()
