"""M01-T06 offline security controls: no hosted settings, network, or credentials."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_m01_security import SecurityError, audit_paths, validate


class SecurityContractTests(unittest.TestCase):
    FILES = (
        "docs/architecture/m01_t06_security_policy.json",
        "docs/architecture/static_pipeline_policy.json",
        "docs/roadmap-status.json",
        ".github/workflows/verify.yml",
        ".github/workflows/pages.yml",
        ".node-version", ".python-version", "pyproject.toml", "uv.lock",
        "package.json", "frontend/package.json", "pnpm-lock.yaml",
        "SECURITY.md", "docs/M01_T06_SECURITY_AND_DEPENDENCIES.md",
        "docs/adr/ADR-0005-manual-security-and-dependency-governance.md",
        "docs/adr/README.md", "CHANGELOG.md",
    )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in self.FILES:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, p)
        self.paths = list(self.FILES)

    def contract(self) -> dict:
        return validate(self.root, tracked_files=self.paths)

    def edit(self, name: str, old: str, new: str) -> None:
        p = self.root / name
        t = p.read_text(encoding="utf-8")
        self.assertIn(old, t)
        p.write_text(t.replace(old, new, 1), encoding="utf-8")

    def policy(self, key: str, value) -> None:
        p = self.root / "docs/architecture/m01_t06_security_policy.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data[key] = value
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def test_fixture_contract_valid(self):
        result = self.contract()
        self.assertEqual(result["status"], "offline_security_contract_validated")
        self.assertFalse(result["github_secret_scanning_verified"])
        self.assertFalse(result["external_dependency_audit_verified"])
        self.assertFalse(result["publication_approved"])

    def test_real_repository_contract_valid(self):
        result = validate()
        self.assertEqual(result["milestone"], "M01-T06")
        self.assertGreater(result["checked_git_visible_text_files"], 10)

    def test_cannot_claim_dependabot_enabled(self):
        self.policy("automated_dependency_updates_enabled_by_increment", True)
        with self.assertRaises(SecurityError):
            self.contract()

    def test_cannot_claim_github_secret_scanning_verified(self):
        self.policy("github_secret_scanning_verified", True)
        with self.assertRaises(SecurityError):
            self.contract()

    def test_cannot_claim_external_dependency_audit(self):
        self.policy("external_dependency_audit_verified", True)
        with self.assertRaises(SecurityError):
            self.contract()

    def test_cannot_claim_publisher_publication(self):
        self.policy("publication_approved", True)
        with self.assertRaises(SecurityError):
            self.contract()

    def test_m01_must_remain_in_progress(self):
        p = self.root / "docs/roadmap-status.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["milestones"][1]["status"] = "not_started"
        p.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_official_source_export_is_still_blocked(self):
        p = self.root / "docs/architecture/static_pipeline_policy.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["publication_gates"]["publisher_reuse_approved"] = True
        p.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_verify_push_trigger_rejected(self):
        self.edit(".github/workflows/verify.yml", "  workflow_dispatch:", "  push:")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_verify_write_permission_rejected(self):
        self.edit(".github/workflows/verify.yml", "  contents: read", "  contents: write")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_verify_cannot_drop_security_check(self):
        self.edit(".github/workflows/verify.yml", "run: python scripts/validate_m01_security.py", "run: echo skipped")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_pages_deploy_permission_escalation_rejected(self):
        self.edit(".github/workflows/pages.yml", "      pages: write", "      actions: write\n      pages: write")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_pages_unconfirmed_deploy_rejected(self):
        self.edit(".github/workflows/pages.yml", "inputs.confirm_release == true", "inputs.confirm_release == false")
        with self.assertRaises(SecurityError):
            self.contract()

    def test_unreviewed_dependency_range_rejected(self):
        self.edit("frontend/package.json", '"next": "16.4.3"', '"next": "^16.4.3"')
        with self.assertRaises(SecurityError):
            self.contract()

    def test_dependabot_schedule_file_rejected(self):
        name = ".github/dependabot.yml"
        p = self.root / name
        p.write_text("version: 2\nupdates: []\n", encoding="utf-8")
        with self.assertRaises(SecurityError):
            validate(self.root, tracked_files=self.paths + [name])

    def test_tracked_environment_secret_path_rejected(self):
        name = ".env.production"
        (self.root / name).write_text("FAKE_ONLY=placeholder\n", encoding="utf-8")
        with self.assertRaises(SecurityError):
            audit_paths(self.root, [name])

    def test_tracked_raw_source_path_rejected(self):
        name = "pipeline/data/raw/source.zip"
        p = self.root / name
        p.parent.mkdir(parents=True)
        p.write_bytes(b"placeholder")
        with self.assertRaises(SecurityError):
            audit_paths(self.root, [name])

    def test_token_indicator_rejected(self):
        name = "scratch.md"
        (self.root / name).write_text("token=" + "ghp_" + "a" * 36, encoding="utf-8")
        with self.assertRaises(SecurityError):
            audit_paths(self.root, [name])

    def test_private_key_header_rejected(self):
        name = "scratch.txt"
        (self.root / name).write_text("-----BEGIN " + "PRIVATE KEY-----", encoding="utf-8")
        with self.assertRaises(SecurityError):
            audit_paths(self.root, [name])

    def test_non_secret_placeholder_allowed(self):
        name = "scratch.md"
        (self.root / name).write_text("GitHub token: ghp_REDACTED", encoding="utf-8")
        self.assertEqual(audit_paths(self.root, [name]), 1)


if __name__ == "__main__":
    unittest.main()
