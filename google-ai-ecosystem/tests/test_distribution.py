from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_skill_archive import build_archive  # noqa: E402
from google_ai_common import iter_skill_distribution_files  # noqa: E402


class SkillDistributionTests(unittest.TestCase):
    def test_allowlist_preserves_sources_and_excludes_local_artifacts(self) -> None:
        members = {
            path.relative_to(SKILL_ROOT).as_posix()
            for path in iter_skill_distribution_files(SKILL_ROOT)
        }
        self.assertIn("SKILL.md", members)
        self.assertIn("LICENSE", members)
        self.assertIn("vendor/gemini-mcp/LICENSE", members)
        self.assertIn("vendor/gemini-mcp/README.md", members)
        self.assertIn("vendor/gemini-mcp/VENDOR.json", members)
        self.assertIn("vendor/gemini-mcp/pnpm-lock.yaml", members)
        self.assertIn("vendor/gemini-mcp/src/index.ts", members)
        self.assertIn("vendor/gemini-mcp/tests/auth-lifecycle.test.ts", members)
        self.assertFalse(any("node_modules" in member for member in members))
        self.assertFalse(any("/dist/" in f"/{member}/" for member in members))
        self.assertFalse(any("__pycache__" in member for member in members))
        self.assertFalse(any(member.startswith("evidence/") for member in members))

    def test_allowlist_rejects_sensitive_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "references").mkdir()
            (root / "SKILL.md").write_text("skill", encoding="utf-8")
            (root / "LICENSE").write_text("license", encoding="utf-8")
            (root / "scripts" / "run.py").write_text("pass\n", encoding="utf-8")
            (root / "scripts" / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / "scripts" / ".env.local").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / "scripts" / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
            (root / "references" / "local.key").write_text("secret", encoding="utf-8")
            (root / "references" / "session.log").write_text("local", encoding="utf-8")

            members = {
                path.relative_to(root).as_posix()
                for path in iter_skill_distribution_files(root)
            }

            self.assertIn("scripts/run.py", members)
            self.assertIn("scripts/.env.example", members)
            self.assertNotIn("scripts/.env", members)
            self.assertNotIn("scripts/.env.local", members)
            self.assertNotIn("references/local.key", members)
            self.assertNotIn("references/session.log", members)

    def test_archive_is_deterministic_and_has_no_machine_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            manifest_one = build_archive(SKILL_ROOT, first)
            manifest_two = build_archive(SKILL_ROOT, second)
            self.assertEqual(manifest_one["archive_sha256"], manifest_two["archive_sha256"])
            self.assertEqual(manifest_one["source_fingerprint"], manifest_two["source_fingerprint"])
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertIn("google-ai-ecosystem/SKILL.md", names)
                self.assertFalse(any("node_modules" in name for name in names))
                self.assertFalse(any("/dist/" in name for name in names))
                self.assertNotIn(str(SKILL_ROOT), json.dumps(manifest_one))


if __name__ == "__main__":
    unittest.main()
