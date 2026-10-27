"""M01-T01 workspace tests: no network or third-party modules."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from activate_m01 import ActivationError, MERGE_SHA, MERGED_PR, M01_NOTE, prepare
from validate_m01_workspace import WorkspaceError, validate


class WorkspaceTests(unittest.TestCase):
    def make_workspace_copy(self, folder: Path) -> Path:
        required = [
            ".editorconfig", "docs/DEVELOPMENT.md", "docs/M01_FOUNDATION_SCOPE.md",
            "frontend/README.md", "pipeline/README.md", "scripts/activate_m01.py",
            "docs/roadmap-status.json", "docs/architecture/static_pipeline_policy.json",
            ".github/workflows/verify.yml", ".github/workflows/pages.yml",
        ]
        for relative in required:
            output = folder / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, output)
        return folder

    def test_public_export_gate_cannot_be_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = self.make_workspace_copy(Path(tmp))
            policy_path = workspace / "docs/architecture/static_pipeline_policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["publication_gates"]["public_data_export_approved"] = True
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaises(WorkspaceError):
                validate(workspace)

    def test_automatic_pages_workflow_trigger_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = self.make_workspace_copy(Path(tmp))
            path = workspace / ".github/workflows/pages.yml"
            path.write_text(path.read_text(encoding="utf-8") + "\n  push:\n", encoding="utf-8")
            with self.assertRaises(WorkspaceError):
                validate(workspace)

    def test_m01_cannot_be_fabricated_as_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = self.make_workspace_copy(Path(tmp))
            path = workspace / "docs/roadmap-status.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["milestones"][1]["status"] = "done"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(WorkspaceError):
                validate(workspace)

    def test_real_repository_workspace(self):
        self.assertEqual(validate()["status"], "m01_t01_workspace_validated")

    def test_activation_preserves_later_m01_notes(self):
        # Once M01-T02 begins, the T01 activator must not rewrite its notes.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/architecture").mkdir(parents=True)
            status = json.loads((ROOT / "docs/roadmap-status.json").read_text(encoding="utf-8"))
            status["milestones"][1]["notes"] = "M01-T01 done; M01-T02 toolchain work in progress"
            (root / "docs/roadmap-status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
            (root / "docs/NORTHSTAR_MASTER_ROADMAP.md").write_text(
                (ROOT / "docs/NORTHSTAR_MASTER_ROADMAP.md").read_text(encoding="utf-8"), encoding="utf-8")
            (root / "docs/architecture/static_pipeline_policy.json").write_text(
                (ROOT / "docs/architecture/static_pipeline_policy.json").read_text(encoding="utf-8"), encoding="utf-8")
            updated, _, _ = prepare(root)
            self.assertIn("M01-T02 toolchain work", updated)

    def test_activation_rejects_unmerged_m00(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/architecture").mkdir(parents=True)
            status = json.loads((ROOT / "docs/roadmap-status.json").read_text(encoding="utf-8"))
            status["milestones"][0]["status"] = "in_progress"
            (root / "docs/roadmap-status.json").write_text(json.dumps(status), encoding="utf-8")
            with self.assertRaises((ActivationError, ValueError)):
                prepare(root)

    def test_activation_preserves_no_real_m01_acceptance(self):
        status = json.loads((ROOT / "docs/roadmap-status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["milestones"][0]["merged_commit"], MERGE_SHA)
        self.assertIn(MERGED_PR, status["milestones"][0]["prs"])
        self.assertEqual(status["milestones"][1]["status"], "in_progress")
        self.assertEqual(status["milestones"][1]["notes"], M01_NOTE)
        self.assertIsNone(status["milestones"][1]["merged_commit"])

    def test_missing_editorconfig_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WorkspaceError):
                validate(Path(tmp))

    def test_future_dependencies_do_not_change_t01_scope(self):
        scope = (ROOT / "docs/M01_FOUNDATION_SCOPE.md").read_text(encoding="utf-8")
        self.assertIn("M01-T02", scope)
        self.assertIn("Licence", scope)
        self.assertIn("workflow_dispatch", scope)


if __name__ == "__main__":
    unittest.main()
