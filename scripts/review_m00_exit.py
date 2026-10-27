#!/usr/bin/env python3
"""Offline M00 acceptance readiness: no PR/merge/publication authorization."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

class ExitReviewError(ValueError):
    """M00 planning/evidence contract is incomplete or altered."""


def _load(root: Path, relative: str) -> dict:
    path = root / relative
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ExitReviewError(f"Cannot read {relative}: {exc}") from exc
    if not isinstance(data, dict):
        raise ExitReviewError(f"Expected a JSON object: {relative}")
    return data


def review(*, root: Path = ROOT) -> dict:
    naming = _load(root, "docs/branding/m00_t06_name_review.json")
    roadmap = _load(root, "docs/roadmap-status.json")
    policy = _load(root, "docs/architecture/static_pipeline_policy.json")
    evidence = _load(root, "docs/evidence-vancouver-m00.json")
    try:
        readme = (root / "README.md").read_text(encoding="utf-8")
        design = (root / "docs/design/M00_T04_REVIEW_DECISION.md").read_text(encoding="utf-8")
        decision = (root / "docs/architecture/M00_T05_REVIEW_DECISION.md").read_text(encoding="utf-8")
        verify = (root / ".github/workflows/verify.yml").read_text(encoding="utf-8")
        pages = (root / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    except OSError as exc:
        raise ExitReviewError(f"Missing review document or workflow: {exc}") from exc

    remote = naming.get("repository_migration")
    if not isinstance(remote, dict) or remote != {
        "status": "verified_completed",
        "scope": "github_repository_slug_only",
        "old_repository": "DevIsola/MetroLens",
        "new_repository": "DevIsola/UrbanGauge",
        "verified_on": "2026-10-27",
        "evidence": "GitHub repository metadata and maintainer git fetch/status/push",
        "deployment_authorized": False,
    }:
        raise ExitReviewError("GitHub rename evidence missing or changed")
    if not readme.startswith("# UrbanGauge\n") or "https://github.com/DevIsola/UrbanGauge" not in readme:
        raise ExitReviewError("Current README identity or repo URL is missing")
    if naming.get("selected_name") != "UrbanGauge" or naming.get("repository_rename_approved") is not True or naming.get("migration_performed") is not True:
        raise ExitReviewError("Repository migration/name decision is inconsistent")
    if any(naming.get(k) is not False for k in ("trademark_clearance_verified", "domain_availability_verified", "public_rebrand_performed", "production_ready")):
        raise ExitReviewError("Unverified brand or production approval was granted")
    items = roadmap.get("milestones")
    if not isinstance(items, list) or len(items) != 12 or [m.get("id") for m in items] != [f"M{i:02d}" for i in range(12)]:
        raise ExitReviewError("Roadmap milestones M00–M11 changed")
    m00, m01 = items[:2]
    if m00.get("status") != "in_progress" or m01.get("status") != "not_started":
        raise ExitReviewError("M00 may not be marked done or M01 started before acceptance")
    if m00.get("merged_commit") is not None or m00.get("accepted_at") is not None:
        raise ExitReviewError("Cannot fabricate M00 merge/acceptance evidence")
    if policy.get("decision_status") != "accepted_for_planning" or policy.get("implementation_active") is not False:
        raise ExitReviewError("ADR-0001 is not accepted only as a plan")
    execution = policy.get("execution", {})
    if (execution.get("github_actions_triggers") != ["workflow_dispatch"] or
        execution.get("push_auto_ci") is not False or execution.get("automatic_deploy") is not False or
        execution.get("scheduled_etl") is not False):
        raise ExitReviewError("Manual-only workflow restrictions changed")
    if policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False:
        raise ExitReviewError("Premature public export enabled")
    if any(value is not False for value in policy.get("publication_gates", {}).values()):
        raise ExitReviewError("Source or metric publication gates activated")
    if evidence.get("region_id") != "vancouver_cma_2021" or evidence.get("approved_for_publication") is not False or evidence.get("metric_comparability_approved") is not False:
        raise ExitReviewError("Source evidence was reclassified as published/comparable")
    if evidence.get("income", {}).get("dguid") != "2021S0503933" or evidence.get("rent", {}).get("source_row") != 36:
        raise ExitReviewError("Audited Vancouver source identity changed")
    if "ACCEPTED" not in design or "ACCEPT" not in decision:
        raise ExitReviewError("Design or architecture acceptance evidence missing")
    for name, content in (("verify", verify), ("pages", pages)):
        if "workflow_dispatch:" not in content:
            raise ExitReviewError(f"{name} workflow is not manual-only")
        if any(line.lstrip().startswith(key) for line in content.splitlines() for key in ("push:", "pull_request:", "schedule:")):
            raise ExitReviewError(f"{name} workflow has automatic triggers")

    return {
        "milestone": "M00",
        "status": "discovery_evidence_ready_for_manual_exit_review",
        "project_name": "UrbanGauge",
        "github_repository": "DevIsola/UrbanGauge",
        "repository_rename_verified": True,
        "design_review_accepted": True,
        "architecture_accepted_for_planning": True,
        "source_specific_vancouver_evidence_documented": True,
        "automatic_deployment_enabled": False,
        "publication_approved": False,
        "rent_to_income_ratio": None,
        "m00_marked_done": False,
        "m01_started": False,
        "remaining_gates": [
            "Maintainer M00 acceptance review and merged PR with actual merge SHA",
            "Record source reuse/attribution disposition; do not publish source data meanwhile",
            "Cross-publisher CMA crosswalk and income/rent comparability remain unapproved",
        ],
        "next_step": "Review M00 evidence, open PR from feat/M00-product-discovery to main, and only mark done after actual acceptance/merge evidence",
    }


def main() -> int:
    try:
        report = review()
    except (ExitReviewError, ValueError, TypeError) as exc:
        print(json.dumps({"milestone": "M00", "status": "invalid", "reason": str(exc), "publication_approved": False}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
