#!/usr/bin/env python3
"""M01-T01 contract: deliberate workspace scaffolding without live publishing."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


class WorkspaceError(ValueError):
    """Repo foundation conflicts with accepted M00 gates."""


def validate(root: Path = ROOT) -> dict:
    required = [
        ".editorconfig", "docs/DEVELOPMENT.md", "docs/M01_FOUNDATION_SCOPE.md",
        "frontend/README.md", "pipeline/README.md", "scripts/activate_m01.py",
        "docs/roadmap-status.json", "docs/architecture/static_pipeline_policy.json",
        ".github/workflows/verify.yml", ".github/workflows/pages.yml",
    ]
    for path in required:
        if not (root / path).is_file():
            raise WorkspaceError(f"Missing M01-T01 file: {path}")
    status = json.loads((root / "docs/roadmap-status.json").read_text(encoding="utf-8"))
    milestones = status.get("milestones", [])
    if len(milestones) != 12 or [m.get("id") for m in milestones] != [f"M{i:02d}" for i in range(12)]:
        raise WorkspaceError("Unexpected roadmap milestone IDs")
    m00, m01 = milestones[:2]
    if (m00.get("status") != "done" or m01.get("status") != "in_progress" or
        m01.get("merged_commit") is not None or m01.get("accepted_at") is not None):
        raise WorkspaceError("M00/M01 milestone state is not the approved transition")
    policy = json.loads((root / "docs/architecture/static_pipeline_policy.json").read_text(encoding="utf-8"))
    if (policy.get("decision_status") != "accepted_for_planning" or
        policy.get("implementation_active") is not False or
        any(v is not False for v in policy.get("publication_gates", {}).values()) or
        policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False):
        raise WorkspaceError("Architecture or publisher gates unexpectedly activated")
    exe = policy.get("execution", {})
    if (exe.get("github_actions_triggers") != ["workflow_dispatch"] or
        exe.get("automatic_deploy") is not False or
        exe.get("push_auto_ci") is not False or
        exe.get("scheduled_etl") is not False):
        raise WorkspaceError("Automatic workflow/ETL trigger enabled")
    for path in [".github/workflows/verify.yml", ".github/workflows/pages.yml"]:
        body = (root / path).read_text(encoding="utf-8")
        if "workflow_dispatch:" not in body or any(
            row.lstrip().startswith(k) for row in body.splitlines() for k in ("push:", "pull_request:", "schedule:")
        ):
            raise WorkspaceError(f"Workflow is not manual-only: {path}")
    if "root = true" not in (root / ".editorconfig").read_text(encoding="utf-8"):
        raise WorkspaceError("Editor conventions missing")
    for path, marker in (("frontend/README.md", "No UI runtime"),
                         ("pipeline/README.md", "No live HTTP ingestion")):
        if marker not in (root / path).read_text(encoding="utf-8"):
            raise WorkspaceError(f"Boundary description incomplete: {path}")
    return {
        "milestone": "M01-T01", "status": "m01_t01_workspace_validated",
        "m00": "done", "m01": "in_progress",
        "framework_installation_required_now": False,
        "automatic_deployment_enabled": False, "publication_approved": False,
        "publisher_join_approved": False,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), indent=2))
        return 0
    except (WorkspaceError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"milestone": "M01-T01", "status": "blocked", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
