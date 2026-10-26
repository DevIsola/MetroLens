#!/usr/bin/env python3
"""Offline M00-T04 paired UX wireframes from re-verified unjoined source evidence.

No network calls, publication permission or production artifact is created.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from preview_vancouver_indicators import IndicatorPreviewError, build_report
from reconcile_vancouver_evidence import ReconciliationError
from probe_official_sources import RAW_DIR, SOURCES

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'docs/design/m00-t04-wireframes.template.html'
DEFAULT_OUTPUT = ROOT / 'local-previews/M00_T04_Vancouver_Paired_Wireframes.html'
EXPECTED = {
    ('studio', '2024-10'): 1575, ('studio', '2025-10'): 1667,
    ('one_bedroom', '2024-10'): 1769, ('one_bedroom', '2025-10'): 1806,
    ('two_bedroom', '2024-10'): 2314, ('two_bedroom', '2025-10'): 2363,
    ('three_plus_bedroom', '2024-10'): 2942, ('three_plus_bedroom', '2025-10'): 3009,
    ('all_bedrooms', '2024-10'): 1924, ('all_bedrooms', '2025-10'): 1963,
}
INCOME = {'2023': 77700, '2024': 78900}
SOURCE_CELLS = {
    ('studio', '2024-10'): ('B36', 'C36'), ('studio', '2025-10'): ('D36', 'E36'),
    ('one_bedroom', '2024-10'): ('F36', 'G36'), ('one_bedroom', '2025-10'): ('H36', 'I36'),
    ('two_bedroom', '2024-10'): ('J36', 'K36'), ('two_bedroom', '2025-10'): ('L36', 'M36'),
    ('three_plus_bedroom', '2024-10'): ('N36', 'O36'),
    ('three_plus_bedroom', '2025-10'): ('P36', 'Q36'),
    ('all_bedrooms', '2024-10'): ('R36', 'S36'),
    ('all_bedrooms', '2025-10'): ('T36', 'U36'),
}



class WireframeError(ValueError):
    """Preview cannot be rendered safely or has unreviewed source evidence."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise WireframeError(reason)


def prepare_data(report: dict) -> dict:
    """Strictly map the reviewed indicator contract into a minimal browser payload."""
    require(type(report) is dict and report.get('status') == 'indicator_preview_for_review'
            and report.get('mode') == 'local_nonpublic_discovery_preview'
            and report.get('region_id') == 'vancouver_cma_2021'
            and report.get('source_specific_evidence_reconciled') is True,
            'No reconciled local indicator-preview evidence')
    for flag in ('geography_crosswalk_approved', 'reference_periods_aligned_for_join',
                 'statistical_populations_comparable_for_join', 'metric_comparability_approved',
                 'publication_approved', 'production_ready'):
        require(report.get(flag) is False, 'Unexpected approval field: ' + flag)
    require(report.get('rent_to_income_ratio') is None, 'Joined ratio must remain null')
    blockers = report.get('blocked_metrics')
    require(isinstance(blockers, list) and len(blockers) == 1 and
            blockers[0].get('metric_id') == 'rent_to_income_pct' and
            blockers[0].get('value') is None and
            set(blockers[0].get('reason_codes', [])) == {
                'different_statistical_units', 'mean_vs_median_aggregates',
                'unreviewed_cmhc_crosswalk', 'unreviewed_period_alignment'},
            'Missing reviewed blocker reasons')
    series = report.get('series')
    require(isinstance(series, list) and len(series) == 2, 'Expected exactly two independent series')
    groups = {entry.get('id'): entry for entry in series if isinstance(entry, dict)}
    require(set(groups) == {'cmhc_average_private_apartment_rent',
                            'cis_median_after_tax_income_economic_family_unit'},
            'Unknown, duplicate or missing source series')
    rent = groups['cmhc_average_private_apartment_rent']
    income = groups['cis_median_after_tax_income_economic_family_unit']
    require(rent.get('source_id') == 'cmhc_rms_2025_vancouver'
            and rent.get('source_sha256') == '2fda7bea9ad42787c1820dd4d60f11091ff2455c4eec1732b14acc97660c3258'
            and rent.get('statistical_unit') == 'rental_apartment_unit'
            and rent.get('measure_type') == 'weighted_mean'
            and rent.get('unit') == 'CAD_per_month'
            and rent.get('source_quality_legend') == {'a': 'Excellent'}
            and rent.get('population_label') == 'Private purpose-built rental apartments (CMHC RMS)',
            'Unexpected CMHC metric definition or fingerprint')
    require(income.get('source_id') == 'statcan_11100190'
            and income.get('source_sha256') == '03677bae1fd1cc412c6563c0b33251d2eb4cf3837712ee7c92aa87d7bec782e4'
            and income.get('statistical_unit') == 'economic_family_or_unattached_person'
            and income.get('measure_type') == 'median'
            and income.get('unit') == 'CAD_2024_constant_per_year'
            and income.get('price_basis') == '2024_constant_dollars'
            and income.get('source_quality_legend') == {'A': 'Acceptable or better (StatsCan standard symbols)'},
            'Unexpected CIS metric definition or fingerprint')
    require(rent.get('official_source_url') == SOURCES['cmhc-vancouver']['url'] and
            income.get('official_source_url') == SOURCES['statcan-cis-income']['url'],
            'Official publisher link differs from the audited source registry')
    rent_points = {}
    require(isinstance(rent.get('observations'), list), 'Missing CMHC observations')
    for item in rent['observations']:
        require(type(item) is dict, 'Invalid rent observation')
        key = (item.get('bedroom_type'), item.get('reference_period'))
        require(key in EXPECTED and key not in rent_points and
                type(item.get('value')) is int and item['value'] == EXPECTED[key] and
                item.get('quality_code') == 'a' and
                (item.get('source_cell'), item.get('source_quality_cell')) == SOURCE_CELLS[key],
                'Rent observation not verified or duplicated')
        rent_points[key] = item['value']
    require(rent_points == EXPECTED, 'Incomplete reviewed CMHC observations')
    income_points = {}
    require(isinstance(income.get('observations'), list), 'Missing CIS observations')
    for item in income['observations']:
        require(type(item) is dict, 'Invalid CIS observation')
        yr = item.get('reference_period')
        require(yr in INCOME and yr not in income_points and
                type(item.get('value')) is int and item['value'] == INCOME[yr] and
                item.get('source_quality_code') == 'A' and
                item.get('source_vector') == 'v96416811' and
                item.get('source_coordinate') == '21.12.1',
                'Income observation not verified or duplicated')
        income_points[yr] = item['value']
    require(income_points == INCOME, 'Incomplete reviewed CIS observations')
    return {
        'region': 'Vancouver CMA',
        'rent': [{'bedroom_type': bedroom, 'period': period, 'value': value, 'quality': 'a'}
                 for (bedroom, period), value in sorted(rent_points.items())],
        'income': [{'period': year, 'value': income_points[year], 'quality': 'A'} for year in sorted(INCOME)],
        'source_links': {'rent': rent['official_source_url'], 'income': income['official_source_url']},
        'cross_source_comparison_allowed': False,
    }


def render_html(report: dict, template: str | None = None) -> str:
    data = prepare_data(report)
    source = TEMPLATE.read_text(encoding='utf-8') if template is None else template
    require(source.count('/*__M00_DATA_JSON__*/') == 1, 'Wireframe HTML placeholder missing or duplicated')
    # JSON lives in a JS assignment; escape HTML/script-breaking chars, including U+2028/2029.
    serialized = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    return source.replace('/*__M00_DATA_JSON__*/', serialized)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR, help='Existing ignored official source files')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT, help='Local HTML, never public')
    args = parser.parse_args(argv)
    try:
        report = build_report(args.raw_dir)
        html = render_html(report)
        resolved = args.output.resolve()
        # Never write source-derived HTML to checked-in docs/frontend/public paths.
        if resolved.is_relative_to(ROOT) and not resolved.is_relative_to(ROOT / 'local-previews'):
            raise WireframeError('Output must be in ignored local-previews/ or outside the repository')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding='utf-8', newline='\n')
    except (WireframeError, IndicatorPreviewError, ReconciliationError, ValueError,
            KeyError, TypeError, OSError, UnicodeError, EOFError) as error:
        print(json.dumps({'milestone': 'M00-T04', 'status': 'blocked', 'reason': str(error),
                          'publication_approved': False, 'production_ready': False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({'milestone': 'M00-T04', 'status': 'local_wireframes_created',
                      'output_path': str(args.output.resolve()),
                      'themes': ['light', 'dark'], 'layouts': ['desktop', 'mobile'],
                      'rent_observations': 10, 'income_observations': 2,
                      'rent_to_income_ratio': None, 'publication_approved': False,
                      'production_ready': False}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
