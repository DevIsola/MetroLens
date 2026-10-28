#!/usr/bin/env python3
"""Offline M01-T02 toolchain/lockfile contract; no install or network access."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
NODE = "24.22.1"
PNPM = "10.34.9"
PYTHON = "3.13"
UV = "0.10.0"


class ToolchainError(ValueError):
    """A version, package lock or M00/M01 safety contract changed unexpectedly."""


def _text(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8-sig")


def _json(root: Path, path: str) -> dict:
    value = json.loads(_text(root, path))
    if not isinstance(value, dict):
        raise ToolchainError(f"Expected JSON object in {path}")
    return value


def validate(root: Path = ROOT) -> dict:
    """Validate metadata, not executable availability; installed versions are checked separately."""
    required = [
        ".node-version", ".python-version", "package.json", "pnpm-workspace.yaml",
        "pnpm-lock.yaml", "pyproject.toml", "uv.lock",
        "docs/roadmap-status.json", "docs/architecture/static_pipeline_policy.json",
        ".github/workflows/verify.yml", ".github/workflows/pages.yml",
    ]
    for item in required:
        if not (root / item).is_file():
            raise ToolchainError(f"Missing required toolchain/repository contract: {item}")
    if _text(root, ".node-version").strip() != NODE:
        raise ToolchainError("Node release no longer matches pinned .node-version")
    if _text(root, ".python-version").strip() != PYTHON:
        raise ToolchainError("Python version no longer matches pinned .python-version")

    package = _json(root, "package.json")
    if (package.get("name") != "urbangauge-workspace" or
        package.get("private") is not True or
        package.get("packageManager") != f"pnpm@{PNPM}"):
        raise ToolchainError("Private package or exact pnpm pin changed")
    if package.get("engines", {}) != {"node": ">=24.22.1 <25", "pnpm": PNPM}:
        raise ToolchainError("Node/pnpm engines do not match the pinned toolchain")
    for key in ("dependencies", "devDependencies", "optionalDependencies"):
        if key in package and not isinstance(package[key], dict):
            raise ToolchainError(f"Malformed package.json {key}")
    scripts = package.get("scripts", {})
    if (not isinstance(scripts, dict) or
        scripts.get("check:toolchains") != "python scripts/validate_m01_toolchains.py" or
        scripts.get("test:python") != "python -m unittest discover -s tests -v"):
        raise ToolchainError("Validation/test entrypoints missing or changed")
    # M01-T03 may add real frontend dependencies and a build command later.
    # Do not assert an empty future dependency graph here.

    workspace = _text(root, "pnpm-workspace.yaml")
    if not re.search(r"(?m)^packages:\s*$", workspace) or not re.search(
        r"(?m)^\s*-\s*['\"]?frontend['\"]?\s*$", workspace
    ):
        raise ToolchainError("pnpm workspace no longer includes frontend/")
    lock = _text(root, "pnpm-lock.yaml")
    if (not re.search(r"(?m)^lockfileVersion:\s*['\"]?9\.0['\"]?\s*$", lock) or
        not re.search(r"(?m)^importers:\s*$", lock) or
        not re.search(r"(?m)^\s{2}\.:(?:\s|$)", lock)):
        raise ToolchainError("pnpm v10 lockfile schema/root importer missing")

    pyproject = tomllib.loads(_text(root, "pyproject.toml"))
    project = pyproject.get("project", {})
    if (project.get("name") != "urbangauge-pipeline" or
        project.get("requires-python") != ">=3.13,<3.14" or
        not isinstance(project.get("dependencies"), list)):
        raise ToolchainError("Python project constraints differ from documented 3.13 lock")
    uv_cfg = pyproject.get("tool", {}).get("uv", {})
    if (uv_cfg.get("package") is not False or
        uv_cfg.get("required-version") != f"=={UV}"):
        raise ToolchainError("uv is not pinned to the non-packaged pipeline workspace")
    uv_lock = tomllib.loads(_text(root, "uv.lock"))
    if (uv_lock.get("version") != 1 or
        uv_lock.get("requires-python") != "==3.13.*" or
        not any(p.get("name") == "urbangauge-pipeline" and
                    p.get("source") == {"virtual": "."} for p in uv_lock.get("package", []))):
        raise ToolchainError("uv.lock does not describe the expected local Python project")

    roadmap = _json(root, "docs/roadmap-status.json")
    milestones = roadmap.get("milestones", [])
    if (len(milestones) != 12 or milestones[0].get("status") != "done" or
        milestones[1].get("status") != "in_progress" or
        any(m.get("status") != "not_started" for m in milestones[2:])):
        raise ToolchainError("M00 done/M01 in progress milestone boundary changed")
    policy = _json(root, "docs/architecture/static_pipeline_policy.json")
    exe = policy.get("execution", {})
    if (policy.get("implementation_active") is not False or
        exe.get("github_actions_triggers") != ["workflow_dispatch"] or
        exe.get("automatic_deploy") is not False or
        exe.get("push_auto_ci") is not False or
        exe.get("scheduled_etl") is not False or
        policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False or
        any(v is not False for v in policy.get("publication_gates", {}).values())):
        raise ToolchainError("Architecture/publication/automatic-workflow safeguard changed")
    for item in (".github/workflows/verify.yml", ".github/workflows/pages.yml"):
        workflow = _text(root, item)
        if "workflow_dispatch:" not in workflow or any(
            line.lstrip().startswith(trigger) for line in workflow.splitlines()
            for trigger in ("push:", "pull_request:", "schedule:")
        ):
            raise ToolchainError(f"Workflow auto-triggered: {item}")

    return {
        "milestone": "M01-T02",
        "status": "toolchain_contract_validated",
        "node": NODE,
        "pnpm": PNPM,
        "python": PYTHON,
        "uv": UV,
        "node_lockfile": "pnpm-lock.yaml",
        "python_lockfile": "uv.lock",
        "third_party_dependencies_installed": False,
        "nextjs_installed": False,
        "m00": "done",
        "m01": "in_progress",
        "automatic_deployment_enabled": False,
        "publication_approved": False,
        "publisher_join_approved": False,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), indent=2))
        return 0
    except (ToolchainError, ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"milestone": "M01-T02", "status": "blocked", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
