"""Comprehensive CLI error handling tests for sseed.

Tests all CLI error paths, exception scenarios, and edge cases to achieve
comprehensive coverage of CLI error handling logic.
"""

import io
import os
import subprocess
import tempfile
import unittest.mock as mock
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sseed.cli import (EXIT_CRYPTO_ERROR, EXIT_SUCCESS, EXIT_USAGE_ERROR,
                       handle_gen_command, handle_restore_command,
                       handle_shard_command, main)
from sseed.exceptions import (EntropyError, FileError, MnemonicError,
                              SecurityError, ShardError, ValidationError)


class TestCLIErrorHandling:
    """Comprehensive CLI error handling tests."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # ===== GEN COMMAND ERROR TESTS =====

    def test_gen_entropy_error_handling(self):
        """Test gen command handling EntropyError."""
        args = mock.MagicMock()
        args.output = None

        with patch(
            "sseed.cli.generate_mnemonic", side_effect=EntropyError("Entropy failure")
        ):
            result = handle_gen_command(args)
            assert result == EXIT_CRYPTO_ERROR

    def test_gen_mnemonic_error_handling(self):
        """Test gen command handling MnemonicError."""
        args = mock.MagicMock()
        args.output = None

        with patch(
            "sseed.cli.generate_mnemonic", side_effect=MnemonicError("Mnemonic failure")
        ):
            result = handle_gen_command(args)
            assert result == EXIT_CRYPTO_ERROR

    def test_gen_security_error_handling(self):
        """Test gen command handling SecurityError."""
        args = mock.MagicMock()
        args.output = None

        with patch(
            "sseed.cli.generate_mnemonic", side_effect=SecurityError("Security failure")
        ):
            result = handle_gen_command(args)
            assert result == EXIT_CRYPTO_ERROR

    def test_gen_validation_error_handling(self):
        """Test gen command handling ValidationError."""
        args = mock.MagicMock()
        args.output = None

        with patch(
            "sseed.cli.generate_mnemonic",
            side_effect=ValidationError("Validation failure"),
        ):
            result = handle_gen_command(args)
            assert result == EXIT_USAGE_ERROR

    def test_gen_file_error_handling(self):
        """Test gen command handling FileError."""
        args = mock.MagicMock()
        args.output = None

        with patch(
            "sseed.cli.generate_mnemonic", side_effect=FileError("File failure")
        ):
            result = handle_gen_command(args)
            assert result == EXIT_USAGE_ERROR

    def test_gen_unexpected_error_handling(self):
        """Test gen command handling unexpected exceptions."""
        args = mock.MagicMock()
        args.output = None

        with patch(
            "sseed.cli.generate_mnemonic", side_effect=RuntimeError("Unexpected error")
        ):
            result = handle_gen_command(args)
            assert result == EXIT_CRYPTO_ERROR

    def test_gen_checksum_validation_failure(self):
        """Test gen command when generated mnemonic fails checksum validation."""
        args = mock.MagicMock()
        args.output = None

        with patch("sseed.cli.generate_mnemonic", return_value="invalid mnemonic"):
            with patch("sseed.cli.validate_mnemonic_checksum", return_value=False):
                result = handle_gen_command(args)
                assert result == EXIT_CRYPTO_ERROR

    def test_gen_file_write_error(self):
        """Test gen command when file writing fails."""
        args = mock.MagicMock()
        args.output = "/invalid/path/file.txt"

        with patch("sseed.cli.generate_mnemonic", return_value="valid mnemonic"):
            with patch("sseed.cli.validate_mnemonic_checksum", return_value=True):
                with patch(
                    "sseed.cli.write_mnemonic_to_file",
                    side_effect=FileError("Write failed"),
                ):
                    result = handle_gen_command(args)
                    assert result == EXIT_USAGE_ERROR

    # ===== SHARD COMMAND ERROR TESTS =====

    def test_shard_invalid_group_config(self):
        """Test shard command with invalid group configuration."""
        args = mock.MagicMock()
        args.group = "invalid-config"
        args.input = None
        args.output = None
        args.separate = False

        with patch(
            "sseed.cli.validate_group_threshold",
            side_effect=ValidationError("Invalid config"),
        ):
            result = handle_shard_command(args)
            assert result == EXIT_USAGE_ERROR

    def test_shard_file_read_error(self):
        """Test shard command when input file reading fails."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = "nonexistent.txt"
        args.output = None
        args.separate = False

        with patch("sseed.cli.validate_group_threshold"):
            with patch(
                "sseed.cli.read_mnemonic_from_file",
                side_effect=FileError("File not found"),
            ):
                result = handle_shard_command(args)
                assert result == EXIT_USAGE_ERROR

    def test_shard_stdin_read_error(self):
        """Test shard command when stdin reading fails."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = None
        args.separate = False

        with patch("sseed.cli.validate_group_threshold"):
            with patch(
                "sseed.cli.read_from_stdin", side_effect=FileError("Stdin read failed")
            ):
                result = handle_shard_command(args)
                assert result == EXIT_USAGE_ERROR

    def test_shard_checksum_validation_failure(self):
        """Test shard command when input mnemonic fails checksum validation."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = None
        args.separate = False

        with patch("sseed.cli.validate_group_threshold"):
            with patch("sseed.cli.read_from_stdin", return_value="invalid mnemonic"):
                with patch("sseed.cli.validate_mnemonic_checksum", return_value=False):
                    result = handle_shard_command(args)
                    assert result == EXIT_CRYPTO_ERROR

    def test_shard_slip39_error(self):
        """Test shard command when SLIP-39 sharding fails."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = None
        args.separate = False

        with patch("sseed.cli.validate_group_threshold"):
            with patch("sseed.cli.read_from_stdin", return_value="valid mnemonic"):
                with patch("sseed.cli.validate_mnemonic_checksum", return_value=True):
                    with patch(
                        "sseed.cli.parse_group_config", return_value=(1, [(3, 5)])
                    ):
                        with patch(
                            "sseed.cli.create_slip39_shards",
                            side_effect=ShardError("Shard failed"),
                        ):
                            result = handle_shard_command(args)
                            assert result == EXIT_CRYPTO_ERROR

    def test_shard_separate_flag_stdout_warning(self):
        """Test shard command warning when --separate used with stdout."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = None
        args.separate = True

        with patch("sseed.cli.validate_group_threshold"):
            with patch("sseed.cli.read_from_stdin", return_value="valid mnemonic"):
                with patch("sseed.cli.validate_mnemonic_checksum", return_value=True):
                    with patch(
                        "sseed.cli.parse_group_config", return_value=(1, [(3, 5)])
                    ):
                        with patch(
                            "sseed.cli.create_slip39_shards",
                            return_value=["shard1", "shard2", "shard3"],
                        ):
                            with patch(
                                "sys.stderr", new_callable=io.StringIO
                            ) as mock_stderr:
                                result = handle_shard_command(args)
                                assert result == EXIT_SUCCESS
                                assert (
                                    "--separate flag ignored" in mock_stderr.getvalue()
                                )

    def test_shard_separate_files_write_error(self):
        """Test shard command when separate file writing fails."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = "shards.txt"
        args.separate = True

        with patch("sseed.cli.validate_group_threshold"):
            with patch("sseed.cli.read_from_stdin", return_value="valid mnemonic"):
                with patch("sseed.cli.validate_mnemonic_checksum", return_value=True):
                    with patch(
                        "sseed.cli.parse_group_config", return_value=(1, [(3, 5)])
                    ):
                        with patch(
                            "sseed.cli.create_slip39_shards",
                            return_value=["shard1", "shard2", "shard3"],
                        ):
                            with patch(
                                "sseed.cli.write_shards_to_separate_files",
                                side_effect=FileError("Write failed"),
                            ):
                                result = handle_shard_command(args)
                                assert result == EXIT_USAGE_ERROR

    def test_shard_single_file_write_error(self):
        """Test shard command when single file writing fails."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = "shards.txt"
        args.separate = False

        with patch("sseed.cli.validate_group_threshold"):
            with patch("sseed.cli.read_from_stdin", return_value="valid mnemonic"):
                with patch("sseed.cli.validate_mnemonic_checksum", return_value=True):
                    with patch(
                        "sseed.cli.parse_group_config", return_value=(1, [(3, 5)])
                    ):
                        with patch(
                            "sseed.cli.create_slip39_shards",
                            return_value=["shard1", "shard2", "shard3"],
                        ):
                            with patch(
                                "sseed.cli.write_shards_to_file",
                                side_effect=FileError("Write failed"),
                            ):
                                result = handle_shard_command(args)
                                assert result == EXIT_USAGE_ERROR

    def test_shard_unexpected_error(self):
        """Test shard command handling unexpected exceptions."""
        args = mock.MagicMock()
        args.group = "3-of-5"
        args.input = None
        args.output = None
        args.separate = False

        with patch("sseed.cli.validate_group_threshold"):
            with patch(
                "sseed.cli.read_from_stdin",
                side_effect=RuntimeError("Unexpected error"),
            ):
                result = handle_shard_command(args)
                assert result == EXIT_CRYPTO_ERROR

    # ===== RESTORE COMMAND ERROR TESTS =====

    def test_restore_file_read_error(self):
        """Test restore command when shard file reading fails."""
        args = mock.MagicMock()
        args.shards = ["shard1.txt", "shard2.txt"]
        args.output = None

        with patch(
            "sseed.cli.read_shards_from_files",
            side_effect=FileError("File read failed"),
        ):
            result = handle_restore_command(args)
            assert result == EXIT_USAGE_ERROR

    def test_restore_shard_integrity_error(self):
        """Test restore command when shard integrity validation fails."""
        args = mock.MagicMock()
        args.shards = ["shard1.txt", "shard2.txt"]
        args.output = None

        with patch(
            "sseed.cli.read_shards_from_files", return_value=["shard1", "shard2"]
        ):
            with patch(
                "sseed.cli.validate_shard_integrity",
                side_effect=ValidationError("Integrity failed"),
            ):
                result = handle_restore_command(args)
                assert result == EXIT_USAGE_ERROR

    def test_restore_reconstruction_error(self):
        """Test restore command when mnemonic reconstruction fails."""
        args = mock.MagicMock()
        args.shards = ["shard1.txt", "shard2.txt"]
        args.output = None

        with patch(
            "sseed.cli.read_shards_from_files", return_value=["shard1", "shard2"]
        ):
            with patch("sseed.cli.validate_shard_integrity"):
                with patch(
                    "sseed.cli.reconstruct_mnemonic_from_shards",
                    side_effect=ShardError("Reconstruction failed"),
                ):
                    result = handle_restore_command(args)
                    assert result == EXIT_CRYPTO_ERROR

    def test_restore_checksum_validation_failure(self):
        """Test restore command when reconstructed mnemonic fails checksum validation."""
        args = mock.MagicMock()
        args.shards = ["shard1.txt", "shard2.txt"]
        args.output = None

        with patch(
            "sseed.cli.read_shards_from_files", return_value=["shard1", "shard2"]
        ):
            with patch("sseed.cli.validate_shard_integrity"):
                with patch(
                    "sseed.cli.reconstruct_mnemonic_from_shards",
                    return_value="invalid mnemonic",
                ):
                    with patch(
                        "sseed.cli.validate_mnemonic_checksum", return_value=False
                    ):
                        result = handle_restore_command(args)
                        assert result == EXIT_CRYPTO_ERROR

    def test_restore_file_write_error(self):
        """Test restore command when output file writing fails."""
        args = mock.MagicMock()
        args.shards = ["shard1.txt", "shard2.txt"]
        args.output = "/invalid/path/restored.txt"

        with patch(
            "sseed.cli.read_shards_from_files", return_value=["shard1", "shard2"]
        ):
            with patch("sseed.cli.validate_shard_integrity"):
                with patch(
                    "sseed.cli.reconstruct_mnemonic_from_shards",
                    return_value="valid mnemonic",
                ):
                    with patch(
                        "sseed.cli.validate_mnemonic_checksum", return_value=True
                    ):
                        with patch(
                            "sseed.cli.write_mnemonic_to_file",
                            side_effect=FileError("Write failed"),
                        ):
                            result = handle_restore_command(args)
                            assert result == EXIT_USAGE_ERROR

    def test_restore_unexpected_error(self):
        """Test restore command handling unexpected exceptions."""
        args = mock.MagicMock()
        args.shards = ["shard1.txt", "shard2.txt"]
        args.output = None

        with patch(
            "sseed.cli.read_shards_from_files",
            side_effect=RuntimeError("Unexpected error"),
        ):
            result = handle_restore_command(args)
            assert result == EXIT_CRYPTO_ERROR

    # ===== MAIN FUNCTION ERROR TESTS =====

    def test_main_argparse_system_exit(self):
        """Test main function handling argparse SystemExit."""
        with patch("sseed.cli.create_parser") as mock_parser:
            mock_parser.return_value.parse_args.side_effect = SystemExit(1)
            result = main(["invalid", "args"])
            assert result == EXIT_USAGE_ERROR

    def test_main_argparse_success_exit(self):
        """Test main function handling argparse SystemExit with code 0."""
        with patch("sseed.cli.create_parser") as mock_parser:
            mock_parser.return_value.parse_args.side_effect = SystemExit(0)
            result = main(["--help"])
            assert result == EXIT_SUCCESS

    # ===== INTEGRATION ERROR TESTS =====

    def test_cli_subprocess_invalid_command(self):
        """Test CLI subprocess with invalid command."""
        result = subprocess.run(
            ["python", "-m", "sseed", "invalid_command"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == EXIT_USAGE_ERROR

    def test_cli_subprocess_invalid_arguments(self):
        """Test CLI subprocess with invalid arguments."""
        result = subprocess.run(
            ["python", "-m", "sseed", "gen", "--invalid-flag"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == EXIT_USAGE_ERROR

    def test_cli_subprocess_missing_required_args(self):
        """Test CLI subprocess with missing required arguments."""
        result = subprocess.run(
            ["python", "-m", "sseed", "restore"],  # Missing shard files
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == EXIT_USAGE_ERROR

    def test_cli_subprocess_file_permission_error(self):
        """Test CLI subprocess with file permission errors."""
        # Create a read-only directory
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "sseed",
                    "gen",
                    "-o",
                    str(readonly_dir / "output.txt"),
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            assert result.returncode in [EXIT_USAGE_ERROR, EXIT_CRYPTO_ERROR]
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_cli_subprocess_nonexistent_input_file(self):
        """Test CLI subprocess with nonexistent input file."""
        result = subprocess.run(
            ["python", "-m", "sseed", "shard", "-i", "nonexistent_file.txt"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == EXIT_USAGE_ERROR
        assert "Error:" in result.stderr

    def test_cli_subprocess_invalid_shard_files(self):
        """Test CLI subprocess with invalid shard files."""
        # Create invalid shard files
        invalid_shard1 = self.temp_dir / "invalid1.txt"
        invalid_shard2 = self.temp_dir / "invalid2.txt"

        invalid_shard1.write_text("invalid shard content")
        invalid_shard2.write_text("another invalid shard")

        result = subprocess.run(
            [
                "python",
                "-m",
                "sseed",
                "restore",
                str(invalid_shard1),
                str(invalid_shard2),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == EXIT_USAGE_ERROR  # Shard validation is usage error
