#!/usr/bin/env python3
"""M01-T03 static scaffold contract. No network, framework execution or publication."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent


class ScaffoldError(ValueError):
    """Workspace violates the static-only, unpublished M01-T03 contract."""


def _read(root: Path, path: str) -> str:
    try:
        return (root / path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ScaffoldError(f"Missing required scaffold file {path}: {exc}") from exc


def review(root: Path = ROOT, *, require_lockfile: bool = True) -> dict:
    root_package = json.loads(_read(root, "package.json"))
    frontend = json.loads(_read(root, "frontend/package.json"))
    tsconfig = json.loads(_read(root, "frontend/tsconfig.json"))
    roadmap = json.loads(_read(root, "docs/roadmap-status.json"))
    policy = json.loads(_read(root, "docs/architecture/static_pipeline_policy.json"))
    config = _read(root, "frontend/next.config.ts")
    home = _read(root, "frontend/app/page.tsx")
    layout = _read(root, "frontend/app/layout.tsx")
    css = _read(root, "frontend/app/globals.css")
    _read(root, "pipeline/src/urbangauge_pipeline/contracts.py")
    workspace = _read(root, "pnpm-workspace.yaml")

    if root_package.get("packageManager") != "pnpm@10.34.9":
        raise ScaffoldError("Root pnpm manager pin drifted")
    if frontend.get("name") != "@urbangauge/frontend" or frontend.get("private") is not True:
        raise ScaffoldError("Frontend workspace must be private and consistently named")
    if "frontend" not in workspace:
        raise ScaffoldError("pnpm workspace omits frontend")
    deps = frontend.get("dependencies", {})
    dev = frontend.get("devDependencies", {})
    for package in ("next", "react", "react-dom"):
        version = deps.get(package)
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise ScaffoldError(f"Dependency must be pinned to an exact version: {package}")
    for package in ("typescript", "@types/react", "@types/react-dom", "@types/node"):
        version = dev.get(package)
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise ScaffoldError(f"Dev dependency must be pinned: {package}")
    if deps["react"] != deps["react-dom"]:
        raise ScaffoldError("React and react-dom versions must be equal")
    if tsconfig.get("compilerOptions", {}).get("strict") is not True or tsconfig["compilerOptions"].get("noEmit") is not True:
        raise ScaffoldError("TypeScript must enable strict and noEmit")
    if not re.search(r"output:\s*['\"]export['\"]", config):
        raise ScaffoldError("Next.js static export must remain enabled")
    if "NEXT_PUBLIC_BASE_PATH" not in config or "trailingSlash: true" not in config:
        raise ScaffoldError("Static project-site base path or direct-deep-link contract missing")
    if "images: { unoptimized: true }" not in config:
        raise ScaffoldError("Static export cannot require the Next.js image optimizer")
    if "next/link" not in home or "source" not in home.lower() or "No public datasets available yet" not in home:
        raise ScaffoldError("Landing page lacks source separation or unpublished-data disclosure")
    if "import \"./globals.css\"" not in layout or "@media" not in css:
        raise ScaffoldError("Shared responsive stylesheet is missing")
    milestones = roadmap.get("milestones", [])
    if len(milestones) < 2 or milestones[0].get("status") != "done" or milestones[1].get("status") != "in_progress":
        raise ScaffoldError("M00/M01 milestone lifecycle is incorrect")
    run = policy.get("execution", {})
    if (run.get("github_actions_triggers") != ["workflow_dispatch"] or run.get("push_auto_ci") is not False or
        run.get("automatic_deploy") is not False or run.get("scheduled_etl") is not False):
        raise ScaffoldError("Automatic workflow/deployment unexpectedly enabled")
    if (policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False or
        any(v is not False for v in policy.get("publication_gates", {}).values())):
        raise ScaffoldError("Unapproved source publication/comparability gate enabled")
    for rel in ("frontend/public", "frontend/app/api"):
        if (root / rel).exists():
            raise ScaffoldError(f"Unexpected public data or API path in static scaffold: {rel}")
    if require_lockfile:
        lock = _read(root, "pnpm-lock.yaml")
        if "lockfileVersion: '9.0'" not in lock or not re.search(r"(?m)^\s{2}frontend:\s*$", lock):
            raise ScaffoldError("pnpm lockfile must include the new frontend importer; regenerate with pinned pnpm 10")

    return {
        "milestone": "M01-T03",
        "status": "static_frontend_scaffold_validated",
        "next": deps["next"],
        "react": deps["react"],
        "typescript": dev["typescript"],
        "strict_typescript": True,
        "static_export_configured": True,
        "pnpm_lockfile_frontend_importer_checked": require_lockfile,
        "production_build_verified": False,
        "automatic_deployment_enabled": False,
        "publication_approved": False,
        "publisher_join_approved": False,
    }


def main() -> int:
    try:
        print(json.dumps(review(), indent=2))
        return 0
    except (ScaffoldError, ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"milestone": "M01-T03", "status": "invalid", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
