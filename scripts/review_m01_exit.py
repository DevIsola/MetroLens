#!/usr/bin/env python3
"""Review M01 foundation before merge; never approve publication or mark M01 done."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.sync_roadmap import StatusValidationError, update_markdown, validate_status


class M01ExitError(ValueError):
    """The repository fails a pre-merge M01 acceptance contract."""


TASK_DOCS = (
    "docs/M01_FOUNDATION_SCOPE.md",
    "docs/M01_T02_TOOLCHAINS.md",
    "docs/M01_T03_APPLICATION_SCAFFOLD.md",
    "docs/M01_T04_REPOSITORY_GOVERNANCE.md",
    "docs/M01_T05_DOCS_AS_CODE.md",
    "docs/M01_T06_SECURITY_AND_DEPENDENCIES.md",
    "docs/M01_T07_STATIC_EXPORT.md",
)
REQUIRED = (
    *TASK_DOCS,
    "CHANGELOG.md", "SECURITY.md", "docs/adr/README.md",
    "docs/M01_PREMERGE_REVIEW.md",
    "docs/roadmap-status.json", "docs/NORTHSTAR_MASTER_ROADMAP.md",
    "docs/architecture/static_pipeline_policy.json",
    "docs/architecture/m01_t04_governance_policy.json",
    "docs/architecture/m01_t06_security_policy.json",
    ".github/workflows/verify.yml", ".github/workflows/pages.yml",
    "scripts/activate_m01.py", "scripts/validate_m01_workspace.py",
    "scripts/validate_m01_toolchains.py", "scripts/validate_m01_frontend.py",
    "scripts/validate_m01_governance.py", "scripts/validate_m01_docs.py",
    "scripts/validate_m01_security.py", "scripts/validate_m01_static_export.py",
    ".node-version", ".python-version", "pnpm-lock.yaml", "uv.lock",
    "frontend/package.json", "frontend/next.config.ts",
    "frontend/app/page.tsx", "frontend/app/methodology/page.tsx",
)


def _read(root: Path, path: str) -> str:
    try:
        return (root / path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise M01ExitError(f"Missing or unreadable {path}: {exc}") from exc


def _json(root: Path, path: str) -> dict:
    try:
        data = json.loads(_read(root, path))
    except ValueError as exc:
        raise M01ExitError(f"Invalid JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise M01ExitError(f"Expected object {path}")
    return data


def _workflow_events(content: str, filename: str) -> None:
    lines = content.splitlines()
    indices = [i for i, line in enumerate(lines) if line == "on:"]
    if len(indices) != 1:
        raise M01ExitError(f"{filename}: exactly one top-level on: map is required")
    events: list[str] = []
    for line in lines[indices[0] + 1:]:
        if line and not line.startswith((" ", "#")):
            break
        match = re.match(r"^  ([A-Za-z][A-Za-z_0-9]*):", line)
        if match:
            events.append(match.group(1))
    if events != ["workflow_dispatch"]:
        raise M01ExitError(f"{filename}: automatic or unexpected triggers {events}")


def review(root: Path = ROOT) -> dict:
    for path in REQUIRED:
        _read(root, path)

    status = _json(root, "docs/roadmap-status.json")
    try:
        validate_status(status)
        markdown = _read(root, "docs/NORTHSTAR_MASTER_ROADMAP.md")
        if update_markdown(markdown, status) != markdown:
            raise M01ExitError("Generated roadmap status is out of sync")
    except StatusValidationError as exc:
        raise M01ExitError(f"Roadmap validation failed: {exc}") from exc

    m00, m01 = status["milestones"][:2]
    if (m00.get("status") != "done" or
        m00.get("merged_commit") != "87e9d035dfbc841c0282ec35da7a3d29707f7ff1" or
        m00.get("prs") != ["https://github.com/DevIsola/UrbanGauge/pull/1"]):
        raise M01ExitError("M00 completed-merge evidence is missing or changed")
    if (m01.get("status") != "in_progress" or m01.get("prs") != [] or
        m01.get("merged_commit") is not None or m01.get("accepted_at") is not None):
        raise M01ExitError("Pre-merge M01 may not claim merged or completed state")

    policy = _json(root, "docs/architecture/static_pipeline_policy.json")
    execution = policy.get("execution", {})
    if (policy.get("decision_status") != "accepted_for_planning" or
        policy.get("implementation_active") is not False or
        policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False or
        not policy.get("publication_gates") or
        any(value is not False for value in policy["publication_gates"].values()) or
        execution.get("github_actions_triggers") != ["workflow_dispatch"] or
        any(execution.get(key) is not False for key in ("push_auto_ci", "automatic_deploy", "scheduled_etl"))):
        raise M01ExitError("Source, deployment or execution restrictions changed")

    gov = _json(root, "docs/architecture/m01_t04_governance_policy.json")
    sec = _json(root, "docs/architecture/m01_t06_security_policy.json")
    if (gov.get("status") != "repository_files_prepared_admin_review_pending" or
        gov.get("license_selected") is not False or
        gov.get("required_status_checks_enabled_by_increment") is not False or
        gov.get("rulesets_configured_by_increment") is not False or
        sec.get("status") != "repository_security_contract_prepared_admin_review_pending" or
        sec.get("license_selected") is not False or
        sec.get("dependabot_config_committed") is not False or
        sec.get("github_secret_scanning_verified") is not False or
        sec.get("external_dependency_audit_verified") is not False):
        raise M01ExitError("Unverified admin, licence or security settings were claimed")

    verify = _read(root, ".github/workflows/verify.yml")
    pages = _read(root, ".github/workflows/pages.yml")
    _workflow_events(verify, "verify.yml")
    _workflow_events(pages, "pages.yml")
    if not re.search(r"(?m)^permissions:\n  contents: read\s*$", verify):
        raise M01ExitError("Manual verifier must be read-only")
    if any(s in verify for s in ("pages: write", "id-token: write", "actions/deploy-pages", "actions/upload-pages-artifact")):
        raise M01ExitError("Verification workflow has a deployment capability")
    for command in ("run: python -m unittest discover -s tests -v",
                    "run: python scripts/validate_m01_security.py",
                    "run: pnpm --dir frontend build",
                    "run: python scripts/validate_m01_static_export.py --smoke --base-path /UrbanGauge"):
        if command not in verify:
            raise M01ExitError(f"Manual verification workflow missing {command}")
    if "output: \"export\"" not in _read(root, "frontend/next.config.ts"):
        raise M01ExitError("Frontend must remain a static export")
    static_guide = _read(root, "docs/M01_T07_STATIC_EXPORT.md")
    if "--smoke --base-path=" not in static_guide or "--smoke --base-path /UrbanGauge" not in static_guide:
        raise M01ExitError("PowerShell root and project-path smoke commands are not documented")
    if "M01 pre-merge review" not in _read(root, "CHANGELOG.md"):
        raise M01ExitError("Pre-merge documentation was not recorded")
    if "root-path smoke" not in _read(root, "docs/M01_PREMERGE_REVIEW.md"):
        raise M01ExitError("Pre-merge review must disclose root-path smoke status")

    return {
        "milestone": "M01",
        "status": "premerge_contract_validated_review_pending",
        "m00": "done", "m01": "in_progress",
        "task_contracts_present": len(TASK_DOCS),
        "manual_only_workflows": True,
        "public_data_export_approved": False,
        "publisher_join_approved": False,
        "automatic_deployment_enabled": False,
        "license_selected": False,
        "root_smoke_verified_by_this_command": False,
        "subpath_smoke_verified_by_this_command": False,
        "hosted_ci_verified_by_this_command": False,
        "pr_merged": False,
        "requires_maintainer_review": True,
        "requires_merge_evidence_before_done": True,
        "open_decisions": [
            "Licence selection or explicitly accepted deferral",
            "Lint tooling gap relative to M01 roadmap",
            "Admin settings, labels and optional hosted security review",
            "Locale route work deferred to M05, if accepted",
            "Root-path smoke output and manual PR review",
        ],
    }


def main() -> int:
    try:
        print(json.dumps(review(), indent=2))
        return 0
    except (M01ExitError, StatusValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"milestone": "M01", "status": "invalid", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
