"""M01-T05 offline docs, roadmap and manual CI contract regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.validate_m01_docs import DocsContractError, validate
from scripts.sync_roadmap import update_markdown

ROOT = Path(__file__).resolve().parent.parent
FILES = (
    'docs/roadmap-status.json', 'docs/NORTHSTAR_MASTER_ROADMAP.md',
    'docs/architecture/static_pipeline_policy.json',
    'docs/M01_T05_DOCS_AS_CODE.md', 'CHANGELOG.md', 'docs/adr/README.md',
    'docs/adr/ADR-0001-static-release-control.md',
    'docs/adr/ADR-0002-unjoined-indicators.md',
    'docs/adr/ADR-0003-naming-and-identity.md',
    'docs/adr/ADR-0004-manual-verification-and-docs-as-code.md',
    '.github/workflows/verify.yml', '.github/workflows/pages.yml',
)


class DocsAsCodeTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        for name in FILES:
            to = root / name
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, to)
        return root

    def test_live_repo_contract(self):
        r = validate()
        self.assertEqual(r['status'], 'docs_as_code_contract_validated')
        self.assertTrue(r['manual_verify_has_frontend_build'])
        self.assertFalse(r['github_actions_run_verified'])
        self.assertFalse(r['publication_approved'])

    def test_drifted_roadmap_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / 'docs/NORTHSTAR_MASTER_ROADMAP.md'
            p.write_text(p.read_text(encoding='utf-8').replace('Em andamento', 'Não iniciado', 1), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_m01_fake_completion_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / 'docs/roadmap-status.json'
            d = json.loads(p.read_text(encoding='utf-8'))
            d['milestones'][1]['status'] = 'done'
            d['milestones'][1]['prs'] = ['https://github.com/owner/repo/pull/999']
            d['milestones'][1]['evidence'] = ['fake evidence']
            d['milestones'][1]['merged_commit'] = 'f' * 40
            d['milestones'][1]['accepted_at'] = '2026-10-28'
            p.write_text(json.dumps(d), encoding='utf-8')
            (root / 'docs/NORTHSTAR_MASTER_ROADMAP.md').write_text(
                update_markdown((root / 'docs/NORTHSTAR_MASTER_ROADMAP.md').read_text(encoding='utf-8'), d),
                encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_missing_adr_index_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / 'docs/adr/README.md'
            p.write_text(p.read_text(encoding='utf-8').replace('ADR-0004-manual-verification-and-docs-as-code.md', 'missing.md'), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_missing_changelog_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            (root / 'CHANGELOG.md').unlink()
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_verify_push_trigger_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / '.github/workflows/verify.yml'
            p.write_text(p.read_text(encoding='utf-8').replace('  workflow_dispatch:\n', '  push:\n', 1), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_verify_extra_pr_trigger_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / '.github/workflows/verify.yml'
            p.write_text(p.read_text(encoding='utf-8').replace('  workflow_dispatch:\n', '  workflow_dispatch:\n  pull_request:\n', 1), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_pages_schedule_trigger_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / '.github/workflows/pages.yml'
            p.write_text(p.read_text(encoding='utf-8').replace('  workflow_dispatch:\n', '  schedule:\n', 1), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_write_permissions_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / '.github/workflows/verify.yml'
            p.write_text(p.read_text(encoding='utf-8').replace('  contents: read', '  contents: write', 1), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_deploy_action_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / '.github/workflows/verify.yml'
            p.write_text(p.read_text(encoding='utf-8') + '\n      - uses: actions/deploy-pages@v4\n', encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_missing_typecheck_step_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / '.github/workflows/verify.yml'
            p.write_text(p.read_text(encoding='utf-8').replace('run: pnpm --dir frontend typecheck', 'run: echo skipped'), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_export_gate_open_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            p = root / 'docs/architecture/static_pipeline_policy.json'
            d = json.loads(p.read_text(encoding='utf-8'))
            d['storage']['public_export']['publication_active'] = True
            p.write_text(json.dumps(d), encoding='utf-8')
            with self.assertRaises(DocsContractError):
                validate(root)

    def test_docs_checker_run_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(Path(tmp))
            before = {name:(root / name).read_bytes() for name in FILES}
            self.assertEqual(validate(root)['status'], 'docs_as_code_contract_validated')
            self.assertEqual(before, {name:(root / name).read_bytes() for name in FILES})


if __name__ == '__main__':
    unittest.main()
