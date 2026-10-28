#!/usr/bin/env python3
"""Offline M01-T06 checks; does not claim hosted security settings or advisories."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


class SecurityError(ValueError):
    """Repository security contract or high-confidence source hygiene gate failed."""


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise SecurityError(f"Cannot read {rel}: {exc}") from exc


def _json(root: Path, rel: str) -> dict:
    try:
        value = json.loads(_read(root, rel))
    except (ValueError, TypeError) as exc:
        raise SecurityError(f"Invalid {rel}: {exc}") from exc
    if not isinstance(value, dict):
        raise SecurityError(f"Expected JSON object: {rel}")
    return value


def _events(source: str, file: str) -> list[str]:
    # Only accept one explicit top-level YAML on: mapping, with one child event.
    matches = list(re.finditer(r"(?m)^on:\s*$", source))
    if len(matches) != 1:
        raise SecurityError(f"{file}: expected exactly one top-level on mapping")
    lines = source[matches[0].end():].splitlines()
    events = []
    for line in lines:
        if line and not line.startswith((" ", "#")):
            break
        event = re.match(r"^  ([A-Za-z][A-Za-z0-9_-]*):", line)
        if event:
            events.append(event.group(1))
    if events != ["workflow_dispatch"]:
        raise SecurityError(f"{file}: unexpected workflow events {events!r}")
    return events


def _permissions(text: str, *, indent: int, label: str) -> dict[str, str]:
    header = " " * indent + "permissions:"
    lines = text.splitlines()
    indexes = [i for i, line in enumerate(lines) if line == header]
    if len(indexes) != 1:
        raise SecurityError(f"{label}: expected one explicit permissions map")
    output: dict[str, str] = {}
    for line in lines[indexes[0] + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if len(line) - len(line.lstrip(" ")) <= indent:
            break
        m = re.fullmatch(" " * (indent + 2) + r"([a-z-]+): (read|write|none)", line)
        if not m or m.group(1) in output:
            raise SecurityError(f"{label}: invalid or duplicate token permission")
        output[m.group(1)] = m.group(2)
    return output


def _workflow_permissions(root: Path) -> None:
    verify = _read(root, ".github/workflows/verify.yml")
    pages = _read(root, ".github/workflows/pages.yml")
    for path, source in (("verify.yml", verify), ("pages.yml", pages)):
        _events(source, path)
    if _permissions(verify, indent=0, label="verify root") != {"contents": "read"}:
        raise SecurityError("Verifier token must be contents:read only")
    if re.search(r"(?m)^    permissions:\s*$", verify):
        raise SecurityError("Verifier job cannot elevate token permissions")
    if any(needle in verify for needle in ("pages: write", "id-token: write", "actions/deploy-pages", "actions/upload-pages-artifact")):
        raise SecurityError("Verifier cannot include deployment or write token permissions")
    if "run: python scripts/validate_m01_security.py" not in verify:
        raise SecurityError("Manual verifier does not run M01 security check")
    if _permissions(pages, indent=0, label="pages root") != {"contents": "read"}:
        raise SecurityError("Pages root must be read-only")
    if pages.count("\n  build:\n") != 1 or pages.count("\n  deploy:\n") != 1:
        raise SecurityError("Pages must have exactly one build and one deploy job")
    build = pages.split("\n  build:\n", 1)[1].split("\n  deploy:\n", 1)[0]
    deploy = pages.split("\n  deploy:\n", 1)[1]
    if _permissions(build, indent=4, label="pages build") != {"contents": "read"}:
        raise SecurityError("Pages build must be read-only")
    if _permissions(deploy, indent=4, label="pages deploy") != {"contents": "read", "pages": "write", "id-token": "write"}:
        raise SecurityError("Pages deploy must contain only narrowly scoped permissions")
    guard = "github.ref == 'refs/heads/main' && inputs.confirm_release == true"
    if build.count(guard) != 1 or deploy.count(guard) != 1:
        raise SecurityError("Pages build/deploy must be explicit main-only, manually confirmed")


# Deliberately high-confidence only: do not mistake this for a comprehensive secret scan.
_TOKEN_PATTERNS = (
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{70,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
)
_SCAN_SUFFIXES = {"", ".md", ".txt", ".py", ".json", ".toml", ".yaml", ".yml", ".ts", ".tsx", ".js", ".mjs", ".css", ".html", ".csv", ".env"}


def _git_paths(root: Path) -> list[str]:
    try:
        p = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root, capture_output=True, check=False, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SecurityError(f"Cannot enumerate Git files: {exc}") from exc
    if p.returncode:
        raise SecurityError("git ls-files failed; verify from a Git working tree")
    return [x.decode("utf-8", errors="surrogateescape") for x in p.stdout.split(b"\0") if x]


def audit_paths(root: Path, names: list[str]) -> int:
    checked = 0
    for raw in names:
        # Git represents path separators as forward slashes even on Windows.
        name = raw.replace("\\", "/")
        rel = PurePosixPath(name)
        if not name or rel.is_absolute() or ".." in rel.parts:
            raise SecurityError(f"Unexpected Git path: {name}")
        low = name.lower()
        basename = rel.name.lower()
        if (low in (".github/dependabot.yml", ".github/dependabot.yaml") or
            basename in (".env", ".env.local", ".env.production", ".env.development", ".npmrc") or
            (basename.startswith(".env.") and basename != ".env.example") or
            rel.suffix.lower() in (".pem", ".key", ".p12", ".pfx") or
            low.startswith(("pipeline/data/raw/", "pipeline/data/bronze/", "pipeline/data/silver/", "pipeline/data/gold/", "frontend/out/", "frontend/public/data/"))):
            raise SecurityError(f"Disallowed Git-visible secret/data/automation path: {name}")
        file = root / Path(*rel.parts)
        if file.is_symlink():
            raise SecurityError(f"Symlink requires manual review: {name}")
        if not file.is_file() or rel.suffix.lower() not in _SCAN_SUFFIXES:
            continue
        if file.stat().st_size > 2_000_000:
            raise SecurityError(f"Oversized text file requires review: {name}")
        try:
            body = file.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            raise SecurityError(f"Cannot inspect text file {name}: {exc}") from exc
        for pattern in _TOKEN_PATTERNS:
            if pattern.search(body):
                raise SecurityError(f"Potential credential detected in {name}; remove/rotate before commit")
        checked += 1
    return checked


def validate(root: Path = ROOT, *, tracked_files: list[str] | None = None) -> dict:
    policy = _json(root, "docs/architecture/m01_t06_security_policy.json")
    if (policy.get("schema_version") != 1 or policy.get("milestone") != "M01-T06" or
        policy.get("status") != "repository_security_contract_prepared_admin_review_pending" or
        policy.get("repository") != "DevIsola/UrbanGauge" or
        policy.get("manual_workflow_triggers_only") is not True):
        raise SecurityError("Security scope/status/repository contract changed")
    expected = {
        "verify_workflow_permission": {"contents": "read"},
        "pages_build_permission": {"contents": "read"},
        "pages_deploy_permission": {"contents": "read", "pages": "write", "id-token": "write"},
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            raise SecurityError(f"Security policy token permissions changed: {key}")
    remain_false = (
        "dependabot_config_committed", "dependabot_repository_setting_verified",
        "github_secret_scanning_verified", "github_private_vulnerability_reporting_verified",
        "github_rulesets_verified", "required_status_checks_enabled_by_increment",
        "automated_dependency_updates_enabled_by_increment", "automatic_ci_enabled_by_increment",
        "automatic_deployment_enabled_by_increment", "scheduled_etl_enabled_by_increment",
        "publication_approved", "publisher_crosswalk_approved",
        "external_dependency_audit_verified", "license_selected",
    )
    if any(policy.get(key) is not False for key in remain_false):
        raise SecurityError("Unverified hosted control, automation, licence, or publication approved")
    if policy.get("security_review_record") != "docs/M01_T06_SECURITY_AND_DEPENDENCIES.md":
        raise SecurityError("Security review record missing")

    status = _json(root, "docs/roadmap-status.json")
    milestones = status.get("milestones", [])
    if len(milestones) != 12 or milestones[0].get("status") != "done" or milestones[1].get("status") != "in_progress":
        raise SecurityError("M00 done / M01 in progress required")
    arch = _json(root, "docs/architecture/static_pipeline_policy.json")
    execution = arch.get("execution", {})
    if (arch.get("decision_status") != "accepted_for_planning" or
        arch.get("implementation_active") is not False or
        arch.get("storage", {}).get("public_export", {}).get("publication_active") is not False or
        not arch.get("publication_gates") or
        any(v is not False for v in arch["publication_gates"].values()) or
        execution.get("github_actions_triggers") != ["workflow_dispatch"] or
        any(execution.get(k) is not False for k in ("automatic_deploy", "push_auto_ci", "scheduled_etl"))):
        raise SecurityError("Research methodology or execution gates were opened")
    _workflow_permissions(root)
    package = _json(root, "package.json")
    frontend = _json(root, "frontend/package.json")
    if package.get("packageManager") != "pnpm@10.34.9":
        raise SecurityError("Pinned pnpm version changed")
    if _read(root, ".node-version").strip() != "24.22.1":
        raise SecurityError("Pinned Node version changed")
    if _read(root, ".python-version").strip() != "3.13":
        raise SecurityError("Pinned Python minor version changed")
    pyproject = _read(root, "pyproject.toml")
    if 'required-version = "==0.10.0"' not in pyproject or 'requires-python = ">=3.13,<3.14"' not in pyproject:
        raise SecurityError("Python and uv toolchain pins changed")
    for kind in ("dependencies", "devDependencies"):
        values = frontend.get(kind, {})
        if not isinstance(values, dict) or not values or any(not isinstance(ver, str) or not re.fullmatch(r"\d+\.\d+\.\d+", ver) for ver in values.values()):
            raise SecurityError(f"Frontend {kind} must retain exact reviewed versions")
    if "lockfileVersion: '9.0'" not in _read(root, "pnpm-lock.yaml"):
        raise SecurityError("pnpm lockfile version absent")
    if "version = 1" not in _read(root, "uv.lock") and "version = 2" not in _read(root, "uv.lock"):
        raise SecurityError("uv.lock format/version not recognized")
    for path, markers in {
        "SECURITY.md": ("private", "workflow_dispatch", "not", "publisher"),
        "docs/M01_T06_SECURITY_AND_DEPENDENCIES.md": ("pnpm.cmd audit", "workflow_dispatch", "publication"),
        "docs/adr/ADR-0005-manual-security-and-dependency-governance.md": ("M01-T06", "Status:", "Dependabot"),
    }.items():
        content = _read(root, path)
        if any(marker.lower() not in content.lower() for marker in markers):
            raise SecurityError(f"Missing security documentation contract: {path}")
    if "ADR-0005-manual-security-and-dependency-governance.md" not in _read(root, "docs/adr/README.md"):
        raise SecurityError("ADR index has not recorded the security decision")
    if "M01-T06" not in _read(root, "CHANGELOG.md"):
        raise SecurityError("Changelog has no M01-T06 entry")
    reviewed = audit_paths(root, tracked_files if tracked_files is not None else _git_paths(root))
    return {
        "milestone": "M01-T06",
        "status": "offline_security_contract_validated",
        "m00": "done", "m01": "in_progress",
        "manual_workflows_only": True,
        "verify_token_read_only": True,
        "pages_deployment_verified": False,
        "dependabot_config_committed": False,
        "github_secret_scanning_verified": False,
        "external_dependency_audit_verified": False,
        "checked_git_visible_text_files": reviewed,
        "limited_credential_pattern_review_passed": True,
        "automatic_deployment_enabled": False,
        "publication_approved": False,
        "publisher_join_approved": False,
        "admin_review_pending": True,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), indent=2))
        return 0
    except (SecurityError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"milestone": "M01-T06", "status": "invalid", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
