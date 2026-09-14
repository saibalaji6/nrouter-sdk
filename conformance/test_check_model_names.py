#!/usr/bin/env python3
"""Tests for the SDK served-model-name conformance checker."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "conformance" / "fixtures" / "model-names"
CHECK_SCRIPT = ROOT / "conformance" / "check_model_names.py"

# Ensure conformance directory is in python path
sys.path.insert(0, str(ROOT / "conformance"))


class TestCheckModelNames(unittest.TestCase):
    """Test suite for check_model_names.py."""

    def test_all_served_exit_0(self):
        """When all candidate models in SDK examples are served, check exits 0."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "served.json"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Expected 0, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}")
        self.assertNotIn("is not served by /v1/models", res.stdout)

    def test_one_unserved_id_exit_1(self):
        """When an example names an unserved model id, check exits 1 with file:line."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk-unserved"),
            "--served",
            str(FIXTURES / "served.json"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1, f"Expected 1, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}")
        expected_finding = 'sdks/ts/examples/unserved.ts:6: model id "unserved-ts-model" is not served by /v1/models'
        self.assertIn(expected_finding, res.stdout)

    def test_placeholder_values_ignored(self):
        """Obvious placeholders (<...>, {...}, $..., YOUR_..., your-model, empty) are ignored."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "served.json"),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["findings"], [])

    def test_router_auto_ignored(self):
        """Router ids beginning with nrouter/ are ignored."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "served.json"),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        models_found = [f["model"] for f in data["findings"]]
        self.assertNotIn("nrouter/auto", models_found)

    def test_plain_array_served_file_accepted(self):
        """A plain JSON array of strings is accepted as a valid served list."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "served-array.json"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

    def test_empty_served_list_exit_2(self):
        """An empty served list is an error and must exit 2."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "served-empty.json"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 2, f"Expected 2, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}")

    def test_missing_served_file_exit_2(self):
        """A missing served file is an error and must exit 2."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "nonexistent-served.json"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 2, f"Expected 2, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}")

    def test_json_shape(self):
        """--json output produces the expected keys: findings, scanned_files, served_count."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk-unserved"),
            "--served",
            str(FIXTURES / "served.json"),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertIn("findings", data)
        self.assertIn("scanned_files", data)
        self.assertIn("served_count", data)
        self.assertEqual(data["served_count"], 3)
        self.assertGreater(data["scanned_files"], 0)
        self.assertEqual(len(data["findings"]), 1)
        finding = data["findings"][0]
        self.assertEqual(finding["file"], "sdks/ts/examples/unserved.ts")
        self.assertEqual(finding["line"], 6)
        self.assertEqual(finding["model"], "unserved-ts-model")

    def test_skipped_directories_not_scanned(self):
        """Directories like node_modules containing unserved model names are ignored."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "served.json"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("unserved-in-node-modules", res.stdout)

    def test_no_network_call_when_served_is_file(self):
        """When --served is a local file path, no network calls are made."""
        from check_model_names import run_check

        def forbid_network(*args, **kwargs):
            raise AssertionError("network call attempted when --served is a file")

        with patch("urllib.request.urlopen", side_effect=forbid_network):
            exit_code, findings, scanned_count, served_count = run_check(
                root_path=FIXTURES / "fake-sdk",
                served_target=str(FIXTURES / "served.json"),
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(findings), 0)
            self.assertEqual(served_count, 3)

    def test_unreadable_file_exit_2(self):
        """An unreadable file must be reported and cause exit code 2."""
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir) / "fake-sdk"
            shutil.copytree(FIXTURES / "fake-sdk", tmp_root)
            unreadable_file = tmp_root / "sdks" / "ts" / "examples" / "client.ts"
            unreadable_file.chmod(0o000)
            try:
                cmd = [
                    sys.executable,
                    str(CHECK_SCRIPT),
                    "--root",
                    str(tmp_root),
                    "--served",
                    str(FIXTURES / "served.json"),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(res.returncode, 2, f"Expected 2, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}")
                self.assertIn("client.ts", res.stderr)
            finally:
                unreadable_file.chmod(0o644)

    def test_scan_scope_sdks_and_agents_only(self):
        """Paths outside sdks/ (e.g. other/demo/x.py) are not scanned; sdks/ts/demo/ is scanned."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk-demo"),
            "--served",
            str(FIXTURES / "served.json"),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        findings = data["findings"]
        found_models = [f["model"] for f in findings]
        self.assertIn("unserved-sdks-demo-model", found_models)
        self.assertNotIn("unserved-other-demo-model", found_models)

    def test_missing_served_file_json_exit_2(self):
        """When --served is missing with --json, output valid JSON with error and exit 2."""
        cmd = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--root",
            str(FIXTURES / "fake-sdk"),
            "--served",
            str(FIXTURES / "nonexistent-served.json"),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        data = json.loads(res.stdout)
        self.assertIn("error", data)
        self.assertTrue(len(data["error"]) > 0)
        self.assertEqual(data["findings"], [])
        self.assertEqual(data["scanned_files"], 0)
        self.assertEqual(data["served_count"], 0)

    def test_unreadable_file_json_exit_2(self):
        """An unreadable file with --json emits valid JSON with error and exits 2."""
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir) / "fake-sdk"
            shutil.copytree(FIXTURES / "fake-sdk", tmp_root)
            unreadable_file = tmp_root / "sdks" / "ts" / "examples" / "client.ts"
            unreadable_file.chmod(0o000)
            try:
                cmd = [
                    sys.executable,
                    str(CHECK_SCRIPT),
                    "--root",
                    str(tmp_root),
                    "--served",
                    str(FIXTURES / "served.json"),
                    "--json",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(res.returncode, 2)
                data = json.loads(res.stdout)
                self.assertIn("error", data)
                self.assertIn("client.ts", data["error"])
                self.assertEqual(data["findings"], [])
                self.assertEqual(data["scanned_files"], 0)
                self.assertEqual(data["served_count"], 0)
            finally:
                unreadable_file.chmod(0o644)


if __name__ == "__main__":
    unittest.main()

