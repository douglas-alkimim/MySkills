#!/usr/bin/env python3
"""Build a deterministic, source-only archive of google-ai-ecosystem."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

from google_ai_common import distribution_fingerprint, iter_skill_distribution_files


SKILL_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PREFIX = "google-ai-ecosystem"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_archive(skill_root: Path, output: Path) -> dict[str, object]:
    root = skill_root.resolve()
    files = iter_skill_distribution_files(root)
    if not files:
        raise ValueError("source distribution is empty")

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)

    members: list[str] = []
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for source in files:
                relative = source.relative_to(root).as_posix()
                member = f"{ARCHIVE_PREFIX}/{relative}"
                info = zipfile.ZipInfo(member, ZIP_TIMESTAMP)
                info.create_system = 3
                mode = 0o755 if relative.startswith("scripts/") and source.suffix == ".py" else 0o644
                info.external_attr = mode << 16
                archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                members.append(member)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    return {
        "schema_version": 1,
        "archive": output.name,
        "archive_sha256": sha256_file(output),
        "source_fingerprint": distribution_fingerprint(root, files),
        "file_count": len(files),
        "members": members,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    manifest = build_archive(args.skill_root, args.output)
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
