#!/usr/bin/env python3
"""Offline M01-T05 documentation and manual-verification contract validator."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
# Resolve imports both as a script and as a namespace-package module on Windows.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.sync_roadmap import StatusValidationError, update_markdown, validate_status


class DocsContractError(ValueError):
    """Documentation or manual-only verification no longer matches its contract."""


def _read(root: Path, name: str) -> str:
    try:
        return (root / name).read_text(encoding="utf-8")
    except OSError as exc:
        raise DocsContractError(f"Missing or unreadable {name}: {exc}") from exc


def _json(root: Path, name: str) -> dict:
    try:
        data = json.loads(_read(root, name))
    except ValueError as exc:
        raise DocsContractError(f"Invalid JSON in {name}: {exc}") from exc
    if not isinstance(data, dict):
        raise DocsContractError(f"Expected JSON object in {name}")
    return data


def _events(workflow: str, name: str) -> list[str]:
    # Parse only top-level 'on' in the deliberately small, indentation-controlled workflow.
    lines = workflow.splitlines()
    on_headers = [i for i, line in enumerate(lines) if line == 'on:']
    if len(on_headers) != 1:
        raise DocsContractError(f"{name}: expected exactly one top-level on: key")
    events = []
    for line in lines[on_headers[0] + 1:]:
        if line and not line.startswith((' ', '#')):
            break
        match = re.fullmatch(r'  ([A-Za-z_][A-Za-z_0-9]*):(?:\s*.*)?', line)
        if match:
            events.append(match.group(1))
    if events != ['workflow_dispatch']:
        raise DocsContractError(f"{name}: triggers must be workflow_dispatch only (found {events})")
    return events


def validate(root: Path = ROOT) -> dict:
    status = _json(root, 'docs/roadmap-status.json')
    try:
        validate_status(status)
        markdown = _read(root, 'docs/NORTHSTAR_MASTER_ROADMAP.md')
        if update_markdown(markdown, status) != markdown:
            raise DocsContractError('Generated roadmap is out of sync; do not auto-rewrite in CI')
    except StatusValidationError as exc:
        raise DocsContractError(f'Invalid milestone contract: {exc}') from exc
    m00, m01 = status['milestones'][:2]
    if m00['status'] != 'done' or m01['status'] != 'in_progress':
        raise DocsContractError('M00 must be done, M01 in progress')
    if m01.get('merged_commit') is not None or m01.get('accepted_at') is not None:
        raise DocsContractError('M01 completion evidence may not be fabricated')

    changelog = _read(root, 'CHANGELOG.md')
    for marker in ('## [Unreleased]', 'M00 discovery acceptance', 'M01-T05',
                   'No automatic CI', 'not approved'):
        # 'not approved' can come from either method or permissions wording.
        if marker not in changelog:
            raise DocsContractError(f'CHANGELOG.md missing: {marker}')
    index = _read(root, 'docs/adr/README.md')
    adrs = (
        'ADR-0001-static-release-control.md',
        'ADR-0002-unjoined-indicators.md',
        'ADR-0003-naming-and-identity.md',
        'ADR-0004-manual-verification-and-docs-as-code.md',
    )
    for name in adrs:
        if name not in index:
            raise DocsContractError(f'ADR index does not link {name}')
        _read(root, 'docs/adr/' + name)
    adr = _read(root, 'docs/adr/' + adrs[-1])
    for marker in ('workflow_dispatch', 'Status:', 'Date:', 'M01-T05', 'publication',
                   'CHANGELOG.md'):
        if marker not in adr:
            raise DocsContractError(f'ADR-0004 missing decision context: {marker}')
    guide = _read(root, 'docs/M01_T05_DOCS_AS_CODE.md')
    for marker in ('python scripts/validate_m01_docs.py',
                   'python scripts/sync_roadmap.py --check',
                   'pnpm.cmd --dir frontend build', 'workflow_dispatch'):
        if marker not in guide:
            raise DocsContractError(f'M01-T05 guide missing: {marker}')

    policy = _json(root, 'docs/architecture/static_pipeline_policy.json')
    execution = policy.get('execution', {})
    if (policy.get('decision_status') != 'accepted_for_planning' or
        policy.get('implementation_active') is not False or
        policy.get('storage', {}).get('public_export', {}).get('publication_active') is not False or
        not policy.get('publication_gates') or
        any(value is not False for value in policy['publication_gates'].values()) or
        execution.get('github_actions_triggers') != ['workflow_dispatch'] or
        any(execution.get(key) is not False for key in ('automatic_deploy', 'push_auto_ci', 'scheduled_etl'))):
        raise DocsContractError('Source publication or automatic execution gates changed')

    verify = _read(root, '.github/workflows/verify.yml')
    pages = _read(root, '.github/workflows/pages.yml')
    _events(verify, 'verify.yml')
    _events(pages, 'pages.yml')
    if not re.search(r'(?m)^permissions:\n  contents: read\s*$', verify):
        raise DocsContractError('Manual verifier must have read-only token permissions')
    if any(s in verify for s in ('pages: write', 'id-token: write', 'actions/deploy-pages',
                                 'actions/upload-pages-artifact', 'environment:\n')):
        raise DocsContractError('Manual verifier cannot deploy or request write privileges')
    required_commands = (
        'python -m unittest discover -s tests -v',
        'python scripts/sync_roadmap.py --check',
        'python scripts/validate_m01_docs.py',
        'pnpm install --frozen-lockfile --ignore-scripts',
        'pnpm --dir frontend typegen',
        'pnpm --dir frontend typecheck',
        'pnpm --dir frontend build',
        'test -s frontend/out/index.html',
    )
    for command in required_commands:
        if f'run: {command}' not in verify:
            raise DocsContractError(f'Manual verifier missing real command: {command}')
    for marker in ('pnpm/action-setup@v4', "version: '10.34.9'",
                   'actions/setup-node@v4', "node-version-file: '.node-version'",
                   'actions/setup-python@v5', "python-version: '3.13'"):
        if marker not in verify:
            raise DocsContractError(f'Manual verifier missing runtime pin: {marker}')

    return {
        'milestone': 'M01-T05',
        'status': 'docs_as_code_contract_validated',
        'm00': 'done', 'm01': 'in_progress',
        'adr_count': len(adrs), 'changelog_present': True,
        'roadmap_synchronized': True,
        'manual_verify_has_frontend_build': True,
        'workflow_triggers': ['workflow_dispatch'],
        'github_actions_run_verified': False,
        'automatic_deployment_enabled': False,
        'publication_approved': False,
        'publisher_join_approved': False,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), indent=2))
        return 0
    except (DocsContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'milestone': 'M01-T05', 'status': 'invalid', 'reason': str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
