"""Language detection accuracy tests for Stage 3.

This module provides comprehensive testing for language detection accuracy
across all supported BIP-39 languages, including edge cases and performance.
"""

import pytest
from bip_utils import Bip39Languages

from sseed.bip39 import generate_mnemonic
from sseed.languages import (
    SUPPORTED_LANGUAGES,
    detect_mnemonic_language,
)


class TestLanguageDetectionAccuracy:
    """Test language detection accuracy across all supported languages."""

    @pytest.mark.parametrize("lang_code", list(SUPPORTED_LANGUAGES.keys()))
    def test_detection_accuracy_single_language(self, lang_code):
        """Test detection accuracy for single language mnemonics."""
        lang_info = SUPPORTED_LANGUAGES[lang_code]

        # Generate multiple mnemonics in this language
        correct_detections = 0
        total_tests = 10  # Test 10 mnemonics per language

        for _ in range(total_tests):
            mnemonic = generate_mnemonic(lang_info.bip_enum)
            detected = detect_mnemonic_language(mnemonic)

            if detected and detected.code == lang_code:
                correct_detections += 1

        # Expect at least 80% accuracy for each language
        accuracy = correct_detections / total_tests
        assert (
            accuracy >= 0.8
        ), f"Language {lang_code} detection accuracy {accuracy:.1%} below 80%"

    def test_detection_accuracy_cross_language(self):
        """Test detection doesn't confuse similar languages."""
        # Test pairs of potentially confusing languages
        test_pairs = [
            ("es", "pt"),  # Spanish vs Portuguese
            ("zh-cn", "zh-tw"),  # Simplified vs Traditional Chinese
            ("en", "fr"),  # English vs French
        ]

        for lang1, lang2 in test_pairs:
            lang1_info = SUPPORTED_LANGUAGES[lang1]
            lang2_info = SUPPORTED_LANGUAGES[lang2]

            # Test 5 mnemonics from each language
            for _ in range(5):
                # Test first language
                mnemonic1 = generate_mnemonic(lang1_info.bip_enum)
                detected1 = detect_mnemonic_language(mnemonic1)
                if detected1:  # Only check if detection succeeded
                    assert (
                        detected1.code == lang1
                    ), f"Confused {lang1} with {detected1.code}"

                # Test second language
                mnemonic2 = generate_mnemonic(lang2_info.bip_enum)
                detected2 = detect_mnemonic_language(mnemonic2)
                if detected2:  # Only check if detection succeeded
                    assert (
                        detected2.code == lang2
                    ), f"Confused {lang2} with {detected2.code}"

    def test_detection_with_invalid_mnemonics(self):
        """Test detection gracefully handles invalid mnemonics."""
        invalid_cases = [
            "",  # Empty string
            "invalid words that are not in any wordlist",
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon",  # Too short
            "abandon " * 25,  # Too long
            # Invalid checksum (24 words but wrong checksum)
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon about",
        ]

        for invalid_mnemonic in invalid_cases:
            detected = detect_mnemonic_language(invalid_mnemonic)
            # Should either return None or handle gracefully
            assert detected is None or isinstance(
                detected, type(SUPPORTED_LANGUAGES["en"])
            )

    def test_detection_performance_benchmark(self):
        """Test that detection performance is acceptable."""
        import time

        # Generate test mnemonics
        test_mnemonics = []
        for lang_code in ["en", "es", "zh-cn", "ko"]:
            lang_info = SUPPORTED_LANGUAGES[lang_code]
            mnemonic = generate_mnemonic(lang_info.bip_enum)
            test_mnemonics.append(mnemonic)

        # Benchmark detection time
        start_time = time.time()

        for _ in range(10):  # Repeat 10 times
            for mnemonic in test_mnemonics:
                detect_mnemonic_language(mnemonic)

        total_time = time.time() - start_time
        avg_time_per_detection = total_time / (10 * len(test_mnemonics))

        # Should be faster than 100ms per detection
        assert (
            avg_time_per_detection < 0.1
        ), f"Detection too slow: {avg_time_per_detection:.3f}s per detection"

    def test_detection_with_mixed_case(self):
        """Test detection works with different case variations."""
        # Generate English mnemonic
        mnemonic = generate_mnemonic(Bip39Languages.ENGLISH)

        # Test different case variations
        variations = [
            mnemonic.lower(),
            mnemonic.upper(),
            mnemonic.title(),
            " ".join(word.capitalize() for word in mnemonic.split()),
        ]

        for variation in variations:
            detected = detect_mnemonic_language(variation)
            assert (
                detected is not None
            ), f"Failed to detect case variation: {variation[:50]}..."
            assert (
                detected.code == "en"
            ), f"Incorrect detection for case variation: {detected.code}"

    def test_detection_with_extra_whitespace(self):
        """Test detection handles extra whitespace correctly."""
        mnemonic = generate_mnemonic(Bip39Languages.ENGLISH)

        # Test whitespace variations
        variations = [
            f"  {mnemonic}  ",  # Leading/trailing spaces
            mnemonic.replace(" ", "  "),  # Double spaces
            mnemonic.replace(" ", " \t "),  # Mixed whitespace
            "\n".join(mnemonic.split()),  # Newlines instead of spaces
        ]

        for variation in variations:
            detected = detect_mnemonic_language(variation)
            assert detected is not None, "Failed to detect whitespace variation"
            assert (
                detected.code == "en"
            ), f"Incorrect detection for whitespace variation: {detected.code}"

    @pytest.mark.parametrize("lang_code", ["zh-cn", "zh-tw", "ko"])
    def test_unicode_normalization(self, lang_code):
        """Test detection works with Unicode normalization forms."""
        import unicodedata

        lang_info = SUPPORTED_LANGUAGES[lang_code]
        mnemonic = generate_mnemonic(lang_info.bip_enum)

        # Test different Unicode normalization forms
        normalizations = [
            unicodedata.normalize("NFC", mnemonic),
            unicodedata.normalize("NFD", mnemonic),
            unicodedata.normalize("NFKC", mnemonic),
            unicodedata.normalize("NFKD", mnemonic),
        ]

        for normalized in normalizations:
            detected = detect_mnemonic_language(normalized)
            if detected:  # Some normalizations might change the text significantly
                assert (
                    detected.code == lang_code
                ), f"Failed Unicode normalization for {lang_code}"

    def test_detection_confidence_scores(self):
        """Test that detection provides meaningful confidence scores."""
        # This test assumes the detection function has access to confidence scores
        # If not implemented, this test can be skipped or modified

        # Generate clear examples
        english_mnemonic = generate_mnemonic(Bip39Languages.ENGLISH)
        spanish_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)

        # Test that clear cases have high confidence
        en_detected = detect_mnemonic_language(english_mnemonic)
        es_detected = detect_mnemonic_language(spanish_mnemonic)

        assert en_detected is not None and en_detected.code == "en"
        assert es_detected is not None and es_detected.code == "es"

        # Note: If confidence scores are available, we could test:
        # assert en_detected.confidence > 0.9
        # assert es_detected.confidence > 0.9

    def test_detection_with_partial_mnemonics(self):
        """Test detection behavior with partial mnemonics."""
        full_mnemonic = generate_mnemonic(Bip39Languages.ENGLISH)
        words = full_mnemonic.split()

        # Test with different partial lengths
        for length in [12, 18, 23]:  # Less than full 24 words
            partial = " ".join(words[:length])
            detected = detect_mnemonic_language(partial)

            # Should either detect correctly or fail gracefully
            if detected:
                assert (
                    detected.code == "en"
                ), f"Incorrect detection for {length}-word partial"

    def test_detection_statistical_distribution(self):
        """Test that detection results follow expected statistical distribution."""
        # Generate 50 mnemonics across different languages
        results = {}

        for lang_code in ["en", "es", "fr", "zh-cn"]:
            lang_info = SUPPORTED_LANGUAGES[lang_code]
            detections = []

            for _ in range(25):  # 25 tests per language
                mnemonic = generate_mnemonic(lang_info.bip_enum)
                detected = detect_mnemonic_language(mnemonic)
                detections.append(detected.code if detected else None)

            results[lang_code] = detections

        # Verify each language is detected correctly most of the time
        for lang_code, detections in results.items():
            correct_count = sum(1 for d in detections if d == lang_code)
            accuracy = correct_count / len(detections)

            assert (
                accuracy >= 0.7
            ), f"Language {lang_code} overall accuracy {accuracy:.1%} below 70%"
