#!/usr/bin/env python3
"""Offline M01-T04 repository-file governance; never asserts GitHub admin settings."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
FORMS = (
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/source_review.yml",
)
WORKFLOWS = (".github/workflows/verify.yml", ".github/workflows/pages.yml")


class GovernanceError(ValueError):
    """Governance files or retained safeguards are not valid."""


def _read(root: Path, path: str) -> str:
    try:
        return (root / path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise GovernanceError(f"Missing or unreadable file {path}: {exc}") from exc


def _json(root: Path, path: str) -> dict:
    try:
        data = json.loads(_read(root, path))
    except ValueError as exc:
        raise GovernanceError(f"Invalid JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GovernanceError(f"Expected object at {path}")
    return data


def _manual_only_workflow(text: str, path: str) -> None:
    # Require an actual top-level YAML event mapping (not a comment or quoted string).
    m = re.search(r"(?m)^on:\s*\n((?:[ \t]+[^\n]*\n|[ \t]*\n)*)", text)
    if m is None:
        raise GovernanceError(f"{path}: missing explicit on event map")
    events = re.findall(r"(?m)^  ([a-zA-Z][a-zA-Z0-9_-]*):", m.group(1))
    if events != ["workflow_dispatch"]:
        raise GovernanceError(f"{path}: only workflow_dispatch is allowed, got {events}")


def validate(root: Path = ROOT) -> dict:
    meta = _json(root, "docs/architecture/m01_t04_governance_policy.json")
    if meta.get("milestone") != "M01-T04" or meta.get("status") != "repository_files_prepared_admin_review_pending":
        raise GovernanceError("M01-T04 must remain a documented governance-file proposal")
    if meta.get("repo") != "DevIsola/UrbanGauge" or meta.get("manual_actions_only") is not True:
        raise GovernanceError("Unexpected repository or action policy")
    restricted = (
        "automatic_ci_enabled_by_increment", "automatic_deployment_enabled_by_increment",
        "required_status_checks_enabled_by_increment", "rulesets_configured_by_increment",
        "labels_created_by_increment", "publication_approved", "source_crosswalk_approved",
        "license_selected",
    )
    if any(meta.get(k) is not False for k in restricted):
        raise GovernanceError("File proposal falsely claims permissions, settings or release")

    roadmap = _json(root, "docs/roadmap-status.json")
    milestones = roadmap.get("milestones", [])
    if len(milestones) != 12 or milestones[0].get("status") != "done" or milestones[1].get("status") not in ("in_progress", "done"):
        raise GovernanceError("M00/M01 milestone state is not valid for M01-T04")
    policy = _json(root, "docs/architecture/static_pipeline_policy.json")
    if policy.get("decision_status") != "accepted_for_planning" or policy.get("implementation_active") is not False:
        raise GovernanceError("M00 architecture wrongly marked active")
    if policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False:
        raise GovernanceError("Public data export became active")
    if any(v is not False for v in policy.get("publication_gates", {}).values()):
        raise GovernanceError("Publication gates opened")
    execution = policy.get("execution", {})
    for key in ("push_auto_ci", "automatic_deploy", "scheduled_etl"):
        if execution.get(key) is not False:
            raise GovernanceError(f"Execution gate opened: {key}")
    if execution.get("github_actions_triggers") != ["workflow_dispatch"]:
        raise GovernanceError("Architecture permits automatic workflow triggers")
    for file in WORKFLOWS:
        _manual_only_workflow(_read(root, file), file)

    pr = _read(root, ".github/PULL_REQUEST_TEMPLATE.md")
    for marker in ("Milestone / task IDs", "Evidence / checks", "Source / methodology / release restrictions", "Risks / rollback"):
        if marker not in pr:
            raise GovernanceError(f"PR template is missing review section: {marker}")
    if "No Pages/Cloudflare/public-data deployment" not in pr or "No new push/PR/scheduled" not in pr:
        raise GovernanceError("PR template does not make publication and execution restrictions explicit")

    contrib = _read(root, "CONTRIBUTING.md")
    doc = _read(root, "docs/M01_T04_REPOSITORY_GOVERNANCE.md")
    for marker in ("licence", "workflow_dispatch", "source", "M01"):
        if marker.lower() not in contrib.lower():
            raise GovernanceError(f"Contributor policy missing {marker}")
    for marker in ("required-status-check", "not", "admin", "publisher"):
        if marker.lower() not in doc.lower():
            raise GovernanceError(f"Governance decisions missing {marker}")

    config = _read(root, ".github/ISSUE_TEMPLATE/config.yml")
    if not re.search(r"(?m)^blank_issues_enabled:\s*true\s*$", config):
        raise GovernanceError("Issue chooser must allow unfitted research reports")
    if not re.search(r"(?m)^contact_links:\s*\[\]\s*$", config):
        raise GovernanceError("Issue chooser must not redirect contributors")

    seen: set[str] = set()
    for file in FORMS:
        source = _read(root, file)
        name = re.search(r"(?m)^name:\s*(.+)$", source)
        if not name or len(name.group(1).strip().strip('"')) <= 3:
            raise GovernanceError(f"{file}: missing valid form name")
        if name.group(1).strip() in seen:
            raise GovernanceError(f"Duplicate issue form name: {file}")
        seen.add(name.group(1).strip())
        if not re.search(r"(?m)^description:\s*.+$", source) or not re.search(r"(?m)^body:\s*$", source):
            raise GovernanceError(f"{file}: missing required issue-form fields")
        ids = re.findall(r"(?m)^    id:\s*([a-zA-Z][a-zA-Z0-9_-]*)\s*$", source)
        if not ids or len(ids) != len(set(ids)):
            raise GovernanceError(f"{file}: missing or duplicate form item ID")
        if not re.search(r"(?m)^\s{6}required:\s*true\s*$", source):
            raise GovernanceError(f"{file}: no mandatory source/issue evidence")
        if re.search(r"(?m)^labels:\s*", source):
            raise GovernanceError(f"{file}: do not auto-assign unconfigured GitHub labels")
    return {
        "milestone": "M01-T04",
        "status": "repository_governance_files_validated",
        "issue_forms": len(FORMS),
        "pr_template_present": True,
        "manual_actions_only": True,
        "rulesets_configured_by_increment": False,
        "required_status_checks_enabled_by_increment": False,
        "labels_created_by_increment": False,
        "automatic_deployment_enabled": False,
        "publication_approved": False,
        "admin_review_pending": True,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), indent=2))
        return 0
    except (GovernanceError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"milestone": "M01-T04", "status": "invalid", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
