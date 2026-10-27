#!/usr/bin/env python3
"""Validate small MANUALLY sourced discovery observations (never an ETL input)."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / 'docs' / 'samples' / 'official-page-observations.csv'
FIELDS = (
    'source_id', 'metric_id', 'region_id', 'source_geo_code', 'reference_period',
    'periodicity', 'statistic', 'segment', 'value', 'unit', 'source_url',
    'extraction_method',
)
ALLOWED_HOSTS = {'www12.statcan.gc.ca', 'www.cmhc-schl.gc.ca', 'www.bankofcanada.ca'}
ALLOWED_METRICS = {
    'median_total_household_income': ('annual', 'median', 'CAD_per_year'),
    'average_turnover_2br_rent': ('monthly_reference', 'mean', 'CAD_per_month'),
    'overnight_rate_target': ('daily', 'rate', 'percent'),
}


def load_and_validate(path: Path = SAMPLE_PATH) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(FIELDS):
            raise ValueError('Sample fixture schema changed or required column missing')
        rows = list(reader)
    if not rows:
        raise ValueError('Sample fixture must not be empty')
    observed = set()
    for row in rows:
        if any(not row[field].strip() for field in FIELDS):
            raise ValueError('Blank sample field')
        key = tuple(row[k] for k in ('source_id', 'metric_id', 'region_id', 'reference_period', 'segment'))
        if key in observed:
            raise ValueError(f'Duplicate sample observation: {key}')
        observed.add(key)
        if row['extraction_method'] != 'manual_official_html':
            raise ValueError('Fixture falsely represents a machine-verified extraction')
        if urlsplit(row['source_url']).scheme != 'https' or urlsplit(row['source_url']).hostname not in ALLOWED_HOSTS:
            raise ValueError('Observation lacks an approved official HTTPS source')
        expected = ALLOWED_METRICS.get(row['metric_id'])
        if expected is None or (row['periodicity'], row['statistic'], row['unit']) != expected:
            raise ValueError('Metric semantics or units mismatch')
        try:
            value = float(row['value'])
        except ValueError as error:
            raise ValueError('Non-numeric value') from error
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Sample value must be positive and finite')
        if row['metric_id'] == 'median_total_household_income' and (row['source_id'] != 'statcan_census2021_profile' or len(row['reference_period']) != 4 or not row['source_geo_code'].startswith('2021S0503')):
            raise ValueError('Census income must be a 2021 Census CMA observation with annual income reference period')
        if row['metric_id'] == 'average_turnover_2br_rent' and (row['source_id'] != 'cmhc_rms2025_report' or row['source_geo_code'] != 'unverified' or len(row['reference_period']) != 7):
            raise ValueError('CMHC geography or month improperly asserted')
        if row['metric_id'] == 'overnight_rate_target' and (row['region_id'] != 'canada' or row['source_id'] != 'boc_v39079' or len(row['reference_period']) != 10):
            raise ValueError('BoC series must be daily and national')
    return rows


def assess_rent_income_join(rent: dict[str, str], income: dict[str, str], *, geography_verified: bool = False) -> tuple[bool, str]:
    """Fail closed: same year is necessary but insufficient for comparability."""
    if rent.get('metric_id') != 'average_turnover_2br_rent' or income.get('metric_id') != 'median_total_household_income':
        return False, 'metric_mismatch'
    if rent.get('region_id') != income.get('region_id'):
        return False, 'region_mismatch'
    if rent.get('reference_period', '')[:4] != income.get('reference_period', '')[:4]:
        return False, 'period_mismatch'
    if not geography_verified:
        return False, 'geography_unverified'
    # These are distinct statistical universes, even when time + CMA align.
    return False, 'population_statistic_mismatch'


if __name__ == '__main__':
    print(f'Validated {len(load_and_validate())} manually transcribed discovery observations; NOT cleared for production')
