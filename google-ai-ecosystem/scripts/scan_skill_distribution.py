#!/usr/bin/env python3
"""Scan the source distribution for machine paths and secret-shaped material."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import zipfile

from google_ai_common import iter_skill_distribution_files


SKILL_ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "windows_user_home": re.compile(
        r"(?i)\b[A-Z]:\\(?:Users|Documents and Settings)\\[^\\/\s`\"'<>|]+"
    ),
    "windows_machine_path": re.compile(r"(?i)\b[A-Z]:\\[^\r\n`\"'<>|]+"),
    "posix_user_home": re.compile(r"(?i)(?:/home|/Users)/[^/\s`\"'<>|]+"),
    "file_uri": re.compile(r"(?i)file:///(?:[A-Z]:/|home/|Users/)[^\s`\"'<>|]+"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
}
GENERIC_WINDOWS_PREFIXES = (
    "c:\\program files\\",
    "c:\\program files (x86)\\",
    "c:\\refs\\",
)
ALLOWED_RULE_FIXTURES = {
    "scripts/scan_skill_distribution.py": {"windows_machine_path"},
    "tests/test_distribution_scanner.py": {
        "windows_user_home",
        "windows_machine_path",
        "private_key",
    },
}


def is_allowed_machine_path(match: str) -> bool:
    normalized = match.lower()
    return normalized.startswith(GENERIC_WINDOWS_PREFIXES)


def scan_text(relative_path: str, text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for rule, pattern in RULES.items():
        for match in pattern.finditer(text):
            if rule == "windows_machine_path" and is_allowed_machine_path(match.group(0)):
                continue
            findings.append({
                "path": relative_path,
                "rule": rule,
                "line": text.count("\n", 0, match.start()) + 1,
            })
    return findings


def decode_text(data: bytes) -> str | None:
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_skill(skill_root: Path) -> dict[str, object]:
    root = skill_root.resolve()
    findings: list[dict[str, object]] = []
    files = iter_skill_distribution_files(root)
    for path in files:
        text = decode_text(path.read_bytes())
        if text is not None:
            relative = path.relative_to(root).as_posix()
            allowed = ALLOWED_RULE_FIXTURES.get(relative, set())
            findings.extend(
                finding for finding in scan_text(relative, text)
                if finding["rule"] not in allowed
            )
    return {"schema_version": 1, "source": "skill", "files_scanned": len(files), "findings": findings}


def scan_archive(archive_path: Path) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    files_scanned = 0
    with zipfile.ZipFile(archive_path) as archive:
        for name in sorted(archive.namelist()):
            if name.endswith("/"):
                continue
            files_scanned += 1
            findings.extend(scan_text("<archive-member>", name))
            text = decode_text(archive.read(name))
            if text is not None:
                logical = name.removeprefix("google-ai-ecosystem/")
                allowed = ALLOWED_RULE_FIXTURES.get(logical, set())
                findings.extend(
                    finding for finding in scan_text(name, text)
                    if finding["rule"] not in allowed
                )
    return {"schema_version": 1, "source": "archive", "files_scanned": files_scanned, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    source.add_argument("--archive", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = scan_archive(args.archive) if args.archive else scan_skill(args.skill_root)
    report["status"] = "pass" if not report["findings"] else "fail"
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status'].upper()} files={report['files_scanned']} findings={len(report['findings'])}")
    return 0 if not report["findings"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
