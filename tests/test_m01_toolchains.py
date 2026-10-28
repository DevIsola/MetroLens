"""Offline M01-T02 contract checks; no Node, uv, network or data files required."""
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
from validate_m01_toolchains import ToolchainError, validate


class ToolchainContractTests(unittest.TestCase):
    FILES = (
        ".node-version", ".python-version", "package.json", "pnpm-workspace.yaml",
        "pnpm-lock.yaml", "pyproject.toml", "uv.lock",
        "docs/roadmap-status.json", "docs/architecture/static_pipeline_policy.json",
        ".github/workflows/verify.yml", ".github/workflows/pages.yml",
    )

    def fixture(self, root: Path) -> Path:
        for file in self.FILES:
            target = root / file
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / file, target)
        return root

    def test_real_workspace_manifest_is_valid(self):
        report = validate()
        self.assertEqual(report["status"], "toolchain_contract_validated")
        self.assertEqual(report["node"], "24.22.1")
        self.assertEqual(report["pnpm"], "10.34.9")
        self.assertFalse(report["publication_approved"])

    def test_wrong_pnpm_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            package = json.loads((root / "package.json").read_text(encoding="utf-8"))
            package["packageManager"] = "pnpm@latest"
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)

    def test_mismatched_node_pin_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            (root / ".node-version").write_text("22.16.0\n", encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)

    def test_broken_pnpm_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            (root / "pnpm-lock.yaml").write_text("lockfileVersion: '7.0'\n", encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)

    def test_broken_python_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            (root / "uv.lock").write_text("version = 1\nrequires-python = '>=3.10'\n", encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)

    def test_future_package_dependencies_are_not_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            package = json.loads((root / "package.json").read_text(encoding="utf-8"))
            package["devDependencies"] = {"typescript": "6.0.0"}
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            # Future package-lock coherence belongs to pnpm --frozen-lockfile, not a fake static assertion.
            self.assertEqual(validate(root)["status"], "toolchain_contract_validated")

    def test_public_export_cannot_be_enabled(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            path = root / "docs/architecture/static_pipeline_policy.json"
            policy = json.loads(path.read_text(encoding="utf-8"))
            policy["publication_gates"]["public_data_export_approved"] = True
            path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)

    def test_automatic_workflows_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / ".github/workflows/verify.yml"
            p.write_text(p.read_text(encoding="utf-8") + "\n  push:\n", encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)

    def test_completed_m01_cannot_be_fabricated(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            p = root / "docs/roadmap-status.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["milestones"][1]["status"] = "done"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ToolchainError):
                validate(root)


if __name__ == "__main__":
    unittest.main()
