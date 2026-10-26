#!/usr/bin/env python3
"""M00-T03 offline display contract: separate Vancouver rent and income series.

Not a production export, validated CMHC/StatsCan join, or a rent-burden model.
All source files stay in the caller's ignored raw directory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from extract_cis_cma_income import extract_verified as extract_cis
from extract_cmhc_cma_rents import extract_verified as extract_rent
from extract_statcan_cma_income import extract_verified as extract_census
from probe_official_sources import RAW_DIR, SOURCES
from reconcile_vancouver_evidence import EVIDENCE, ReconciliationError, reconcile


class IndicatorPreviewError(ValueError):
    """Publisher evidence is invalid or insufficient for an offline preview."""


def require(test: bool, reason: str) -> None:
    if not test:
        raise IndicatorPreviewError(reason)


def assemble_preview(census: dict, cis: dict, rent: dict, evidence: dict) -> dict:
    """Prepare independent unjoined series; NEVER calculate cross-source statistics."""
    # The existing reconciliation enforces the independently reviewed Census
    # and CMHC evidence contract, including original source fingerprints.
    source_review = reconcile(census, rent, evidence)
    require(source_review['status'] == 'source_evidence_reconciled', 'Census/CMHC reconciliation unavailable')
    require(isinstance(cis, dict) and cis.get('status') == 'candidate_extracted_for_review'
            and cis.get('file_audit_status') == 'file_verified', 'CIS extraction is not independently verified')
    require(cis.get('official_source_url') == SOURCES['statcan-cis-income']['url'] and
            rent.get('official_source_url') == SOURCES['cmhc-vancouver']['url'],
            'Publisher citation URL changed from reviewed official origin')
    require(cis.get('source_id') == 'statcan_11100190'
            and cis.get('source_sha256') == '03677bae1fd1cc412c6563c0b33251d2eb4cf3837712ee7c92aa87d7bec782e4',
            'CIS publisher identity or fingerprint changed')
    require(cis.get('dguid') == census.get('dguid') == '2021S0503933'
            and cis.get('geographic_vintage') == '2021_census_definitions'
            and cis.get('geography_label') == 'Vancouver, British Columbia',
            'CIS Vancouver geography differs from reviewed source')
    require(cis.get('income_concept') == 'Median after-tax income'
            and cis.get('economic_family_type') == 'Economic families and persons not in an economic family'
            and cis.get('price_basis') == '2024_constant_dollars'
            and cis.get('full_source_scanned') is True,
            'CIS income concept, population, price basis or scan gate differs')
    for name in ('candidate_only',):
        require(cis.get(name) is True, 'CIS candidate status removed')
    for name in ('census_private_households_equivalent', 'statistical_populations_comparable',
                 'geography_crosswalk_approved', 'reference_periods_aligned',
                 'metric_comparability_approved', 'publication_approved', 'production_ready'):
        require(cis.get(name) is False, 'CIS self-approval or comparison claim detected: ' + name)
    require(cis.get('rent_to_income_ratio') is None, 'CIS unexpected rent/income ratio')
    cis_obs = cis.get('observations')
    require(isinstance(cis_obs, list) and len(cis_obs) == 2, 'CIS observation count changed')
    reviewed_income = {'2023': 77700, '2024': 78900}
    income_cards: list[dict] = []
    seen = set()
    for obs in cis_obs:
        require(isinstance(obs, dict), 'Malformed CIS record')
        year = obs.get('reference_period')
        require(isinstance(year, str) and year in reviewed_income and year not in seen,
                'Unexpected or duplicate CIS period')
        seen.add(year)
        require(obs.get('metric_id') == 'cis_median_after_tax_income_economic_family_unit'
                and type(obs.get('value')) is int and obs['value'] == reviewed_income[year]
                and obs.get('unit') == 'CAD_2024_constant_per_year'
                and obs.get('measure_type') == 'median'
                and obs.get('statistical_population') == 'economic_families_and_persons_not_in_economic_families'
                and obs.get('source_status_code') == 'A'
                and obs.get('status') == 'observed_candidate_only'
                and obs.get('approved_for_affordability_join') is False
                and obs.get('source_symbol') is None and obs.get('source_terminated') is None
                and obs.get('source_vector') == 'v96416811'
                and obs.get('source_coordinate') == '21.12.1',
                'CIS value or source metadata differs from reviewed evidence')
        income_cards.append({
            'reference_period': year,
            'value': obs['value'], 'source_quality_code': 'A',
            'source_vector': obs['source_vector'], 'source_coordinate': obs['source_coordinate'],
        })
    require(set(reviewed_income) == seen, 'Incomplete reviewed CIS year coverage')

    # All five apartment categories appear in the contract so users can choose
    # bedroom filters without silently aggregating mean and median statistics.
    bedroom_types = ('studio', 'one_bedroom', 'two_bedroom', 'three_plus_bedroom', 'all_bedrooms')
    rent_records = rent.get('records')
    require(isinstance(rent_records, list) and len(rent_records) == 10, 'Unexpected rental record count')
    rent_cards: list[dict] = []
    seen_rents = set()
    for r in rent_records:
        require(isinstance(r, dict), 'Malformed rental record')
        key = (r.get('bedroom_type'), r.get('reference_period'))
        require(key not in seen_rents and key[0] in bedroom_types
                and key[1] in ('2024-10', '2025-10'), 'Duplicate/unexpected rental record')
        seen_rents.add(key)
        require(r.get('status') == 'observed'
                and r.get('quality_code') == 'a'
                and r.get('quality_description') == 'Excellent'
                and r.get('metric_id') == 'cmhc_average_private_apartment_rent'
                and type(r.get('value_cad_per_month')) in (int, float)
                and 0 < r['value_cad_per_month'] < 100000
                and isinstance(r.get('cell'), str)
                and isinstance(r.get('quality_cell'), str),
                'Rental observation metadata or source quality changed')
        rent_cards.append({
            'reference_period': key[1], 'bedroom_type': key[0],
            'value': r['value_cad_per_month'],
            'quality_code': r['quality_code'],
            'source_cell': r['cell'], 'source_quality_cell': r['quality_cell'],
        })
    require(len(seen_rents) == 10, 'Incomplete rental observations')
    return {
        'schema_version': 1,
        'milestone': 'M00-T03',
        'status': 'indicator_preview_for_review',
        'mode': 'local_nonpublic_discovery_preview',
        'region_id': 'vancouver_cma_2021',
        'source_specific_evidence_reconciled': True,
        'geography_crosswalk_approved': False,
        'reference_periods_aligned_for_join': False,
        'statistical_populations_comparable_for_join': False,
        'metric_comparability_approved': False,
        'publication_approved': False,
        'production_ready': False,
        'rent_to_income_ratio': None,
        'series': [
            {
                'id': 'cmhc_average_private_apartment_rent',
                'display_label': 'Average private apartment rent — Vancouver CMA',
                'source_id': rent['source_id'], 'official_source_url': rent['official_source_url'],
                'source_sha256': rent['source_sha256'],
                'source_location': 'Table 1.1.2; Vancouver CMA; worksheet row 36',
                'population_label': 'Private purpose-built rental apartments (CMHC RMS)',
                'statistical_unit': 'rental_apartment_unit',
                'measure_type': 'weighted_mean',
                'unit': 'CAD_per_month',
                'frequency': 'annual_october_snapshot',
                'price_basis': 'source_reported_rent_dollars',
                'observations': sorted(rent_cards, key=lambda o: (o['bedroom_type'], o['reference_period'])),
                'source_quality_legend': {'a': 'Excellent'},
                'method_note': 'Weighted mean of sampled units, including occupied and vacant; not asking or turnover-only rent. No inflation adjustment.',
            },
            {
                'id': 'cis_median_after_tax_income_economic_family_unit',
                'display_label': 'Median after-tax income — economic families and unattached persons',
                'source_id': cis['source_id'], 'official_source_url': cis['official_source_url'],
                'source_sha256': cis['source_sha256'],
                'source_location': 'Vector v96416811; coordinate 21.12.1',
                'population_label': 'Economic families and persons not in an economic family (CIS)',
                'statistical_unit': 'economic_family_or_unattached_person',
                'measure_type': 'median',
                'unit': 'CAD_2024_constant_per_year',
                'frequency': 'annual',
                'price_basis': '2024_constant_dollars',
                'observations': sorted(income_cards, key=lambda o: o['reference_period']),
                'source_quality_legend': {'A': 'Acceptable or better (StatsCan standard symbols)'},
                'method_note': 'Not an all-private-household income measure. The 2024 CIS release revised some preceding estimates.',
            },
        ],
        'blocked_metrics': [{
            'metric_id': 'rent_to_income_pct',
            'value': None,
            'reason_codes': ['different_statistical_units', 'mean_vs_median_aggregates',
                             'unreviewed_cmhc_crosswalk', 'unreviewed_period_alignment'],
        }],
        'required_display_disclosures': [
            'Show source name, population, unit, date and quality code beside each individual series.',
            'The rent and income series do not measure the same units or a matched tenant sample.',
            'No rent burden, affordability score, rent-to-income ratio, or shared trend comparison is approved.',
            'Review publisher attribution and reuse requirements before any public release.',
        ],
    }


def build_report(raw_dir: Path = RAW_DIR, evidence_path: Path = EVIDENCE) -> dict:
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    census = extract_census(raw_dir)
    rent = extract_rent(raw_dir)
    cis = extract_cis(raw_dir)
    return assemble_preview(census, cis, rent, evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.raw_dir, args.evidence)
    except (IndicatorPreviewError, ReconciliationError, ValueError, KeyError, TypeError,
            OSError, UnicodeError, EOFError) as error:
        print(json.dumps({'milestone': 'M00-T03', 'status': 'blocked', 'reason': str(error),
                          'production_ready': False, 'publication_approved': False,
                          'metric_comparability_approved': False, 'rent_to_income_ratio': None}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
