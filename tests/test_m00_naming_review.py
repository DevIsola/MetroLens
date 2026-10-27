"""M00-T06 project name is selected without granting legal/remote release approvals."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from review_m00_naming import NamingReviewError, reference_inventory, validate_review


class NamingReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / 'docs/branding/m00_t06_name_review.json').read_text(encoding='utf-8'))

    def changed(self, field, value):
        obj = copy.deepcopy(self.base)
        obj[field] = value
        return obj

    def test_maintainer_selects_repository_name_without_trademark_claim(self):
        report = validate_review(self.base)
        self.assertEqual(report['status'], 'repository_project_name_selected')
        self.assertFalse(report['maintainer_selection_required'])
        self.assertFalse(report['final_identity_decision_required'])
        self.assertTrue(report['project_name_approved'])
        self.assertEqual(report['project_name_scope'], 'public_research_repository_not_service_or_app')
        self.assertTrue(report['known_public_use_risk_acknowledged'])
        self.assertEqual(report['preferred_name'], 'UrbanGauge')
        self.assertEqual(report['selected_name'], 'UrbanGauge')
        self.assertFalse(report['migration_performed'])

    def test_cli_reports_pending_and_counts_references(self):
        result = subprocess.run([sys.executable, 'scripts/review_m00_naming.py'], cwd=ROOT,
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['decision_status'], 'maintainer_selected_repository_project_name_with_known_risk')
        self.assertGreater(data['existing_reference_inventory']['metrolens']['tracked_files'], 0)

    def test_review_inventory_is_bounded(self):
        items = reference_inventory()
        self.assertEqual(set(items), {'metrolens', 'northstar', 'observatory_descriptor'})
        self.assertTrue(all(len(x['sample_paths']) <= 8 for x in items.values()))

    def test_other_selected_name_rejected(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('selected_name', 'MetroLens'))

    def test_premature_acceptance_rejected(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('decision_status', 'accepted'))

    def test_domain_clearance_cannot_be_fabricated(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('domain_availability_verified', True))

    def test_trademark_clearance_cannot_be_fabricated(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('trademark_clearance_verified', True))

    def test_repository_rename_cannot_be_preapproved(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('repository_rename_approved', True))

    def test_public_rebrand_cannot_be_preapproved(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('public_rebrand_performed', True))

    def test_removed_collision_url_rejected(self):
        data = copy.deepcopy(self.base)
        next(c for c in data['candidates'] if c['name'] == 'MetroLens')['evidence_urls'] = []
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_http_collision_url_rejected(self):
        data = copy.deepcopy(self.base)
        next(c for c in data['candidates'] if c['name'] == 'Living Ledger')['evidence_urls'][0] = 'http://livingledger.net/'
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_missing_candidate_rejected(self):
        data = copy.deepcopy(self.base)
        data['candidates'].pop()
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_unverified_is_not_available(self):
        data = copy.deepcopy(self.base)
        next(c for c in data['candidates'] if c['name'] == 'CityMargin')['clearance_status'] = 'available'
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_missing_migration_plan_rejected(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.base, root=ROOT / 'does-not-exist')

    def test_preference_must_be_exact_and_explicit(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('preferred_name', 'MetroLens'))

    def test_preference_date_cannot_be_removed(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('preference_date', None))

    def test_no_second_project_selection_is_needed(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('final_identity_decision_required', True))

    def test_identity_migration_stays_unapproved(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('identity_migration_approved', True))

    def test_research_project_reference_cannot_be_removed(self):
        data = copy.deepcopy(self.base)
        urban = next(v for v in data['candidates'] if v['name'] == 'UrbanGauge')
        urban['evidence_urls'].remove('https://uosarch.ac.kr/uosarch_people/%ED%99%A9%EC%A7%80%EC%9D%80/')
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_game_publisher_reference_cannot_be_removed(self):
        data = copy.deepcopy(self.base)
        urban = next(v for v in data['candidates'] if v['name'] == 'UrbanGauge')
        urban['evidence_urls'].remove('https://www.classification.gov.au/titles/word-play-city-edition')
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_domain_asking_price_is_not_registry_clearance(self):
        data = copy.deepcopy(self.base)
        urban = next(v for v in data['candidates'] if v['name'] == 'UrbanGauge')
        urban['domain_marketplace_evidence']['verification'] = 'registered_and_cleared'
        with self.assertRaises(NamingReviewError):
            validate_review(data)

    def test_broad_legal_brand_acceptance_without_clearance_rejected(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('decision_status', 'accepted'))

    def test_user_accepted_name_cannot_be_scoped_as_commercial_service(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('project_name_scope', 'hosted_commercial_service'))

    def test_risk_acknowledgement_is_preserved(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('known_public_use_risk_acknowledged', False))

    def test_no_exclusive_trademark_rights_claimed(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('no_exclusive_trademark_rights_claimed', False))

    def test_public_repository_name_selected_without_renaming_remote(self):
        self.assertTrue((ROOT / 'README.md').read_text(encoding='utf-8').startswith('# UrbanGauge\n'))
        report = validate_review(self.base)
        self.assertFalse(report['repository_rename_approved'])
        self.assertFalse(report['trademark_clearance_verified'])

    def test_commercial_review_requirement_cannot_disappear(self):
        with self.assertRaises(NamingReviewError):
            validate_review(self.changed('future_commercial_brand_clearance_required', False))

    def test_naming_review_does_not_mutate_repository(self):
        before = (ROOT / 'docs/branding/m00_t06_name_review.json').read_bytes()
        validate_review(self.base)
        reference_inventory()
        self.assertEqual(before, (ROOT / 'docs/branding/m00_t06_name_review.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
