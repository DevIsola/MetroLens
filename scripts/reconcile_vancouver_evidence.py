#!/usr/bin/env python3
"""Reconcile user-reviewed Vancouver Census and CMHC source evidence (M00).

The report can confirm independently reproducible source-specific observations.
It cannot approve source joins, inferred incomes, household rent burdens, or a release.
No network calls or raw-data persistence; read-only access to the ignored probe dir.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from extract_cmhc_cma_rents import extract_verified as extract_rent
from extract_statcan_cma_income import extract_verified as extract_income
from probe_official_sources import RAW_DIR

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / 'docs' / 'evidence-vancouver-m00.json'


class ReconciliationError(ValueError):
    """One or both source observations cannot be matched to review evidence."""


def _assert(predicate: bool, reason: str) -> None:
    if not predicate:
        raise ReconciliationError(reason)


def reconcile(income: dict, rent: dict, evidence: dict) -> dict:
    """Fail closed against the pinned review evidence, not against mere source labels."""
    _assert(evidence.get('schema_version') == 1 and
            evidence.get('region_id') == 'vancouver_cma_2021' and
            evidence.get('approved_for_publication') is False and
            evidence.get('metric_comparability_approved') is False,
            'Invalid or authorization-bearing review evidence')
    reviewed_income, reviewed_rent = evidence.get('income'), evidence.get('rent')
    _assert(isinstance(reviewed_income, dict) and isinstance(reviewed_rent, dict),
            'Missing publisher review evidence')
    for source, doc, expected in (('income', income, reviewed_income), ('rent', rent, reviewed_rent)):
        _assert(isinstance(doc, dict) and doc.get('status') == 'extracted_for_review',
                f'{source}: audited extraction unavailable')
        _assert(doc.get('file_audit_status') == 'file_verified' and
                doc.get('source_id') == expected['source_id'] and
                doc.get('source_sha256') == expected['sha256'],
                f'{source}: source identity or SHA-256 differs from reviewed evidence')
        _assert(doc.get('publication_approved') is False and
                doc.get('production_ready') is False and
                doc.get('metric_comparability_approved') is False and
                doc.get('geography_crosswalk_approved') is False,
                f'{source}: unexpected source approval flags')
    _assert(income.get('dguid') == reviewed_income['dguid'] == '2021S0503933' and
            income.get('coordinate') == reviewed_income['coordinate'] == '5381.1.1' and
            income.get('cma_code_2021') == '933' and
            income.get('population_universe') == 'all_private_households' and
            income.get('geographic_vintage') == '2021_census_definitions' and
            income.get('income_reference_year') == int(reviewed_income['reference_year']) == 2020 and
            income.get('household_size') == 'Total - Households by household size' and
            income.get('household_type') == 'Total – Household type including census family structure',
            'Income geography, household aggregate, or reference period differs from review')
    expected_income = {
        'household_count': ('2021', 'households', 'count', reviewed_income['household_count_2021']),
        'median_total_household_income': ('2020', 'CAD_per_year', 'median', reviewed_income['median_total_income_2020']),
        'median_after_tax_household_income': ('2020', 'CAD_per_year', 'median', reviewed_income['median_after_tax_income_2020']),
    }
    obs = income.get('observations')
    _assert(isinstance(obs, list) and len(obs) == len(expected_income), 'Income observation count differs')
    seen = set()
    for item in obs:
        _assert(isinstance(item, dict) and item.get('metric_id') in expected_income,
                'Unexpected Census income observation')
        key = item['metric_id']
        _assert(key not in seen, 'Duplicate income measure')
        seen.add(key)
        period, unit, typ, value = expected_income[key]
        _assert(item.get('status') == 'observed' and item.get('source_symbol') is None and
                item.get('reference_period') == period and item.get('unit') == unit and
                item.get('measure_type') == typ and type(item.get('value')) is int and
                item['value'] == value,
                f'{key}: income value, period, unit or suppression flag changed')
    _assert(rent.get('sheet') == reviewed_rent['worksheet'] == 'Table 1.1.2' and
            rent.get('source_row') == reviewed_rent['source_row'] == 36 and
            rent.get('geography_label') == 'Vancouver CMA' and
            rent.get('geographic_vintage') == '2021_census_definitions' and
            rent.get('rental_universe') == 'private_purpose_built_rental_apartments' and
            rent.get('rent_measure') == 'average_of_surveyed_units_not_turnover_or_asking_rent',
            'Rent geography, worksheet or surveyed population differs from review')
    months = reviewed_rent['reference_periods']
    _assert(months == ['2024-10', '2025-10'], 'Rent period benchmark changed')
    bedroom_types = ('studio', 'one_bedroom', 'two_bedroom', 'three_plus_bedroom', 'all_bedrooms')
    keys = {(bedroom, month) for bedroom in bedroom_types for month in months}
    records = rent.get('records')
    _assert(isinstance(records, list) and len(records) == 10, 'Rent observation count differs')
    seen = set()
    for item in records:
        _assert(isinstance(item, dict), 'Malformed rent record')
        key = (item.get('bedroom_type'), item.get('reference_period'))
        _assert(key in keys and key not in seen, 'Unexpected or duplicated rent bedroom/period')
        seen.add(key)
        _assert(item.get('metric_id') == 'cmhc_average_private_apartment_rent' and
                item.get('status') == 'observed' and item.get('quality_code') == 'a' and
                isinstance(item.get('value_cad_per_month'), (int, float)) and
                not isinstance(item.get('value_cad_per_month'), bool) and
                0 < item['value_cad_per_month'] < 100000,
                'Rent value or quality flag differs from reviewed all-excellent CMA aggregate')
        if key == ('two_bedroom', '2024-10'):
            _assert(item['value_cad_per_month'] == reviewed_rent['two_bedroom_2024'], '2024 two-bedroom benchmark changed')
        if key == ('two_bedroom', '2025-10'):
            _assert(item['value_cad_per_month'] == reviewed_rent['two_bedroom_2025'], '2025 two-bedroom benchmark changed')
    return {
        'schema_version': 1,
        'milestone': 'M00',
        'status': 'source_evidence_reconciled',
        'region_id': 'vancouver_cma_2021',
        'review_date': evidence['review_date'],
        'source_evidence': {
            'income': {'source_id': income['source_id'], 'sha256': income['source_sha256'],
                       'reference_period': '2020', 'dguid': income['dguid'],
                       'coordinate': income['coordinate'], 'metric_count': len(obs)},
            'rent': {'source_id': rent['source_id'], 'sha256': rent['source_sha256'],
                     'reference_periods': months, 'worksheet': rent['sheet'],
                     'source_row': rent['source_row'], 'metric_count': len(records)},
        },
        'shared_geographic_vintage': '2021_census_definitions',
        'geographic_identifier_crosswalk_verified': False,
        'reference_periods_aligned': False,
        'statistical_populations_comparable': False,
        'rent_to_income_ratio': None,
        'metric_comparability_approved': False,
        'publication_approved': False,
        'production_ready': False,
        'remaining_gates': list(evidence['review_gates_remaining']),
        'note': 'Source-specific observations match reviewed local evidence; no statistical join or household rent burden is authorized.',
    }


def build_report(raw_dir: Path, evidence_path: Path = EVIDENCE) -> dict:
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    income = extract_income(raw_dir)
    rent = extract_rent(raw_dir)
    return reconcile(income, rent, evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    args = parser.parse_args(argv)
    try:
        result = build_report(args.raw_dir, args.evidence)
    except (ReconciliationError, ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({'milestone': 'M00', 'status': 'blocked', 'reason': str(exc),
                          'metric_comparability_approved': False,
                          'publication_approved': False, 'rent_to_income_ratio': None}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
