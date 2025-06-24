"""Tests for CLI error handling edge cases and missing coverage."""

import io
import sys
import unittest
from unittest.mock import (
    Mock,
    patch,
)

from sseed.cli.error_handling import (
    handle_common_errors,
    handle_top_level_errors,
)
from sseed.exceptions import (
    EntropyError,
    FileError,
    MnemonicError,
    SecurityError,
    ShardError,
    SseedError,
    ValidationError,
)


class TestCLIErrorHandlingEdgeCases(unittest.TestCase):
    """Test edge cases for CLI error handling decorators."""

    def test_handle_common_errors_entropy_error(self):
        """Test handle_common_errors decorator with EntropyError."""

        @handle_common_errors("test operation")
        def failing_function():
            raise EntropyError("Test entropy error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Cryptographic error: Test entropy error", error_output)

    def test_handle_common_errors_mnemonic_error(self):
        """Test handle_common_errors decorator with MnemonicError."""

        @handle_common_errors("test operation")
        def failing_function():
            raise MnemonicError("Test mnemonic error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Cryptographic error: Test mnemonic error", error_output)

    def test_handle_common_errors_security_error(self):
        """Test handle_common_errors decorator with SecurityError."""

        @handle_common_errors("test operation")
        def failing_function():
            raise SecurityError("Test security error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Cryptographic error: Test security error", error_output)

    def test_handle_common_errors_shard_error(self):
        """Test handle_common_errors decorator with ShardError."""

        @handle_common_errors("test operation")
        def failing_function():
            raise ShardError("Test shard error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Cryptographic error: Test shard error", error_output)

    def test_handle_common_errors_file_error(self):
        """Test handle_common_errors decorator with FileError."""

        @handle_common_errors("test operation")
        def failing_function():
            raise FileError("Test file error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 3)  # EXIT_FILE_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("File error: Test file error", error_output)

    def test_handle_common_errors_validation_error(self):
        """Test handle_common_errors decorator with ValidationError."""

        @handle_common_errors("test operation")
        def failing_function():
            raise ValidationError("Test validation error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 4)  # EXIT_VALIDATION_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Validation error: Test validation error", error_output)

    def test_handle_common_errors_unexpected_exception(self):
        """Test handle_common_errors decorator with unexpected exception."""

        @handle_common_errors("test operation")
        def failing_function():
            raise RuntimeError("Unexpected runtime error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR (fallback)
        error_output = captured_error.getvalue()
        self.assertIn("Unexpected error: Unexpected runtime error", error_output)

    def test_handle_top_level_errors_keyboard_interrupt(self):
        """Test handle_top_level_errors decorator with KeyboardInterrupt."""

        @handle_top_level_errors
        def interrupted_function():
            raise KeyboardInterrupt()

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = interrupted_function()

        self.assertEqual(exit_code, 130)  # EXIT_INTERRUPTED
        error_output = captured_error.getvalue()
        self.assertIn("Operation cancelled by user", error_output)

    def test_handle_top_level_errors_file_error(self):
        """Test handle_top_level_errors decorator with FileError."""

        @handle_top_level_errors
        def failing_function():
            raise FileError("Top level file error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 3)  # EXIT_FILE_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("File error: Top level file error", error_output)

    def test_handle_top_level_errors_validation_error(self):
        """Test handle_top_level_errors decorator with ValidationError."""

        @handle_top_level_errors
        def failing_function():
            raise ValidationError("Top level validation error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 4)  # EXIT_VALIDATION_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Validation error: Top level validation error", error_output)

    def test_handle_top_level_errors_mnemonic_error(self):
        """Test handle_top_level_errors decorator with MnemonicError."""

        @handle_top_level_errors
        def failing_function():
            raise MnemonicError("Top level mnemonic error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Cryptographic error: Top level mnemonic error", error_output)

    def test_handle_top_level_errors_security_error(self):
        """Test handle_top_level_errors decorator with SecurityError."""

        @handle_top_level_errors
        def failing_function():
            raise SecurityError("Top level security error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Cryptographic error: Top level security error", error_output)

    def test_handle_top_level_errors_sseed_error(self):
        """Test handle_top_level_errors decorator with SseedError."""

        @handle_top_level_errors
        def failing_function():
            raise SseedError("Top level sseed error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 1)  # EXIT_USAGE_ERROR
        error_output = captured_error.getvalue()
        self.assertIn("Error: Top level sseed error", error_output)

    def test_handle_top_level_errors_unexpected_exception(self):
        """Test handle_top_level_errors decorator with unexpected exception."""

        @handle_top_level_errors
        def failing_function():
            raise RuntimeError("Top level unexpected error")

        captured_error = io.StringIO()

        with patch("sys.stderr", captured_error):
            exit_code = failing_function()

        self.assertEqual(exit_code, 2)  # EXIT_CRYPTO_ERROR (fallback)
        error_output = captured_error.getvalue()
        self.assertIn("Unexpected error: Top level unexpected error", error_output)

    def test_error_decorators_preserve_function_metadata(self):
        """Test that error decorators preserve original function metadata."""

        @handle_common_errors("test")
        def test_function():
            """Test function docstring."""
            return 0

        @handle_top_level_errors
        def top_level_function():
            """Top level function docstring."""
            return 0

        # Check that function names and docstrings are preserved
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "Test function docstring.")
        self.assertEqual(top_level_function.__name__, "top_level_function")
        self.assertEqual(top_level_function.__doc__, "Top level function docstring.")

    def test_successful_function_execution(self):
        """Test that decorators don't interfere with successful function execution."""

        @handle_common_errors("test")
        def successful_function():
            return 42

        @handle_top_level_errors
        def successful_top_level():
            return 99

        # Both should return their original values
        self.assertEqual(successful_function(), 42)
        self.assertEqual(successful_top_level(), 99)


if __name__ == "__main__":
    unittest.main()
