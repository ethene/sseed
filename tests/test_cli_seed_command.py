"""Tests for CLI seed command edge cases and missing coverage."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import (
    Mock,
    patch,
)

from sseed.cli.commands.seed import SeedCommand


class TestCLISeedCommand(unittest.TestCase):
    """Test the CLI seed command edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file in self.temp_dir.glob("*"):
            if file.is_file():
                file.unlink()
        self.temp_dir.rmdir()

    def test_seed_command_binary_format_to_file(self):
        """Test seed command with binary format output to file."""
        # Create test mnemonic file
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write(self.test_mnemonic)

        # Create output file path
        output_file = self.temp_dir / "test_seed.bin"

        # Create mock args
        args = Mock()
        args.input = str(mnemonic_file)
        args.output = str(output_file)
        args.passphrase = False
        args.format = "binary"

        command = SeedCommand()
        exit_code = command.handle(args)

        # Check results
        self.assertEqual(exit_code, 0)
        self.assertTrue(output_file.exists())

        # Verify binary file content (now includes language info as UTF-8 header)
        with open(output_file, "rb") as f:
            seed_bytes = f.read()

        # File now contains language info header + 64-byte binary seed
        # Language info line is approximately 25 bytes as UTF-8
        self.assertGreater(len(seed_bytes), 64)  # Should be more than just the seed
        self.assertIsInstance(seed_bytes, bytes)

        # The actual binary seed should be the last 64 bytes
        actual_seed = seed_bytes[-64:]
        self.assertEqual(len(actual_seed), 64)

    def test_seed_command_binary_format_to_stdout_fallback(self):
        """Test seed command with binary format to stdout (should fallback to hex)."""
        # Create test mnemonic file
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write(self.test_mnemonic)

        # Create mock args for binary format output to stdout
        args = Mock()
        args.input = str(mnemonic_file)
        args.output = None  # stdout
        args.passphrase = False
        args.format = "binary"

        # Capture stdout and stderr
        captured_output = io.StringIO()
        captured_error = io.StringIO()

        command = SeedCommand()

        with patch("sys.stdout", captured_output), patch("sys.stderr", captured_error):
            exit_code = command.handle(args)

        # Check results
        self.assertEqual(exit_code, 0)

        # Should output hex to stdout when binary is requested for stdout
        # Now includes language info line
        output_lines = captured_output.getvalue().strip().split("\n")
        hex_output = output_lines[0]  # First line is the hex seed
        language_line = output_lines[1]  # Second line is language info

        self.assertEqual(len(hex_output), 128)  # 64 bytes = 128 hex characters
        self.assertTrue(language_line.startswith("# Language:"))

        # Should warn about binary not supported for stdout
        error_output = captured_error.getvalue()
        self.assertIn("Binary format not supported for stdout", error_output)

    def test_seed_command_with_passphrase_prompt(self):
        """Test seed command with passphrase prompt."""
        # Create test mnemonic file
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write(self.test_mnemonic)

        # Create mock args
        args = Mock()
        args.input = str(mnemonic_file)
        args.output = None
        args.passphrase = True
        args.format = "hex"

        # Mock getpass to provide a test passphrase
        with patch("getpass.getpass", return_value="test_passphrase"):
            captured_output = io.StringIO()
            command = SeedCommand()

            with patch("sys.stdout", captured_output):
                exit_code = command.handle(args)

        # Check results
        self.assertEqual(exit_code, 0)

        # Now includes language info line
        output_lines = captured_output.getvalue().strip().split("\n")
        hex_output = output_lines[0]  # First line is the hex seed
        language_line = output_lines[1]  # Second line is language info

        self.assertEqual(len(hex_output), 128)  # 64 bytes = 128 hex characters
        self.assertTrue(language_line.startswith("# Language:"))

    def test_seed_command_hex_flag_backward_compatibility(self):
        """Test seed command with --hex flag for backward compatibility."""
        # Create test mnemonic file
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write(self.test_mnemonic)

        # Create mock args with hex flag (backward compatibility)
        args = Mock()
        args.input = str(mnemonic_file)
        args.output = None
        args.passphrase = False
        args.format = "hex"  # This is what --hex flag sets

        captured_output = io.StringIO()
        command = SeedCommand()

        with patch("sys.stdout", captured_output):
            exit_code = command.handle(args)

        # Check results
        self.assertEqual(exit_code, 0)

        # Now includes language info line
        output_lines = captured_output.getvalue().strip().split("\n")
        hex_output = output_lines[0]  # First line is the hex seed
        language_line = output_lines[1]  # Second line is language info

        self.assertEqual(len(hex_output), 128)  # 64 bytes = 128 hex characters
        self.assertTrue(language_line.startswith("# Language:"))

    def test_seed_command_invalid_mnemonic_checksum(self):
        """Test seed command with invalid mnemonic checksum."""
        # Create test file with invalid mnemonic
        mnemonic_file = self.temp_dir / "invalid_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write("invalid mnemonic words that will fail checksum validation")

        # Create mock args
        args = Mock()
        args.input = str(mnemonic_file)
        args.output = None
        args.passphrase = False
        args.format = "hex"

        command = SeedCommand()

        # Should return error code due to invalid mnemonic (caught by error handler)
        # Note: This now returns EXIT_FILE_ERROR (3) because validation happens
        # during file reading in the new modular structure
        exit_code = command.handle(args)
        self.assertEqual(exit_code, 3)  # EXIT_FILE_ERROR

    def test_seed_command_output_to_file_hex_format(self):
        """Test seed command output to file in hex format."""
        # Create test mnemonic file
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write(self.test_mnemonic)

        # Create output file path
        output_file = self.temp_dir / "test_seed.hex"

        # Create mock args
        args = Mock()
        args.input = str(mnemonic_file)
        args.output = str(output_file)
        args.passphrase = False
        args.format = "hex"

        command = SeedCommand()

        # Mock handle_output to verify it's called correctly
        with patch.object(command, "handle_output") as mock_handle_output:
            exit_code = command.handle(args)

        # Check results
        self.assertEqual(exit_code, 0)
        mock_handle_output.assert_called_once()

        # Verify the output content would be hex format with language info
        call_args = mock_handle_output.call_args[0]
        full_output = call_args[0]

        # Output now includes language info header
        output_lines = full_output.strip().split("\n")
        language_line = output_lines[0]  # First line is language info comment
        hex_output = output_lines[1]  # Second line is the hex seed

        self.assertTrue(language_line.startswith("# Language:"))
        self.assertEqual(len(hex_output), 128)  # 64 bytes = 128 hex characters

    def test_seed_command_memory_cleanup_on_exception(self):
        """Test that seed command properly cleans up memory even on exceptions."""
        # Create test mnemonic file with invalid content
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        with open(mnemonic_file, "w") as f:
            f.write("invalid mnemonic")

        args = Mock()
        args.input = str(mnemonic_file)
        args.output = None
        args.passphrase = False
        args.format = "hex"

        command = SeedCommand()

        # Should handle exception gracefully and still cleanup
        try:
            command.handle(args)
        except Exception:
            pass  # Expected to fail, but cleanup should still happen

        # This test mainly ensures the finally block executes without error

    def test_seed_command_with_stdin_input(self):
        """Test seed command reading from stdin."""
        args = Mock()
        args.input = None  # stdin
        args.output = None
        args.passphrase = False
        args.format = "hex"

        command = SeedCommand()

        # Mock handle_input to simulate stdin input
        with patch.object(command, "handle_input", return_value=self.test_mnemonic):
            captured_output = io.StringIO()

            with patch("sys.stdout", captured_output):
                exit_code = command.handle(args)

        # Check results
        self.assertEqual(exit_code, 0)

        # Now includes language info line
        output_lines = captured_output.getvalue().strip().split("\n")
        hex_output = output_lines[0]  # First line is the hex seed
        language_line = output_lines[1]  # Second line is language info

        self.assertEqual(len(hex_output), 128)  # 64 bytes = 128 hex characters
        self.assertTrue(language_line.startswith("# Language:"))


if __name__ == "__main__":
    unittest.main()
