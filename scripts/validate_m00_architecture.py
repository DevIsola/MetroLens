#!/usr/bin/env python3
"""Validate accepted-for-planning M00-T05 architecture; NEVER build or publish data."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / 'docs' / 'architecture' / 'static_pipeline_policy.json'


class ArchitectureError(ValueError):
    """An architecture policy guard failed."""


def validate_policy(policy: dict, *, root: Path = ROOT) -> dict:
    """Assert the reviewed discovery boundaries remain fail-closed."""
    if not isinstance(policy, dict) or policy.get('schema_version') != 1 or policy.get('milestone') != 'M00-T05':
        raise ArchitectureError('Unsupported M00-T05 policy schema or milestone')
    if policy.get('decision_status') != 'accepted_for_planning' or policy.get('implementation_active') is not False:
        raise ArchitectureError('M00-T05 must remain accepted for planning only; no implementation activation')
    storage = policy.get('storage')
    if not isinstance(storage, dict):
        raise ArchitectureError('Storage contract missing')
    ignore = (root / '.gitignore').read_text(encoding='utf-8')
    for name, expected in (
        ('raw', 'pipeline/data/raw/'),
        ('bronze', 'pipeline/data/bronze/'),
        ('silver', 'pipeline/data/silver/'),
        ('gold', 'pipeline/data/gold/'),
    ):
        entry = storage.get(name)
        if not isinstance(entry, dict) or entry.get('directory') != expected or entry.get('gitignored') is not True or entry.get('browser_served') is not False:
            raise ArchitectureError(f'Unsafe or missing {name} storage boundary')
        if not re.search(rf'(?m)^{re.escape(expected)}$', ignore):
            raise ArchitectureError(f'Gitignore is missing {name} source/derived data boundary')
    if storage['raw'].get('format') != 'publisher_original' or storage['silver'].get('format') != 'parquet':
        raise ArchitectureError('Unexpected raw/Parquet format contract')
    exported = storage.get('public_export')
    if not isinstance(exported, dict) or exported.get('format') != 'versioned_json_shards' or exported.get('approved_only') is not True or exported.get('publication_active') is not False:
        raise ArchitectureError('Public export must be versioned, approved-only and inactive')
    runtime = policy.get('runtime')
    if not isinstance(runtime, dict) or runtime.get('frontend') != 'nextjs_static_export' or runtime.get('application_server_required') is not False:
        raise ArchitectureError('Static frontend boundary missing')
    if runtime.get('client_charts') != 'echarts' or runtime.get('client_maps') != 'maplibre' or runtime.get('geodata_requires_licence_review') is not True:
        raise ArchitectureError('Interactive maps/charts or geodata licence gate missing')
    if runtime.get('interactive_requirements_milestones') != ['M05', 'M06', 'M08']:
        raise ArchitectureError('Interactive UX requirements must be allocated to M05/M06/M08')
    execution = policy.get('execution')
    if not isinstance(execution, dict) or execution.get('github_actions_triggers') != ['workflow_dispatch']:
        raise ArchitectureError('GitHub Actions must remain manual-only')
    for flag in ('push_auto_ci', 'automatic_deploy', 'scheduled_etl'):
        if execution.get(flag) is not False:
            raise ArchitectureError(f'Execution must not activate {flag}')
    if execution.get('schedule_review_milestone') != 'M09' or execution.get('deployment_branch') != 'main' or execution.get('requires_explicit_release_confirmation') is not True:
        raise ArchitectureError('Release branch/confirmation or schedule policy changed')
    for name in ('verify.yml', 'pages.yml'):
        body = (root / '.github' / 'workflows' / name).read_text(encoding='utf-8')
        match = re.search(r'(?ms)^on:\s*\n(.*?)(?=^permissions:)', body)
        if match is None or not re.search(r'(?m)^  workflow_dispatch:', match.group(1)):
            raise ArchitectureError(f'{name} has no manual workflow trigger')
        for forbidden in ('push', 'pull_request', 'schedule', 'workflow_run', 'release', 'merge_group', 'create'):
            if re.search(rf'(?m)^  {forbidden}\s*:', match.group(1)):
                raise ArchitectureError(f'{name} contains forbidden automatic trigger {forbidden}')
    pages = (root / '.github' / 'workflows' / 'pages.yml').read_text(encoding='utf-8')
    if 'github.ref == \'refs/heads/main\'' not in pages or 'inputs.confirm_release == true' not in pages:
        raise ArchitectureError('Pages lacks main/confirm guard')
    gates = policy.get('publication_gates')
    if not isinstance(gates, dict) or set(gates) != {
        'publisher_reuse_approved', 'cmhc_statcan_crosswalk_approved',
        'rent_income_join_approved', 'public_data_export_approved',
    } or any(value is not False for value in gates.values()):
        raise ArchitectureError('Publication and comparison gates must remain false')
    for filename in (policy.get('review_record'), policy.get('adr'), policy.get('maintainer_decision_record')):
        if not isinstance(filename, str) or not filename.startswith('docs/') or '..' in Path(filename).parts or not (root / filename).is_file():
            raise ArchitectureError('Missing or invalid architecture/design review document')
    adr = (root / policy['adr']).read_text(encoding='utf-8')
    decision = (root / policy['review_record']).read_text(encoding='utf-8')
    maintainer = (root / policy['maintainer_decision_record']).read_text(encoding='utf-8')
    if ('accepted for architectural planning' not in adr or
            'ACCEPT ADR-0001' not in maintainer or
            '2026-10-26' not in maintainer or
            'M05' not in decision or 'M06' not in decision):
        raise ArchitectureError('ADR acceptance or UX decision record missing')
    return {
        'milestone': 'M00-T05',
        'status': 'architecture_decision_validated',
        'decision_status': 'accepted_for_planning',
        'reviewed_M00_T04_design_decisions': 3,
        'raw_storage': 'gitignored_source_originals_and_manifests',
        'silver_format': 'parquet',
        'browser_export_format': 'approved_versioned_json_only',
        'interactive_charts_planned': 'M05/M08',
        'interactive_maps_planned': 'M06',
        'workflow_triggers': ['workflow_dispatch'],
        'automatic_deployment_enabled': False,
        'production_ready': False,
        'publication_approved': False,
        'rent_to_income_ratio': None,
        'maintainer_acceptance_required': False,
        'implementation_active': False,
    }


def main() -> int:
    try:
        policy = json.loads(POLICY.read_text(encoding='utf-8'))
        report = validate_policy(policy)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'milestone': 'M00-T05', 'status': 'invalid', 'reason': str(error),
                          'production_ready': False, 'publication_approved': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
