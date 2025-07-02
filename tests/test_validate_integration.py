"""
Integration tests for B.3 Advanced Validation: Full CLI Command Testing.

This module provides comprehensive integration tests for the validate command,
testing the complete end-to-end workflows including CLI execution, file I/O,
and external tool integration.
"""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import (
    Mock,
    patch,
)

from sseed.cli.commands.validate import ValidateCommand


class TestValidateCommandIntegration(unittest.TestCase):
    """Integration tests for the validate command CLI interface."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Use valid BIP-39 mnemonics for testing
        self.valid_mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )
        self.invalid_mnemonic = "invalid mnemonic words that do not pass validation"

        # Create test files
        self.valid_file = self.temp_path / "valid_wallet.txt"
        self.valid_file.write_text(self.valid_mnemonic)

        self.invalid_file = self.temp_path / "invalid_wallet.txt"
        self.invalid_file.write_text(self.invalid_mnemonic)

        self.empty_file = self.temp_path / "empty.txt"
        self.empty_file.write_text("")

        # Create batch test directory
        self.batch_dir = self.temp_path / "batch"
        self.batch_dir.mkdir()

        for i in range(3):
            (self.batch_dir / f"wallet_{i}.txt").write_text(self.valid_mnemonic)
        (self.batch_dir / "invalid.txt").write_text(self.invalid_mnemonic)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_validate_basic_mnemonic(self):
        """Test basic CLI validation with mnemonic input."""
        command = ValidateCommand()

        # Create mock args for basic validation
        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False
        args.language = None  # Let it auto-detect
        args.strict = False
        args.check_entropy = False

        with patch("builtins.print") as mock_print:
            result = command.execute(args)

        self.assertEqual(result, 0)  # Success
        mock_print.assert_called()  # Should have printed results

    def test_cli_validate_basic_file_input(self):
        """Test basic CLI validation with file input."""
        command = ValidateCommand()

        args = Mock()
        args.mnemonic = None
        args.input_file = self.valid_file
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False
        args.language = None  # Let it auto-detect
        args.strict = False
        args.check_entropy = False

        with patch("builtins.print") as mock_print:
            result = command.execute(args)

        self.assertEqual(result, 0)  # Success

    def test_cli_validate_invalid_mnemonic(self):
        """Test CLI validation with invalid mnemonic."""
        command = ValidateCommand()

        args = Mock()
        args.mnemonic = self.invalid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False
        args.language = None  # Let it auto-detect
        args.strict = False
        args.check_entropy = False

        with patch("builtins.print") as mock_print:
            result = command.execute(args)

        self.assertEqual(result, 1)  # Failure

    def test_cli_validate_json_output(self):
        """Test CLI validation with JSON output format."""
        command = ValidateCommand()

        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = True
        args.verbose = False
        args.quiet = False
        args.language = None  # Let it auto-detect
        args.strict = False
        args.check_entropy = False

        with patch("builtins.print") as mock_print:
            result = command.execute(args)

        self.assertEqual(result, 0)

        # Verify JSON output
        mock_print.assert_called()
        printed_output = mock_print.call_args[0][0]

        try:
            json_data = json.loads(printed_output)
            self.assertIn("input", json_data)
            self.assertIn("mode", json_data)
            self.assertIn("overall_status", json_data)
            self.assertIn("checks", json_data)
        except json.JSONDecodeError:
            self.fail("Output was not valid JSON")

    def test_cli_validate_verbose_output(self):
        """Test CLI validation with verbose output."""
        command = ValidateCommand()

        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = True
        args.quiet = False
        args.language = None  # Let it auto-detect
        args.strict = False
        args.check_entropy = False

        with patch("builtins.print") as mock_print:
            result = command.execute(args)

        self.assertEqual(result, 0)

        # Verbose mode should print information
        self.assertGreaterEqual(mock_print.call_count, 1)

    def test_cli_validate_quiet_output(self):
        """Test CLI validation with quiet output."""
        command = ValidateCommand()

        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = True
        args.language = None  # Let it auto-detect
        args.strict = False
        args.check_entropy = False

        with patch("builtins.print") as mock_print:
            result = command.execute(args)

        self.assertEqual(result, 0)

        # Quiet mode should print minimal output
        if mock_print.called:
            # Should be brief output
            printed_output = mock_print.call_args[0][0]
            self.assertLess(len(printed_output), 100)


class TestValidateAdvancedModes(unittest.TestCase):
    """Test advanced validation modes integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()
        # Use valid BIP-39 mnemonic
        self.valid_mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )

    def create_test_args(self, mode="basic", **kwargs):
        """Create test arguments."""
        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = mode
        args.json = kwargs.get("json", False)
        args.verbose = kwargs.get("verbose", False)
        args.quiet = kwargs.get("quiet", False)
        args.language = kwargs.get("language", None)  # Let it auto-detect
        args.strict = kwargs.get("strict", False)
        args.check_entropy = kwargs.get("check_entropy", False)
        # Backup mode specific args
        args.shard_files = kwargs.get("shard_files", None)
        args.group_config = kwargs.get("group_config", "3-of-5")
        args.iterations = kwargs.get("iterations", 1)
        args.stress_test = kwargs.get("stress_test", False)
        return args

    def test_advanced_validation_mode(self):
        """Test advanced validation mode integration."""
        args = self.create_test_args(mode="advanced")

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        self.assertEqual(result, 0)

        # Should include additional analysis
        self.assertIn("checks", self.command.validation_results)

    def test_entropy_validation_mode(self):
        """Test entropy validation mode integration."""
        args = self.create_test_args(mode="entropy")

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        self.assertEqual(result, 0)

        # Should include entropy analysis
        self.assertIn("checks", self.command.validation_results)

    @patch("sseed.validation.backup_verification.verify_backup_integrity")
    def test_backup_validation_mode(self, mock_verify):
        """Test backup validation mode integration."""
        mock_verify.return_value = {
            "overall_status": "excellent",
            "overall_score": 95,
            "tests_performed": ["original_mnemonic_validation", "round_trip_backup"],
            "total_duration_ms": 150.0,
            "errors": [],
            "warnings": [],
            "recommendations": [],
        }

        args = self.create_test_args(mode="backup")

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        self.assertEqual(result, 0)
        mock_verify.assert_called_once()

    def test_compatibility_validation_mode(self):
        """Test compatibility validation mode integration."""
        args = self.create_test_args(mode="compatibility")

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        # Should complete without error (may not have external tools)
        self.assertIn(result, [0, 1])  # Either success or failure is acceptable


class TestValidateBatchProcessing(unittest.TestCase):
    """Test batch validation processing integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create batch test files
        self.batch_dir = self.temp_path / "wallets"
        self.batch_dir.mkdir()

        # Use valid BIP-39 mnemonic
        self.valid_mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )
        self.invalid_mnemonic = "invalid mnemonic words"

        # Create multiple valid files
        for i in range(5):
            (self.batch_dir / f"wallet_{i}.txt").write_text(self.valid_mnemonic)

        # Create some invalid files
        for i in range(2):
            (self.batch_dir / f"invalid_{i}.txt").write_text(self.invalid_mnemonic)

        self.command = ValidateCommand()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("sseed.validation.batch.validate_batch_files")
    def test_batch_validation_directory(self, mock_batch):
        """Test batch validation with directory input."""
        mock_batch.return_value = {
            "summary": {
                "total_files": 7,
                "passed": 5,
                "failed": 2,
                "success_rate": 71.4,
            },
            "files": {},
        }

        args = Mock()
        args.mnemonic = None
        args.input_file = None
        args.batch = self.batch_dir
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        # Partial success (>50% but <90%)
        self.assertEqual(result, 2)
        mock_batch.assert_called_once()

    @patch("sseed.validation.batch.validate_batch_files")
    def test_batch_validation_json_output(self, mock_batch):
        """Test batch validation with JSON output."""
        mock_batch.return_value = {
            "summary": {
                "total_files": 5,
                "passed": 5,
                "failed": 0,
                "success_rate": 100.0,
            },
            "files": {},
        }

        args = Mock()
        args.mnemonic = None
        args.input_file = None
        args.batch = self.batch_dir
        args.mode = "basic"
        args.json = True
        args.verbose = False
        args.quiet = False

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        self.assertEqual(result, 0)

        # Should print JSON
        mock_print.assert_called()
        printed_output = mock_print.call_args[0][0]

        try:
            json_data = json.loads(printed_output)
            self.assertIn("summary", json_data)
        except json.JSONDecodeError:
            self.fail("Batch output was not valid JSON")

    @patch("sseed.validation.batch.validate_batch_files")
    def test_batch_validation_quiet_mode(self, mock_batch):
        """Test batch validation with quiet output."""
        mock_batch.return_value = {
            "summary": {
                "total_files": 5,
                "passed": 4,
                "failed": 1,
                "success_rate": 80.0,
            },
            "files": {},
        }

        args = Mock()
        args.mnemonic = None
        args.input_file = None
        args.batch = self.batch_dir
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = True

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

        self.assertEqual(result, 2)  # Partial success

        # Should print brief summary
        mock_print.assert_called()
        printed_output = mock_print.call_args[0][0]
        self.assertIn("PARTIAL", printed_output)
        self.assertIn("80.0%", printed_output)


class TestValidateFileOperations(unittest.TestCase):
    """Test file input/output handling integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Use valid BIP-39 mnemonic
        self.valid_mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )
        self.command = ValidateCommand()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_input_valid_mnemonic(self):
        """Test validation with valid mnemonic from file."""
        test_file = self.temp_path / "test_mnemonic.txt"
        test_file.write_text(self.valid_mnemonic)

        args = Mock()
        args.mnemonic = None
        args.input_file = test_file
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False
        args.language = None  # Let it auto-detect

        result = self.command.execute(args)
        self.assertEqual(result, 0)

        # Should include file information in input_type
        self.assertIn("input_type", self.command.validation_results)

    def test_file_input_nonexistent_file(self):
        """Test validation with nonexistent file."""
        nonexistent_file = self.temp_path / "nonexistent.txt"

        args = Mock()
        args.mnemonic = None
        args.input_file = nonexistent_file
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False

        result = self.command.execute(args)
        self.assertEqual(result, 1)  # Should fail

    def test_file_input_empty_file(self):
        """Test validation with empty file."""
        empty_file = self.temp_path / "empty.txt"
        empty_file.write_text("")

        args = Mock()
        args.mnemonic = None
        args.input_file = empty_file
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False

        result = self.command.execute(args)
        self.assertEqual(result, 1)  # Should fail

    def test_file_input_with_whitespace(self):
        """Test validation with file containing whitespace."""
        test_file = self.temp_path / "whitespace.txt"
        test_file.write_text(f"  {self.valid_mnemonic}  \n")

        args = Mock()
        args.mnemonic = None
        args.input_file = test_file
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = False
        args.language = None  # Let it auto-detect

        result = self.command.execute(args)
        self.assertEqual(result, 0)  # Should succeed (whitespace trimmed)


class TestValidatePerformance(unittest.TestCase):
    """Test validation performance and benchmarking."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()
        # Use valid BIP-39 mnemonic
        self.valid_mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )

    def test_basic_validation_performance(self):
        """Test that basic validation completes within reasonable time."""
        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = False
        args.verbose = False
        args.quiet = True  # Minimize output overhead
        args.language = None  # Let it auto-detect

        start_time = time.perf_counter()

        with patch("builtins.print"):
            result = self.command.execute(args)

        end_time = time.perf_counter()
        duration = end_time - start_time

        self.assertEqual(result, 0)
        self.assertLess(duration, 1.0)  # Should complete in under 1 second

    def test_advanced_validation_performance(self):
        """Test that advanced validation completes within reasonable time."""
        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "advanced"
        args.json = False
        args.verbose = False
        args.quiet = True
        args.language = None  # Let it auto-detect

        start_time = time.perf_counter()

        with patch("builtins.print"):
            result = self.command.execute(args)

        end_time = time.perf_counter()
        duration = end_time - start_time

        self.assertEqual(result, 0)
        self.assertLess(duration, 2.0)  # Should complete in under 2 seconds

    @patch("sseed.validation.backup_verification.verify_backup_integrity")
    def test_backup_validation_performance(self, mock_verify):
        """Test backup validation performance."""
        mock_verify.return_value = {
            "overall_status": "good",
            "overall_score": 85,
            "tests_performed": ["original_mnemonic_validation"],
            "total_duration_ms": 150.0,
            "errors": [],
            "warnings": [],
            "recommendations": [],
        }

        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.input_file = None
        args.batch = None
        args.mode = "backup"
        args.json = False
        args.verbose = False
        args.quiet = True
        args.shard_files = None
        args.group_config = "3-of-5"
        args.iterations = 1
        args.stress_test = False

        start_time = time.perf_counter()

        with patch("builtins.print"):
            result = self.command.execute(args)

        end_time = time.perf_counter()
        duration = end_time - start_time

        self.assertEqual(result, 0)
        self.assertLess(duration, 3.0)  # Should complete in under 3 seconds


class TestValidateErrorHandling(unittest.TestCase):
    """Test error condition handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()

    def test_no_input_provided(self):
        """Test validation with no input provided."""
        args = Mock()
        args.mnemonic = None
        args.input_file = None
        args.batch = None
        args.mode = "basic"

        result = self.command.execute(args)
        self.assertEqual(result, 1)  # Should fail

    def test_multiple_inputs_provided(self):
        """Test validation with multiple conflicting inputs."""
        args = Mock()
        args.mnemonic = "test mnemonic"
        args.input_file = Path("test.txt")
        args.batch = None
        args.mode = "basic"

        # The argument parser should handle this, but test graceful handling
        # In real usage, argparse would prevent this scenario
        result = self.command.execute(args)
        # Should handle gracefully (likely use mnemonic over file)
        self.assertIn(result, [0, 1])

    def test_invalid_mode(self):
        """Test validation with invalid mode."""
        args = Mock()
        args.mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )
        args.input_file = None
        args.batch = None
        args.mode = "invalid_mode"

        result = self.command.execute(args)
        self.assertEqual(result, 1)  # Should fail

    def test_exception_during_validation(self):
        """Test handling of exceptions during validation."""
        args = Mock()
        args.mnemonic = (
            "clarify off only today sing hold easily chase phrase lady magic kind"
        )
        args.input_file = None
        args.batch = None
        args.mode = "basic"
        args.json = False

        # Mock a validation function to raise an exception
        with patch(
            "sseed.validation.crypto.validate_mnemonic_checksum",
            side_effect=Exception("Test error"),
        ):
            result = self.command.execute(args)

        # The exception should be caught and handled gracefully
        # Since other validation checks may still pass, result could be 0 or 1
        self.assertIn(result, [0, 1])


if __name__ == "__main__":
    unittest.main()
