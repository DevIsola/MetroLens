#!/usr/bin/env python3
"""M01-T07 local static-export contract and loopback-only HTTP smoke checks.

No external network, build, deployment, or data publication is performed here.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sys
import threading
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent


class StaticExportError(ValueError):
    """Static application contract or exported artifact is invalid."""


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise StaticExportError(f"Missing or unreadable {rel}: {exc}") from exc


def check_contract(root: Path = ROOT) -> dict:
    config = _read(root, "frontend/next.config.ts")
    home = _read(root, "frontend/app/page.tsx")
    detail = _read(root, "frontend/app/methodology/page.tsx")
    workflow = _read(root, ".github/workflows/verify.yml")
    policy = json.loads(_read(root, "docs/architecture/static_pipeline_policy.json"))
    roadmap = json.loads(_read(root, "docs/roadmap-status.json"))
    if not re.search(r"output:\s*['\"]export['\"]", config) or "trailingSlash: true" not in config:
        raise StaticExportError("Static export with directory-like deep links is required")
    if "NEXT_PUBLIC_BASE_PATH" not in config or "images: { unoptimized: true }" not in config:
        raise StaticExportError("Build-time project subpath or static image policy missing")
    if 'href="/methodology"' not in home or "next/link" not in home:
        raise StaticExportError("Homepage does not link to the methodology route via Next Link")
    if 'href="/"' not in detail or "next/link" not in detail:
        raise StaticExportError("Methodology route lacks Next Link back to the homepage")
    if not all(word in detail.lower() for word in ("source", "publication", "comparability")):
        raise StaticExportError("Methodology route omits source-methodology disclosures")
    if (root / "frontend/app/api").exists() or (root / "frontend/public/data").exists():
        raise StaticExportError("API route or unapproved public data path present")
    ms = roadmap.get("milestones", [])
    if len(ms) != 12 or ms[0].get("status") != "done" or ms[1].get("status") != "in_progress":
        raise StaticExportError("M00/M01 milestone states inconsistent")
    execution = policy.get("execution", {})
    if (policy.get("implementation_active") is not False or
        policy.get("storage", {}).get("public_export", {}).get("publication_active") is not False or
        not policy.get("publication_gates") or
        any(value is not False for value in policy["publication_gates"].values()) or
        execution.get("github_actions_triggers") != ["workflow_dispatch"] or
        any(execution.get(key) is not False for key in ("automatic_deploy", "push_auto_ci", "scheduled_etl"))):
        raise StaticExportError("Publication or execution gates were relaxed")
    if not re.search(r"(?m)^on:\s*\n  workflow_dispatch:\s*$", workflow):
        raise StaticExportError("Verifier workflow lost its manual trigger")
    for marker in (
        "NEXT_PUBLIC_BASE_PATH: /UrbanGauge",
        "run: pnpm --dir frontend build",
        "run: python scripts/validate_m01_static_export.py --smoke --base-path /UrbanGauge",
    ):
        if marker not in workflow:
            raise StaticExportError(f"Manual verifier missing local project-path evidence: {marker}")
    if any(item in workflow for item in ("actions/deploy-pages", "actions/upload-pages-artifact", "pages: write", "id-token: write")):
        raise StaticExportError("Read-only verification workflow contains a deployment capability")
    return {
        "milestone": "M01-T07",
        "status": "static_export_contract_validated",
        "m00": "done",
        "m01": "in_progress",
        "expected_project_base_path": "/UrbanGauge",
        "deep_link_route": "/methodology/",
        "production_build_verified": False,
        "loopback_http_smoke_verified": False,
        "automatic_deployment_enabled": False,
        "publication_approved": False,
        "publisher_join_approved": False,
    }


class _References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        items = dict(attrs)
        if tag in ("a", "link") and items.get("href"):
            self.refs.append((tag, items["href"] or ""))
        if tag in ("script", "img") and items.get("src"):
            self.refs.append((tag, items["src"] or ""))


def _normalize_prefix(prefix: str) -> str:
    if prefix and not re.fullmatch(r"/[A-Za-z0-9-]+(?:/[A-Za-z0-9-]+)*", prefix):
        raise StaticExportError("Base path must be empty or a safe /segment path without trailing slash")
    return prefix


def smoke_export(root: Path = ROOT, *, prefix: str = "/UrbanGauge") -> dict:
    prefix = _normalize_prefix(prefix)
    export = (root / "frontend/out").resolve()
    if not (export / "index.html").is_file() or not (export / "methodology/index.html").is_file():
        raise StaticExportError("Build the static homepage and methodology deep link before --smoke")

    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(export), **kwargs)

        def log_message(self, fmt, *args):
            return  # Local smoke only; output is machine-readable JSON.

        def translate_path(self, path):
            raw = unquote(urlsplit(path).path)
            if prefix and not (raw == prefix or raw.startswith(prefix + "/")):
                return str(export / "__outside_base_path__")
            relative = raw[len(prefix):] if prefix else raw
            segments = [part for part in relative.split("/") if part]
            if any(part in (".", "..") or "\\" in part or "\0" in part for part in segments):
                return str(export / "__invalid_path__")
            target = export.joinpath(*segments).resolve()
            if not target.is_relative_to(export):
                return str(export / "__invalid_path__")
            return str(target)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        port = server.server_address[1]
        origin = f"http://127.0.0.1:{port}"
        pages = [prefix + "/", prefix + "/methodology/"]
        found_assets: set[str] = set()
        for path in pages:
            try:
                with urlopen(origin + path, timeout=5) as response:
                    html = response.read().decode("utf-8")
                    if response.status != 200 or "<html" not in html.lower():
                        raise StaticExportError(f"Invalid HTTP HTML response at {path}")
            except (OSError, UnicodeError) as exc:
                raise StaticExportError(f"Cannot GET page at {path}: {exc}") from exc
            refs = _References()
            refs.feed(html)
            for tag, ref in refs.refs:
                url = urlsplit(ref)
                if url.scheme or url.netloc or ref.startswith("#") or not url.path.startswith("/"):
                    continue
                if prefix and not (url.path == prefix or url.path.startswith(prefix + "/")):
                    raise StaticExportError(f"Unprefixed absolute URL in {path}: {ref}")
                if tag in ("link", "script") and "/_next/" in url.path:
                    found_assets.add(url.path)
            if path == pages[0] and prefix + "/methodology/" not in [urlsplit(r).path for t, r in refs.refs if t == "a"]:
                raise StaticExportError("Homepage lacks a prefixed clickable methodology link")
            if path == pages[1] and prefix + "/" not in [urlsplit(r).path for t, r in refs.refs if t == "a"]:
                raise StaticExportError("Deep link lacks a prefixed link back to the homepage")
        if not found_assets:
            raise StaticExportError("Next.js static HTML lacks local prefixed assets")
        checked = 0
        for asset in sorted(found_assets)[:4]:
            try:
                with urlopen(origin + asset, timeout=5) as response:
                    if response.status != 200 or not response.read(1):
                        raise StaticExportError(f"Missing static asset {asset}")
                    checked += 1
            except (OSError, UnicodeError) as exc:
                raise StaticExportError(f"Cannot GET static asset {asset}: {exc}") from exc
        return {
            "milestone": "M01-T07",
            "status": "loopback_static_export_smoke_passed",
            "base_path": prefix,
            "checked_pages": pages,
            "checked_static_assets": checked,
            "http_bind": "127.0.0.1",
            "external_network_used": False,
            "automatic_deployment_enabled": False,
            "publication_approved": False,
        }
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="Serve existing static export on an ephemeral loopback port and GET pages/assets")
    parser.add_argument("--base-path", default="/UrbanGauge", help="Build-time prefix: /UrbanGauge or an empty string")
    args = parser.parse_args()
    try:
        report = check_contract()
        if args.smoke:
            report = smoke_export(prefix=args.base_path)
        print(json.dumps(report, indent=2))
        return 0
    except (StaticExportError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"milestone": "M01-T07", "status": "invalid", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
