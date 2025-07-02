"""Tests for the version command functionality."""

import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from sseed import __version__
from sseed.cli import handle_version_command
from sseed.cli.main import main


class TestVersionCommand(unittest.TestCase):
    """Test the version command functionality."""

    def test_version_command_human_readable(self):
        """Test version command with human-readable output."""

        # Mock argparse namespace
        class MockArgs:
            json = False

        args = MockArgs()
        exit_code = handle_version_command(args)

        self.assertEqual(exit_code, 0)

    def test_version_command_json_output(self):
        """Test version command with JSON output."""

        # Mock argparse namespace
        class MockArgs:
            json = True

        args = MockArgs()

        # Capture stdout
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = handle_version_command(args)

        output = f.getvalue()

        self.assertEqual(exit_code, 0)

        # Verify JSON output is valid
        try:
            version_data = json.loads(output)
            self.assertIn("sseed", version_data)
            self.assertIn("python", version_data)
            self.assertIn("platform", version_data)
            self.assertIn("dependencies", version_data)
            self.assertEqual(version_data["sseed"], __version__)
        except json.JSONDecodeError:
            self.fail("Version command did not produce valid JSON")

    def test_version_command_via_main(self):
        """Test version command through main CLI entry point."""
        with patch("sys.argv", ["sseed", "version"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)

    def test_version_command_json_via_main(self):
        """Test version command with --json flag through main CLI."""
        with patch("sys.argv", ["sseed", "version", "--json"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)

    def test_version_command_help(self):
        """Test version command help output."""
        with patch("sys.argv", ["sseed", "version", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_version_command_subprocess(self):
        """Test version command via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "sseed", "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("SSeed v", result.stdout)
        self.assertIn(__version__, result.stdout)
        self.assertIn("Core Information:", result.stdout)
        self.assertIn("Dependencies:", result.stdout)

    def test_version_command_json_subprocess(self):
        """Test version command JSON output via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "sseed", "version", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0)

        # Parse JSON output (skip log lines and find complete JSON)
        lines = result.stdout.strip().split("\n")

        # Find the start of JSON output
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        self.assertNotEqual(json_start, -1, "No JSON output found")

        # Get all lines from JSON start to end
        json_output = "\n".join(lines[json_start:])

        try:
            version_data = json.loads(json_output)
            self.assertIn("sseed", version_data)
            self.assertEqual(version_data["sseed"], __version__)
            self.assertIn("python", version_data)
            self.assertIn("platform", version_data)
            self.assertIn("dependencies", version_data)

            # Verify platform information
            platform_info = version_data["platform"]
            self.assertIn("system", platform_info)
            self.assertIn("release", platform_info)
            self.assertIn("machine", platform_info)
            self.assertIn("architecture", platform_info)

            # Verify dependencies
            dependencies = version_data["dependencies"]
            self.assertIn("bip-utils", dependencies)
            self.assertIn("shamir-mnemonic", dependencies)

        except json.JSONDecodeError as e:
            self.fail(
                f"Version command did not produce valid JSON: {e}\nOutput: {json_output}"
            )

    def test_version_in_help_listing(self):
        """Test that version command appears in main help."""
        result = subprocess.run(
            [sys.executable, "-m", "sseed", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("version", result.stdout)
        self.assertIn("Show version and system information", result.stdout)

    @patch("importlib.metadata.version")
    def test_version_command_missing_dependency(self, mock_version):
        """Test version command when a dependency is missing."""

        # Mock a missing dependency
        def side_effect(package):
            if package == "bip-utils":
                from importlib.metadata import PackageNotFoundError

                raise PackageNotFoundError("Package not found")
            return "0.3.0"  # shamir-mnemonic version

        mock_version.side_effect = side_effect

        class MockArgs:
            json = True

        args = MockArgs()

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = handle_version_command(args)

        output = f.getvalue()

        self.assertEqual(exit_code, 0)

        # Verify JSON output handles missing dependency
        version_data = json.loads(output)
        self.assertEqual(version_data["dependencies"]["bip-utils"], "not installed")
        self.assertEqual(version_data["dependencies"]["shamir-mnemonic"], "0.3.0")


if __name__ == "__main__":
    unittest.main()
