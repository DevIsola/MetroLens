"""Regression tests for the auditable roadmap status contract."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.sync_roadmap import (
    ROADMAP_PATH,
    ROOT,
    START,
    END,
    STATUS_PATH,
    StatusValidationError,
    update_markdown,
    validate_status,
)


class RoadmapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))

    def test_status_is_valid(self):
        validate_status(self.data)

    def test_checked_in_table_matches_status(self):
        text = ROADMAP_PATH.read_text(encoding="utf-8")
        self.assertEqual(text, update_markdown(text, self.data))
        self.assertIn("M00       | Discovery", text)

    def test_script_check_exit_zero(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sync_roadmap.py"), "--check"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_duplicate_or_missing_milestone_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["milestones"][1]["id"] = "M00"
        with self.assertRaises(StatusValidationError):
            validate_status(bad)

    def test_done_without_merge_evidence_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["milestones"][0].update(status="done", prs=[], evidence=[], merged_commit=None, accepted_at=None)
        with self.assertRaises(StatusValidationError):
            validate_status(bad)

    def test_done_with_fake_sha_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["milestones"][0].update(
            status="done", prs=["https://github.com/owner/repo/pull/1"],
            evidence=["https://github.com/owner/repo/actions/runs/1"],
            merged_commit="HEAD", accepted_at="2026-10-26",
        )
        with self.assertRaises(StatusValidationError):
            validate_status(bad)

    def test_generated_block_preserves_rest_of_roadmap(self):
        orig = ROADMAP_PATH.read_text(encoding="utf-8")
        updated = update_markdown(orig, self.data)
        self.assertEqual(orig.split(START)[0], updated.split(START)[0])
        self.assertEqual(orig.split(END)[1], updated.split(END)[1])


if __name__ == "__main__":
    unittest.main()
