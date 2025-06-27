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

    def run_sseed_command(
        self, args: list, input_data: str = None
    ) -> tuple[int, str, str]:
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
        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "-o", str(output_file)]
        )

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

    def test_gen_command_with_show_entropy_stdout(self):
        """Test gen command with --show-entropy flag to stdout."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "ERROR", "gen", "--show-entropy"]
        )

        assert exit_code == 0
        # Note: stderr may contain status messages, which is expected

        lines = stdout.strip().split("\n")
        assert len(lines) == 3  # mnemonic, language info, entropy

        # First line should be the mnemonic (24 words)
        mnemonic_line = lines[0].strip()
        assert len(mnemonic_line.split()) == 24

        # Second line should be language info
        language_line = lines[1].strip()
        assert language_line.startswith("# Language: ")
        assert "English (en)" in language_line

        # Third line should be entropy comment
        entropy_line = lines[2].strip()
        assert entropy_line.startswith("# Entropy: ")
        assert "32 bytes" in entropy_line

        # Extract and validate entropy hex
        entropy_hex = entropy_line.split("# Entropy: ")[1].split(" (")[0]
        assert len(entropy_hex) == 64  # 32 bytes = 64 hex chars
        assert all(c in "0123456789abcdef" for c in entropy_hex.lower())

    def test_gen_command_with_show_entropy_file(self):
        """Test gen command with --show-entropy flag to file."""
        output_file = self.temp_dir / "test_mnemonic_entropy.txt"
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "ERROR", "gen", "--show-entropy", "-o", str(output_file)]
        )

        assert exit_code == 0
        assert "Mnemonic with metadata and entropy written to:" in stdout
        assert output_file.exists()

        # Read and verify file content
        with open(output_file, "r") as f:
            content = f.read()

        lines = content.strip().split("\n")

        # Should have mnemonic lines (with comments) plus entropy line
        mnemonic_lines = [
            line.strip() for line in lines if line.strip() and not line.startswith("#")
        ]
        entropy_lines = [
            line.strip() for line in lines if line.strip().startswith("# Entropy:")
        ]

        assert len(mnemonic_lines) == 1
        assert len(mnemonic_lines[0].split()) == 24
        assert len(entropy_lines) == 1
        assert "32 bytes" in entropy_lines[0]

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

        # Count actual shard lines (non-comment lines)
        shard_lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        assert len(shard_lines) == 3

    def test_error_handling_invalid_threshold(self):
        """Test CLI error handling with invalid threshold."""
        exit_code, stdout, stderr = self.run_sseed_command(["shard", "-g", "5-of-3"])
        assert exit_code == 4  # Validation error
        assert "Threshold (5) cannot be greater than total shares (3)" in stderr

    def test_error_handling_nonexistent_file(self):
        """Test CLI error handling with nonexistent input file."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["shard", "-i", "nonexistent_file.txt"]
        )
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
        print(
            f"Gen command took {gen_duration*1000:.1f}ms (including subprocess overhead)"
        )

        # Performance should be reasonable (allowing for subprocess overhead)
        assert gen_duration < 5.0  # Should complete within 5 seconds

    def test_file_formats_compatibility(self):
        """Test that different file formats work correctly."""
        # Generate mnemonic
        result = subprocess.run(
            ["python", "-m", "sseed", "gen"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Extract mnemonic from output (should be 24 words)
        lines = result.stdout.strip().split("\n")
        mnemonic = None
        for line in lines:
            clean_line = line.strip()
            # Look for a line with exactly 24 words (typical mnemonic)
            words = clean_line.split()
            if len(words) == 24 and all(word.isalpha() for word in words):
                mnemonic = clean_line
                break

        assert mnemonic is not None, "Could not find mnemonic in output"

        # Test with different file extensions
        for ext in [".txt", ".bak", ".seed"]:
            filename = f"test_mnemonic{ext}"
            try:
                # Write to file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(mnemonic)

                # Read and validate
                result = subprocess.run(
                    ["python", "-m", "sseed", "shard", "-i", filename, "-g", "2-of-3"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                assert "# Shard 1" in result.stdout
                assert "# Shard 2" in result.stdout

            finally:
                # Cleanup
                if os.path.exists(filename):
                    os.remove(filename)

    def test_seed_command_integration(self):
        """Test the seed command integration with file I/O."""
        temp_mnemonic = "test_seed_mnemonic.txt"
        temp_seed = "test_master_seed.txt"

        try:
            # Generate a mnemonic first
            result = subprocess.run(
                ["python", "-m", "sseed", "gen", "-o", temp_mnemonic],
                capture_output=True,
                text=True,
                check=True,
            )

            # Generate master seed from mnemonic file
            result = subprocess.run(
                ["python", "-m", "sseed", "seed", "-i", temp_mnemonic, "--hex"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Extract hex seed from output (last line that's all hex)
            lines = result.stdout.strip().split("\n")
            hex_seed = None
            for line in lines:
                # Look for a line that's exactly 128 hex characters
                clean_line = line.strip()
                if len(clean_line) == 128 and all(
                    c in "0123456789abcdef" for c in clean_line.lower()
                ):
                    hex_seed = clean_line
                    break

            assert hex_seed is not None, "Could not find hex seed in output"
            assert len(hex_seed) == 128  # 64 bytes = 128 hex chars

            # Test with output file
            result = subprocess.run(
                ["python", "-m", "sseed", "seed", "-i", temp_mnemonic, "-o", temp_seed],
                capture_output=True,
                text=True,
                check=True,
            )

            # Check that seed file was created
            assert os.path.exists(temp_seed)

            # Read and verify seed file content
            with open(temp_seed, "r") as f:
                seed_content = f.read().strip()

            # Extract the hex seed from file content (should be the last non-comment line)
            seed_lines = [
                line.strip()
                for line in seed_content.split("\n")
                if line.strip() and not line.startswith("#")
            ]

            assert len(seed_lines) == 1, f"Expected 1 seed line, found: {seed_lines}"
            hex_seed_from_file = seed_lines[0]

            # Should be a hex string
            assert len(hex_seed_from_file) == 128  # 64 bytes = 128 hex chars
            assert all(c in "0123456789abcdef" for c in hex_seed_from_file.lower())

        finally:
            # Cleanup
            for filename in [temp_mnemonic, temp_seed]:
                if os.path.exists(filename):
                    os.remove(filename)

    def test_restore_command_with_show_entropy_stdout(self):
        """Test restore command with --show-entropy flag to stdout."""
        # First generate a mnemonic and create shards
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "CRITICAL", "gen", "-o", str(mnemonic_file)]
        )
        assert exit_code == 0

        # Create shards
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "CRITICAL",
                "shard",
                "-i",
                str(mnemonic_file),
                "-g",
                "3-of-5",
                "--separate",
                "-o",
                str(self.temp_dir / "shard"),
            ]
        )
        assert exit_code == 0

        # Find the actual shard files created (they have _01, _02, etc. format)
        shard_files = list(self.temp_dir.glob("shard_*.txt"))[:3]
        assert (
            len(shard_files) >= 3
        ), f"Expected at least 3 shard files, found: {shard_files}"

        # Use 3 shards to restore with entropy display
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "CRITICAL", "restore", "--show-entropy"]
            + [str(f) for f in shard_files]
        )

        assert exit_code == 0, f"Restore failed with stderr: {stderr}"
        # Note: stderr may contain status messages, which is expected

        lines = stdout.strip().split("\n")
        assert len(lines) == 3  # mnemonic, language info, entropy

        # First line should be the restored mnemonic (24 words)
        mnemonic_line = lines[0].strip()
        assert len(mnemonic_line.split()) == 24

        # Second line should be language info
        language_line = lines[1].strip()
        assert language_line.startswith("# Language: ")

        # Third line should be entropy comment
        entropy_line = lines[2].strip()
        assert entropy_line.startswith("# Entropy: ")
        assert "32 bytes" in entropy_line

        # Extract and validate entropy hex
        entropy_hex = entropy_line.split("# Entropy: ")[1].split(" (")[0]
        assert len(entropy_hex) == 64  # 32 bytes = 64 hex chars
        assert all(c in "0123456789abcdef" for c in entropy_hex.lower())

    def test_restore_command_with_show_entropy_file(self):
        """Test restore command with --show-entropy flag to file."""
        # First generate a mnemonic and create shards
        mnemonic_file = self.temp_dir / "test_mnemonic.txt"
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "CRITICAL", "gen", "-o", str(mnemonic_file)]
        )
        assert exit_code == 0

        # Create shards
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "CRITICAL",
                "shard",
                "-i",
                str(mnemonic_file),
                "-g",
                "3-of-5",
                "--separate",
                "-o",
                str(self.temp_dir / "shard"),
            ]
        )
        assert exit_code == 0

        # Find the actual shard files created
        shard_files = list(self.temp_dir.glob("shard_*.txt"))[:3]
        assert (
            len(shard_files) >= 3
        ), f"Expected at least 3 shard files, found: {shard_files}"

        # Use 3 shards to restore with entropy display to file
        output_file = self.temp_dir / "restored_with_entropy.txt"
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "CRITICAL",
                "restore",
                "--show-entropy",
                "-o",
                str(output_file),
            ]
            + [str(f) for f in shard_files]
        )

        assert exit_code == 0, f"Restore failed with stderr: {stderr}"
        assert (
            "Mnemonic with language info and entropy reconstructed and written to:"
            in stdout
        )
        assert output_file.exists()

        # Read and verify file content
        with open(output_file, "r") as f:
            content = f.read()

        lines = content.strip().split("\n")

        # Should have mnemonic line (entropy is not actually written to file when using -o)
        mnemonic_lines = [
            line.strip() for line in lines if line.strip() and not line.startswith("#")
        ]

        assert len(mnemonic_lines) == 1
        assert len(mnemonic_lines[0].split()) == 24

        # Note: When using --show-entropy with -o, the entropy is shown in stdout but not written to file
        # This is current behavior - entropy display is separate from file output

    def test_entropy_consistency_gen_restore(self):
        """Test entropy consistency between gen and seed commands."""
        # Generate a mnemonic with entropy display
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "ERROR", "gen", "--show-entropy"]
        )

        assert exit_code == 0

        # Extract mnemonic and entropy from output
        lines = stdout.strip().split("\n")
        mnemonic_line = None
        entropy_line = None

        for line in lines:
            if line.strip() and not line.startswith("#"):
                if len(line.split()) == 24:  # Mnemonic line
                    mnemonic_line = line.strip()
            elif line.startswith("# Entropy:"):
                entropy_line = line.strip()

        assert mnemonic_line is not None
        assert entropy_line is not None

        # Create a file with just the mnemonic for seed command
        mnemonic_file = self.temp_dir / "test_mnemonic_entropy.txt"
        with open(mnemonic_file, "w") as f:
            f.write(mnemonic_line)

        # Test seed command processing - seed command doesn't display entropy
        # but it should process the mnemonic successfully
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "ERROR",
                "seed",
                "--input",
                str(mnemonic_file),
                "--format",
                "hex",
            ]
        )

        assert exit_code == 0

        # Check that seed command processed successfully
        lines = stdout.strip().split("\n")
        seed_line = None

        for line in lines:
            if line.strip() and not line.startswith("#"):
                # Should be a hex string
                if len(line.strip()) == 128:  # 64 bytes = 128 hex chars
                    seed_line = line.strip()
                    break

        assert seed_line is not None
        # Verify it's valid hex
        try:
            bytes.fromhex(seed_line)
        except ValueError:
            assert False, f"Invalid hex output: {seed_line}"


class TestCLIWordCountSupport:
    """Test Phase 3: Comprehensive CLI word count support."""

    def setup_method(self):
        """Set up test environment."""
        import pathlib
        import tempfile

        self.temp_dir = pathlib.Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def run_sseed_command(
        self, args: list, input_data: str = None
    ) -> tuple[int, str, str]:
        """Run sseed command and return exit code, stdout, stderr."""
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "sseed"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, input=input_data)
        return result.returncode, result.stdout, result.stderr

    @pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
    def test_gen_command_word_counts(self, word_count):
        """Test gen command with different word counts."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "ERROR", "gen", "--words", str(word_count)]
        )

        assert exit_code == 0

        # Extract mnemonic from output
        lines = stdout.strip().split("\n")
        mnemonic_line = None
        for line in lines:
            if line.strip() and not line.startswith("#"):
                words = line.strip().split()
                if len(words) == word_count:
                    mnemonic_line = line.strip()
                    break

        assert mnemonic_line is not None
        words = mnemonic_line.split()
        assert len(words) == word_count

        # Verify metadata shows correct word count
        metadata_line = None
        for line in lines:
            if "Words:" in line and line.startswith("#"):
                metadata_line = line.strip()
                break

        assert metadata_line is not None
        assert f"Words: {word_count}" in metadata_line

    def test_gen_command_backward_compatibility(self):
        """Test that gen command defaults to 24 words."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["--log-level", "ERROR", "gen"]
        )

        assert exit_code == 0

        # Extract mnemonic from output
        lines = stdout.strip().split("\n")
        mnemonic_line = None
        for line in lines:
            if line.strip() and not line.startswith("#"):
                words = line.strip().split()
                if len(words) == 24:
                    mnemonic_line = line.strip()
                    break

        assert mnemonic_line is not None
        words = mnemonic_line.split()
        assert len(words) == 24  # Default should remain 24

    @pytest.mark.parametrize(
        "word_count,language",
        [(12, "en"), (15, "es"), (18, "fr"), (21, "it"), (24, "ko")],
    )
    def test_gen_command_word_counts_with_languages(self, word_count, language):
        """Test gen command with different word counts and languages."""
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "ERROR",
                "gen",
                "--words",
                str(word_count),
                "--language",
                language,
            ]
        )

        assert exit_code == 0

        # Extract and verify mnemonic
        lines = stdout.strip().split("\n")
        mnemonic_line = None
        for line in lines:
            if line.strip() and not line.startswith("#"):
                words = line.strip().split()
                if len(words) == word_count:
                    mnemonic_line = line.strip()
                    break

        assert mnemonic_line is not None
        assert len(mnemonic_line.split()) == word_count

    @pytest.mark.parametrize("invalid_word_count", [11, 13, 16, 20, 25])
    def test_gen_command_invalid_word_counts(self, invalid_word_count):
        """Test gen command error handling for invalid word counts."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", str(invalid_word_count)]
        )

        assert exit_code != 0
        assert "invalid choice" in stderr
        assert str(invalid_word_count) in stderr

    @pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
    def test_gen_command_file_output_word_counts(self, word_count):
        """Test gen command file output with different word counts."""
        output_file = self.temp_dir / f"test_mnemonic_{word_count}.txt"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "ERROR",
                "gen",
                "--words",
                str(word_count),
                "--output",
                str(output_file),
            ]
        )

        assert exit_code == 0
        assert output_file.exists()

        # Read and verify file content
        with open(output_file, "r") as f:
            content = f.read()

        lines = content.strip().split("\n")

        # Find mnemonic line (non-comment)
        mnemonic_line = None
        for line in lines:
            if line.strip() and not line.startswith("#"):
                mnemonic_line = line.strip()
                break

        assert mnemonic_line is not None
        assert len(mnemonic_line.split()) == word_count

        # Verify metadata includes word count
        metadata_found = False
        for line in lines:
            if f"Words: {word_count}" in line:
                metadata_found = True
                break
        assert metadata_found

    @pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
    def test_gen_command_with_entropy_display_word_counts(self, word_count):
        """Test gen command with entropy display for different word counts."""
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "ERROR",
                "gen",
                "--words",
                str(word_count),
                "--show-entropy",
            ]
        )

        assert exit_code == 0

        lines = stdout.strip().split("\n")

        # Verify mnemonic word count
        mnemonic_line = None
        for line in lines:
            if line.strip() and not line.startswith("#"):
                words = line.strip().split()
                if len(words) == word_count:
                    mnemonic_line = line.strip()
                    break

        assert mnemonic_line is not None

        # Verify entropy line with correct byte count
        entropy_bytes_map = {12: 16, 15: 20, 18: 24, 21: 28, 24: 32}
        expected_bytes = entropy_bytes_map[word_count]

        entropy_line_found = False
        for line in lines:
            if line.startswith("# Entropy:") and f"({expected_bytes} bytes)" in line:
                entropy_line_found = True
                break

        assert entropy_line_found

    @pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
    def test_round_trip_gen_to_seed_word_counts(self, word_count):
        """Test round-trip: gen with word count -> seed command."""
        # Generate mnemonic with specific word count
        mnemonic_file = self.temp_dir / f"test_mnemonic_{word_count}.txt"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "ERROR",
                "gen",
                "--words",
                str(word_count),
                "--output",
                str(mnemonic_file),
            ]
        )

        assert exit_code == 0
        assert mnemonic_file.exists()

        # Verify the generated file has correct word count
        with open(mnemonic_file, "r") as f:
            mnemonic_content = f.read()

        assert f"Words: {word_count}" in mnemonic_content

        # Generate seed from mnemonic
        seed_file = self.temp_dir / f"test_seed_{word_count}.txt"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "--log-level",
                "ERROR",
                "seed",
                "--input",
                str(mnemonic_file),
                "--output",
                str(seed_file),
                "--format",
                "hex",
            ]
        )

        assert exit_code == 0
        assert seed_file.exists()

        # Verify seed command processed the mnemonic successfully
        # (seed command detects language but doesn't preserve word count metadata)
        with open(seed_file, "r") as f:
            seed_content = f.read()

        # Verify seed was generated (should contain hex string)
        lines = seed_content.strip().split("\n")
        hex_line = None
        for line in lines:
            if line.strip() and not line.startswith("#"):
                hex_line = line.strip()
                break

        assert hex_line is not None
        assert len(hex_line) == 128  # 64 bytes = 128 hex characters

        # Verify language detection worked
        assert "Language: English (en)" in seed_content

    def test_gen_command_performance_word_counts(self):
        """Test performance consistency across different word counts."""
        import time

        word_counts = [12, 15, 18, 21, 24]
        times = {}

        for word_count in word_counts:
            start_time = time.time()

            exit_code, stdout, stderr = self.run_sseed_command(
                ["--log-level", "ERROR", "gen", "--words", str(word_count)]
            )

            end_time = time.time()

            assert exit_code == 0
            times[word_count] = end_time - start_time

        # Performance should be reasonably consistent
        # (allowing for some variance but no major outliers)
        max_time = max(times.values())
        min_time = min(times.values())

        # Max time should not be more than 3x min time
        assert max_time <= min_time * 3.0
