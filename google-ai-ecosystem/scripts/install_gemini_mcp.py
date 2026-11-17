#!/usr/bin/env python3
"""Install the bundled Gemini Web MCP into a versioned managed runtime."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Optional, Sequence

from google_ai_common import (
    CHROME_HELP_URL,
    default_output_dir,
    default_runtime_root,
    find_chrome,
    fingerprint_tree,
    resolve_command,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = SKILL_ROOT / "vendor" / "gemini-mcp"
RUNTIME_MARKER = ".google-ai-ecosystem-runtime.json"
RELEASE_EXCLUDED_NAMES = {
    ".git",
    ".mypy_cache",
    ".pnpm-store",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "browser_state",
    "chrome_profile",
    "chrome_profile_instances",
    "coverage",
    "dist",
    "node_modules",
}
RELEASE_EXCLUDED_SUFFIXES = {".db", ".pyc", ".pyo", ".sqlite", ".sqlite3", ".temp", ".tmp"}


class InstallError(RuntimeError):
    pass


def run_checked(command: Sequence[str], *, cwd: Optional[Path] = None) -> None:
    completed = subprocess.run(list(command), cwd=str(cwd) if cwd else None, check=False)
    if completed.returncode != 0:
        raise InstallError(f"command failed with exit code {completed.returncode}: {' '.join(command)}")


def ensure_chrome(*, apply: bool, skip_install: bool, install_consent: bool = False) -> tuple[Optional[Path], str]:
    existing = find_chrome()
    if existing:
        return existing, "already-installed"
    if skip_install:
        return None, "missing-install-skipped"
    if platform.system() != "Windows":
        if apply:
            raise InstallError(
                f"Google Chrome is required. Install it from {CHROME_HELP_URL} and rerun the installer."
            )
        return None, "missing-manual-install-required"

    winget = resolve_command("winget") or resolve_command("winget.exe")
    if not winget:
        if apply:
            raise InstallError(
                f"Google Chrome is missing and winget is unavailable. Install Chrome from {CHROME_HELP_URL}."
            )
        return None, "missing-winget-required"

    if not apply:
        return None, "missing-requires-explicit-install-chrome-consent"
    if not install_consent:
        raise InstallError(
            "Google Chrome is missing. Re-run with --install-chrome only after the user explicitly consents."
        )

    run_checked(
        (
            winget,
            "install",
            "--id",
            "Google.Chrome",
            "--exact",
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--disable-interactivity",
        )
    )
    installed = find_chrome()
    if not installed:
        raise InstallError(
            "winget reported completion but a supported Google Chrome executable was not found"
        )
    return installed, "installed-with-winget"


def validate_vendor() -> None:
    required = (
        VENDOR_DIR / "package.json",
        VENDOR_DIR / "pnpm-lock.yaml",
        VENDOR_DIR / "tsconfig.json",
        VENDOR_DIR / "src" / "index.ts",
        VENDOR_DIR / "LICENSE",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise InstallError("bundled Gemini MCP is incomplete: " + ", ".join(missing))


def release_plan(runtime_root: Path) -> tuple[str, Path]:
    fingerprint = fingerprint_tree(VENDOR_DIR, excluded_names=RELEASE_EXCLUDED_NAMES)
    return fingerprint, runtime_root / "releases" / fingerprint[:16]


def release_copy_ignore(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in RELEASE_EXCLUDED_NAMES
        or Path(name).suffix.lower() in RELEASE_EXCLUDED_SUFFIXES
    }


def copy_release(release_dir: Path, fingerprint: str) -> bool:
    if release_dir.exists():
        marker = release_dir / RUNTIME_MARKER
        if not marker.is_file():
            raise InstallError(
                f"release directory exists without the managed-runtime marker: {release_dir}"
            )
        return False

    release_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        VENDOR_DIR,
        release_dir,
        ignore=release_copy_ignore,
    )
    marker_data = {
        "managed_by": "google-ai-ecosystem",
        "vendor_fingerprint": fingerprint,
        "source": str(VENDOR_DIR),
    }
    (release_dir / RUNTIME_MARKER).write_text(
        json.dumps(marker_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return True


def build_release(release_dir: Path, pnpm: str) -> None:
    run_checked((pnpm, "install", "--frozen-lockfile"), cwd=release_dir)
    run_checked((pnpm, "build"), cwd=release_dir)
    if not (release_dir / "dist" / "index.js").is_file():
        raise InstallError("MCP build completed without dist/index.js")
    run_checked((pnpm, "test"), cwd=release_dir)
    run_checked((pnpm, "run", "smoke"), cwd=release_dir)
    run_checked((pnpm, "run", "package:check"), cwd=release_dir)
    run_checked((pnpm, "run", "provenance:check"), cwd=release_dir)


def codex_server_exists(codex: str, server_name: str, *, cwd: Path) -> bool:
    completed = subprocess.run(
        (codex, "mcp", "get", server_name),
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def get_codex_registration(codex: str, server_name: str, *, cwd: Path) -> Optional[dict[str, Any]]:
    completed = subprocess.run(
        (codex, "mcp", "get", server_name, "--json"),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise InstallError("Codex returned invalid JSON for the existing MCP registration") from exc
    if not isinstance(value, dict):
        raise InstallError("Codex returned an invalid MCP registration object")
    return value


def codex_config_path() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return (Path(configured).expanduser() if configured else Path.home() / ".codex") / "config.toml"


def project_codex_config_path(project_root: Path) -> Path:
    return project_root / ".codex" / "config.toml"


def restore_file_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def candidate_registration_command(
    codex: str,
    server_name: str,
    release_dir: Path,
    output_dir: Path,
) -> list[str]:
    environment = {
        "HEADLESS": "true",
        "CONVERSATION_URL": "https://gemini.google.com/app",
        "GEMINI_OUTPUT_DIR": str(output_dir),
        "MEDIA_GENERATION_TIMEOUT_MS": "720000",
        "RESEARCH_TIMEOUT_MS": "900000",
    }
    command = [codex, "mcp", "add", server_name]
    for key, value in environment.items():
        command.extend(("--env", f"{key}={value}"))
    command.extend(("--", resolve_command("node") or "node", str(release_dir / "dist" / "index.js")))
    return command


def render_project_registration(server_name: str, release_dir: Path, output_dir: Path) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", server_name):
        raise InstallError("server name must contain only letters, digits, underscore, or hyphen")

    def quoted(value: object) -> str:
        return json.dumps(str(value), ensure_ascii=False)

    node = resolve_command("node") or "node"
    entrypoint = release_dir / "dist" / "index.js"
    environment = {
        "HEADLESS": "true",
        "CONVERSATION_URL": "https://gemini.google.com/app",
        "GEMINI_OUTPUT_DIR": str(output_dir),
        "MEDIA_GENERATION_TIMEOUT_MS": "720000",
        "RESEARCH_TIMEOUT_MS": "900000",
    }
    lines = [
        f"[mcp_servers.{server_name}]",
        f"command = {quoted(node)}",
        f"args = [{quoted(entrypoint)}]",
        f"cwd = {quoted(release_dir)}",
        "enabled = true",
        "startup_timeout_sec = 120",
        "tool_timeout_sec = 1200",
        'default_tools_approval_mode = "prompt"',
        "",
        f"[mcp_servers.{server_name}.env]",
    ]
    lines.extend(f"{key} = {quoted(value)}" for key, value in environment.items())
    return "\n".join(lines) + "\n"


def replace_project_registration(content: str, server_name: str, block: str) -> str:
    prefix = f"mcp_servers.{server_name}"
    retained: list[str] = []
    skip = False
    for line in content.splitlines(keepends=True):
        header = re.match(r"^\s*\[([^\]]+)\]\s*(?:#.*)?(?:\r?\n)?$", line)
        if header:
            section = header.group(1).strip()
            skip = section == prefix or section.startswith(f"{prefix}.")
        if not skip:
            retained.append(line)
    result = "".join(retained).rstrip()
    return f"{result}\n\n{block}" if result else block


def register_codex(
    *,
    codex: str,
    server_name: str,
    release_dir: Path,
    output_dir: Path,
    project_root: Path,
    replace: bool,
    scope: str = "user",
) -> None:
    verification_cwd = project_root if scope == "project" else Path.home()
    existing = get_codex_registration(codex, server_name, cwd=verification_cwd)
    if existing is not None and not replace:
        raise InstallError(
            f"Codex MCP server {server_name!r} already exists. Use --replace-registration after reviewing it."
        )
    config_path = project_codex_config_path(project_root) if scope == "project" else codex_config_path()
    config_existed = config_path.is_file()
    config_snapshot = config_path.read_bytes() if config_existed else b""
    command = candidate_registration_command(codex, server_name, release_dir, output_dir)

    try:
        if scope == "project":
            current = config_snapshot.decode("utf-8") if config_existed else ""
            block = render_project_registration(server_name, release_dir, output_dir)
            restore_file_atomically(config_path, replace_project_registration(current, server_name, block).encode("utf-8"))
        else:
            if existing is not None:
                run_checked((codex, "mcp", "remove", server_name), cwd=verification_cwd)
            run_checked(command, cwd=verification_cwd)
        registered = get_codex_registration(codex, server_name, cwd=verification_cwd)
        transport = registered.get("transport", {}) if registered else {}
        expected_entrypoint = str(release_dir / "dist" / "index.js")
        if registered is None or transport.get("type") != "stdio" or expected_entrypoint not in transport.get("args", []):
            raise InstallError("candidate MCP registration did not verify after cutover")
    except Exception as exc:
        try:
            if config_existed:
                restore_file_atomically(config_path, config_snapshot)
            else:
                config_path.unlink(missing_ok=True)
        except OSError as restore_error:
            raise InstallError(
                "MCP registration failed and the prior Codex configuration could not be restored"
            ) from restore_error
        if isinstance(exc, InstallError):
            raise
        raise InstallError("MCP registration failed; the prior Codex configuration was restored") from exc


def host_snippet(host: str, server_name: str, dist_path: Path, output_dir: Path) -> dict[str, Any]:
    server = {
        "command": resolve_command("node") or "node",
        "args": [str(dist_path)],
        "env": {
            "HEADLESS": "true",
            "CONVERSATION_URL": "https://gemini.google.com/app",
            "GEMINI_OUTPUT_DIR": str(output_dir),
            "MEDIA_GENERATION_TIMEOUT_MS": "720000",
            "RESEARCH_TIMEOUT_MS": "900000",
        },
    }
    return {"host": host, "mcpServers": {server_name: server}}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("codex", "claude", "cursor", "none"), default="codex")
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-dir", type=Path, help="Managed runtime root override.")
    parser.add_argument("--output-dir", type=Path, help="Generated media output directory.")
    parser.add_argument("--server-name", default="gemini")
    parser.add_argument("--register", action="store_true", help="Register the built server with the selected host.")
    parser.add_argument("--replace-registration", action="store_true")
    parser.add_argument("--skip-chrome-install", action="store_true")
    parser.add_argument(
        "--install-chrome",
        action="store_true",
        help="Explicit consent to install Google Chrome with winget when it is absent.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Perform installation and optional registration.")
    mode.add_argument("--dry-run", action="store_true", help="Print the plan without changing the host (default).")
    parser.add_argument("--json", action="store_true")
    return parser


def install(args: argparse.Namespace) -> dict[str, Any]:
    validate_vendor()
    project_root = args.project_root.expanduser().resolve()
    if not project_root.is_dir():
        raise InstallError(f"project root is not a directory: {project_root}")
    runtime_root = (
        args.runtime_dir.expanduser().resolve()
        if args.runtime_dir
        else default_runtime_root(args.scope, project_root).resolve()
    )
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else default_output_dir(args.scope, project_root).resolve()
    )
    fingerprint, release_dir = release_plan(runtime_root)
    apply = bool(args.apply)

    chrome, chrome_action = ensure_chrome(
        apply=apply,
        skip_install=args.skip_chrome_install,
        install_consent=bool(getattr(args, "install_chrome", False)),
    )
    node = resolve_command("node") or resolve_command("node.exe")
    pnpm = resolve_command("pnpm") or resolve_command("pnpm.cmd")
    if not node:
        raise InstallError("Node.js is required but was not found")
    if not pnpm:
        raise InstallError("pnpm is required but was not found")

    result: dict[str, Any] = {
        "mode": "apply" if apply else "dry-run",
        "host": args.host,
        "scope": args.scope,
        "project_root": str(project_root),
        "runtime_root": str(runtime_root),
        "release_dir": str(release_dir),
        "vendor_fingerprint": fingerprint,
        "output_dir": str(output_dir),
        "node": node,
        "pnpm": pnpm,
        "chrome": str(chrome) if chrome else None,
        "chrome_action": chrome_action,
        "register": bool(args.register),
    }

    if not apply:
        result["host_config"] = host_snippet(
            args.host, args.server_name, release_dir / "dist" / "index.js", output_dir
        )
        return result

    if not chrome:
        raise InstallError(
            f"Google Chrome is required for the Gemini MCP. Install it from {CHROME_HELP_URL}."
        )

    created = copy_release(release_dir, fingerprint)
    output_dir.mkdir(parents=True, exist_ok=True)
    build_release(release_dir, pnpm)
    result["release_created"] = created
    result["built"] = True

    if args.register:
        if args.host != "codex":
            raise InstallError(
                f"automatic registration is currently implemented only for Codex; use the emitted {args.host} config snippet"
            )
        codex = resolve_command("codex") or resolve_command("codex.exe")
        if not codex:
            raise InstallError("Codex CLI was not found for --register")
        register_codex(
            codex=codex,
            server_name=args.server_name,
            release_dir=release_dir,
            output_dir=output_dir,
            project_root=project_root,
            replace=args.replace_registration,
            scope=args.scope,
        )
        result["registered"] = True
    else:
        result["registered"] = False
        result["host_config"] = host_snippet(
            args.host, args.server_name, release_dir / "dist" / "index.js", output_dir
        )
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = install(args)
    except (InstallError, OSError, ValueError) as exc:
        print(f"install_gemini_mcp: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"mode: {result['mode']}")
        print(f"Chrome: {result['chrome'] or result['chrome_action']}")
        print(f"runtime: {result['release_dir']}")
        print(f"output: {result['output_dir']}")
        if result.get("built"):
            print("MCP build: ok")
        if result.get("registered"):
            print(f"Codex MCP registration: {args.server_name}")
        elif result.get("host_config"):
            print("host configuration:")
            print(json.dumps(result["host_config"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
