from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_gemini_mcp as installer  # noqa: E402


class GeminiInstallerTests(unittest.TestCase):
    def test_new_registration_does_not_emit_legacy_auto_login(self) -> None:
        snippet = installer.host_snippet(
            "codex", "gemini", Path("release") / "dist" / "index.js", Path("output")
        )
        environment = snippet["mcpServers"]["gemini"]["env"]
        self.assertNotIn("AUTO_LOGIN_ENABLED", environment)
        rendered = installer.render_project_registration(
            "gemini", Path("release"), Path("output")
        )
        self.assertNotIn("AUTO_LOGIN_ENABLED", rendered)

    def test_release_ignore_excludes_generated_and_machine_state(self) -> None:
        ignored = installer.release_copy_ignore(
            "unused",
            ["src", "node_modules", "dist", "__pycache__", "state.sqlite3", "source.ts"],
        )
        self.assertEqual(
            ignored,
            {"node_modules", "dist", "__pycache__", "state.sqlite3"},
        )

    def test_provenance_verifier_ignores_only_the_managed_runtime_receipt(self) -> None:
        verifier = (
            installer.VENDOR_DIR / "scripts" / "verify-provenance.mjs"
        ).read_text(encoding="utf-8")
        self.assertIn(installer.RUNTIME_MARKER, verifier)
        self.assertIn("runtimeMetadataFiles", verifier)

    def test_existing_chrome_is_never_reinstalled(self) -> None:
        chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        with mock.patch.object(installer, "find_chrome", return_value=chrome), mock.patch.object(
            installer, "run_checked"
        ) as run_checked:
            found, action = installer.ensure_chrome(apply=True, skip_install=False)
        self.assertEqual(found, chrome)
        self.assertEqual(action, "already-installed")
        run_checked.assert_not_called()

    def test_missing_windows_chrome_is_planned_through_winget(self) -> None:
        with mock.patch.object(installer, "find_chrome", return_value=None), mock.patch.object(
            installer.platform, "system", return_value="Windows"
        ), mock.patch.object(installer, "resolve_command", return_value="winget.exe"):
            found, action = installer.ensure_chrome(apply=False, skip_install=False)
        self.assertIsNone(found)
        self.assertEqual(action, "missing-requires-explicit-install-chrome-consent")

    def test_missing_windows_chrome_uses_exact_silent_package(self) -> None:
        discoveries = iter([None, Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")])
        with mock.patch.object(installer, "find_chrome", side_effect=lambda: next(discoveries)), mock.patch.object(
            installer.platform, "system", return_value="Windows"
        ), mock.patch.object(installer, "resolve_command", return_value="winget.exe"), mock.patch.object(
            installer, "run_checked"
        ) as run_checked:
            _, action = installer.ensure_chrome(
                apply=True, skip_install=False, install_consent=True
            )
        self.assertEqual(action, "installed-with-winget")
        command = run_checked.call_args.args[0]
        self.assertEqual(command[:5], ("winget.exe", "install", "--id", "Google.Chrome", "--exact"))
        self.assertIn("--silent", command)
        self.assertIn("--disable-interactivity", command)

    def test_missing_chrome_requires_explicit_consent(self) -> None:
        with mock.patch.object(installer, "find_chrome", return_value=None), mock.patch.object(
            installer.platform, "system", return_value="Windows"
        ), mock.patch.object(installer, "resolve_command", return_value="winget.exe"), mock.patch.object(
            installer, "run_checked"
        ) as run_checked:
            with self.assertRaisesRegex(installer.InstallError, "explicitly consents"):
                installer.ensure_chrome(apply=True, skip_install=False, install_consent=False)
        run_checked.assert_not_called()

    def test_dry_run_does_not_create_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            runtime = project / "runtime"
            args = argparse.Namespace(
                host="codex",
                scope="project",
                project_root=project,
                runtime_dir=runtime,
                output_dir=project / "output",
                server_name="gemini",
                register=False,
                replace_registration=False,
                skip_chrome_install=False,
                install_chrome=False,
                apply=False,
                dry_run=True,
                json=True,
            )
            with mock.patch.object(installer, "find_chrome", return_value=Path("chrome.exe")), mock.patch.object(
                installer, "resolve_command", side_effect=lambda name: f"resolved-{name}"
            ):
                result = installer.install(args)
            self.assertEqual(result["mode"], "dry-run")
            self.assertEqual(result["chrome_action"], "already-installed")
            self.assertFalse(runtime.exists())
            self.assertIn("mcpServers", result["host_config"])

    def test_existing_registration_is_untouched_without_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            with mock.patch.object(installer, "get_codex_registration", return_value={"name": "gemini"}), mock.patch.object(
                installer, "run_checked"
            ) as run_checked:
                with self.assertRaisesRegex(installer.InstallError, "already exists"):
                    installer.register_codex(
                        codex="codex",
                        server_name="gemini",
                        release_dir=project / "release",
                        output_dir=project / "output",
                        project_root=project,
                        replace=False,
                    )
            run_checked.assert_not_called()

    def test_failed_cutover_restores_exact_codex_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            codex_home = project / "codex-home"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            before = b'[mcp_servers.gemini]\ncommand = "old"\n'
            config.write_bytes(before)
            existing = {"name": "gemini", "transport": {"type": "stdio", "command": "old", "args": []}}

            def fail_add(command, **_kwargs):
                if "add" in command:
                    config.write_text("partially changed", encoding="utf-8")
                    raise installer.InstallError("injected add failure")

            with mock.patch.dict(installer.os.environ, {"CODEX_HOME": str(codex_home)}), mock.patch.object(
                installer, "get_codex_registration", return_value=existing
            ), mock.patch.object(installer, "run_checked", side_effect=fail_add):
                with self.assertRaises(installer.InstallError):
                    installer.register_codex(
                        codex="codex",
                        server_name="gemini",
                        release_dir=project / "release",
                        output_dir=project / "output",
                        project_root=project,
                        replace=True,
                    )
            self.assertEqual(config.read_bytes(), before)

    def test_successful_cutover_verifies_candidate_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            release = project / "release"
            expected = str(release / "dist" / "index.js")
            existing = {"name": "gemini", "transport": {"type": "stdio", "command": "old", "args": []}}
            candidate = {"name": "gemini", "transport": {"type": "stdio", "command": "node", "args": [expected]}}
            with mock.patch.dict(installer.os.environ, {"CODEX_HOME": str(project / "codex-home")}), mock.patch.object(
                installer, "get_codex_registration", side_effect=[existing, candidate]
            ), mock.patch.object(installer, "run_checked") as run_checked:
                installer.register_codex(
                    codex="codex",
                    server_name="gemini",
                    release_dir=release,
                    output_dir=project / "output",
                    project_root=project,
                    replace=True,
                )
            self.assertEqual(run_checked.call_count, 2)

    def test_project_scope_updates_local_config_and_preserves_other_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            config = project / ".codex" / "config.toml"
            config.parent.mkdir()
            config.write_text(
                '[features]\nexample = true\n\n[mcp_servers.gemini]\ncommand = "old"\n\n'
                '[mcp_servers.gemini.env]\nHEADLESS = "false"\n\n[mcp_servers.other]\ncommand = "other"\n',
                encoding="utf-8",
            )
            release = project / "release"
            expected = str(release / "dist" / "index.js")
            existing = {"name": "gemini", "transport": {"type": "stdio", "command": "old", "args": []}}
            candidate = {"name": "gemini", "transport": {"type": "stdio", "command": "node", "args": [expected]}}

            with mock.patch.object(
                installer, "get_codex_registration", side_effect=[existing, candidate]
            ), mock.patch.object(installer, "run_checked") as run_checked:
                installer.register_codex(
                    codex="codex",
                    server_name="gemini",
                    release_dir=release,
                    output_dir=project / "output",
                    project_root=project,
                    replace=True,
                    scope="project",
                )

            rendered = config.read_text(encoding="utf-8")
            self.assertIn("[features]", rendered)
            self.assertIn("[mcp_servers.other]", rendered)
            self.assertEqual(rendered.count("[mcp_servers.gemini]"), 1)
            self.assertIn(expected.replace("\\", "\\\\"), rendered)
            self.assertNotIn("AUTO_LOGIN_ENABLED", rendered)
            run_checked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
