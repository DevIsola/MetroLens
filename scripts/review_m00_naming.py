#!/usr/bin/env python3
"""Read-only M00-T06 naming review. Repository label is not legal clearance."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / 'docs/branding/m00_t06_name_review.json'
_CANDIDATES = {'MetroLens', 'CityMargin', 'UrbanGauge', 'Living Ledger', 'Civic Ledger'}
_REQUIRED = ('domain_availability_verified', 'trademark_clearance_verified',
             'app_store_clearance_verified', 'brand_identity_approved',
             'repository_rename_approved', 'migration_performed',
             'public_rebrand_performed', 'production_ready')
_REFERENCE_PATTERNS = {
    'metrolens': re.compile(r'(?i)metro[ -]?lens'),
    'northstar': re.compile(r'(?i)northstar'),
    'observatory_descriptor': re.compile(r'(?i)canada affordability(?:\s*&\s*opportunity)? observatory'),
}


class NamingReviewError(ValueError):
    """Missing or prematurely authorized naming evidence."""


def validate_review(review: dict, *, root: Path = ROOT) -> dict:
    """Verify selected research-project label without granting trademark or remote rename."""
    if not isinstance(review, dict) or review.get('schema_version') != 1 or review.get('milestone') != 'M00-T06':
        raise NamingReviewError('Unsupported naming review schema or milestone')
    if review.get('decision_status') != 'maintainer_selected_repository_project_name_with_known_risk':
        raise NamingReviewError('Expected maintainer-selected repository name and acknowledged known risks')
    if (review.get('preferred_name') != 'UrbanGauge' or
            review.get('preference_date') != '2026-10-26' or
            review.get('final_identity_decision_required') is not False or
            review.get('identity_migration_approved') is not False or
            review.get('selected_name') != 'UrbanGauge' or
            review.get('selection_date') != '2026-10-26'):
        raise NamingReviewError('UrbanGauge project selection/date changed or remote migration silently approved')
    if review.get('working_codename') != 'MetroLens':
        raise NamingReviewError('Existing repository codename must remain until separately authorized remote migration')
    required_project_flags = {
        'project_name_approved': True,
        'project_name_scope': 'public_noncommercial_open_source_repository',
        'known_public_use_risk_acknowledged': True,
        'no_exclusive_trademark_rights_claimed': True,
        'project_readme_name_updated': True,
        'future_commercial_brand_clearance_required': True,
    }
    if any(review.get(key) != value for key, value in required_project_flags.items()):
        raise NamingReviewError('Repository-only name acceptance or scope safeguards are invalid')
    readme = root / 'README.md'
    if not readme.is_file() or not readme.read_text(encoding='utf-8').startswith('# UrbanGauge\n'):
        raise NamingReviewError('README title must match selected repository project name')
    if any(review.get(flag) is not False for flag in _REQUIRED):
        raise NamingReviewError('Domain, trademark, commercial branding, remote migration and production must remain unapproved')
    entries = review.get('candidates')
    if not isinstance(entries, list) or len(entries) != len(_CANDIDATES):
        raise NamingReviewError('Candidate set incomplete')
    if {v.get('name') for v in entries if isinstance(v, dict)} != _CANDIDATES:
        raise NamingReviewError('Candidate names missing or duplicated')
    with_evidence = {}
    for entry in entries:
        if not isinstance(entry.get('editorial_fit'), str) or not entry['editorial_fit'].strip() or not entry.get('tradeoff'):
            raise NamingReviewError('Every candidate needs a positioning benefit and risk')
        if entry.get('clearance_status') != 'unverified':
            raise NamingReviewError('Candidate cannot claim trademark/domain clearance')
        signal = entry.get('public_use_signal')
        urls = entry.get('evidence_urls')
        if signal not in {'not_concluded', 'observed_other_products'} or not isinstance(urls, list):
            raise NamingReviewError('Candidate collision evidence malformed')
        if signal == 'observed_other_products' and not urls:
            raise NamingReviewError('Observed collision must have evidence URL')
        if signal == 'not_concluded' and urls:
            raise NamingReviewError('Unreviewed collision must not contain implied verification')
        if any(not isinstance(url, str) or not url.startswith('https://') for url in urls):
            raise NamingReviewError('Collision references must be HTTPS URLs')
        with_evidence[entry['name']] = len(urls)
    if (with_evidence.get('MetroLens', 0) < 2 or
            with_evidence.get('Living Ledger', 0) < 2 or
            with_evidence.get('UrbanGauge', 0) < 2):
        raise NamingReviewError('Known public-use evidence must not be removed')
    urban = next(entry for entry in entries if entry['name'] == 'UrbanGauge')
    expected_evidence_urls = {
        'https://uosarch.ac.kr/uosarch_people/%ED%99%A9%EC%A7%80%EC%9D%80/',
        'https://www.classification.gov.au/titles/word-play-city-edition',
    }
    if not expected_evidence_urls.issubset(set(urban['evidence_urls'])):
        raise NamingReviewError('UrbanGauge historical research and app-publisher evidence missing')
    market = urban.get('domain_marketplace_evidence')
    if (not isinstance(market, dict) or market.get('domain') != 'urbangauge.com' or
            market.get('url') != 'https://www.brandzilla.io/name/UrbanGauge.com' or
            market.get('observed_asking_price_usd') != 2695 or
            market.get('observed_on') != '2026-10-26' or
            market.get('verification') != 'marketplace_listing_only_not_registry_or_ownership_clearance'):
        raise NamingReviewError('UrbanGauge .com listing must remain labelled as unverified marketplace evidence')
    if not isinstance(review.get('required_clearance_steps'), list) or len(review['required_clearance_steps']) < 5:
        raise NamingReviewError('Trademarks, domains, stores and maintainer gates missing')
    for path in ('docs/adr/ADR-0003-naming-and-identity.md',
                 'docs/branding/M00_T06_MIGRATION_PLAN.md',
                 'docs/architecture/M00_T05_REVIEW_DECISION.md'):
        if not (root / path).is_file():
            raise NamingReviewError(f'Missing named review record: {path}')
    return {
        'milestone': 'M00-T06',
        'status': 'repository_project_name_selected',
        'decision_status': 'maintainer_selected_repository_project_name_with_known_risk',
        'preferred_name': 'UrbanGauge',
        'preference_date': '2026-10-26',
        'final_identity_decision_required': False,
        'project_name_approved': True,
        'project_name_scope': 'public_noncommercial_open_source_repository',
        'known_public_use_risk_acknowledged': True,
        'future_commercial_brand_clearance_required': True,
        'candidate_names': [v['name'] for v in entries],
        'documented_public_use_signals': [v['name'] for v in entries if v['public_use_signal'] == 'observed_other_products'],
        'candidates_legally_cleared': 0,
        'selected_name': 'UrbanGauge',
        'domain_availability_verified': False,
        'trademark_clearance_verified': False,
        'repository_rename_approved': False,
        'migration_performed': False,
        'production_ready': False,
        'maintainer_selection_required': False,
        'domain_marketplace_listing': 'urbangauge.com; USD 2695 asking (2026-10-26); not cleared',
    }


def reference_inventory(*, root: Path = ROOT) -> dict:
    """Bounded sample from tracked text files; no source bytes changed."""
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=root, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise NamingReviewError('Cannot inventory tracked paths in Git repository')
    inventory = {}
    for name, needle in _REFERENCE_PATTERNS.items():
        matched = []
        for raw_path in result.stdout.split(b'\0'):
            if not raw_path:
                continue
            path = Path(raw_path.decode('utf-8'))
            if path.suffix.lower() not in {'.md', '.json', '.py', '.html', '.txt', '.yml', '.yaml', '.toml', '.css', '.ts', '.tsx'}:
                continue
            try:
                body = (root / path).read_text(encoding='utf-8')
            except (UnicodeError, OSError):
                continue
            if needle.search(body):
                matched.append(path.as_posix())
        inventory[name] = {'tracked_files': len(matched), 'sample_paths': matched[:8],
                           'sample_is_complete': len(matched) <= 8}
    return inventory


def main() -> int:
    try:
        review = json.loads(REVIEW.read_text(encoding='utf-8'))
        report = validate_review(review)
        report['existing_reference_inventory'] = reference_inventory()
    except (NamingReviewError, OSError, ValueError, TypeError) as error:
        print(json.dumps({'milestone': 'M00-T06', 'status': 'invalid',
                          'reason': str(error), 'migration_performed': False,
                          'production_ready': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
