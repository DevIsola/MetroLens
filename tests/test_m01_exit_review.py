"""M01 pre-merge safety contract; no hosted operations or publication."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from review_m01_exit import M01ExitError, REQUIRED, review


class M01PremergeReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in REQUIRED:
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dest)

    def edit(self, rel: str, old: str, new: str) -> None:
        p = self.root / rel
        s = p.read_text(encoding="utf-8")
        self.assertIn(old, s, f"Expected source span missing: {rel}")
        p.write_text(s.replace(old, new, 1), encoding="utf-8")

    def json_change(self, path: str, mutate) -> None:
        p = self.root / path
        value = json.loads(p.read_text(encoding="utf-8"))
        mutate(value)
        p.write_text(json.dumps(value, indent=2), encoding="utf-8")

    def test_real_repository_contract(self):
        report = review()
        self.assertEqual(report["status"], "premerge_contract_validated_review_pending")
        self.assertFalse(report["pr_merged"])
        self.assertFalse(report["public_data_export_approved"])

    def test_fixture_valid(self):
        report = review(self.root)
        self.assertEqual(report["task_contracts_present"], 7)
        self.assertTrue(report["requires_maintainer_review"])

    def test_premerge_cannot_claim_m01_done(self):
        self.json_change("docs/roadmap-status.json", lambda d: d["milestones"][1].update(status="done"))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_premerge_cannot_claim_merge_sha(self):
        self.json_change("docs/roadmap-status.json", lambda d: d["milestones"][1].update(merged_commit="a" * 40))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_m00_merge_sha_is_pinned(self):
        self.json_change("docs/roadmap-status.json", lambda d: d["milestones"][0].update(merged_commit="b" * 40))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_roadmap_must_be_synchronized(self):
        self.edit("docs/NORTHSTAR_MASTER_ROADMAP.md", "<!-- ROADMAP_STATUS_START -->", "<!-- ROADMAP_START -->")
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_missing_task_doc_rejected(self):
        (self.root / "docs/M01_T03_APPLICATION_SCAFFOLD.md").unlink()
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_publisher_gate_must_remain_closed(self):
        self.json_change("docs/architecture/static_pipeline_policy.json", lambda d: d["publication_gates"].update(public_data_export_approved=True))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_auto_ci_must_remain_disabled(self):
        self.json_change("docs/architecture/static_pipeline_policy.json", lambda d: d["execution"].update(push_auto_ci=True))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_verify_auto_trigger_rejected(self):
        self.edit(".github/workflows/verify.yml", "  workflow_dispatch:", "  push:")
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_pages_auto_trigger_rejected(self):
        self.edit(".github/workflows/pages.yml", "  workflow_dispatch:", "  schedule:")
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_verify_permission_escalation_rejected(self):
        self.edit(".github/workflows/verify.yml", "  contents: read", "  contents: write")
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_false_license_selection_rejected(self):
        self.json_change("docs/architecture/m01_t04_governance_policy.json", lambda d: d.update(license_selected=True))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_false_secret_scanning_claim_rejected(self):
        self.json_change("docs/architecture/m01_t06_security_policy.json", lambda d: d.update(github_secret_scanning_verified=True))
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_missing_real_static_smoke_command_rejected(self):
        self.edit(".github/workflows/verify.yml", "run: python scripts/validate_m01_static_export.py --smoke --base-path /UrbanGauge", "run: echo skipped")
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_windows_empty_arg_regression_rejected(self):
        self.edit("docs/M01_T07_STATIC_EXPORT.md", "--smoke --base-path=", '--smoke --base-path ""')
        with self.assertRaises(M01ExitError):
            review(self.root)

    def test_missing_static_deep_link_rejected(self):
        (self.root / "frontend/app/methodology/page.tsx").unlink()
        with self.assertRaises(M01ExitError):
            review(self.root)


if __name__ == "__main__":
    unittest.main()
