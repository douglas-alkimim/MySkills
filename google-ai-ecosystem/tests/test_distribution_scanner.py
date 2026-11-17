from __future__ import annotations

from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from scan_skill_distribution import scan_text  # noqa: E402


class DistributionScannerTests(unittest.TestCase):
    def test_flags_user_home_without_copying_matched_value(self) -> None:
        findings = scan_text("report.md", r"artifact: C:\Users\example-user\repo\result.png")
        self.assertTrue(any(item["rule"] == "windows_user_home" for item in findings))
        self.assertTrue(all("match" not in item for item in findings))

    def test_allows_generic_program_and_fixture_paths(self) -> None:
        text = "\n".join(
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\refs\reference.png",
            ]
        )
        self.assertEqual(scan_text("fixture.py", text), [])

    def test_flags_private_key_marker(self) -> None:
        findings = scan_text("secret.txt", "-----BEGIN PRIVATE KEY-----")
        self.assertEqual(findings[0]["rule"], "private_key")


if __name__ == "__main__":
    unittest.main()
