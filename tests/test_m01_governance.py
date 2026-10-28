"""M01-T04 offline governance contract: mock hostile edits, no hosted mutations."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_m01_governance import FORMS, WORKFLOWS, GovernanceError, validate


class GovernanceTests(unittest.TestCase):
    FILES = (
        *FORMS, *WORKFLOWS,
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/PULL_REQUEST_TEMPLATE.md", "CONTRIBUTING.md",
        "docs/M01_T04_REPOSITORY_GOVERNANCE.md",
        "docs/architecture/m01_t04_governance_policy.json",
        "docs/roadmap-status.json",
        "docs/architecture/static_pipeline_policy.json",
    )

    def fixture(self, root: Path) -> Path:
        for relative in self.FILES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root

    def test_real_repo_files_validate(self):
        report = validate()
        self.assertEqual(report["status"], "repository_governance_files_validated")
        self.assertEqual(report["issue_forms"], 3)
        self.assertFalse(report["required_status_checks_enabled_by_increment"])
        self.assertFalse(report["publication_approved"])

    def test_missing_issue_form_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            (root / FORMS[0]).unlink()
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_duplicate_form_ids_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / FORMS[0]
            source = p.read_text(encoding="utf-8")
            p.write_text(source.replace("id: environment", "id: reproduction"), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_uncreated_labels_not_assigned(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / FORMS[1]
            p.write_text(p.read_text(encoding="utf-8") + "\nlabels: [type:feature]\n", encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_manual_verify_cannot_be_auto_triggered(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / WORKFLOWS[0]
            p.write_text(p.read_text(encoding="utf-8").replace("  workflow_dispatch:\n", "  push:\n"), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_manual_pages_cannot_gain_schedule(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / WORKFLOWS[1]
            p.write_text(p.read_text(encoding="utf-8").replace("  workflow_dispatch:\n", "  schedule:\n", 1), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_publication_gate_must_remain_false(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / "docs/architecture/static_pipeline_policy.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["storage"]["public_export"]["publication_active"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_unverified_required_status_checks_not_claimed(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / "docs/architecture/m01_t04_governance_policy.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["required_status_checks_enabled_by_increment"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_m00_not_done_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / "docs/roadmap-status.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["milestones"][0]["status"] = "in_progress"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_m01_not_started_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / "docs/roadmap-status.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["milestones"][1]["status"] = "not_started"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)

    def test_missing_pr_disclosures_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / ".github/PULL_REQUEST_TEMPLATE.md"
            p.write_text(p.read_text(encoding="utf-8").replace("No new push/PR/scheduled", "Push automated"), encoding="utf-8")
            with self.assertRaises(GovernanceError):
                validate(root)


if __name__ == "__main__":
    unittest.main()
