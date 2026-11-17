#!/usr/bin/env python3
"""Shared, dependency-free helpers for the Google AI ecosystem skill."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import platform
import shutil
from typing import Iterable, Optional


CHROME_HELP_URL = "https://support.google.com/chrome/answer/95346"

SKILL_DISTRIBUTION_TOP_LEVEL_FILES = {"LICENSE", "SKILL.md"}
SKILL_DISTRIBUTION_TOP_LEVEL_DIRS = {"agents", "references", "scripts", "tests", "vendor"}
SKILL_DISTRIBUTION_EXCLUDED_DIRS = {
    ".auth",
    ".git",
    ".mypy_cache",
    ".pnpm-store",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "auth_state",
    "browser_state",
    "chrome_profile",
    "chrome_profile_instances",
    "coverage",
    "dist",
    "evidence",
    "logs",
    "node_modules",
    "session_state",
    "temp",
    "tmp",
}
SKILL_DISTRIBUTION_EXCLUDED_SUFFIXES = {
    ".db",
    ".key",
    ".log",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".sqlite",
    ".sqlite3",
    ".temp",
    ".tgz",
    ".tmp",
    ".zip",
}
VENDOR_TOP_LEVEL_FILES = {
    "LICENSE",
    "README.md",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "tsconfig.json",
    "VENDOR.json",
}
VENDOR_TOP_LEVEL_DIRS = {"docs", "scripts", "src", "tests"}


def resolve_command(name: str) -> Optional[str]:
    """Return an executable resolved through PATH without invoking it."""
    return shutil.which(name)


def chrome_candidates() -> list[Path]:
    """Return supported Google Chrome executable candidates for this platform."""
    system = platform.system()
    candidates: list[Path] = []

    if system == "Windows":
        for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(variable)
            if base:
                candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
        candidates.extend(
            Path(value)
            for value in (
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            )
        )
    elif system == "Darwin":
        candidates.extend(
            (
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path.home() / "Applications" / "Google Chrome.app" / "Contents" / "MacOS" / "Google Chrome",
            )
        )
    else:
        for command in ("google-chrome", "google-chrome-stable"):
            resolved = resolve_command(command)
            if resolved:
                candidates.append(Path(resolved))
        candidates.extend(
            (
                Path("/usr/bin/google-chrome"),
                Path("/usr/bin/google-chrome-stable"),
                Path("/opt/google/chrome/google-chrome"),
            )
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = os.path.normcase(str(candidate))
        if normalized not in seen:
            seen.add(normalized)
            unique.append(candidate)
    return unique


def find_chrome() -> Optional[Path]:
    """Find a supported Google Chrome executable, excluding Chromium derivatives."""
    for candidate in chrome_candidates():
        if candidate.is_file():
            return candidate.resolve()
    return None


def default_user_data_root() -> Path:
    """Return a platform-appropriate writable root for managed runtime data."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) if base else Path.home() / "AppData" / "Local"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def default_runtime_root(scope: str, project_root: Optional[Path]) -> Path:
    if scope == "project":
        if project_root is None:
            raise ValueError("--project-root is required for project scope")
        return project_root / ".google-ai-ecosystem" / "runtime" / "gemini-mcp"
    return default_user_data_root() / "google-ai-ecosystem" / "runtime" / "gemini-mcp"


def default_output_dir(scope: str, project_root: Optional[Path]) -> Path:
    if scope == "project":
        if project_root is None:
            raise ValueError("--project-root is required for project scope")
        return project_root / "gemini-output"
    return default_user_data_root() / "google-ai-ecosystem" / "output"


def fingerprint_tree(root: Path, *, excluded_names: Iterable[str] = ()) -> str:
    """Hash file names and contents deterministically for versioned releases."""
    excluded = set(excluded_names)
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if any(part in excluded for part in path.relative_to(root).parts):
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def iter_skill_distribution_files(skill_root: Path) -> list[Path]:
    """Return the source-only skill distribution using a conservative allowlist."""
    root = skill_root.resolve()
    result: list[Path] = []
    for candidate in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = candidate.relative_to(root)
        parts = relative.parts
        if not parts or any(part in SKILL_DISTRIBUTION_EXCLUDED_DIRS for part in parts):
            continue
        if candidate.name == ".env" or (
            candidate.name.startswith(".env.") and not candidate.name.endswith(".example")
        ):
            continue
        if candidate.suffix.lower() in SKILL_DISTRIBUTION_EXCLUDED_SUFFIXES:
            continue
        if len(parts) == 1:
            if parts[0] not in SKILL_DISTRIBUTION_TOP_LEVEL_FILES:
                continue
        elif parts[0] not in SKILL_DISTRIBUTION_TOP_LEVEL_DIRS:
            continue
        if parts[0] == "vendor":
            if len(parts) < 3 or parts[1] != "gemini-mcp":
                continue
            vendor_relative = parts[2:]
            if len(vendor_relative) == 1:
                if vendor_relative[0] not in VENDOR_TOP_LEVEL_FILES:
                    continue
            elif vendor_relative[0] not in VENDOR_TOP_LEVEL_DIRS:
                continue
        result.append(candidate)
    return result


def distribution_fingerprint(skill_root: Path, files: Optional[Iterable[Path]] = None) -> str:
    """Hash relative paths and bytes for a source distribution without machine paths."""
    root = skill_root.resolve()
    digest = hashlib.sha256()
    selected = list(files) if files is not None else iter_skill_distribution_files(root)
    for candidate in sorted(selected, key=lambda item: item.relative_to(root).as_posix()):
        relative = candidate.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        with candidate.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()
