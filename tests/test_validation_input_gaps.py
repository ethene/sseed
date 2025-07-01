"""Tests to fill coverage gaps in sseed.validation.input module."""

from unittest.mock import patch

import pytest

from sseed.exceptions import ValidationError
from sseed.validation.input import (
    normalize_input,
    sanitize_filename,
    validate_mnemonic_words,
)


class TestValidationInputGaps:
    """Test specific gaps in validation input module."""

    @patch("sseed.validation.input.unicodedata.normalize")
    def test_normalize_input_exception_handling(self, mock_normalize):
        """Test exception handling in normalize_input function."""
        # This should trigger lines 61-64 - exception handling
        mock_normalize.side_effect = Exception("Unicode normalization failed")

        with pytest.raises(ValidationError, match="Failed to normalize input"):
            normalize_input("test input")

    def test_validate_mnemonic_words_non_string_word(self):
        """Test ValidationError for non-string word type."""
        # This should trigger line 113 - non-string word type
        # Need valid length (12 words) to reach individual word validation
        words_with_non_string = [
            "word1",
            "word2",
            123,
            "word4",
            "word5",
            "word6",
            "word7",
            "word8",
            "word9",
            "word10",
            "word11",
            "word12",
        ]

        with pytest.raises(ValidationError, match="Word at position 3 is not a string"):
            validate_mnemonic_words(words_with_non_string)

    def test_sanitize_filename_empty_after_sanitization(self):
        """Test ValidationError for filename empty after sanitization."""
        # This should trigger line 174 - filename empty after sanitization
        with pytest.raises(
            ValidationError, match="Filename is empty after sanitization"
        ):
            sanitize_filename(
                "   .  "
            )  # Only spaces and dots, becomes empty after strip

    def test_additional_edge_cases_for_coverage(self):
        """Test additional cases to ensure complete coverage."""
        # Test valid cases to ensure no regressions

        # Test normalize_input with valid input
        result = normalize_input("  test input  ")
        assert "test input" in result

        # Test validate_mnemonic_words with valid strings (12 words)
        valid_words = [
            "word1",
            "word2",
            "word3",
            "word4",
            "word5",
            "word6",
            "word7",
            "word8",
            "word9",
            "word10",
            "word11",
            "word12",
        ]
        validate_mnemonic_words(valid_words)  # Should not raise

        # Test sanitize_filename with valid input
        result = sanitize_filename("valid_filename.txt")
        assert result == "valid_filename.txt"
