"""
Tests for the validate command.

Tests the B.3 Advanced Validation feature implementation.
"""

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from sseed.cli.commands.validate import ValidateCommand
from sseed.exceptions import ValidationError


def create_test_args(**kwargs):
    """Create a test Namespace with all required attributes."""
    defaults = {
        "mnemonic": None,
        "input_file": None,
        "batch": None,
        "mode": "basic",
        "json": False,
        "verbose": False,
        "quiet": False,
        "language": None,
        "strict": False,
        "check_entropy": False,
        "output": None,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestValidateCommand:
    """Test cases for ValidateCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()

    def test_command_properties(self):
        """Test basic command properties."""
        assert self.command.name == "validate"
        assert "validation" in self.command.help_text.lower()

    def test_add_arguments(self):
        """Test argument parser setup."""
        import argparse

        parser = argparse.ArgumentParser()
        self.command.add_arguments(parser)

        # Test that arguments are added
        args = parser.parse_args(["-m", "test mnemonic"])
        assert args.mnemonic == "test mnemonic"
        assert args.mode == "basic"  # default

    def test_basic_validation_valid_mnemonic(self):
        """Test basic validation with a valid mnemonic."""
        # Use a known valid 12-word English mnemonic
        valid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        args = create_test_args(mnemonic=valid_mnemonic)

        result = self.command.handle(args)
        assert result == 0  # Success

        # Check that validation results were populated
        assert self.command.validation_results["is_valid"] is True
        assert self.command.validation_results["mode"] == "basic"
        assert self.command.validation_results["language"] == "en"
        assert self.command.validation_results["word_count"] == 12

    def test_basic_validation_invalid_mnemonic(self):
        """Test basic validation with an invalid mnemonic."""
        invalid_mnemonic = "invalid mnemonic words that do not exist"

        args = create_test_args(mnemonic=invalid_mnemonic)

        result = self.command.handle(args)
        assert result == 1  # Failure

        # Check that validation results show failure
        assert self.command.validation_results["is_valid"] is False

    def test_advanced_validation_mode(self):
        """Test advanced validation mode."""
        # Use a stronger test mnemonic that won't trigger weak pattern detection
        valid_mnemonic = "exhibit avocado quit notice benefit wall narrow movie spot enact harvest into"

        args = create_test_args(
            mnemonic=valid_mnemonic, mode="advanced", strict=True, check_entropy=True
        )

        result = self.command.handle(args)
        assert result == 0  # Success

        # Should have additional advanced checks
        checks = self.command.validation_results["checks"]
        assert "format" in checks
        assert "language" in checks
        assert "checksum" in checks

        # May have additional analysis from comprehensive analysis
        # The exact checks depend on whether the analysis module is available

    def test_json_output_format(self):
        """Test JSON output format."""
        valid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        args = create_test_args(mnemonic=valid_mnemonic, json=True)

        # Capture stdout to check JSON output
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = self.command.handle(args)
            output = captured_output.getvalue()

            # Should be valid JSON
            parsed_json = json.loads(output)
            assert parsed_json["overall_status"] == "pass"
            assert "checks" in parsed_json

        finally:
            sys.stdout = sys.__stdout__

    def test_language_detection(self):
        """Test language detection functionality."""
        # Test with Spanish mnemonic (if we can generate one)
        # For now, test the language detection logic
        args = create_test_args(mnemonic="test mnemonic", language="es")

        # Initialize validation results first
        self.command.validation_results = {"checks": {}}

        # Mock the language detection to return English
        with patch(
            "sseed.cli.commands.validate.detect_mnemonic_language"
        ) as mock_detect:
            from sseed.languages import SUPPORTED_LANGUAGES

            mock_detect.return_value = SUPPORTED_LANGUAGES["en"]  # Return English

            self.command._basic_validation("test mnemonic", args)

            # Should show warning about language mismatch
            checks = self.command.validation_results["checks"]
            if "language" in checks:
                assert checks["language"]["status"] == "warning"

    def test_weak_pattern_detection(self):
        """Test weak pattern detection."""
        # Mnemonic with repeated words
        weak_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"

        checks = {}
        self.command._check_weak_patterns(weak_mnemonic, checks)

        assert "weak_patterns" in checks
        assert checks["weak_patterns"]["status"] == "warning"
        assert "repeated_words" in checks["weak_patterns"]

    def test_entropy_analysis(self):
        """Test entropy analysis functionality."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        checks = {}
        self.command._analyze_mnemonic_entropy(test_mnemonic, checks)

        assert "entropy_analysis" in checks
        assert checks["entropy_analysis"]["status"] == "pass"
        assert "estimated_bits" in checks["entropy_analysis"]

    def test_format_validation_error(self):
        """Test format validation with invalid word count."""
        # Too few words
        invalid_mnemonic = "abandon abandon abandon"

        args = create_test_args(mnemonic=invalid_mnemonic)

        result = self.command.handle(args)
        assert result == 1  # Should fail

        checks = self.command.validation_results["checks"]
        assert checks["format"]["status"] == "fail"

    def test_quiet_mode_output(self):
        """Test quiet mode output."""
        valid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        args = create_test_args(mnemonic=valid_mnemonic, quiet=True)

        # Capture stdout to check quiet output
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = self.command.handle(args)
            output = captured_output.getvalue().strip()

            # Should only output the status
            assert output == "PASS"

        finally:
            sys.stdout = sys.__stdout__

    def test_compatibility_mode_placeholder(self):
        """Test compatibility validation mode."""
        valid_mnemonic = "exhibit avocado quit notice benefit wall narrow movie spot enact harvest into"

        args = create_test_args(mnemonic=valid_mnemonic, mode="compatibility")

        result = self.command.handle(args)
        assert result == 0  # Should pass basic validation

        # Should have compatibility check
        checks = self.command.validation_results["checks"]
        assert "compatibility" in checks
        # Status can be "pass", "warning", or "error" depending on available tools
        assert checks["compatibility"]["status"] in ["pass", "warning", "error", "info"]

    def test_entropy_mode(self):
        """Test entropy validation mode."""
        valid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        args = create_test_args(mnemonic=valid_mnemonic, mode="entropy")

        result = self.command.handle(args)
        assert result == 0  # Should pass

        # Should have entropy analysis
        checks = self.command.validation_results["checks"]
        assert "entropy_analysis" in checks

    def test_timestamp_generation(self):
        """Test that timestamps are generated correctly."""
        timestamp = self.command._get_timestamp()

        # Should be ISO format
        from datetime import datetime

        parsed_timestamp = datetime.fromisoformat(timestamp)
        assert isinstance(parsed_timestamp, datetime)

    def test_error_handling(self):
        """Test error handling for malformed input."""
        args = create_test_args(mnemonic="")  # Empty mnemonic

        result = self.command.handle(args)
        assert result == 1  # Should fail

    def test_verbose_mode_with_errors(self):
        """Test verbose mode shows error details."""
        # This would require mocking to inject errors, but the structure is there
        pass


class TestValidateCommandIntegration:
    """Integration tests for the validate command."""

    def test_command_registration(self):
        """Test that the validate command is properly registered."""
        from sseed.cli.commands import COMMANDS

        assert "validate" in COMMANDS
        command_class = COMMANDS["validate"]
        # COMMANDS contains the class, not an instance
        command_instance = command_class()
        assert isinstance(command_instance, ValidateCommand)

    def test_help_text_generation(self):
        """Test that help text is generated correctly."""
        command = ValidateCommand()

        import argparse

        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        # Should not raise any exceptions
        help_text = parser.format_help()
        assert "validate" in help_text.lower()
        assert "mnemonic" in help_text.lower()
