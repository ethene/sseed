"""Tests for CLI examples functionality."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock

from sseed.cli.examples import show_examples


class TestCLIExamples(unittest.TestCase):
    """Test the CLI examples functionality."""

    def test_show_examples_output(self):
        """Test that show_examples produces expected output."""
        # Create a mock namespace (examples command doesn't use args)
        mock_args = Mock()

        # Capture stdout
        stdout_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer):
            exit_code = show_examples(mock_args)

        output = stdout_buffer.getvalue()

        # Test exit code
        self.assertEqual(exit_code, 0)

        # Test that output contains expected sections
        self.assertIn("🔐 SSeed Usage Examples", output)
        self.assertIn("📝 Basic Generation:", output)
        self.assertIn("🔗 Sharding (SLIP-39) with Language Detection:", output)
        self.assertIn("🔄 Restoration with Auto-Detection:", output)
        self.assertIn("🌱 Master Seed Generation (BIP-39 → BIP-32):", output)
        self.assertIn("📋 Information:", output)
        self.assertIn("🚀 Complete Multi-Language Workflows:", output)
        self.assertIn("📚 Tips & Best Practices:", output)

        # Test specific commands are mentioned
        self.assertIn("sseed gen", output)
        self.assertIn("sseed shard", output)
        self.assertIn("sseed restore", output)
        self.assertIn("sseed seed", output)
        self.assertIn("sseed version", output)
        self.assertIn("sseed examples", output)

        # Test that help guidance is included
        self.assertIn("--help", output)
        self.assertIn("--show-entropy", output)
        self.assertIn("--separate", output)

        # Test that best practices are mentioned
        self.assertIn("different secure locations", output)
        self.assertIn("Test recovery", output)
        self.assertIn("passphrases", output)

    def test_show_examples_return_value(self):
        """Test that show_examples returns the correct exit code."""
        mock_args = Mock()

        # Suppress output for this test
        with redirect_stdout(io.StringIO()):
            exit_code = show_examples(mock_args)

        self.assertEqual(exit_code, 0)

    def test_show_examples_with_none_args(self):
        """Test that show_examples works with None as args."""
        # Suppress output for this test
        with redirect_stdout(io.StringIO()):
            exit_code = show_examples(None)

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
