"""Comprehensive tests for custom entropy CLI functionality.

Tests the Phase 3 CLI integration of custom entropy sources including:
- Hex entropy input with quality validation
- Dice entropy input with quality validation
- Quality analysis display
- Security warnings and override flags
- Integration with existing features
"""

import subprocess
import tempfile
from pathlib import Path


class TestCustomEntropyCLI:
    """Test custom entropy CLI functionality."""

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

    def test_help_shows_custom_entropy_options(self):
        """Test that help displays custom entropy options."""
        exit_code, stdout, stderr = self.run_sseed_command(["gen", "--help"])

        assert exit_code == 0
        assert "--entropy-hex" in stdout
        assert "--entropy-dice" in stdout
        assert "--allow-weak" in stdout
        assert "--force" in stdout
        assert "--entropy-analysis" in stdout

    def test_hex_entropy_good_quality(self):
        """Test hex entropy with good quality."""
        # Use good quality hex entropy
        hex_entropy = "abcdef123456789012345678abcdef00"

        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-hex", hex_entropy, "--entropy-analysis"]
        )

        assert exit_code == 0
        assert "WARNING: Using custom hex entropy" in stdout
        assert "Quality Score: 100/100" in stdout
        assert "✅ Entropy quality acceptable" in stdout
        assert "Entropy: Custom (hex)" in stdout

    def test_hex_entropy_weak_quality_rejected(self):
        """Test that weak hex entropy is rejected without override flags."""
        # Use weak entropy (all zeros)
        hex_entropy = "00000000000000000000000000000000"

        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-hex", hex_entropy, "--entropy-analysis"]
        )

        assert exit_code == 1
        assert "SECURITY WARNING: Entropy quality insufficient" in stdout
        assert "Use --allow-weak to override" in stdout

    def test_hex_entropy_weak_quality_with_allow_weak(self):
        """Test that weak entropy still requires --force even with --allow-weak."""
        # Use weak entropy (repeating pattern)
        hex_entropy = "deadbeefdeadbeefdeadbeefdeadbeef"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "gen",
                "--words",
                "12",
                "--entropy-hex",
                hex_entropy,
                "--entropy-analysis",
                "--allow-weak",
            ]
        )

        assert exit_code == 1
        assert "Use --force to proceed despite warnings" in stdout

    def test_hex_entropy_weak_quality_with_force(self):
        """Test that weak entropy works with both --allow-weak and --force."""
        # Use weak entropy (repeating pattern)
        hex_entropy = "deadbeefdeadbeefdeadbeefdeadbeef"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "gen",
                "--words",
                "12",
                "--entropy-hex",
                hex_entropy,
                "--entropy-analysis",
                "--allow-weak",
                "--force",
            ]
        )

        assert exit_code == 0
        assert "PROCEEDING WITH WEAK ENTROPY (DANGEROUS)" in stdout
        assert "Entropy: Custom (hex)" in stdout

    def test_dice_entropy_good_quality(self):
        """Test dice entropy with sufficient rolls."""
        # Use sufficient dice rolls for 12 words (16 bytes = 128 bits)
        # Need at least 128/2.585 ≈ 50 rolls
        dice_rolls = "1,2,3,4,5,6," * 20  # 120 rolls, more than enough
        dice_rolls = dice_rolls.rstrip(",")

        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-dice", dice_rolls, "--entropy-analysis"]
        )

        assert exit_code == 0
        assert "WARNING: Using custom dice entropy" in stdout
        assert "Quality Score: 100/100" in stdout
        assert "✅ Entropy quality acceptable" in stdout
        assert "Entropy: Custom (dice)" in stdout

    def test_dice_entropy_insufficient_rolls(self):
        """Test that insufficient dice rolls are rejected."""
        # Use too few dice rolls
        dice_rolls = "1,2,3,4,5,6"  # Only 6 rolls, need ~50

        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-dice", dice_rolls]
        )

        assert exit_code == 1
        assert "Custom entropy error:" in stdout
        assert "Insufficient dice rolls" in stdout

    def test_mutually_exclusive_entropy_sources(self):
        """Test that hex and dice entropy are mutually exclusive."""
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "gen",
                "--words",
                "12",
                "--entropy-hex",
                "deadbeef",
                "--entropy-dice",
                "123456",
            ]
        )

        assert exit_code == 1  # CLI error
        assert "not allowed with argument" in stderr

    def test_custom_entropy_with_file_output(self):
        """Test custom entropy with file output."""
        hex_entropy = "abcdef123456789012345678abcdef00"
        output_file = self.temp_dir / "test_custom_entropy.txt"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "gen",
                "--words",
                "12",
                "--entropy-hex",
                hex_entropy,
                "--output",
                str(output_file),
                "--show-entropy",
            ]
        )

        assert exit_code == 0

        # Check file contents
        with open(output_file, "r") as f:
            content = f.read()

        assert "Entropy: Custom (hex)" in content
        assert hex_entropy in content
        assert "profit hunt setup hamster" in content  # Should be deterministic

    def test_custom_entropy_with_different_languages(self):
        """Test custom entropy with different languages."""
        hex_entropy = "abcdef123456789012345678abcdef00"

        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--language", "es", "--entropy-hex", hex_entropy]
        )

        assert exit_code == 0
        assert "Language: Spanish (es)" in stdout
        assert "Entropy: Custom (hex)" in stdout

    def test_entropy_analysis_detailed_output(self):
        """Test detailed entropy analysis output."""
        # Use entropy with known patterns
        hex_entropy = "deadbeefdeadbeefdeadbeefdeadbeef"

        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "gen",
                "--words",
                "12",
                "--entropy-hex",
                hex_entropy,
                "--entropy-analysis",
                "--allow-weak",
                "--force",
            ]
        )

        assert exit_code == 0
        assert "📊 Entropy Quality Analysis:" in stdout
        assert "Quality Score:" in stdout
        assert "Warnings:" in stdout
        assert "repeating" in stdout.lower()

    def test_system_entropy_still_works(self):
        """Test that system entropy generation still works normally."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--language", "en"]
        )

        assert exit_code == 0
        assert "Language: English (en), Words: 12" in stdout
        # Should NOT contain "Entropy: Custom"
        assert "Entropy: Custom" not in stdout

    def test_invalid_hex_entropy(self):
        """Test invalid hex entropy handling."""
        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-hex", "invalid_hex_string"]
        )

        assert exit_code == 1
        assert "Custom entropy error:" in stdout

    def test_invalid_dice_entropy(self):
        """Test invalid dice entropy handling."""
        exit_code, stdout, stderr = self.run_sseed_command(
            [
                "gen",
                "--words",
                "12",
                "--entropy-dice",
                "1,2,3,7,8,9",  # 7,8,9 are invalid dice values
            ]
        )

        assert exit_code == 1
        assert "Custom entropy error:" in stdout
        assert "Invalid dice value" in stdout

    def test_dice_entropy_different_formats(self):
        """Test different dice input formats."""
        # Test space-separated format
        dice_rolls = " ".join(["1", "2", "3", "4", "5", "6"] * 20)  # 120 rolls

        exit_code, stdout, stderr = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-dice", dice_rolls]
        )

        assert exit_code == 0
        assert "✅ Entropy quality acceptable" in stdout

    def test_custom_entropy_deterministic_output(self):
        """Test that same custom entropy produces same mnemonic."""
        hex_entropy = "abcdef123456789012345678abcdef00"

        # Generate mnemonic twice with same entropy
        exit_code1, stdout1, stderr1 = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-hex", hex_entropy]
        )

        exit_code2, stdout2, stderr2 = self.run_sseed_command(
            ["gen", "--words", "12", "--entropy-hex", hex_entropy]
        )

        assert exit_code1 == 0
        assert exit_code2 == 0

        # Extract mnemonic from output (line before the metadata comment)
        def extract_mnemonic(output):
            lines = output.strip().split("\n")
            for line in lines:
                if (
                    not line.startswith("#")
                    and not line.startswith("⚠️")
                    and not line.startswith("✅")
                ):
                    if " " in line and len(line.split()) >= 12:
                        return line.strip()
            return None

        mnemonic1 = extract_mnemonic(stdout1)
        mnemonic2 = extract_mnemonic(stdout2)

        assert (
            mnemonic1 == mnemonic2
        ), f"Mnemonics should be identical: '{mnemonic1}' vs '{mnemonic2}'"
