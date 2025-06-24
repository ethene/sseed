"""Comprehensive tests to improve coverage in multiple modules."""

import argparse
import io
import logging
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import (
    Mock,
    patch,
)

from sseed.cli.main import main
from sseed.cli.parser import (
    SSeedArgumentParser,
    create_parser,
    parse_args,
)
from sseed.file_operations import write_mnemonic_to_file
from sseed.logging_config import (
    get_logger,
    log_security_event,
    setup_logging,
)


class TestCoverageImprovements(unittest.TestCase):
    """Test various edge cases to improve overall coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files recursively
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_sseed_argument_parser_error(self):
        """Test SSeedArgumentParser error handling."""
        parser = SSeedArgumentParser(prog="test")

        with self.assertRaises(SystemExit) as cm:
            parser.error("test error message")

        self.assertEqual(cm.exception.code, 1)  # EXIT_USAGE_ERROR

    def test_create_parser_with_prog_override(self):
        """Test create_parser with program name override."""
        parser = create_parser(prog="custom-sseed")
        self.assertEqual(parser.prog, "custom-sseed")

    def test_parse_args_no_command_specified(self):
        """Test parse_args when no command is specified (should exit)."""
        with patch("sys.argv", ["sseed"]):
            with self.assertRaises(SystemExit) as cm:
                parse_args([])

            self.assertEqual(cm.exception.code, 1)  # EXIT_USAGE_ERROR

    def test_parse_args_with_explicit_args(self):
        """Test parse_args with explicitly provided arguments."""
        args = parse_args(["examples"])
        self.assertTrue(hasattr(args, "func"))
        self.assertEqual(args.command, "examples")

    def test_main_function_no_command(self):
        """Test main function when no command is provided."""
        with patch("sys.argv", ["sseed"]):
            with patch.object(sys.stdout, "write"):
                exit_code = main()

            self.assertEqual(exit_code, 0)  # Should print help and exit successfully

    def test_main_function_with_examples_command(self):
        """Test main function with examples command."""
        with patch("sys.argv", ["sseed", "examples"]):
            with patch.object(sys.stdout, "write"):
                exit_code = main()

            self.assertEqual(exit_code, 0)

    def test_write_mnemonic_to_file_no_comments(self):
        """Test writing mnemonic to file without comments."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        test_file = self.temp_dir / "test_no_comments.txt"

        write_mnemonic_to_file(test_mnemonic, str(test_file), include_comments=False)

        self.assertTrue(test_file.exists())

        with open(test_file, "r") as f:
            content = f.read()

        # Should only contain the mnemonic, no comments
        lines = content.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], test_mnemonic)

    def test_write_mnemonic_to_file_with_invalid_path(self):
        """Test writing mnemonic to file with invalid path."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        # Try to write to a path that can't be created (use a more reliable invalid path)
        invalid_path = str(self.temp_dir / "nonexistent" / "\x00invalid" / "path.txt")

        from sseed.exceptions import FileError

        with self.assertRaises(FileError):
            write_mnemonic_to_file(test_mnemonic, invalid_path)

    def test_logging_config_setup_logging(self):
        """Test logging configuration setup."""
        log_dir = self.temp_dir / "test_logs"

        # Test with custom log directory
        setup_logging(log_level="DEBUG", log_dir=str(log_dir))

        # Check that log directory was created
        self.assertTrue(log_dir.exists())

        # Test logger functionality
        logger = get_logger("test.module")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test.module")

    def test_log_security_event_with_extra_data(self):
        """Test logging security events with extra data."""
        # Set up a temporary log handler to capture output
        test_logger = logging.getLogger("sseed.security")
        test_handler = logging.StreamHandler(io.StringIO())
        test_handler.setLevel(logging.WARNING)
        test_logger.addHandler(test_handler)
        test_logger.setLevel(logging.WARNING)

        extra_data = {"user": "test", "action": "suspicious"}
        log_security_event("Test security event", extra_data)

        # Clean up
        test_logger.removeHandler(test_handler)

    def test_log_security_event_without_extra_data(self):
        """Test logging security events without extra data."""
        # Set up a temporary log handler to capture output
        test_logger = logging.getLogger("sseed.security")
        test_handler = logging.StreamHandler(io.StringIO())
        test_handler.setLevel(logging.WARNING)
        test_logger.addHandler(test_handler)
        test_logger.setLevel(logging.WARNING)

        log_security_event("Test security event without extra data")

        # Clean up
        test_logger.removeHandler(test_handler)

    def test_parser_with_version_flag(self):
        """Test parser with version flag."""
        parser = create_parser()

        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["--version"])

        self.assertEqual(cm.exception.code, 0)

    def test_parser_with_log_level_flag(self):
        """Test parser with log level flag."""
        parser = create_parser()
        args = parser.parse_args(["--log-level", "DEBUG", "examples"])

        self.assertEqual(args.log_level, "DEBUG")
        self.assertEqual(args.command, "examples")

    def test_examples_command_help(self):
        """Test examples command help."""
        parser = create_parser()

        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["examples", "--help"])

        self.assertEqual(cm.exception.code, 0)

    def test_file_operations_directory_creation(self):
        """Test file operations with nested directory creation."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        nested_file = self.temp_dir / "subdir" / "nested" / "test.txt"

        # Should create all necessary directories
        write_mnemonic_to_file(test_mnemonic, str(nested_file))

        self.assertTrue(nested_file.exists())
        self.assertTrue(nested_file.parent.exists())

    def test_parser_command_registration(self):
        """Test that all commands are properly registered in parser."""
        parser = create_parser()

        # Should have subparsers for all commands
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        self.assertEqual(len(subparsers_actions), 1)
        subparser = subparsers_actions[0]

        # Should include examples and main commands
        command_names = list(subparser.choices.keys())
        self.assertIn("examples", command_names)
        self.assertIn("gen", command_names)
        self.assertIn("shard", command_names)
        self.assertIn("restore", command_names)
        self.assertIn("seed", command_names)
        self.assertIn("version", command_names)

    def test_main_error_handling_integration(self):
        """Test main function error handling integration."""
        # Test that the error handling decorator is properly applied
        with patch("sys.argv", ["sseed", "gen", "--invalid-flag"]):
            with self.assertRaises(SystemExit) as cm:
                main()

            # Should handle argument parsing error with exit code 1
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
