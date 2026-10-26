#!/usr/bin/env python3
"""M00-T03: fail-closed rent/income comparability triage, NOT a metric engine.

No observed rent/income ratio is computed here. Even a pair with complete
metadata only becomes eligible for an independent methodology review, not for
publication. Discovery-page samples must never be treated as released data.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Mapping
from urllib.parse import urlsplit

if __package__:
    from .validate_source_samples import SAMPLE_PATH, load_and_validate
else:
    from validate_source_samples import SAMPLE_PATH, load_and_validate

INCOME_METRIC = 'median_total_household_income'
RENT_METRIC = 'average_turnover_2br_rent'
COMPARISON_ID = 'annualized_mean_turnover_2br_rent_vs_median_total_household_income'
_RECOGNIZED_QUALITY = {'observed'}  # Missing/suppressed/unknown values cannot be used.
_INCOME_SOURCES = {'statcan_census2021_profile', 'statcan_98100058'}
_RENT_SOURCES = {'cmhc_rms2025_report', 'cmhc_rms_2025_vancouver', 'cmhc_rms_2025_toronto'}
_INCOME_HOSTS = {'www12.statcan.gc.ca', 'www150.statcan.gc.ca', 'www.statcan.gc.ca'}
_RENT_HOSTS = {'www.cmhc-schl.gc.ca', 'assets.cmhc-schl.gc.ca'}


def _official_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parts = urlsplit(value)
        return parts.scheme == 'https' and bool(parts.hostname) and not parts.username and not parts.password
    except ValueError:
        return False


def _publisher_url(value: object, allowed_hosts: set[str]) -> bool:
    return _official_url(value) and urlsplit(value).hostname in allowed_hosts


def _value_valid(row: Mapping[str, object]) -> bool:
    try:
        raw = row.get('value')
        if raw is None or isinstance(raw, bool):
            return False
        value = float(raw)
        return math.isfinite(value) and value > 0
    except (ValueError, TypeError, OverflowError):
        return False


def _period_valid(value: object, pattern: str, fmt: str) -> bool:
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        return False
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def _documented_gate(record: object, *, fields: tuple[str, ...]) -> bool:
    if not isinstance(record, dict) or record.get('status') != 'reviewed':
        return False
    return all(isinstance(record.get(field), str) and bool(record[field].strip()) for field in fields)


def assess_pair(
    rent: Mapping[str, object],
    income: Mapping[str, object],
    *,
    evidence: Mapping[str, object] | None = None,
) -> dict:
    """Deterministic, non-authorizing review readiness assessment.

    Missing fields yield explicit reason codes. Human review is mandatory even
    for ``ready_for_methodology_review``. This function does not trust a single
    `approved` boolean, and never computes an observed numerical ratio.
    """
    blockers: list[str] = []
    gaps: list[str] = []
    evidence = evidence if isinstance(evidence, dict) else {}

    if rent.get('metric_id') != RENT_METRIC or income.get('metric_id') != INCOME_METRIC:
        blockers.append('metric_definition_mismatch')
    if rent.get('source_id') not in _RENT_SOURCES or income.get('source_id') not in _INCOME_SOURCES:
        blockers.append('source_role_mismatch')
    if rent.get('unit') != 'CAD_per_month' or income.get('unit') != 'CAD_per_year':
        blockers.append('unit_mismatch')
    if (rent.get('statistic'), income.get('statistic')) != ('mean', 'median'):
        blockers.append('statistic_mismatch')
    if (rent.get('segment'), income.get('segment')) != ('turnover_2br_purpose_built', 'all_private_households'):
        blockers.append('population_definition_mismatch')
    if rent.get('periodicity') != 'monthly_reference' or income.get('periodicity') != 'annual':
        blockers.append('periodicity_mismatch')
    if not _value_valid(rent) or not _value_valid(income):
        blockers.append('invalid_or_missing_value')
    if (not isinstance(rent.get('region_id'), str) or not rent['region_id'] or
            rent.get('region_id') != income.get('region_id')):
        blockers.append('region_mismatch')

    rent_period = rent.get('reference_period')
    income_period = income.get('reference_period')
    valid_periods = _period_valid(rent_period, r'\d{4}-\d{2}', '%Y-%m') and _period_valid(income_period, r'\d{4}', '%Y')
    if not valid_periods:
        blockers.append('invalid_period_format')
    elif rent_period[:4] != income_period:
        blockers.append('reference_year_mismatch')

    if rent.get('quality_flag') not in _RECOGNIZED_QUALITY or income.get('quality_flag') not in _RECOGNIZED_QUALITY:
        gaps.append('quality_flags_not_verified')
    if not _publisher_url(rent.get('source_url'), _RENT_HOSTS) or not _publisher_url(income.get('source_url'), _INCOME_HOSTS):
        gaps.append('source_provenance_missing')

    geo = evidence.get('geography_crosswalk')
    geo_fields = ('region_id', 'rent_geo_code', 'income_geo_code', 'boundary_vintage', 'evidence_url')
    if (not _documented_gate(geo, fields=geo_fields) or
            geo['region_id'] != rent.get('region_id') or
            geo['rent_geo_code'] != rent.get('source_geo_code') or
            geo['income_geo_code'] != income.get('source_geo_code') or
            geo['rent_geo_code'] == 'unverified' or geo['income_geo_code'] == 'unverified' or
            not _official_url(geo['evidence_url'])):
        gaps.append('geography_crosswalk_not_reviewed')

    alignment = evidence.get('period_alignment')
    if (not _documented_gate(alignment, fields=('method', 'evidence_url')) or
            alignment['method'] != 'same_calendar_year' or
            not _official_url(alignment['evidence_url'])):
        gaps.append('period_alignment_not_reviewed')
    population = evidence.get('population_interpretation')
    if (not _documented_gate(population, fields=('methodology_note', 'evidence_url')) or
            not _official_url(population['evidence_url'])):
        gaps.append('population_interpretation_not_reviewed')
    terms = evidence.get('reuse_terms')
    if (not _documented_gate(terms, fields=('statcan_terms_url', 'cmhc_terms_url')) or
            not _official_url(terms['statcan_terms_url']) or
            not _official_url(terms['cmhc_terms_url'])):
        gaps.append('reuse_terms_not_reviewed')

    status = 'blocked' if blockers else 'needs_evidence' if gaps else 'ready_for_methodology_review'
    return {
        'comparison_id': COMPARISON_ID,
        'region_id': rent.get('region_id') if isinstance(rent.get('region_id'), str) else None,
        'status': status,
        'blockers': blockers,
        'evidence_gaps': gaps,
        'methodology_review_required': True,
        'approved_for_publication': False,
        'computed_value': None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=Path, default=SAMPLE_PATH,
                        help='Discovery-only sample CSV; no publisher downloads are required')
    args = parser.parse_args(argv)
    observations = load_and_validate(args.samples)
    income = {row['region_id']: row for row in observations if row['metric_id'] == INCOME_METRIC}
    results = [assess_pair(row, income[row['region_id']]) for row in observations
               if row['metric_id'] == RENT_METRIC and row['region_id'] in income]
    print(json.dumps({'milestone': 'M00-T03', 'discovery_samples_only': True,
                      'publication_approved': False, 'comparisons': results}, indent=2))
    return 0  # A blocked data comparison is an expected finding, not a CLI error.


if __name__ == '__main__':
    raise SystemExit(main())
