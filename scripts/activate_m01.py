#!/usr/bin/env python3
"""Explicit, offline M01-T01 roadmap transition after verified M00 merge."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from sync_roadmap import update_markdown, validate_status

ROOT = Path(__file__).resolve().parent.parent
MERGE_SHA = "87e9d035dfbc841c0282ec35da7a3d29707f7ff1"
MERGED_PR = "https://github.com/DevIsola/UrbanGauge/pull/1"
M01_NOTE = (
    "M01-T01 engineering foundation started 2026-10-27 after accepted and merged "
    "M00 discovery. Local onboarding, frontend/pipeline boundaries and workspace "
    "validation only. Runtime pinning/lockfiles, actual packages, CI governance, "
    "static export and licence selection remain pending; Actions/ETL/publication "
    "remain manual-only or disabled."
)


class ActivationError(ValueError):
    """Do not alter the roadmap if an acceptance prerequisite is missing."""


def prepare(root: Path) -> tuple[str, str, bool]:
    status_path = root / "docs/roadmap-status.json"
    roadmap_path = root / "docs/NORTHSTAR_MASTER_ROADMAP.md"
    data = json.loads(status_path.read_text(encoding="utf-8"))
    validate_status(data)
    m00, m01 = data["milestones"][:2]
    if (m00["id"] != "M00" or m00["status"] != "done" or
        m00.get("merged_commit") != MERGE_SHA or MERGED_PR not in m00.get("prs", []) or
        not m00.get("accepted_at") or not m00.get("evidence")):
        raise ActivationError("M00 verified merge/acceptance evidence is missing")
    if m01["id"] != "M01" or m01["status"] not in {"not_started", "in_progress"}:
        raise ActivationError("M01 cannot start from the current state")
    if m01.get("prs") or m01.get("merged_commit") or m01.get("accepted_at"):
        raise ActivationError("M01 must not have fabricated PR or merge evidence")
    policy = json.loads((root / "docs/architecture/static_pipeline_policy.json").read_text(encoding="utf-8"))
    gates = policy.get("publication_gates", {})
    execution = policy.get("execution", {})
    if (policy.get("implementation_active") is not False or
        any(flag is not False for flag in gates.values()) or
        execution.get("github_actions_triggers") != ["workflow_dispatch"] or
        execution.get("automatic_deploy") is not False or
        execution.get("scheduled_etl") is not False):
        raise ActivationError("M00 publication/deployment protections changed")
    # A subsequent M01-T02+ update is legitimate; never overwrite its notes.
    already = m01["status"] == "in_progress"
    if not already:
        m01["status"] = "in_progress"
        m01["notes"] = M01_NOTE
        data["updated_at"] = "2026-10-27"
    validate_status(data)
    original_roadmap = roadmap_path.read_text(encoding="utf-8")
    rendered = update_markdown(original_roadmap, data)
    original_status = status_path.read_text(encoding="utf-8")
    updated_status = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return (updated_status, rendered,
            already and original_roadmap == rendered and original_status == updated_status)



def on_branch(root: Path) -> str:
    proc = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode:
        raise ActivationError("Not a valid Git working tree")
    return proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Review intended update; do not write")
    group.add_argument("--apply", action="store_true", help="Apply validated roadmap state change")
    args = parser.parse_args()
    try:
        branch = on_branch(ROOT)
        if branch != "feat/M01-engineering-foundation":
            raise ActivationError(f"Expected feat/M01-engineering-foundation; found {branch!r}")
        data, markdown, unchanged = prepare(ROOT)
        if args.apply and not unchanged:
            (ROOT / "docs/roadmap-status.json").write_text(data, encoding="utf-8", newline="\n")
            (ROOT / "docs/NORTHSTAR_MASTER_ROADMAP.md").write_text(markdown, encoding="utf-8", newline="\n")
        result = {
            "milestone": "M01-T01",
            "status": "m01_roadmap_activated" if args.apply else "m01_activation_dry_run_passed",
            "branch": branch,
            "m00": "done",
            "m01": "in_progress" if args.apply or unchanged else "not_started_until_apply",
            "changed_paths": [] if (unchanged or not args.apply) else ["docs/roadmap-status.json", "docs/NORTHSTAR_MASTER_ROADMAP.md"],
            "automatic_deployment_enabled": False,
            "publication_approved": False,
        }
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"milestone": "M01-T01", "status": "blocked", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
