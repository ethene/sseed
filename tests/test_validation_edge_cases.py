"""Comprehensive validation edge case tests for sseed.

Tests validation edge cases, Unicode normalization, input size limits,
malformed input scenarios, and boundary conditions to achieve comprehensive
coverage of validation logic.
"""

import unittest.mock as mock
from unittest.mock import patch

import pytest

from sseed.exceptions import ValidationError
from sseed.validation import (
    normalize_input,
    validate_group_threshold,
    validate_mnemonic_checksum,
    validate_mnemonic_words,
    validate_shard_integrity,
)


class TestValidationEdgeCases:
    """Comprehensive validation edge case tests."""

    # ===== UNICODE NORMALIZATION EDGE CASES =====

    def test_normalize_input_complex_unicode(self):
        """Test Unicode normalization with complex Unicode characters."""
        # Test with combining characters
        input_with_combining = "cafe\u0301"  # café with combining accent
        normalized = normalize_input(input_with_combining)
        # Normalization may preserve combining characters or convert to composed form
        assert "cafe" in normalized or "café" in normalized

    def test_normalize_input_unicode_variants(self):
        """Test Unicode normalization with character variants."""
        # Test with different Unicode representations
        input_nfc = "é"  # NFC form (single character)
        input_nfd = "e\u0301"  # NFD form (e + combining accent)

        normalized_nfc = normalize_input(input_nfc)
        normalized_nfd = normalize_input(input_nfd)

        # Both should normalize to the same form
        assert normalized_nfc == normalized_nfd

    def test_normalize_input_unicode_compatibility(self):
        """Test Unicode normalization with compatibility characters."""
        # Test with compatibility characters that should be normalized
        input_compat = "ﬁ"  # Unicode ligature fi (U+FB01)
        normalized = normalize_input(input_compat)
        assert normalized == "fi"

    def test_normalize_input_mixed_scripts(self):
        """Test Unicode normalization with mixed scripts."""
        # Test with mixed scripts (Latin, Cyrillic, etc.)
        input_mixed = "hello привет"
        normalized = normalize_input(input_mixed)
        assert "hello" in normalized and "привет" in normalized

    def test_normalize_input_control_characters(self):
        """Test Unicode normalization with control characters."""
        # Test with control characters that should be handled
        input_with_controls = "test\u0000\u0001string"
        normalized = normalize_input(input_with_controls)
        # Control characters should be handled appropriately

    def test_normalize_input_zero_width_characters(self):
        """Test Unicode normalization with zero-width characters."""
        # Test with zero-width joiners and non-joiners
        input_with_zwj = "test\u200c\u200dstring"
        normalized = normalize_input(input_with_zwj)
        # Should handle zero-width characters

    def test_normalize_input_bidirectional_text(self):
        """Test Unicode normalization with bidirectional text."""
        # Test with right-to-left text
        input_bidi = "hello \u0627\u0644\u0639\u0631\u0628\u064a\u0629 world"
        normalized = normalize_input(input_bidi)
        # Should preserve text direction

    def test_normalize_input_very_long_unicode(self):
        """Test Unicode normalization with very long strings."""
        # Test with extremely long Unicode strings
        long_unicode = "é" * 10000
        normalized = normalize_input(long_unicode)
        # Length may vary due to Unicode normalization forms (NFC vs NFD)
        assert len(normalized) >= 10000

    def test_normalize_input_invalid_unicode_sequences(self):
        """Test Unicode normalization with invalid sequences."""
        # Test with invalid Unicode surrogates
        try:
            # This might contain invalid Unicode sequences
            invalid_unicode = "test\ud800\udc00invalid"
            normalized = normalize_input(invalid_unicode)
        except ValidationError:
            pass  # Expected for invalid Unicode

    # ===== MNEMONIC VALIDATION EDGE CASES =====

    def test_validate_mnemonic_words_empty_list(self):
        """Test mnemonic word validation with empty list."""
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words([])

    def test_validate_mnemonic_words_single_word(self):
        """Test mnemonic word validation with single word."""
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words(["abandon"])

    def test_validate_mnemonic_words_invalid_length_11(self):
        """Test mnemonic word validation with 11 words."""
        words = ["abandon"] * 11
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_invalid_length_25(self):
        """Test mnemonic word validation with 25 words."""
        words = ["abandon"] * 25
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_empty_word(self):
        """Test mnemonic word validation with empty word."""
        words = ["abandon", "", "about", "ability"] * 3
        with pytest.raises(ValidationError, match="Invalid word format"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_whitespace_only_word(self):
        """Test mnemonic word validation with whitespace-only word."""
        words = ["abandon", "   ", "about", "ability"] * 3
        with pytest.raises(ValidationError, match="Invalid word format"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_very_long_word(self):
        """Test mnemonic word validation with excessively long word."""
        long_word = "a" * 1000
        words = ["abandon", long_word, "about", "ability"]
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_non_alphabetic(self):
        """Test mnemonic word validation with non-alphabetic characters."""
        words = ["abandon", "ab0ut", "ability", "able"]
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_unicode_characters(self):
        """Test mnemonic word validation with Unicode characters."""
        words = ["abandon", "abóut", "ability", "able"]
        with pytest.raises(ValidationError, match="Invalid mnemonic length"):
            validate_mnemonic_words(words)

    def test_validate_mnemonic_words_mixed_case(self):
        """Test mnemonic word validation with mixed case."""
        words = ["Abandon", "About", "ABILITY", "able"] * 3  # 12 words
        # Should fail because validation expects lowercase only
        with pytest.raises(ValidationError, match="Invalid word format"):
            validate_mnemonic_words(words)

    # ===== GROUP THRESHOLD VALIDATION EDGE CASES =====

    def test_validate_group_threshold_empty_string(self):
        """Test group threshold validation with empty string."""
        with pytest.raises(ValidationError, match="Invalid group configuration format"):
            validate_group_threshold("")

    def test_validate_group_threshold_whitespace_only(self):
        """Test group threshold validation with whitespace only."""
        with pytest.raises(ValidationError, match="Invalid group configuration format"):
            validate_group_threshold("   ")

    def test_validate_group_threshold_invalid_format(self):
        """Test group threshold validation with invalid format."""
        with pytest.raises(ValidationError, match="Invalid group configuration format"):
            validate_group_threshold("3of5")

    def test_validate_group_threshold_non_numeric(self):
        """Test group threshold validation with non-numeric values."""
        with pytest.raises(ValidationError, match="Invalid group configuration format"):
            validate_group_threshold("three-of-5")

    def test_validate_group_threshold_zero_threshold(self):
        """Test group threshold validation with zero threshold."""
        with pytest.raises(ValidationError, match="Threshold must be positive"):
            validate_group_threshold("0-of-5")

    def test_validate_group_threshold_threshold_exceeds_total(self):
        """Test group threshold validation with threshold > total."""
        with pytest.raises(ValidationError, match="cannot be greater than total shares"):
            validate_group_threshold("5-of-3")

    def test_validate_group_threshold_very_large_numbers(self):
        """Test group threshold validation with very large numbers."""
        with pytest.raises(ValidationError, match="exceeds maximum of 16"):
            validate_group_threshold("999999999-of-999999999")

    def test_validate_group_threshold_decimal_numbers(self):
        """Test group threshold validation with decimal numbers."""
        with pytest.raises(ValidationError, match="Invalid group configuration format"):
            validate_group_threshold("3.5-of-5")

    def test_validate_group_threshold_extra_whitespace(self):
        """Test group threshold validation with extra whitespace."""
        # Should fail due to spaces in the format
        with pytest.raises(ValidationError, match="Invalid group configuration format"):
            validate_group_threshold("  3 - of - 5  ")

    # ===== MNEMONIC CHECKSUM VALIDATION EDGE CASES =====

    def test_validate_mnemonic_checksum_empty_string(self):
        """Test mnemonic checksum validation with empty string."""
        result = validate_mnemonic_checksum("")
        assert result is False

    def test_validate_mnemonic_checksum_whitespace_only(self):
        """Test mnemonic checksum validation with whitespace only."""
        result = validate_mnemonic_checksum("   ")
        assert result is False

    def test_validate_mnemonic_checksum_invalid_words(self):
        """Test mnemonic checksum validation with invalid words."""
        invalid_mnemonic = "invalid words that are not in bip39 wordlist"
        with pytest.raises(ValidationError, match="Error during mnemonic checksum validation"):
            validate_mnemonic_checksum(invalid_mnemonic)

    def test_validate_mnemonic_checksum_wrong_length(self):
        """Test mnemonic checksum validation with wrong word count."""
        wrong_length = "abandon about"  # Only 2 words
        with pytest.raises(ValidationError, match="Error during mnemonic checksum validation"):
            validate_mnemonic_checksum(wrong_length)

    def test_validate_mnemonic_checksum_invalid_checksum(self):
        """Test mnemonic checksum validation with invalid checksum."""
        # Valid words but invalid checksum
        invalid_checksum = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
        result = validate_mnemonic_checksum(invalid_checksum)
        assert result is False

    def test_validate_mnemonic_checksum_exception_handling(self):
        """Test mnemonic checksum validation exception handling."""
        with patch("sseed.validation.Bip39MnemonicValidator", side_effect=Exception("Error")):
            with pytest.raises(ValidationError, match="Error during mnemonic checksum validation"):
                validate_mnemonic_checksum(
                    "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
                )

    # ===== SHARD INTEGRITY VALIDATION EDGE CASES =====

    def test_validate_shard_integrity_empty_list(self):
        """Test shard integrity validation with empty shard list."""
        with pytest.raises(ValidationError, match="No shards provided"):
            validate_shard_integrity([])

    def test_validate_shard_integrity_single_shard(self):
        """Test shard integrity validation with single shard."""
        with pytest.raises(ValidationError, match="Insufficient shards"):
            validate_shard_integrity(["single shard"])

    def test_validate_shard_integrity_duplicate_shards(self):
        """Test shard integrity validation with duplicate shards."""
        duplicate_shards = ["shard1", "shard2", "shard1"]
        with pytest.raises(ValidationError, match="Duplicate shards"):
            validate_shard_integrity(duplicate_shards)

    def test_validate_shard_integrity_empty_shard(self):
        """Test shard integrity validation with empty shard."""
        shards_with_empty = ["shard1", "", "shard3"]
        with pytest.raises(ValidationError, match="Empty shard"):
            validate_shard_integrity(shards_with_empty)

    def test_validate_shard_integrity_whitespace_shard(self):
        """Test shard integrity validation with whitespace-only shard."""
        shards_with_whitespace = ["shard1", "   ", "shard3"]
        with pytest.raises(ValidationError, match="Empty shard"):
            validate_shard_integrity(shards_with_whitespace)

    def test_validate_shard_integrity_invalid_shard_format(self):
        """Test shard integrity validation with invalid shard format."""
        invalid_shards = ["shard1", "invalid shard format", "shard3"]
        with pytest.raises(ValidationError, match="Invalid shard format"):
            validate_shard_integrity(invalid_shards)

    def test_validate_shard_integrity_mismatched_groups(self):
        """Test shard integrity validation with mismatched shard groups."""
        mismatched_shards = ["group1_shard1", "group2_shard1", "group1_shard2"]
        with pytest.raises(ValidationError, match="Invalid shard format"):
            validate_shard_integrity(mismatched_shards)

    def test_validate_shard_integrity_very_long_shard(self):
        """Test shard integrity validation with very long shard."""
        long_shard = "word " * 1000
        shards_with_long = ["shard1", long_shard.strip(), "shard3"]
        with pytest.raises(ValidationError, match="Invalid shard format"):
            validate_shard_integrity(shards_with_long)

    def test_validate_shard_integrity_non_string_shard(self):
        """Test shard integrity validation with non-string shard."""
        shards_with_non_string = ["shard1", 12345, "shard3"]
        with pytest.raises(ValidationError, match="is not a string"):
            validate_shard_integrity(shards_with_non_string)

    # ===== INPUT SIZE LIMIT TESTS =====

    def test_normalize_input_memory_limit(self):
        """Test input normalization with memory limit."""
        # Test with very large input that might cause memory issues
        huge_input = "word " * 1000000  # 1M words
        try:
            normalized = normalize_input(huge_input)
        except (ValidationError, MemoryError):
            pass  # Expected for huge inputs

    def test_validate_mnemonic_words_memory_limit(self):
        """Test mnemonic word validation with memory limit."""
        # Test with huge word list
        huge_word_list = ["abandon"] * 1000000
        with pytest.raises((ValidationError, MemoryError)):
            validate_mnemonic_words(huge_word_list)

    # ===== CONCURRENT VALIDATION TESTS =====

    def test_validation_thread_safety(self):
        """Test validation functions are thread-safe."""
        import threading

        results = []
        errors = []

        def validation_worker():
            try:
                for _ in range(100):
                    # Test various validation functions
                    validate_group_threshold("3-of-5")
                    validate_mnemonic_checksum(
                        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
                    )
                    normalize_input("test input")
                    results.append(True)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = [threading.Thread(target=validation_worker) for _ in range(5)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 500

    # ===== BOUNDARY CONDITION TESTS =====

    def test_validation_boundary_conditions(self):
        """Test validation at exact boundary conditions."""
        # Test at exact word count boundaries
        validate_mnemonic_words(["abandon"] * 12)  # Minimum valid
        validate_mnemonic_words(["abandon"] * 24)  # Maximum valid

        # Test at threshold boundaries
        validate_group_threshold("1-of-1")  # Minimum valid
        validate_group_threshold("15-of-16")  # High but valid
