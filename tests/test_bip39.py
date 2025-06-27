"""Tests for sseed.bip39 module.

Tests BIP-39 mnemonic generation and validation as implemented in Phase 2.
"""

import pytest
from bip_utils import Bip39Languages

from sseed.bip39 import (
    generate_mnemonic,
    get_language_code_from_bip_enum,
    get_mnemonic_entropy,
    parse_mnemonic,
    validate_mnemonic,
    word_count_to_entropy_bytes,
)
from sseed.exceptions import (
    CryptoError,
    MnemonicError,
    ValidationError,
)


class TestBip39Operations:
    """Test BIP-39 mnemonic operations."""

    def test_generate_mnemonic(self) -> None:
        """Test BIP-39 mnemonic generation."""
        mnemonic = generate_mnemonic()

        # Should be a string with 24 words
        assert isinstance(mnemonic, str)
        words = mnemonic.split()
        assert len(words) == 24

        # All words should be lowercase alphabetic
        for word in words:
            assert word.islower()
            assert word.isalpha()

    def test_generate_mnemonic_uniqueness(self) -> None:
        """Test that generated mnemonics are unique."""
        mnemonics = [generate_mnemonic() for _ in range(10)]

        # All mnemonics should be unique
        assert len(set(mnemonics)) == 10

    def test_validate_mnemonic_valid(self) -> None:
        """Test validation of valid mnemonics."""
        mnemonic = generate_mnemonic()

        assert validate_mnemonic(mnemonic) is True

    def test_validate_mnemonic_invalid(self) -> None:
        """Test validation of invalid mnemonics."""
        # Invalid checksum - using words that exist but wrong checksum
        invalid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"

        assert validate_mnemonic(invalid_mnemonic) is False

    def test_validate_mnemonic_empty(self) -> None:
        """Test validation of empty mnemonic."""
        assert validate_mnemonic("") is False
        assert validate_mnemonic("   ") is False

    def test_parse_mnemonic(self) -> None:
        """Test mnemonic parsing."""
        mnemonic = generate_mnemonic()
        words = parse_mnemonic(mnemonic)

        assert isinstance(words, list)
        assert len(words) == 24
        assert all(isinstance(word, str) for word in words)

    def test_parse_mnemonic_with_whitespace(self) -> None:
        """Test parsing mnemonic with extra whitespace."""
        mnemonic = generate_mnemonic()
        mnemonic_with_spaces = f"  {mnemonic}  "

        words = parse_mnemonic(mnemonic_with_spaces)
        assert len(words) == 24

    def test_parse_mnemonic_invalid(self) -> None:
        """Test parsing invalid mnemonic."""
        with pytest.raises(MnemonicError):
            parse_mnemonic("")

        with pytest.raises(MnemonicError):
            parse_mnemonic("invalid word count")

    def test_get_mnemonic_entropy(self) -> None:
        """Test entropy extraction from mnemonic."""
        mnemonic = generate_mnemonic()
        entropy = get_mnemonic_entropy(mnemonic)

        assert isinstance(entropy, bytes)
        assert len(entropy) == 32  # 256 bits for 24-word mnemonic

    def test_get_mnemonic_entropy_invalid(self) -> None:
        """Test entropy extraction from invalid mnemonic."""
        invalid_mnemonic = "invalid mnemonic with wrong checksum"

        with pytest.raises(MnemonicError):
            get_mnemonic_entropy(invalid_mnemonic)

    def test_round_trip(self) -> None:
        """Test round-trip: generate -> validate -> extract entropy."""
        # Generate mnemonic
        mnemonic = generate_mnemonic()

        # Validate it
        assert validate_mnemonic(mnemonic) is True

        # Extract entropy
        entropy = get_mnemonic_entropy(mnemonic)
        assert len(entropy) == 32

        # Parse words
        words = parse_mnemonic(mnemonic)
        assert len(words) == 24


class TestWordCountSupport:
    """Test Phase 3: Comprehensive word count support."""

    @pytest.mark.parametrize(
        "word_count,expected_entropy_bytes",
        [(12, 16), (15, 20), (18, 24), (21, 28), (24, 32)],
    )
    def test_generate_mnemonic_word_counts(self, word_count, expected_entropy_bytes):
        """Test mnemonic generation with different word counts."""
        mnemonic = generate_mnemonic(word_count=word_count)
        words = mnemonic.split()

        # Verify word count
        assert len(words) == word_count

        # Verify all words are valid
        for word in words:
            assert word.islower()
            assert word.isalpha()

        # Test entropy consistency
        entropy = get_mnemonic_entropy(mnemonic)
        assert len(entropy) == expected_entropy_bytes

        # Verify mnemonic is valid
        assert validate_mnemonic(mnemonic) is True

    def test_generate_mnemonic_backward_compatibility(self):
        """Test that default behavior is unchanged."""
        mnemonic = generate_mnemonic()  # No word_count parameter
        words = mnemonic.split()
        assert len(words) == 24  # Should still default to 24 words

    @pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
    def test_generate_mnemonic_uniqueness_by_word_count(self, word_count):
        """Test that generated mnemonics are unique for each word count."""
        mnemonics = [generate_mnemonic(word_count=word_count) for _ in range(5)]

        # All mnemonics should be unique
        assert len(set(mnemonics)) == 5

        # All should have correct word count
        for mnemonic in mnemonics:
            assert len(mnemonic.split()) == word_count

    @pytest.mark.parametrize("invalid_word_count", [6, 8, 10, 11, 13, 16, 20, 25, 30])
    def test_generate_mnemonic_invalid_word_counts(self, invalid_word_count):
        """Test error handling for invalid word counts."""
        with pytest.raises(CryptoError) as exc_info:
            generate_mnemonic(word_count=invalid_word_count)

        assert f"Invalid word count: {invalid_word_count}" in str(exc_info.value)
        assert "Must be one of: [12, 15, 18, 21, 24]" in str(exc_info.value)

    @pytest.mark.parametrize(
        "word_count,language",
        [
            (12, Bip39Languages.ENGLISH),
            (15, Bip39Languages.SPANISH),
            (18, Bip39Languages.FRENCH),
            (21, Bip39Languages.ITALIAN),
            (24, Bip39Languages.PORTUGUESE),
            (12, Bip39Languages.CZECH),
            (15, Bip39Languages.CHINESE_SIMPLIFIED),
            (18, Bip39Languages.CHINESE_TRADITIONAL),
            (21, Bip39Languages.KOREAN),
        ],
    )
    def test_generate_mnemonic_word_counts_with_languages(self, word_count, language):
        """Test all word counts work with all supported languages."""
        mnemonic = generate_mnemonic(language=language, word_count=word_count)
        words = mnemonic.split()

        # Verify word count
        assert len(words) == word_count

        # Verify mnemonic is valid for the language
        assert validate_mnemonic(mnemonic, language) is True

    @pytest.mark.parametrize(
        "word_count,expected_bytes", [(12, 16), (15, 20), (18, 24), (21, 28), (24, 32)]
    )
    def test_word_count_to_entropy_bytes_mapping(self, word_count, expected_bytes):
        """Test word count to entropy bytes mapping helper function."""
        result = word_count_to_entropy_bytes(word_count)
        assert result == expected_bytes

    @pytest.mark.parametrize("invalid_word_count", [11, 13, 16, 20, 25])
    def test_word_count_to_entropy_bytes_invalid(self, invalid_word_count):
        """Test word count to entropy mapping with invalid counts."""
        with pytest.raises(ValidationError) as exc_info:
            word_count_to_entropy_bytes(invalid_word_count)

        assert f"Invalid word count: {invalid_word_count}" in str(exc_info.value)

    @pytest.mark.parametrize(
        "language,expected_code",
        [
            (Bip39Languages.ENGLISH, "en"),
            (Bip39Languages.SPANISH, "es"),
            (Bip39Languages.FRENCH, "fr"),
            (Bip39Languages.ITALIAN, "it"),
            (Bip39Languages.PORTUGUESE, "pt"),
            (Bip39Languages.CZECH, "cs"),
            (Bip39Languages.CHINESE_SIMPLIFIED, "zh-cn"),
            (Bip39Languages.CHINESE_TRADITIONAL, "zh-tw"),
            (Bip39Languages.KOREAN, "ko"),
        ],
    )
    def test_get_language_code_from_bip_enum(self, language, expected_code):
        """Test language enum to code conversion helper function."""
        result = get_language_code_from_bip_enum(language)
        assert result == expected_code


class TestRoundTripAllWordCounts:
    """Test round-trip operations for all word counts."""

    @pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
    def test_round_trip_all_word_counts(self, word_count):
        """Test round-trip: generate -> validate -> extract entropy for all word counts."""
        # Generate mnemonic with specific word count
        mnemonic = generate_mnemonic(word_count=word_count)

        # Verify word count
        words = mnemonic.split()
        assert len(words) == word_count

        # Validate it
        assert validate_mnemonic(mnemonic) is True

        # Extract entropy and verify length
        entropy = get_mnemonic_entropy(mnemonic)
        expected_entropy_bytes = word_count_to_entropy_bytes(word_count)
        assert len(entropy) == expected_entropy_bytes

        # Parse words
        words = parse_mnemonic(mnemonic)
        assert len(words) == word_count

    @pytest.mark.parametrize(
        "word_count,language",
        [
            (12, Bip39Languages.ENGLISH),
            (15, Bip39Languages.SPANISH),
            (18, Bip39Languages.FRENCH),
            (21, Bip39Languages.CHINESE_SIMPLIFIED),
            (24, Bip39Languages.KOREAN),
        ],
    )
    def test_round_trip_word_counts_with_languages(self, word_count, language):
        """Test round-trip with different word counts and languages."""
        # Generate mnemonic
        mnemonic = generate_mnemonic(language=language, word_count=word_count)

        # Verify word count
        assert len(mnemonic.split()) == word_count

        # Validate with correct language
        assert validate_mnemonic(mnemonic, language) is True

        # Extract and verify entropy
        entropy = get_mnemonic_entropy(mnemonic)
        expected_bytes = word_count_to_entropy_bytes(word_count)
        assert len(entropy) == expected_bytes
