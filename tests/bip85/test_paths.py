"""Tests for BIP85 path validation and formatting utilities.

Tests covering:
- Parameter validation
- Path formatting and parsing
- Application-specific validation
- Error handling
"""

import pytest

from sseed.bip85.exceptions import Bip85ValidationError
from sseed.bip85.paths import (
    BIP39_VALID_WORD_COUNTS,
    BIP85_APPLICATIONS,
    calculate_entropy_bytes_needed,
    format_bip85_path,
    format_parameter_summary,
    get_application_name,
    parse_bip85_path,
    validate_bip85_parameters,
    validate_derivation_index_range,
)


class TestValidateBip85Parameters:
    """Test BIP85 parameter validation."""

    def test_valid_parameters(self):
        """Test validation of valid parameter combinations."""
        # BIP39 parameters
        validate_bip85_parameters(39, 12, 0)
        validate_bip85_parameters(39, 24, 1000)

        # Hex parameters
        validate_bip85_parameters(128, 32, 500)

        # Password parameters
        validate_bip85_parameters(9999, 20, 100)

    def test_invalid_application_type(self):
        """Test validation of non-integer applications."""
        with pytest.raises(Bip85ValidationError, match="Application must be integer"):
            validate_bip85_parameters("39", 12, 0)

        with pytest.raises(Bip85ValidationError, match="Application must be integer"):
            validate_bip85_parameters(39.5, 12, 0)

    def test_invalid_application_range(self):
        """Test validation of application range."""
        with pytest.raises(
            Bip85ValidationError, match="Application must be 0-4294967295"
        ):
            validate_bip85_parameters(-1, 12, 0)

        with pytest.raises(
            Bip85ValidationError, match="Application must be 0-4294967295"
        ):
            validate_bip85_parameters(2**32, 12, 0)

    def test_invalid_length_type(self):
        """Test validation of non-integer lengths."""
        with pytest.raises(Bip85ValidationError, match="Length must be integer"):
            validate_bip85_parameters(39, "12", 0)

        with pytest.raises(Bip85ValidationError, match="Length must be integer"):
            validate_bip85_parameters(39, 12.5, 0)

    def test_invalid_length_range(self):
        """Test validation of length range."""
        with pytest.raises(Bip85ValidationError, match="Length must be 0-4294967295"):
            validate_bip85_parameters(39, -1, 0)

        with pytest.raises(Bip85ValidationError, match="Length must be 0-4294967295"):
            validate_bip85_parameters(39, 2**32, 0)

    def test_invalid_index_type(self):
        """Test validation of non-integer indices."""
        with pytest.raises(Bip85ValidationError, match="Index must be integer"):
            validate_bip85_parameters(39, 12, "0")

        with pytest.raises(Bip85ValidationError, match="Index must be integer"):
            validate_bip85_parameters(39, 12, 0.5)

    def test_invalid_index_range(self):
        """Test validation of index range."""
        with pytest.raises(Bip85ValidationError, match="Index must be 0 to 2147483647"):
            validate_bip85_parameters(39, 12, -1)

        with pytest.raises(Bip85ValidationError, match="Index must be 0 to 2147483647"):
            validate_bip85_parameters(39, 12, 2**31)

    def test_bip39_word_count_validation_strict(self):
        """Test BIP39 word count validation in strict mode."""
        # Valid word counts
        for word_count in BIP39_VALID_WORD_COUNTS:
            validate_bip85_parameters(39, word_count, 0, strict=True)

        # Invalid word count
        with pytest.raises(Bip85ValidationError, match="Invalid word count for BIP39"):
            validate_bip85_parameters(39, 13, 0, strict=True)

    def test_bip39_word_count_validation_non_strict(self):
        """Test BIP39 word count validation in non-strict mode."""
        # Should allow invalid word count in non-strict mode
        validate_bip85_parameters(39, 13, 0, strict=False)

    def test_hd_seed_validation(self):
        """Test HD-Seed WIF validation."""
        validate_bip85_parameters(2, 512, 0, strict=True)

        with pytest.raises(
            Bip85ValidationError, match="HD-Seed WIF length must be 512"
        ):
            validate_bip85_parameters(2, 256, 0, strict=True)

    def test_xprv_validation(self):
        """Test XPRV validation."""
        validate_bip85_parameters(32, 512, 0, strict=True)

        with pytest.raises(Bip85ValidationError, match="XPRV length must be 512"):
            validate_bip85_parameters(32, 256, 0, strict=True)

    def test_hex_validation(self):
        """Test hex application validation."""
        # Valid ranges
        validate_bip85_parameters(128, 16, 0, strict=True)
        validate_bip85_parameters(128, 64, 0, strict=True)

        # Invalid ranges
        with pytest.raises(Bip85ValidationError, match="Hex length must be 16-64"):
            validate_bip85_parameters(128, 15, 0, strict=True)

        with pytest.raises(Bip85ValidationError, match="Hex length must be 16-64"):
            validate_bip85_parameters(128, 65, 0, strict=True)

    def test_password_validation(self):
        """Test password application validation."""
        # Valid ranges
        validate_bip85_parameters(9999, 10, 0, strict=True)
        validate_bip85_parameters(9999, 128, 0, strict=True)

        # Invalid ranges
        with pytest.raises(
            Bip85ValidationError, match="Password length must be 10-128"
        ):
            validate_bip85_parameters(9999, 9, 0, strict=True)

        with pytest.raises(
            Bip85ValidationError, match="Password length must be 10-128"
        ):
            validate_bip85_parameters(9999, 129, 0, strict=True)


class TestFormatBip85Path:
    """Test BIP85 path formatting."""

    def test_path_formatting(self):
        """Test formatting derivation paths."""
        path = format_bip85_path(39, 12, 0)
        assert path == "m/83696968'/39'/12'/0'"

        path = format_bip85_path(128, 32, 1000)
        assert path == "m/83696968'/128'/32'/1000'"

        path = format_bip85_path(2, 512, 2147483647)
        assert path == "m/83696968'/2'/512'/2147483647'"


class TestParseBip85Path:
    """Test BIP85 path parsing."""

    def test_valid_path_parsing(self):
        """Test parsing valid BIP85 paths."""
        app, length, index = parse_bip85_path("m/83696968'/39'/12'/0'")
        assert app == 39
        assert length == 12
        assert index == 0

        app, length, index = parse_bip85_path("m/83696968'/128'/64'/1000'")
        assert app == 128
        assert length == 64
        assert index == 1000

    def test_invalid_path_format(self):
        """Test parsing invalid path formats."""
        with pytest.raises(Bip85ValidationError, match="Invalid BIP85 path format"):
            parse_bip85_path("m/44'/0'/0'/0'/0'")  # Wrong purpose

        with pytest.raises(Bip85ValidationError, match="Invalid BIP85 path format"):
            parse_bip85_path("m/83696968'/39'/12'/0")  # Missing hardened marker

        with pytest.raises(Bip85ValidationError, match="Invalid BIP85 path format"):
            parse_bip85_path("83696968'/39'/12'/0'")  # Missing m/

    def test_invalid_numeric_values(self):
        """Test parsing paths with invalid numeric values."""
        with pytest.raises(Bip85ValidationError, match="Invalid word count for BIP39"):
            parse_bip85_path("m/83696968'/39'/13'/0'")  # Invalid BIP39 word count

    def test_path_whitespace_handling(self):
        """Test parsing paths with whitespace."""
        app, length, index = parse_bip85_path("  m/83696968'/39'/12'/0'  ")
        assert app == 39
        assert length == 12
        assert index == 0


class TestGetApplicationName:
    """Test application name lookup."""

    def test_known_applications(self):
        """Test lookup of known application names."""
        assert get_application_name(39) == "BIP39 Mnemonic"
        assert get_application_name(2) == "HD-Seed WIF"
        assert get_application_name(32) == "XPRV"
        assert get_application_name(128) == "Hex"
        assert get_application_name(9999) == "Password"

    def test_unknown_applications(self):
        """Test lookup of unknown application names."""
        assert get_application_name(999) == "Unknown (999)"
        assert get_application_name(0) == "Unknown (0)"


class TestCalculateEntropyBytesNeeded:
    """Test entropy bytes calculation."""

    def test_bip39_entropy_calculation(self):
        """Test entropy calculation for BIP39."""
        assert calculate_entropy_bytes_needed(39, 12) == 16
        assert calculate_entropy_bytes_needed(39, 15) == 20
        assert calculate_entropy_bytes_needed(39, 18) == 24
        assert calculate_entropy_bytes_needed(39, 21) == 28
        assert calculate_entropy_bytes_needed(39, 24) == 32

    def test_bip39_invalid_word_count(self):
        """Test entropy calculation for invalid BIP39 word counts."""
        with pytest.raises(Bip85ValidationError, match="Invalid BIP39 word count"):
            calculate_entropy_bytes_needed(39, 13)

    def test_hd_seed_entropy_calculation(self):
        """Test entropy calculation for HD-Seed WIF."""
        assert calculate_entropy_bytes_needed(2, 512) == 64

    def test_xprv_entropy_calculation(self):
        """Test entropy calculation for XPRV."""
        assert calculate_entropy_bytes_needed(32, 512) == 64

    def test_hex_entropy_calculation(self):
        """Test entropy calculation for hex."""
        assert calculate_entropy_bytes_needed(128, 16) == 16
        assert calculate_entropy_bytes_needed(128, 32) == 32
        assert calculate_entropy_bytes_needed(128, 64) == 64

    def test_hex_invalid_length(self):
        """Test entropy calculation for invalid hex lengths."""
        with pytest.raises(Bip85ValidationError, match="Invalid hex length"):
            calculate_entropy_bytes_needed(128, 15)

        with pytest.raises(Bip85ValidationError, match="Invalid hex length"):
            calculate_entropy_bytes_needed(128, 65)

    def test_password_entropy_calculation(self):
        """Test entropy calculation for passwords."""
        assert calculate_entropy_bytes_needed(9999, 10) == 10
        assert calculate_entropy_bytes_needed(9999, 64) == 64
        assert calculate_entropy_bytes_needed(9999, 100) == 64  # Capped at 64

    def test_password_invalid_length(self):
        """Test entropy calculation for invalid password lengths."""
        with pytest.raises(Bip85ValidationError, match="Invalid password length"):
            calculate_entropy_bytes_needed(9999, 9)

        with pytest.raises(Bip85ValidationError, match="Invalid password length"):
            calculate_entropy_bytes_needed(9999, 129)

    def test_unknown_application(self):
        """Test entropy calculation for unknown applications."""
        # Should return 64 bytes for unknown applications
        assert calculate_entropy_bytes_needed(999, 100) == 64


class TestValidateDerivationIndexRange:
    """Test derivation index range validation."""

    def test_valid_index_range(self):
        """Test validation of valid indices."""
        validate_derivation_index_range(0)
        validate_derivation_index_range(1000)
        validate_derivation_index_range(2**31 - 1)

    def test_invalid_index_range(self):
        """Test validation of invalid indices."""
        with pytest.raises(Bip85ValidationError, match="Index must be 0 to 2147483647"):
            validate_derivation_index_range(-1)

        with pytest.raises(Bip85ValidationError, match="Index must be 0 to 2147483647"):
            validate_derivation_index_range(2**31)

    def test_max_index_validation(self):
        """Test validation with maximum index limit."""
        validate_derivation_index_range(500, max_index=1000)

        with pytest.raises(Bip85ValidationError, match="Index exceeds maximum"):
            validate_derivation_index_range(1500, max_index=1000)


class TestFormatParameterSummary:
    """Test parameter summary formatting."""

    def test_bip39_summary(self):
        """Test summary formatting for BIP39."""
        summary = format_parameter_summary(39, 12, 0)

        assert summary["application"] == 39
        assert summary["application_name"] == "BIP39 Mnemonic"
        assert summary["length"] == 12
        assert summary["index"] == 0
        assert summary["derivation_path"] == "m/83696968'/39'/12'/0'"
        assert summary["entropy_bytes"] == 16

    def test_hex_summary(self):
        """Test summary formatting for hex."""
        summary = format_parameter_summary(128, 32, 100)

        assert summary["application"] == 128
        assert summary["application_name"] == "Hex"
        assert summary["length"] == 32
        assert summary["index"] == 100
        assert summary["derivation_path"] == "m/83696968'/128'/32'/100'"
        assert summary["entropy_bytes"] == 32

    def test_unknown_application_summary(self):
        """Test summary formatting for unknown application."""
        summary = format_parameter_summary(999, 50, 10)

        assert summary["application"] == 999
        assert summary["application_name"] == "Unknown (999)"
        assert summary["length"] == 50
        assert summary["index"] == 10
        assert summary["derivation_path"] == "m/83696968'/999'/50'/10'"
        assert summary["entropy_bytes"] == 64  # Default for unknown apps


class TestConstants:
    """Test BIP85 constants and mappings."""

    def test_bip85_applications_constant(self):
        """Test BIP85 applications mapping."""
        assert 39 in BIP85_APPLICATIONS
        assert 2 in BIP85_APPLICATIONS
        assert 32 in BIP85_APPLICATIONS
        assert 128 in BIP85_APPLICATIONS
        assert 9999 in BIP85_APPLICATIONS

        assert BIP85_APPLICATIONS[39] == "BIP39 Mnemonic"

    def test_bip39_valid_word_counts(self):
        """Test BIP39 valid word counts set."""
        assert BIP39_VALID_WORD_COUNTS == {12, 15, 18, 21, 24}
        assert 13 not in BIP39_VALID_WORD_COUNTS
        assert 16 not in BIP39_VALID_WORD_COUNTS
