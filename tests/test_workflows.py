"""Fail closed if someone adds an accidental expensive automatic CI/deploy trigger."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowCostPolicyTests(unittest.TestCase):
    def test_workflows_exist_and_dispatch_only(self):
        paths = sorted(WORKFLOWS.glob("*.yml"))
        self.assertEqual({p.name for p in paths}, {"pages.yml", "verify.yml"})
        for path in paths:
            body = path.read_text(encoding="utf-8")
            # `on` must be a top-level mapping, not a YAML string or folded event list.
            self.assertRegex(body, r"(?m)^on:\s*$")
            on_block = body.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
            self.assertRegex(on_block, r"(?m)^  workflow_dispatch:\s*$")
            for trigger in ("push", "pull_request", "schedule", "workflow_run", "release", "create", "merge_group"):
                self.assertNotRegex(on_block, rf"(?m)^  {trigger}:\s*")

    def test_pages_requires_confirmation_and_main_branch(self):
        body = (WORKFLOWS / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("inputs.confirm_release == true", body)
        self.assertIn("github.ref == 'refs/heads/main'", body)
        self.assertIn("needs: build", body)
        self.assertIn("environment:\n      name: github-pages", body)
        self.assertIn("cancel-in-progress: false", body)
        self.assertIn("pnpm install --frozen-lockfile", body)
        self.assertIn("frontend/out", body)
        self.assertIn("actions/deploy-pages@v4", body)


if __name__ == "__main__":
    unittest.main()
