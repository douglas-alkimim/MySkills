#!/usr/bin/env python3
"""Run one bounded Antigravity CLI delegation and validate its JSON envelope."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


SUCCESS_STATUS = "SUCCESS"
MAX_ARGV_PROMPT_CHARS = 12_000


class DelegateTimeoutError(TimeoutError):
    pass


def resolve_agy(explicit: Optional[str] = None) -> str:
    """Resolve agy from an explicit value, AGY_BIN, PATH, or official defaults."""
    requested = explicit or os.environ.get("AGY_BIN")
    if requested:
        requested_path = Path(requested).expanduser()
        if requested_path.is_file():
            return str(requested_path.resolve())
        resolved = shutil.which(requested)
        if resolved:
            return resolved
        raise FileNotFoundError(f"Antigravity CLI not found at or as: {requested}")

    for command_name in ("agy", "agy.exe"):
        resolved = shutil.which(command_name)
        if resolved:
            return resolved

    home = Path.home()
    candidates = [
        home / ".local" / "bin" / "agy",
        home / "AppData" / "Local" / "agy" / "bin" / "agy.exe",
    ]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "agy" / "bin" / "agy.exe")

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())

    raise FileNotFoundError(
        "Antigravity CLI (agy) was not found in PATH, AGY_BIN, or its official "
        "default locations. Verify installation with the official Google docs."
    )


def read_prompt(prompt: Optional[str], prompt_file: Optional[str]) -> str:
    if prompt is not None:
        value = prompt
    elif prompt_file == "-":
        value = sys.stdin.read()
    elif prompt_file:
        value = Path(prompt_file).expanduser().read_text(encoding="utf-8")
    else:
        raise ValueError("Provide --prompt or --prompt-file.")

    if not value.strip():
        raise ValueError("The delegation prompt is empty.")
    return value


def validate_argv_prompt(prompt: str) -> None:
    if len(prompt) > MAX_ARGV_PROMPT_CHARS:
        raise ValueError(
            f"Prompt exceeds the {MAX_ARGV_PROMPT_CHARS}-character argv transport limit. "
            "Split the task or use a CLI transport only after `agy --help` proves support."
        )
    sensitive_patterns = (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"(?i)\b(api[_-]?key|password|passwd|access[_-]?token|refresh[_-]?token|authorization)\s*[:=]\s*\S+",
    )
    if any(re.search(pattern, prompt) for pattern in sensitive_patterns):
        raise ValueError(
            "Prompt appears to contain a credential and cannot be placed in process argv. "
            "Remove the secret; no safer Antigravity prompt transport was verified."
        )


def probe_prompt_transport(agy_bin: str) -> Dict[str, Any]:
    """Inspect local CLI help without sending a prompt; do not infer undocumented flags."""
    try:
        completed = subprocess.run(
            [agy_bin, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"probed": False, "transport": "argv", "reason": "help unavailable"}
    help_text = f"{completed.stdout}\n{completed.stderr}"
    documented = [flag for flag in ("--prompt-file", "--prompt-stdin") if flag in help_text]
    return {
        "probed": completed.returncode == 0,
        "transport": "argv",
        "documented_alternatives": documented,
        "reason": "wrapper keeps argv until an alternative is integration-tested",
    }


def build_command(
    agy_bin: str,
    prompt: str,
    *,
    mode: Optional[str] = None,
    model: Optional[str] = None,
    effort: Optional[str] = None,
    agent: Optional[str] = None,
    conversation: Optional[str] = None,
    continue_latest: bool = False,
    print_timeout: str = "15m",
    json_schema: Optional[str] = None,
    disable_slash_commands: bool = False,
    add_dirs: Optional[Sequence[str]] = None,
    sandbox: bool = False,
) -> List[str]:
    command = [
        agy_bin,
        "-p",
        prompt,
        "--output-format",
        "json",
        "--print-timeout",
        print_timeout,
    ]

    optional_pairs = (
        ("--mode", mode),
        ("--model", model),
        ("--effort", effort),
        ("--agent", agent),
        ("--conversation", conversation),
        ("--json-schema", json_schema),
    )
    for flag, value in optional_pairs:
        if value:
            command.extend((flag, value))

    if continue_latest:
        command.append("--continue")
    if disable_slash_commands:
        command.append("--disable-slash-commands")
    if sandbox:
        command.append("--sandbox")
    for directory in add_dirs or ():
        command.extend(("--add-dir", directory))

    return command


def parse_envelope(stdout: str) -> Dict[str, Any]:
    """Parse a JSON object, tolerating benign preamble lines before the final object."""
    raw = stdout.strip()
    if not raw:
        raise ValueError("Antigravity produced no JSON output.")

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    objects: List[Dict[str, Any]] = []
    for candidate in [line.strip() for line in raw.splitlines() if line.strip()]:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
    if len(objects) == 1:
        return objects[0]
    if len(objects) > 1:
        raise ValueError("Antigravity stdout contained multiple JSON objects; terminal output is ambiguous.")
    raise ValueError("Antigravity stdout did not contain exactly one parseable JSON object.")


def validate_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    status = envelope.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("Antigravity envelope requires a non-empty string status.")
    response = envelope.get("response")
    if not isinstance(response, str):
        raise ValueError("Antigravity envelope requires a string response.")
    conversation_id = envelope.get("conversation_id")
    if status == SUCCESS_STATUS and (not isinstance(conversation_id, str) or not conversation_id):
        raise ValueError("A SUCCESS envelope requires a non-empty string conversation_id.")
    if "error" in envelope and envelope["error"] is not None and not isinstance(envelope["error"], str):
        raise ValueError("Antigravity envelope error must be a string or null.")
    return envelope


def run_delegate(
    command: Sequence[str],
    cwd: Path,
    *,
    wrapper_timeout_seconds: float = 20 * 60,
    terminate_grace_seconds: float = 5,
) -> Tuple[Dict[str, Any], int, str]:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        list(command),
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = process.communicate(timeout=wrapper_timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        terminate_process_tree(process, force=False)
        try:
            process.communicate(timeout=terminate_grace_seconds)
        except subprocess.TimeoutExpired:
            terminate_process_tree(process, force=True)
            process.communicate()
        raise DelegateTimeoutError(
            f"Antigravity wrapper timeout after {wrapper_timeout_seconds:.1f}s; process tree was stopped"
        ) from exc
    envelope = validate_envelope(parse_envelope(stdout))
    return envelope, process.returncode, stderr


def terminate_process_tree(process: subprocess.Popen[str], *, force: bool) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        command = ["taskkill", "/PID", str(process.pid), "/T"]
        if force:
            command.append("/F")
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if process.poll() is None:
            (process.kill if force else process.terminate)()
    else:
        os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one Antigravity CLI prompt with JSON output and fail unless the "
            "terminal status is SUCCESS. This wrapper does not bypass permissions."
        )
    )
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="Prompt text. Prefer --prompt-file for long prompts.")
    prompt_group.add_argument(
        "--prompt-file",
        help="UTF-8 prompt file, or '-' to read the prompt from stdin.",
    )
    parser.add_argument("--cwd", default=".", help="Workspace directory for the CLI process.")
    parser.add_argument("--agy-bin", help="Explicit agy executable path or command name.")
    parser.add_argument("--mode", choices=("plan", "accept-edits", "auto"))
    parser.add_argument("--model", help="Model identifier from `agy models`.")
    parser.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"))
    parser.add_argument("--agent", help="Configured agent name from `agy agents`.")
    conversation_group = parser.add_mutually_exclusive_group()
    conversation_group.add_argument("--conversation", help="Explicit conversation ID to resume.")
    conversation_group.add_argument(
        "--continue",
        dest="continue_latest",
        action="store_true",
        help="Continue the workspace's most recent conversation.",
    )
    parser.add_argument(
        "--print-timeout",
        default="15m",
        help="Antigravity print timeout, such as 90s or 15m (default: 15m).",
    )
    parser.add_argument("--json-schema", help="Path to a JSON schema accepted by agy.")
    parser.add_argument("--disable-slash-commands", action="store_true")
    parser.add_argument("--add-dir", action="append", default=[], help="Additional authorized workspace directory.")
    parser.add_argument("--sandbox", action="store_true", help="Request the CLI terminal sandbox when supported.")
    parser.add_argument(
        "--response-only",
        action="store_true",
        help="Print only the response string instead of the validated JSON envelope.",
    )
    parser.add_argument(
        "--wrapper-timeout-seconds",
        type=float,
        default=20 * 60,
        help="Total wrapper process timeout, distinct from --print-timeout (default: 1200).",
    )
    parser.add_argument(
        "--terminate-grace-seconds",
        type=float,
        default=5,
        help="Grace period between terminate and forced process-tree kill.",
    )
    parser.add_argument(
        "--probe-transport",
        action="store_true",
        help="Print a local help-based prompt transport capability report and exit.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        workspace = Path(args.cwd).expanduser().resolve(strict=True)
        if not workspace.is_dir():
            raise NotADirectoryError(f"Workspace is not a directory: {workspace}")
        agy_bin = resolve_agy(args.agy_bin)
        if args.probe_transport:
            print(json.dumps(probe_prompt_transport(agy_bin), ensure_ascii=False, separators=(",", ":")))
            return 0
        prompt = read_prompt(args.prompt, args.prompt_file)
        validate_argv_prompt(prompt)
        schema = str(Path(args.json_schema).expanduser().resolve(strict=True)) if args.json_schema else None
        add_dirs = [str(Path(item).expanduser().resolve(strict=True)) for item in args.add_dir]
        command = build_command(
            agy_bin,
            prompt,
            mode=args.mode,
            model=args.model,
            effort=args.effort,
            agent=args.agent,
            conversation=args.conversation,
            continue_latest=args.continue_latest,
            print_timeout=args.print_timeout,
            json_schema=schema,
            disable_slash_commands=args.disable_slash_commands,
            add_dirs=add_dirs,
            sandbox=args.sandbox,
        )
        envelope, process_code, diagnostics = run_delegate(
            command,
            workspace,
            wrapper_timeout_seconds=args.wrapper_timeout_seconds,
            terminate_grace_seconds=args.terminate_grace_seconds,
        )
    except DelegateTimeoutError as exc:
        print(f"agy_delegate: WRAPPER_TIMEOUT: {exc}", file=sys.stderr)
        return 4
    except (FileNotFoundError, NotADirectoryError, OSError, ValueError) as exc:
        print(f"agy_delegate: {exc}", file=sys.stderr)
        return 2

    if diagnostics:
        print(f"agy_delegate: Antigravity emitted {len(diagnostics)} diagnostic characters on stderr.", file=sys.stderr)

    status = envelope["status"]
    if process_code != 0:
        print(f"agy_delegate: Antigravity exited with code {process_code}.", file=sys.stderr)
        return 4
    if status != SUCCESS_STATUS:
        print(f"agy_delegate: terminal status is {status!r}, not {SUCCESS_STATUS}.", file=sys.stderr)
        return 3

    if args.response_only:
        response = envelope["response"]
        print(response, end="" if response.endswith("\n") else "\n")
    else:
        print(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
