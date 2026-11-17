#!/usr/bin/env python3
"""Read-only environment verification for Google AI ecosystem components."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Optional, Sequence

from google_ai_common import find_chrome, resolve_command


SKILL_ROOT = Path(__file__).resolve().parents[1]
VENDORED_MCP = SKILL_ROOT / "vendor" / "gemini-mcp"


def command_version(command: Optional[str], args: Sequence[str]) -> Optional[str]:
    if not command:
        return None
    try:
        completed = subprocess.run(
            [command, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    first_line = completed.stdout.strip().splitlines()
    return first_line[0] if completed.returncode == 0 and first_line else None


def inspect(runtime_dir: Optional[Path] = None) -> dict[str, Any]:
    node = resolve_command("node")
    pnpm = resolve_command("pnpm") or resolve_command("pnpm.cmd")
    agy = resolve_command("agy") or resolve_command("agy.exe")
    codex = resolve_command("codex") or resolve_command("codex.exe")
    chrome = find_chrome()
    runtime = runtime_dir.resolve() if runtime_dir else None

    return {
        "skill_root": str(SKILL_ROOT),
        "python": {"path": sys.executable, "version": sys.version.split()[0]},
        "node": {"path": node, "version": command_version(node, ("--version",))},
        "pnpm": {"path": pnpm, "version": command_version(pnpm, ("--version",))},
        "antigravity": {"path": agy, "version": command_version(agy, ("--version",))},
        "chrome": {"path": str(chrome) if chrome else None, "installed": chrome is not None},
        "codex": {"path": codex, "version": command_version(codex, ("--version",))},
        "vendored_mcp": {
            "path": str(VENDORED_MCP),
            "present": (VENDORED_MCP / "package.json").is_file()
            and (VENDORED_MCP / "src" / "index.ts").is_file(),
        },
        "runtime": {
            "path": str(runtime) if runtime else None,
            "built": bool(runtime and (runtime / "dist" / "index.js").is_file()),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, help="Optional installed MCP runtime to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result = inspect(args.runtime_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for component in ("python", "node", "pnpm", "antigravity", "chrome", "codex"):
            data = result[component]
            state = data.get("path") or "not found"
            version = data.get("version")
            print(f"{component}: {state}{f' ({version})' if version else ''}")
        print(f"vendored_mcp: {'ok' if result['vendored_mcp']['present'] else 'missing'}")
        if result["runtime"]["path"]:
            print(f"runtime: {'built' if result['runtime']['built'] else 'not built'}")

    required_ok = result["node"]["path"] and result["pnpm"]["path"] and result["vendored_mcp"]["present"]
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
