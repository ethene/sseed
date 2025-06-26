"""Tests for validation module functionality.

Tests the validation functions implemented in Phase 5:
- Mnemonic checksum validation
- Threshold logic validation
- Duplicate shard detection
- Shard integrity validation
"""

from unittest.mock import patch

import pytest

from sseed.exceptions import ValidationError
from sseed.validation import (
    detect_duplicate_shards,
    normalize_input,
    sanitize_filename,
    validate_group_threshold,
    validate_mnemonic_checksum,
    validate_mnemonic_words,
    validate_shard_integrity,
)


class TestNormalization:
    """Test input normalization functionality."""

    def test_normalize_input_basic(self):
        """Test basic input normalization."""
        result = normalize_input("  test string  ")
        assert result == "test string"

    def test_normalize_input_unicode(self):
        """Test Unicode NFKD normalization."""
        # Test with Unicode characters that have composed forms
        result = normalize_input("café")  # é is a composed character
        assert isinstance(result, str)
        assert len(result) >= 4  # NFKD may decompose é into e + ́

    def test_normalize_input_empty(self):
        """Test normalization of empty/whitespace strings."""
        assert normalize_input("") == ""
        assert normalize_input("   ") == ""
        assert normalize_input("\t\n") == ""

    def test_normalize_input_invalid_type(self):
        """Test normalization with invalid input types."""
        with pytest.raises(ValidationError) as exc_info:
            normalize_input(123)
        assert "Input must be a string" in str(exc_info.value)


class TestMnemonicValidation:
    """Test mnemonic validation functionality."""

    def test_validate_mnemonic_words_valid_24(self):
        """Test validation of valid 24-word mnemonic."""
        words = ["abandon"] * 24
        validate_mnemonic_words(words)  # Should not raise

    def test_validate_mnemonic_words_valid_12(self):
        """Test validation of valid 12-word mnemonic."""
        words = ["abandon"] * 12
        validate_mnemonic_words(words)  # Should not raise

    def test_validate_mnemonic_words_invalid_length(self):
        """Test validation with invalid word count."""
        words = ["abandon"] * 10  # Invalid length
        with pytest.raises(ValidationError) as exc_info:
            validate_mnemonic_words(words)
        assert "Invalid mnemonic length: 10" in str(exc_info.value)

    def test_validate_mnemonic_words_invalid_format(self):
        """Test validation with invalid word format."""
        words = ["abandon"] * 11 + ["UPPERCASE"]  # Invalid format
        with pytest.raises(ValidationError) as exc_info:
            validate_mnemonic_words(words)
        assert "Invalid word format at position 12" in str(exc_info.value)

    def test_validate_mnemonic_words_not_list(self):
        """Test validation with non-list input."""
        with pytest.raises(ValidationError) as exc_info:
            validate_mnemonic_words("not a list")
        assert "Mnemonic words must be a list" in str(exc_info.value)

    @patch("bip_utils.Bip39MnemonicValidator")
    def test_validate_mnemonic_checksum_valid(self, mock_validator):
        """Test checksum validation with valid mnemonic."""
        mock_validator.return_value.IsValid.return_value = True

        # Use a real BIP-39 mnemonic for testing
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        result = validate_mnemonic_checksum(mnemonic)
        assert result is True

    @patch("bip_utils.Bip39MnemonicValidator")
    def test_validate_mnemonic_checksum_invalid(self, mock_validator):
        """Test checksum validation with invalid mnemonic."""
        mock_validator.return_value.IsValid.return_value = False

        # Use an invalid mnemonic
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
        result = validate_mnemonic_checksum(mnemonic)
        assert result is False

    def test_validate_mnemonic_checksum_empty(self):
        """Test checksum validation with empty mnemonic."""
        result = validate_mnemonic_checksum("")
        assert result is False


class TestThresholdValidation:
    """Test threshold configuration validation."""

    def test_validate_group_threshold_valid(self):
        """Test validation of valid threshold configurations."""
        threshold, total = validate_group_threshold("3-of-5")
        assert threshold == 3
        assert total == 5

    def test_validate_group_threshold_edge_cases(self):
        """Test validation of edge case threshold configurations."""
        # Minimum valid
        threshold, total = validate_group_threshold("1-of-1")
        assert threshold == 1
        assert total == 1

        # Maximum valid
        threshold, total = validate_group_threshold("16-of-16")
        assert threshold == 16
        assert total == 16

    def test_validate_group_threshold_invalid_format(self):
        """Test validation with invalid threshold format."""
        with pytest.raises(ValidationError) as exc_info:
            validate_group_threshold("3of5")  # Missing dash
        assert "Invalid group configuration format" in str(exc_info.value)

    def test_validate_group_threshold_invalid_numbers(self):
        """Test validation with invalid threshold numbers."""
        with pytest.raises(ValidationError) as exc_info:
            validate_group_threshold("0-of-5")  # Zero threshold
        assert "Threshold must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            validate_group_threshold("5-of-3")  # Threshold > total
        assert "cannot be greater than total shares" in str(exc_info.value)

    def test_validate_group_threshold_too_many_shares(self):
        """Test validation with too many total shares."""
        with pytest.raises(ValidationError) as exc_info:
            validate_group_threshold("10-of-20")  # Too many shares
        assert "exceeds maximum of 16" in str(exc_info.value)

    def test_validate_group_threshold_not_string(self):
        """Test validation with non-string input."""
        with pytest.raises(ValidationError) as exc_info:
            validate_group_threshold(123)
        assert "Group configuration must be a string" in str(exc_info.value)


class TestDuplicateDetection:
    """Test duplicate shard detection functionality."""

    def test_detect_duplicate_shards_none(self):
        """Test duplicate detection with no duplicates."""
        shards = ["shard1", "shard2", "shard3"]
        duplicates = detect_duplicate_shards(shards)
        assert duplicates == []

    def test_detect_duplicate_shards_found(self):
        """Test duplicate detection with duplicates present."""
        shards = ["shard1", "shard2", "shard1", "shard3", "shard2"]
        duplicates = detect_duplicate_shards(shards)
        assert len(duplicates) == 2
        assert "shard1" in duplicates
        assert "shard2" in duplicates

    def test_detect_duplicate_shards_empty_list(self):
        """Test duplicate detection with empty list."""
        duplicates = detect_duplicate_shards([])
        assert duplicates == []

    def test_detect_duplicate_shards_single_item(self):
        """Test duplicate detection with single item."""
        duplicates = detect_duplicate_shards(["shard1"])
        assert duplicates == []

    def test_detect_duplicate_shards_normalization(self):
        """Test duplicate detection with normalized input."""
        shards = ["  shard1  ", "shard2", "shard1", "  shard2  "]
        duplicates = detect_duplicate_shards(shards)
        assert len(duplicates) == 2
        assert "shard1" in duplicates
        assert "shard2" in duplicates

    def test_detect_duplicate_shards_invalid_input(self):
        """Test duplicate detection with invalid input."""
        with pytest.raises(ValidationError) as exc_info:
            detect_duplicate_shards("not a list")
        assert "Shards must be a list" in str(exc_info.value)

    def test_detect_duplicate_shards_invalid_shard_type(self):
        """Test duplicate detection with invalid shard type."""
        with pytest.raises(ValidationError) as exc_info:
            detect_duplicate_shards(["shard1", 123, "shard2"])
        assert "Shard at position 1 is not a string" in str(exc_info.value)

    def test_detect_duplicate_shards_empty_shard(self):
        """Test duplicate detection with empty shard."""
        with pytest.raises(ValidationError) as exc_info:
            detect_duplicate_shards(["shard1", "", "shard2"])
        assert "Empty shard at position 1" in str(exc_info.value)


class TestShardIntegrity:
    """Test shard integrity validation."""

    def test_validate_shard_integrity_valid(self):
        """Test shard integrity validation with valid shards."""
        # Create mock 20-word shards
        shards = [
            " ".join(["word"] * 20),
            " ".join(["test"] * 20),
            " ".join(["shard"] * 20),
        ]
        validate_shard_integrity(shards)  # Should not raise

    def test_validate_shard_integrity_no_shards(self):
        """Test shard integrity validation with no shards."""
        with pytest.raises(ValidationError) as exc_info:
            validate_shard_integrity([])
        assert "No shards provided for validation" in str(exc_info.value)

    def test_validate_shard_integrity_duplicates(self):
        """Test shard integrity validation with duplicates."""
        shard = " ".join(["word"] * 20)
        shards = [shard, shard, " ".join(["test"] * 20)]
        with pytest.raises(ValidationError) as exc_info:
            validate_shard_integrity(shards)
        assert "Duplicate shards detected" in str(exc_info.value)

    def test_validate_shard_integrity_insufficient_shards(self):
        """Test shard integrity validation with insufficient shards."""
        shards = [" ".join(["word"] * 20)]  # Only one shard
        with pytest.raises(ValidationError) as exc_info:
            validate_shard_integrity(shards)
        assert "Insufficient shards: 1" in str(exc_info.value)

    def test_validate_shard_integrity_invalid_format(self):
        """Test shard integrity validation with invalid shard format."""
        shards = [
            " ".join(["word"] * 20),  # Valid 20-word shard
            " ".join(["test"] * 15),  # Invalid 15-word shard
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_shard_integrity(shards)
        assert "Invalid shard format at position 1" in str(exc_info.value)

    def test_validate_shard_integrity_not_list(self):
        """Test shard integrity validation with non-list input."""
        with pytest.raises(ValidationError) as exc_info:
            validate_shard_integrity("not a list")
        assert "Shards must be a list" in str(exc_info.value)


class TestFilenameSanitization:
    """Test filename sanitization functionality."""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("test_file.txt")
        assert result == "test_file.txt"

    def test_sanitize_filename_special_characters(self):
        """Test sanitization of special characters."""
        result = sanitize_filename("test<>file?.txt")
        assert result == "test__file_.txt"

    def test_sanitize_filename_path_separators(self):
        """Test sanitization of path separators."""
        result = sanitize_filename("path/to\\file.txt")
        assert result == "path_to_file.txt"

    def test_sanitize_filename_unicode(self):
        """Test sanitization with Unicode characters."""
        result = sanitize_filename("tëst_fïlé.txt")
        assert isinstance(result, str)
        assert ".txt" in result

    def test_sanitize_filename_empty(self):
        """Test sanitization of empty filename."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_filename("")
        assert "Filename cannot be empty" in str(exc_info.value)

    def test_sanitize_filename_whitespace_only(self):
        """Test sanitization of whitespace-only filename."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_filename("   ")
        assert "Filename cannot be empty" in str(exc_info.value)

    def test_sanitize_filename_not_string(self):
        """Test sanitization with non-string input."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_filename(123)
        assert "Filename must be a string" in str(exc_info.value)
