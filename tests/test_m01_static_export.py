"""M01-T07: local-only export validation without Next runtime dependencies."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_m01_static_export import StaticExportError, check_contract, smoke_export


class StaticExportContractTests(unittest.TestCase):
    FILES = (
        "frontend/next.config.ts", "frontend/app/page.tsx",
        "frontend/app/methodology/page.tsx", ".github/workflows/verify.yml",
        "docs/architecture/static_pipeline_policy.json", "docs/roadmap-status.json",
    )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in self.FILES:
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dest)

    def modify(self, name, old, new):
        p = self.root / name
        text = p.read_text(encoding="utf-8")
        self.assertIn(old, text)
        p.write_text(text.replace(old, new, 1), encoding="utf-8")

    def prepare_export(self, prefix="/UrbanGauge"):
        out = self.root / "frontend/out"
        for rel in ("methodology", "_next/static/css", "_next/static/chunks"):
            (out / rel).mkdir(parents=True, exist_ok=True)
        (out / "_next/static/css/test.css").write_text("body{color:#fff}", encoding="utf-8")
        (out / "_next/static/chunks/app.js").write_text("console.log('synthetic');", encoding="utf-8")
        assets = (
            f'<link rel="stylesheet" href="{prefix}/_next/static/css/test.css">'
            f'<script src="{prefix}/_next/static/chunks/app.js"></script>'
        )
        home = f'<html><head>{assets}</head><body><a href="{prefix}/methodology/">Methods</a></body></html>'
        detail = f'<html><head>{assets}</head><body><a href="{prefix}/">Home</a></body></html>'
        (out / "index.html").write_text(home, encoding="utf-8")
        (out / "methodology/index.html").write_text(detail, encoding="utf-8")
        return out

    def test_real_repository_contract(self):
        report = check_contract()
        self.assertEqual(report["status"], "static_export_contract_validated")
        self.assertFalse(report["publication_approved"])

    def test_valid_fixture_contract(self):
        self.assertEqual(check_contract(self.root)["deep_link_route"], "/methodology/")

    def test_non_static_export_rejected(self):
        self.modify("frontend/next.config.ts", 'output: "export"', 'output: "standalone"')
        with self.assertRaises(StaticExportError):
            check_contract(self.root)

    def test_missing_navigation_link_rejected(self):
        self.modify("frontend/app/page.tsx", 'href="/methodology"', 'href="/unrelated"')
        with self.assertRaises(StaticExportError):
            check_contract(self.root)

    def test_publication_gate_change_rejected(self):
        p = self.root / "docs/architecture/static_pipeline_policy.json"
        policy = json.loads(p.read_text(encoding="utf-8"))
        policy["publication_gates"]["public_data_export_approved"] = True
        p.write_text(json.dumps(policy), encoding="utf-8")
        with self.assertRaises(StaticExportError):
            check_contract(self.root)

    def test_verify_must_remain_manual(self):
        self.modify(".github/workflows/verify.yml", "  workflow_dispatch:", "  push:")
        with self.assertRaises(StaticExportError):
            check_contract(self.root)

    def test_smoke_requires_real_export_paths(self):
        with self.assertRaises(StaticExportError):
            smoke_export(self.root)

    def test_prefix_smoke_fetches_pages_and_assets(self):
        self.prepare_export()
        report = smoke_export(self.root, prefix="/UrbanGauge")
        self.assertEqual(report["status"], "loopback_static_export_smoke_passed")
        self.assertEqual(report["checked_static_assets"], 2)
        self.assertEqual(len(report["checked_pages"]), 2)
        self.assertFalse(report["external_network_used"])

    def test_root_mode_smoke(self):
        self.prepare_export(prefix="")
        self.assertEqual(smoke_export(self.root, prefix="")["base_path"], "")

    def test_unprefixed_asset_is_rejected(self):
        out = self.prepare_export()
        path = out / "index.html"
        path.write_text(path.read_text(encoding="utf-8").replace('/UrbanGauge/_next/', '/_next/'), encoding="utf-8")
        with self.assertRaises(StaticExportError):
            smoke_export(self.root)

    def test_invalid_base_path_rejected(self):
        self.prepare_export()
        with self.assertRaises(StaticExportError):
            smoke_export(self.root, prefix="/UrbanGauge/../admin")


if __name__ == "__main__":
    unittest.main()
