"""Integration tests for sseed CLI commands.

Tests the complete CLI interface functionality as specified in Phase 7
requirement 32: Add integration tests for CLI commands.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def run_sseed_command(self, args: list, input_data: str = None) -> tuple[int, str, str]:
        """Run sseed command and return exit code, stdout, stderr."""
        cmd = ["python", "-m", "sseed"] + args
        result = subprocess.run(
            cmd,
            input=input_data,
            text=True,
            capture_output=True,
            cwd=Path(__file__).parent.parent,  # Run from project root
        )
        return result.returncode, result.stdout, result.stderr

    def test_gen_command_success(self):
        """Test gen command executes successfully."""
        exit_code, stdout, stderr = self.run_sseed_command(["gen"])
        assert exit_code == 0
        # Should have some output containing words
        assert len(stdout) > 100  # Should have substantial output

    def test_gen_command_to_file_success(self):
        """Test gen command with file output."""
        output_file = self.temp_dir / "test_mnemonic.txt"
        exit_code, stdout, stderr = self.run_sseed_command(["gen", "-o", str(output_file)])

        assert exit_code == 0
        assert output_file.exists()

        # Read and verify mnemonic file
        with open(output_file, "r") as f:
            content = f.read()

        # Should have mnemonic content
        assert len(content) > 50
        # Should have exactly one line with 24 words (excluding comments)
        mnemonic_lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ]
        assert len(mnemonic_lines) == 1
        assert len(mnemonic_lines[0].split()) == 24

    def test_round_trip_integration(self):
        """Test complete round-trip: gen -> shard -> restore."""
        # Step 1: Generate mnemonic to file
        mnemonic_file = self.temp_dir / "original.txt"
        exit_code, _, _ = self.run_sseed_command(["gen", "-o", str(mnemonic_file)])
        assert exit_code == 0

        # Read original mnemonic
        with open(mnemonic_file, "r") as f:
            content = f.read()
        original_mnemonic = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ][0]

        # Step 2: Shard mnemonic to separate files
        exit_code, _, _ = self.run_sseed_command(
            [
                "shard",
                "--separate",
                "-i",
                str(mnemonic_file),
                "-o",
                str(self.temp_dir / "shards.txt"),
            ]
        )
        assert exit_code == 0

        # Verify shard files exist
        shard_files = [self.temp_dir / f"shards_{i:02d}.txt" for i in range(1, 6)]
        for shard_file in shard_files:
            assert shard_file.exists()

        # Step 3: Restore from threshold number of shards (3 out of 5)
        restore_files = [str(f) for f in shard_files[:3]]
        exit_code, stdout, stderr = self.run_sseed_command(["restore"] + restore_files)
        assert exit_code == 0

        # Extract restored mnemonic from output
        lines = stdout.strip().split("\n")
        restored_mnemonic = None
        for line in lines:
            words = line.strip().split()
            if len(words) == 24:
                restored_mnemonic = line.strip()
                break

        assert restored_mnemonic is not None
        assert restored_mnemonic == original_mnemonic

    def test_shard_command_different_groups(self):
        """Test shard command with different group configurations."""
        # Generate a test mnemonic
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        self.run_sseed_command(["gen", "-o", str(mnemonic_file)])

        # Test 2-of-3 configuration
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "shard",
                "-g",
                "2-of-3",
                "-i",
                str(mnemonic_file),
                "-o",
                str(self.temp_dir / "shards_2of3.txt"),
            ]
        )
        assert exit_code == 0

        # Check that output file was created
        shards_file = self.temp_dir / "shards_2of3.txt"
        assert shards_file.exists()

        # Should contain 3 shards
        with open(shards_file, "r") as f:
            content = f.read()

        # Count shard references in comments
        shard_count = content.count("# Shard")
        assert shard_count == 3

    def test_error_handling_invalid_threshold(self):
        """Test CLI error handling with invalid threshold."""
        exit_code, stdout, stderr = self.run_sseed_command(["shard", "-g", "5-of-3"])
        assert exit_code == 1  # Usage error
        assert "Invalid group configuration" in stderr

    def test_error_handling_nonexistent_file(self):
        """Test CLI error handling with nonexistent input file."""
        exit_code, stdout, stderr = self.run_sseed_command(["shard", "-i", "nonexistent_file.txt"])
        assert exit_code == 3  # File I/O error (improved exit codes)
        assert "File error:" in stderr

    def test_help_commands(self):
        """Test help functionality for all commands."""
        # Test main help
        exit_code, stdout, stderr = self.run_sseed_command(["--help"])
        assert exit_code == 0
        assert "usage:" in stdout
        assert "gen" in stdout
        assert "shard" in stdout
        assert "restore" in stdout

        # Test command-specific help
        for cmd in ["gen", "shard", "restore"]:
            exit_code, stdout, stderr = self.run_sseed_command([cmd, "--help"])
            assert exit_code == 0
            assert "usage:" in stdout

    def test_separate_files_feature(self):
        """Test the separate files feature specifically."""
        # Generate mnemonic
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        self.run_sseed_command(["gen", "-o", str(mnemonic_file)])

        # Shard with separate files
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "shard",
                "--separate",
                "-i",
                str(mnemonic_file),
                "-o",
                str(self.temp_dir / "shards.txt"),
            ]
        )

        assert exit_code == 0
        assert "separate files" in stdout

        # Verify all 5 shard files exist and have correct format
        for i in range(1, 6):
            shard_file = self.temp_dir / f"shards_{i:02d}.txt"
            assert shard_file.exists()

            with open(shard_file, "r") as f:
                content = f.read()

            # Should have proper comment header
            assert "# SLIP-39 Shard File" in content
            assert f"# Shard {i} of 5" in content
            assert "# File format: Plain text UTF-8" in content

            # Should have exactly one shard line (not comment)
            shard_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]
            assert len(shard_lines) == 1
            assert len(shard_lines[0].split()) >= 20  # SLIP-39 shards are long

    def test_performance_basic(self):
        """Test basic performance of CLI commands."""
        import time

        # Test gen command
        start_time = time.time()
        exit_code, stdout, stderr = self.run_sseed_command(["gen"])
        gen_duration = time.time() - start_time

        assert exit_code == 0
        print(f"Gen command took {gen_duration*1000:.1f}ms (including subprocess overhead)")

        # Performance should be reasonable (allowing for subprocess overhead)
        assert gen_duration < 5.0  # Should complete within 5 seconds

    def test_file_formats_compatibility(self):
        """Test that file formats are properly handled across commands."""
        # Generate with comments
        mnemonic_file = self.temp_dir / "mnemonic_with_comments.txt"
        self.run_sseed_command(["gen", "-o", str(mnemonic_file)])

        # Should be able to read the file and shard it
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "shard",
                "-i",
                str(mnemonic_file),
                "-o",
                str(self.temp_dir / "test_shards.txt"),
            ]
        )
        assert exit_code == 0

        # Shards file should exist and have proper format
        shards_file = self.temp_dir / "test_shards.txt"
        assert shards_file.exists()

        with open(shards_file, "r") as f:
            content = f.read()

        assert "# SLIP-39 Shards File" in content
        assert "UTF-8" in content
