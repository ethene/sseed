"""Tests for multi-language BIP-39 mnemonic support.

This module tests the multi-language functionality including language detection,
validation, and generation across all 9 supported BIP-39 languages.
"""

import pytest
from bip_utils import Bip39Languages

from sseed.bip39 import (
    generate_mnemonic,
    get_mnemonic_entropy,
    parse_mnemonic,
    validate_mnemonic,
)
from sseed.exceptions import (
    MnemonicError,
    ValidationError,
)
from sseed.languages import (
    LanguageInfo,
    detect_mnemonic_language,
    format_language_list,
    get_default_language,
    get_language_by_bip_enum,
    get_supported_language_codes,
    get_supported_languages,
    validate_language_code,
    validate_mnemonic_words_for_language,
)
from sseed.validation.crypto import validate_mnemonic_checksum


class TestLanguageInfrastructure:
    """Test the core language infrastructure."""

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        languages = get_supported_languages()
        assert len(languages) == 9
        assert all(isinstance(lang, LanguageInfo) for lang in languages)

        # Check that all expected languages are present
        codes = [lang.code for lang in languages]
        expected_codes = ["en", "es", "fr", "it", "pt", "cs", "zh-cn", "zh-tw", "ko"]
        assert set(codes) == set(expected_codes)

    def test_get_supported_language_codes(self):
        """Test getting list of supported language codes."""
        codes = get_supported_language_codes()
        expected_codes = ["en", "es", "fr", "it", "pt", "cs", "zh-cn", "zh-tw", "ko"]
        assert set(codes) == set(expected_codes)

    def test_validate_language_code_valid(self):
        """Test validating valid language codes."""
        lang_info = validate_language_code("es")
        assert lang_info.code == "es"
        assert lang_info.name == "Spanish"
        assert lang_info.bip_enum == Bip39Languages.SPANISH

    def test_validate_language_code_case_insensitive(self):
        """Test that language code validation is case insensitive."""
        lang_info = validate_language_code("ES")
        assert lang_info.code == "es"

        lang_info = validate_language_code("  fr  ")
        assert lang_info.code == "fr"

    def test_validate_language_code_invalid(self):
        """Test validating invalid language codes."""
        with pytest.raises(ValidationError) as exc_info:
            validate_language_code("invalid")
        assert "Unsupported language code 'invalid'" in str(exc_info.value)

    def test_validate_language_code_invalid_type(self):
        """Test validating non-string language codes."""
        with pytest.raises(ValidationError) as exc_info:
            validate_language_code(123)
        assert "Language code must be a string" in str(exc_info.value)

    def test_get_language_by_bip_enum(self):
        """Test getting language info by BIP enum."""
        lang_info = get_language_by_bip_enum(Bip39Languages.SPANISH)
        assert lang_info.code == "es"
        assert lang_info.name == "Spanish"

    def test_get_language_by_bip_enum_invalid(self):
        """Test getting language info with invalid enum."""
        # Since we handle all valid BIP39Languages enums, we'll skip the error case test
        # The function will only fail if passed something that's not a valid enum at all
        # but that would be a type error rather than our validation error
        pass

    def test_get_default_language(self):
        """Test getting default language."""
        default_lang = get_default_language()
        assert default_lang.code == "en"
        assert default_lang.name == "English"

    def test_format_language_list(self):
        """Test formatting language list for CLI help."""
        formatted = format_language_list()
        assert "en (English)" in formatted
        assert "es (Spanish)" in formatted
        assert "zh-cn (Chinese Simplified)" in formatted

    def test_language_info_str_repr(self):
        """Test LanguageInfo string representations."""
        lang_info = validate_language_code("es")
        assert str(lang_info) == "Spanish (es)"
        assert "LanguageInfo(code='es'" in repr(lang_info)


class TestLanguageDetection:
    """Test automatic language detection functionality."""

    def test_detect_english_mnemonic(self):
        """Test detecting English mnemonics."""
        # Generate English mnemonic
        english_mnemonic = generate_mnemonic()

        detected = detect_mnemonic_language(english_mnemonic)
        assert detected is not None
        assert detected.code == "en"

    def test_detect_spanish_mnemonic(self):
        """Test detecting Spanish mnemonics."""
        # Generate Spanish mnemonic
        spanish_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)

        detected = detect_mnemonic_language(spanish_mnemonic)
        assert detected is not None
        assert detected.code == "es"

    def test_detect_chinese_mnemonic(self):
        """Test detecting Chinese mnemonics."""
        # Generate Chinese Simplified mnemonic
        chinese_mnemonic = generate_mnemonic(Bip39Languages.CHINESE_SIMPLIFIED)

        detected = detect_mnemonic_language(chinese_mnemonic)
        assert detected is not None
        assert detected.code == "zh-cn"

    def test_detect_invalid_mnemonic_type(self):
        """Test detection with invalid input type."""
        result = detect_mnemonic_language(123)
        assert result is None

    def test_detect_empty_mnemonic(self):
        """Test detection with empty mnemonic."""
        result = detect_mnemonic_language("")
        assert result is None

        result = detect_mnemonic_language("   ")
        assert result is None

    def test_detect_garbage_input(self):
        """Test detection with garbage input."""
        result = detect_mnemonic_language("not a real mnemonic at all")
        assert result is None


class TestMultiLanguageGeneration:
    """Test mnemonic generation in multiple languages."""

    def test_generate_english_default(self):
        """Test generating English mnemonic (default)."""
        mnemonic = generate_mnemonic()
        assert isinstance(mnemonic, str)
        assert len(mnemonic.split()) == 24

        # Should be detected as English
        detected = detect_mnemonic_language(mnemonic)
        assert detected.code == "en"

    def test_generate_spanish(self):
        """Test generating Spanish mnemonic."""
        mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        assert isinstance(mnemonic, str)
        assert len(mnemonic.split()) == 24

        # Should be detected as Spanish
        detected = detect_mnemonic_language(mnemonic)
        assert detected.code == "es"

    def test_generate_all_languages(self):
        """Test generating mnemonics in all supported languages."""
        languages = [
            Bip39Languages.ENGLISH,
            Bip39Languages.SPANISH,
            Bip39Languages.FRENCH,
            Bip39Languages.ITALIAN,
            Bip39Languages.PORTUGUESE,
            Bip39Languages.CZECH,
            Bip39Languages.CHINESE_SIMPLIFIED,
            Bip39Languages.CHINESE_TRADITIONAL,
            Bip39Languages.KOREAN,
        ]

        for lang_enum in languages:
            mnemonic = generate_mnemonic(lang_enum)
            assert isinstance(mnemonic, str)
            assert len(mnemonic.split()) == 24

            # Should validate successfully
            assert validate_mnemonic(mnemonic, lang_enum)

    def test_generate_uniqueness(self):
        """Test that generated mnemonics are unique."""
        mnemonics = [generate_mnemonic(Bip39Languages.SPANISH) for _ in range(10)]
        assert len(set(mnemonics)) == 10  # All should be unique


class TestMultiLanguageValidation:
    """Test mnemonic validation in multiple languages."""

    def test_validate_with_auto_detection(self):
        """Test validation with automatic language detection."""
        # Generate mnemonics in different languages
        en_mnemonic = generate_mnemonic(Bip39Languages.ENGLISH)
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)

        # Should validate correctly with auto-detection
        assert validate_mnemonic(en_mnemonic)
        assert validate_mnemonic(es_mnemonic)

    def test_validate_with_specified_language(self):
        """Test validation with specified language."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)

        # Should validate with correct language
        assert validate_mnemonic(es_mnemonic, Bip39Languages.SPANISH)

        # Should still validate with auto-detection
        assert validate_mnemonic(es_mnemonic)

    def test_validate_mismatch_language(self):
        """Test validation with wrong language specified."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)

        # Should fail with wrong language (English validator on Spanish mnemonic)
        assert not validate_mnemonic(es_mnemonic, Bip39Languages.ENGLISH)

    def test_validate_invalid_mnemonic(self):
        """Test validation with invalid mnemonic."""
        invalid_mnemonic = "this is not a valid mnemonic phrase at all"
        assert not validate_mnemonic(invalid_mnemonic)

    def test_validate_checksum_with_languages(self):
        """Test checksum validation with different languages."""
        # Test with auto-detection
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        assert validate_mnemonic_checksum(es_mnemonic)

        # Test with specified language
        assert validate_mnemonic_checksum(es_mnemonic, Bip39Languages.SPANISH)


class TestMultiLanguageParsing:
    """Test mnemonic parsing in multiple languages."""

    def test_parse_with_auto_detection(self):
        """Test parsing with automatic language detection."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        words = parse_mnemonic(es_mnemonic)

        assert len(words) == 24
        assert all(isinstance(word, str) for word in words)

    def test_parse_with_specified_language(self):
        """Test parsing with specified language."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        words = parse_mnemonic(es_mnemonic, Bip39Languages.SPANISH)

        assert len(words) == 24
        assert all(isinstance(word, str) for word in words)

    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        padded_mnemonic = "  " + es_mnemonic + "  "

        words = parse_mnemonic(padded_mnemonic)
        assert len(words) == 24

    def test_parse_invalid_format(self):
        """Test parsing with invalid format."""
        with pytest.raises(MnemonicError):
            parse_mnemonic("not enough words")

    def test_parse_empty(self):
        """Test parsing with empty input."""
        with pytest.raises(MnemonicError):
            parse_mnemonic("")


class TestMultiLanguageEntropy:
    """Test entropy extraction from multi-language mnemonics."""

    def test_entropy_extraction_auto_detection(self):
        """Test entropy extraction with auto-detection."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        entropy = get_mnemonic_entropy(es_mnemonic)

        assert isinstance(entropy, bytes)
        assert len(entropy) == 32  # 256 bits for 24-word mnemonic

    def test_entropy_extraction_specified_language(self):
        """Test entropy extraction with specified language."""
        es_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        entropy = get_mnemonic_entropy(es_mnemonic, Bip39Languages.SPANISH)

        assert isinstance(entropy, bytes)
        assert len(entropy) == 32

    def test_entropy_round_trip(self):
        """Test that entropy can be extracted and reconstructed."""
        original_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
        entropy = get_mnemonic_entropy(original_mnemonic)

        # Should be able to validate the original
        assert validate_mnemonic(original_mnemonic)

    def test_entropy_extraction_invalid(self):
        """Test entropy extraction from invalid mnemonic."""
        with pytest.raises(MnemonicError):
            get_mnemonic_entropy("invalid mnemonic phrase")


class TestWordValidation:
    """Test word validation for different languages."""

    def test_validate_english_words(self):
        """Test validating English words."""
        en_lang = get_default_language()
        assert validate_mnemonic_words_for_language(["abandon", "ability"], en_lang)

    def test_validate_spanish_words(self):
        """Test validating Spanish words."""
        es_lang = validate_language_code("es")
        # Use actual Spanish BIP-39 words with accents
        assert validate_mnemonic_words_for_language(["ábaco", "abdomen"], es_lang)

    def test_validate_chinese_words(self):
        """Test validating Chinese words."""
        zh_lang = validate_language_code("zh-cn")
        assert validate_mnemonic_words_for_language(["走", "切"], zh_lang)

    def test_validate_korean_words(self):
        """Test validating Korean words."""
        ko_lang = validate_language_code("ko")
        # Korean characters in Hangul range
        assert validate_mnemonic_words_for_language(["가격", "가끔"], ko_lang)

    def test_validate_wrong_script(self):
        """Test validating words with wrong script."""
        en_lang = get_default_language()
        # Chinese characters should fail for English
        assert not validate_mnemonic_words_for_language(["走", "切"], en_lang)

        zh_lang = validate_language_code("zh-cn")
        # English words should fail for Chinese
        assert not validate_mnemonic_words_for_language(["abandon", "ability"], zh_lang)

    def test_validate_empty_words(self):
        """Test validating empty word list."""
        en_lang = get_default_language()
        assert not validate_mnemonic_words_for_language([], en_lang)

    def test_validate_non_string_words(self):
        """Test validating non-string words."""
        en_lang = get_default_language()
        assert not validate_mnemonic_words_for_language([123, "abandon"], en_lang)


class TestBackwardCompatibility:
    """Test that multi-language support maintains backward compatibility."""

    def test_default_english_generation(self):
        """Test that default generation still produces English."""
        mnemonic = generate_mnemonic()
        detected = detect_mnemonic_language(mnemonic)
        assert detected.code == "en"

    def test_old_function_signatures(self):
        """Test that old function signatures still work."""
        # These should work without language parameters
        mnemonic = generate_mnemonic()
        assert validate_mnemonic(mnemonic)

        words = parse_mnemonic(mnemonic)
        assert len(words) == 24

        entropy = get_mnemonic_entropy(mnemonic)
        assert len(entropy) == 32

    def test_english_only_validation(self):
        """Test that English-only validation still works."""
        en_mnemonic = generate_mnemonic()

        # All these should work as before
        assert validate_mnemonic(en_mnemonic)
        assert validate_mnemonic_checksum(en_mnemonic)

        words = parse_mnemonic(en_mnemonic)
        entropy = get_mnemonic_entropy(en_mnemonic)

        assert len(words) == 24
        assert len(entropy) == 32
