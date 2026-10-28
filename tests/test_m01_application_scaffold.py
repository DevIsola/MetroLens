"""M01-T03 modular static foundation; no network or npm dependencies in these tests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_m01_frontend import ScaffoldError, review

sys.path.insert(0, str(ROOT / "pipeline/src"))
from urbangauge_pipeline import SourceReference


class ApplicationScaffoldTests(unittest.TestCase):
    FILES = (
        "package.json", "frontend/package.json", "frontend/tsconfig.json",
        "frontend/next.config.ts", "frontend/app/page.tsx", "frontend/app/layout.tsx",
        "frontend/app/globals.css", "pipeline/src/urbangauge_pipeline/contracts.py",
        "pnpm-workspace.yaml", "pnpm-lock.yaml", "docs/roadmap-status.json",
        "docs/architecture/static_pipeline_policy.json",
    )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in self.FILES:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)

    def replace(self, name: str, old: str, new: str):
        file = self.root / name
        text = file.read_text(encoding="utf-8")
        self.assertIn(old, text)
        file.write_text(text.replace(old, new), encoding="utf-8")

    def test_valid_scaffold_after_lockfile_resolved(self):
        result = review(self.root)
        self.assertEqual(result["status"], "static_frontend_scaffold_validated")
        self.assertTrue(result["strict_typescript"])
        self.assertFalse(result["publication_approved"])

    def test_unresolved_frontend_lockfile_is_rejected(self):
        self.replace("pnpm-lock.yaml", "  frontend:", "  outdated:")
        with self.assertRaises(ScaffoldError):
            review(self.root)

    def test_non_static_next_config_is_rejected(self):
        self.replace("frontend/next.config.ts", 'output: "export"', 'output: "standalone"')
        with self.assertRaises(ScaffoldError):
            review(self.root)

    def test_typescript_strict_required(self):
        self.replace("frontend/tsconfig.json", '"strict": true', '"strict": false')
        with self.assertRaises(ScaffoldError):
            review(self.root)

    def test_automatic_deploy_cannot_be_enabled(self):
        path = self.root / "docs/architecture/static_pipeline_policy.json"
        d = json.loads(path.read_text(encoding="utf-8"))
        d["execution"]["automatic_deploy"] = True
        path.write_text(json.dumps(d), encoding="utf-8")
        with self.assertRaises(ScaffoldError):
            review(self.root)

    def test_publication_gate_remains_closed(self):
        path = self.root / "docs/architecture/static_pipeline_policy.json"
        d = json.loads(path.read_text(encoding="utf-8"))
        d["publication_gates"]["rent_income_join_approved"] = True
        path.write_text(json.dumps(d), encoding="utf-8")
        with self.assertRaises(ScaffoldError):
            review(self.root)

    def test_no_public_api_or_source_export(self):
        (self.root / "frontend/app/api").mkdir(parents=True)
        with self.assertRaises(ScaffoldError):
            review(self.root)

    def test_source_reference_keeps_provenance_metadata(self):
        ref = SourceReference(
            source_id="cma-rent", region_id="vancouver_cma_2021",
            reference_period="2025-10", statistical_population="purpose_built_apartments",
            unit="CAD_per_month", source_sha256="a" * 64,
        )
        self.assertEqual(ref.statistical_population, "purpose_built_apartments")
        self.assertFalse(hasattr(ref, "rent_to_income_ratio"))

    def test_source_reference_rejects_invalid_sha(self):
        with self.assertRaises(ValueError):
            SourceReference("source", "region", "2025-10", "apartments", "CAD", "NOT_A_SHA")

    def test_source_reference_rejects_unlabelled_population(self):
        with self.assertRaises(ValueError):
            SourceReference("source", "region", "2025-10", " ", "CAD", "a" * 64)


if __name__ == "__main__":
    unittest.main()
