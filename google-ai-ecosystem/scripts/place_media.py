#!/usr/bin/env python3
"""Atomically place Gemini staging media inside one authorized repository root."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Optional


class PlacementError(RuntimeError):
    pass


@dataclass(frozen=True)
class DetectedMedia:
    kind: str
    extension: str
    mime_type: str


@dataclass(frozen=True)
class PlacementResult:
    repository: str
    relative_path: str
    bytes: int
    sha256: str
    media_kind: str
    mime_type: str
    staging_preserved: bool


IMAGE_CONVENTIONS = (
    "assets/media/images",
    "assets/images",
    "public/images",
    "static/images",
    "docs/images",
    "images",
)
VIDEO_CONVENTIONS = (
    "assets/media/videos",
    "assets/videos",
    "public/videos",
    "static/videos",
    "videos",
)
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_media(path: Path) -> DetectedMedia:
    with path.open("rb") as handle:
        header = handle.read(32)
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return DetectedMedia("image", ".png", "image/png")
    if header.startswith(b"\xff\xd8\xff"):
        return DetectedMedia("image", ".jpg", "image/jpeg")
    if header[:6] in (b"GIF87a", b"GIF89a"):
        return DetectedMedia("image", ".gif", "image/gif")
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return DetectedMedia("image", ".webp", "image/webp")
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand == b"qt  ":
            return DetectedMedia("video", ".mov", "video/quicktime")
        return DetectedMedia("video", ".mp4", "video/mp4")
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        return DetectedMedia("video", ".webm", "video/webm")
    raise PlacementError("unsupported or invalid media signature")


def sanitize_filename(value: str, extension: str) -> str:
    stem = Path(value).stem
    stem = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "-", stem)
    stem = re.sub(r"\s+", "-", stem).strip(" .-")
    if not stem:
        stem = "gemini-media"
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        stem = f"media-{stem.lower()}"
    return f"{stem[:120]}{extension}"


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_directory(root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve(strict=False)
    if not _contained(root, resolved):
        raise PlacementError("destination escapes the authorized repository root")
    try:
        relative = candidate.absolute().relative_to(root)
    except ValueError as exc:
        raise PlacementError("destination escapes the authorized repository root") from exc
    current = root
    is_junction = getattr(os.path, "isjunction", lambda _path: False)
    for part in relative.parts:
        current = current / part
        if current.exists() and (current.is_symlink() or is_junction(current)):
            raise PlacementError("destination resolves through an unsafe symlink or junction")
    return resolved


def _default_directory(root: Path, kind: str) -> Path:
    conventions = IMAGE_CONVENTIONS if kind == "image" else VIDEO_CONVENTIONS
    for relative in conventions:
        candidate = root / relative
        if candidate.is_dir():
            return _resolve_directory(root, candidate)
    plural = "images" if kind == "image" else "videos"
    return _resolve_directory(root, root / "artifacts" / "media" / plural)


def _choose_target(
    root: Path,
    source: Path,
    detected: DetectedMedia,
    destination: Optional[Path],
) -> Path:
    if destination is None:
        directory = _default_directory(root, detected.kind)
        return directory / sanitize_filename(source.name, detected.extension)

    raw = destination if destination.is_absolute() else root / destination
    suffix = raw.suffix.lower()
    if suffix:
        allowed_suffixes = {detected.extension}
        if detected.extension == ".jpg":
            allowed_suffixes.add(".jpeg")
        if suffix not in allowed_suffixes:
            raise PlacementError("destination extension does not match detected media type")
        directory = _resolve_directory(root, raw.parent)
        return directory / sanitize_filename(raw.name, detected.extension)
    directory = _resolve_directory(root, raw)
    return directory / sanitize_filename(source.name, detected.extension)


def _available_path(candidate: Path, start: int = 1) -> Path:
    if start == 1 and not candidate.exists() and not candidate.is_symlink():
        return candidate
    for index in range(max(2, start), 10_000):
        option = candidate.with_name(f"{candidate.stem}-{index}{candidate.suffix}")
        if not option.exists() and not option.is_symlink():
            return option
    raise PlacementError("unable to allocate a collision-free media filename")


def _publish_atomic_no_replace(temporary: Path, final: Path) -> None:
    """Publish atomically without replacing an existing path."""
    if os.name == "nt":
        # MoveFile on Windows is atomic within a volume and fails if final exists.
        os.rename(temporary, final)
        return
    # POSIX rename replaces an existing path, so use an atomic hardlink instead.
    os.link(temporary, final)
    temporary.unlink()


def place_media(
    source: Path,
    repository_root: Path,
    kind: str,
    destination: Optional[Path] = None,
) -> PlacementResult:
    normalized_kind = kind.lower().rstrip("s")
    if normalized_kind not in {"image", "video"}:
        raise PlacementError("kind must be image or video")

    root = repository_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise PlacementError("authorized repository root is not a directory")
    if not os.access(root, os.W_OK):
        raise PlacementError("authorized repository root is not writable")

    staging = source.expanduser().resolve(strict=True)
    if not staging.is_file() or staging.stat().st_size <= 0:
        raise PlacementError("staging media is missing or empty")
    detected = detect_media(staging)
    if detected.kind != normalized_kind:
        raise PlacementError("detected media kind does not match the requested kind")

    candidate = _choose_target(root, staging, detected, destination)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    directory = _resolve_directory(root, candidate.parent)
    if not directory.is_dir() or not os.access(directory, os.W_OK):
        raise PlacementError("destination directory is not writable")
    candidate = directory / candidate.name
    if candidate.is_symlink() or not _contained(root, candidate.resolve(strict=False)):
        raise PlacementError("destination resolves through an unsafe symlink")

    source_hash = sha256_file(staging)
    source_size = staging.stat().st_size
    with tempfile.NamedTemporaryFile(
        dir=directory, prefix=".gemini-media-", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
    final: Path | None = None
    try:
        with staging.open("rb") as source_handle, temporary.open("wb") as target_handle:
            shutil.copyfileobj(source_handle, target_handle, length=1024 * 1024)
            target_handle.flush()
            os.fsync(target_handle.fileno())
        if temporary.stat().st_size != source_size or sha256_file(temporary) != source_hash:
            raise PlacementError("atomic copy verification failed")
        temporary_detected = detect_media(temporary)
        if temporary_detected != detected:
            raise PlacementError("copied media type changed during placement")

        attempt = 1
        while True:
            final = _available_path(candidate, attempt)
            try:
                _publish_atomic_no_replace(temporary, final)
                break
            except FileExistsError:
                attempt += 1
            except OSError as exc:
                raise PlacementError("filesystem cannot publish the verified copy atomically") from exc
        temporary.unlink(missing_ok=True)
        if final.stat().st_size != source_size or sha256_file(final) != source_hash:
            final.unlink(missing_ok=True)
            raise PlacementError("published media failed final integrity verification")
    finally:
        temporary.unlink(missing_ok=True)

    assert final is not None
    return PlacementResult(
        repository="<PROJECT_ROOT>",
        relative_path=final.relative_to(root).as_posix(),
        bytes=source_size,
        sha256=source_hash,
        media_kind=detected.kind,
        mime_type=detected.mime_type,
        staging_preserved=staging.exists(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--kind", choices=("image", "video"), required=True)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    try:
        result = place_media(args.source, args.repository_root, args.kind, args.destination)
    except (OSError, PlacementError, ValueError) as exc:
        print(json.dumps({"success": False, "code": "MEDIA_PLACEMENT_FAILED", "error": str(exc)}))
        return 2
    print(json.dumps({"success": True, "data": asdict(result)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
