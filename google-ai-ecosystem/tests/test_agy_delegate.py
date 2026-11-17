import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agy_delegate.py"
SPEC = importlib.util.spec_from_file_location("agy_delegate", SCRIPT_PATH)
agy_delegate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agy_delegate)


class AgyDelegateTests(unittest.TestCase):
    def test_build_command_uses_structured_output_without_permission_bypass(self):
        command = agy_delegate.build_command(
            "agy",
            "Review the code.",
            mode="plan",
            model="example-model",
            effort="high",
            conversation="conversation-1",
            print_timeout="5m",
            disable_slash_commands=True,
            add_dirs=["/authorized"],
        )

        self.assertIn("--output-format", command)
        self.assertIn("json", command)
        self.assertIn("--mode", command)
        self.assertIn("plan", command)
        self.assertIn("--conversation", command)
        self.assertNotIn("--dangerously-skip-permissions", command)

    def test_parse_envelope_accepts_final_json_line(self):
        payload = {"status": "SUCCESS", "response": "ok", "conversation_id": "c1"}
        parsed = agy_delegate.parse_envelope("diagnostic preamble\n" + json.dumps(payload))
        self.assertEqual(payload, parsed)

    def test_parse_envelope_rejects_ambiguous_json_objects(self):
        with self.assertRaisesRegex(ValueError, "multiple JSON"):
            agy_delegate.parse_envelope(
                json.dumps({"status": "SUCCESS"}) + "\n" + json.dumps({"status": "SUCCESS"})
            )

    def test_validate_envelope_requires_typed_success_fields(self):
        invalid = [
            {},
            {"status": "SUCCESS", "response": "ok"},
            {"status": "SUCCESS", "response": 42, "conversation_id": "c1"},
            {"status": "SUCCESS", "response": "ok", "conversation_id": 42},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                agy_delegate.validate_envelope(payload)

    def test_argv_transport_rejects_large_and_sensitive_prompts(self):
        with self.assertRaisesRegex(ValueError, "argv transport limit"):
            agy_delegate.validate_argv_prompt("x" * (agy_delegate.MAX_ARGV_PROMPT_CHARS + 1))
        with self.assertRaisesRegex(ValueError, "credential"):
            agy_delegate.validate_argv_prompt("API_KEY=synthetic-secret-value")

    def test_main_returns_success_and_emits_validated_envelope(self):
        payload = {"status": "SUCCESS", "response": "AGY_OK\n", "conversation_id": "c1"}
        completed = subprocess.CompletedProcess(
            args=["agy"],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_binary = Path(temporary_directory) / "agy.exe"
            fake_binary.touch()
            stdout = io.StringIO()
            with mock.patch.object(
                agy_delegate, "run_delegate", return_value=(payload, 0, "")
            ), mock.patch(
                "sys.stdout", stdout
            ):
                result = agy_delegate.main(
                    [
                        "--agy-bin",
                        str(fake_binary),
                        "--cwd",
                        temporary_directory,
                        "--mode",
                        "plan",
                        "--prompt",
                        "Reply with AGY_OK.",
                    ]
                )

        self.assertEqual(0, result)
        self.assertEqual(payload, json.loads(stdout.getvalue()))

    def test_main_fails_when_terminal_status_is_not_success(self):
        payload = {"status": "ERROR", "response": "", "error": "failed"}
        completed = subprocess.CompletedProcess(
            args=["agy"],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_binary = Path(temporary_directory) / "agy.exe"
            fake_binary.touch()
            with mock.patch.object(
                agy_delegate, "run_delegate", return_value=(payload, 0, "")
            ), mock.patch(
                "sys.stdout", io.StringIO()
            ), mock.patch("sys.stderr", io.StringIO()):
                result = agy_delegate.main(
                    [
                        "--agy-bin",
                        str(fake_binary),
                        "--cwd",
                        temporary_directory,
                        "--prompt",
                        "Do a task.",
                    ]
                )

        self.assertEqual(3, result)

    def test_nonzero_process_never_emits_response_only(self):
        payload = {"status": "SUCCESS", "response": "must-not-print", "conversation_id": "c1"}
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_binary = Path(temporary_directory) / "agy.exe"
            fake_binary.touch()
            stdout = io.StringIO()
            with mock.patch.object(
                agy_delegate, "run_delegate", return_value=(payload, 9, "synthetic stderr")
            ), mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", io.StringIO()):
                result = agy_delegate.main(
                    [
                        "--agy-bin",
                        str(fake_binary),
                        "--cwd",
                        temporary_directory,
                        "--prompt",
                        "Do a task.",
                        "--response-only",
                    ]
                )
        self.assertEqual(4, result)
        self.assertEqual("", stdout.getvalue())

    def test_hung_process_is_stopped_by_wrapper_timeout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            command = [sys.executable, "-c", "import time; time.sleep(30)"]
            with self.assertRaises(agy_delegate.DelegateTimeoutError):
                agy_delegate.run_delegate(
                    command,
                    Path(temporary_directory),
                    wrapper_timeout_seconds=0.1,
                    terminate_grace_seconds=0.5,
                )

    def test_transport_probe_does_not_send_a_prompt(self):
        completed = subprocess.CompletedProcess(
            args=["agy", "--help"],
            returncode=0,
            stdout="usage: agy -p PROMPT",
            stderr="",
        )
        with mock.patch.object(agy_delegate.subprocess, "run", return_value=completed) as run:
            result = agy_delegate.probe_prompt_transport("agy")
        self.assertEqual("argv", result["transport"])
        self.assertEqual(["agy", "--help"], run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
