"""M00-T05 planning acceptance must not activate publication or automation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_m00_architecture import ArchitectureError, validate_policy


class StaticPipelinePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / 'docs/architecture/static_pipeline_policy.json').read_text(encoding='utf-8'))

    def modify(self, *path, value):
        data = copy.deepcopy(self.policy)
        at = data
        for part in path[:-1]:
            at = at[part]
        at[path[-1]] = value
        return data

    def test_accepted_planning_contract_validates(self):
        result = validate_policy(self.policy)
        self.assertEqual(result['status'], 'architecture_decision_validated')
        self.assertFalse(result['maintainer_acceptance_required'])
        self.assertFalse(result['implementation_active'])
        self.assertIsNone(result['rent_to_income_ratio'])
        self.assertFalse(result['publication_approved'])

    def test_cli_outputs_review_only_json(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_m00_architecture.py')], cwd=ROOT,
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['decision_status'], 'accepted_for_planning')

    def test_rejects_automatic_deploy(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('execution', 'automatic_deploy', value=True))

    def test_rejects_nonmanual_workflow(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('execution', 'github_actions_triggers', value=['push', 'workflow_dispatch']))

    def test_rejects_activated_schedule(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('execution', 'scheduled_etl', value=True))

    def test_rejects_raw_public_dir(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('storage', 'raw', 'directory', value='frontend/public/data/'))

    def test_rejects_raw_browser_delivery(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('storage', 'raw', 'browser_served', value=True))

    def test_rejects_parquet_browser_delivery(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('storage', 'silver', 'browser_served', value=True))

    def test_rejects_public_export_activation(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('storage', 'public_export', 'publication_active', value=True))

    def test_rejects_publisher_reuse_approval(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('publication_gates', 'publisher_reuse_approved', value=True))

    def test_rejects_affordability_join_approval(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('publication_gates', 'rent_income_join_approved', value=True))

    def test_rejects_static_server_dependency(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('runtime', 'application_server_required', value=True))

    def test_rejects_dropped_interactive_maps(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('runtime', 'client_maps', value=None))

    def test_rejects_removed_accessible_visual_milestones(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('runtime', 'interactive_requirements_milestones', value=['M05']))

    def test_rejects_unreviewed_policy_decision(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('decision_status', value='proposed_for_review'))

    def test_rejects_implementation_activation(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('implementation_active', value=True))

    def test_rejects_missing_acceptance_record(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('maintainer_decision_record', value='docs/architecture/missing.md'))

    def test_rejects_unreviewed_top_level_schema(self):
        with self.assertRaises(ArchitectureError):
            validate_policy(self.modify('schema_version', value=99))


if __name__ == '__main__':
    unittest.main()
