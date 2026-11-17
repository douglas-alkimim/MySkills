from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from place_media import PlacementError, place_media, sanitize_filename  # noqa: E402


PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-image"
MP4 = b"\x00\x00\x00\x18ftypisom" + b"synthetic-video"


class MediaPlacementTests(unittest.TestCase):
    def fixture(self, directory: str, name: str, content: bytes) -> Path:
        path = Path(directory) / name
        path.write_bytes(content)
        return path

    def test_explicit_destination_is_relative_verified_and_preserves_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            staging = self.fixture(directory, "staging.png", PNG)
            result = place_media(staging, root, "image", Path("public/images/hello.png"))
            final = root / result.relative_path
            self.assertEqual(result.relative_path, "public/images/hello.png")
            self.assertEqual(final.read_bytes(), PNG)
            self.assertEqual(result.sha256, hashlib.sha256(PNG).hexdigest())
            self.assertTrue(staging.exists())

    def test_existing_convention_wins_and_collision_gets_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            convention = root / "assets" / "videos"
            convention.mkdir(parents=True)
            staging = self.fixture(directory, "clip.mp4", MP4)
            first = place_media(staging, root, "video")
            second = place_media(staging, root, "video")
            self.assertEqual(first.relative_path, "assets/videos/clip.mp4")
            self.assertEqual(second.relative_path, "assets/videos/clip-2.mp4")

    def test_neutral_repository_uses_artifacts_media_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            staging = self.fixture(directory, "image.png", PNG)
            result = place_media(staging, root, "image")
            self.assertEqual(result.relative_path, "artifacts/media/images/image.png")

    def test_traversal_and_type_mismatch_fail_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            staging = self.fixture(directory, "image.png", PNG)
            with self.assertRaises(PlacementError):
                place_media(staging, root, "image", Path("../outside.png"))
            with self.assertRaises(PlacementError):
                place_media(staging, root, "video")
            self.assertFalse((Path(directory) / "outside.png").exists())

    def test_symlink_escape_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            link = root / "linked"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except OSError:
                self.skipTest("directory symlinks are not available")
            staging = self.fixture(directory, "image.png", PNG)
            with self.assertRaises(PlacementError):
                place_media(staging, root, "image", Path("linked/result.png"))

    def test_link_component_guard_fails_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            linked = root / "linked"
            linked.mkdir(parents=True)
            staging = self.fixture(directory, "image.png", PNG)
            with mock.patch("place_media.os.path.isjunction", return_value=True, create=True):
                with self.assertRaises(PlacementError):
                    place_media(staging, root, "image", Path("linked/result.png"))
            self.assertFalse((linked / "result.png").exists())

    def test_empty_file_and_partial_publish_failure_leave_no_visible_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            empty = self.fixture(directory, "empty.png", b"")
            with self.assertRaises(PlacementError):
                place_media(empty, root, "image")
            staging = self.fixture(directory, "image.png", PNG)
            with mock.patch("place_media._publish_atomic_no_replace", side_effect=OSError("injected")):
                with self.assertRaises(PlacementError):
                    place_media(staging, root, "image")
            self.assertEqual(list(root.rglob("*.tmp")), [])
            self.assertEqual(list(root.rglob("*.png")), [])

    def test_filename_is_safe_for_windows_and_posix(self) -> None:
        self.assertEqual(sanitize_filename("CON.png", ".png"), "media-con.png")
        self.assertEqual(sanitize_filename("hello-world?.png", ".png"), "hello-world.png")


if __name__ == "__main__":
    unittest.main()
