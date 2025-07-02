"""Comprehensive tests for sseed.validation.analysis module."""

import time
from unittest.mock import (
    Mock,
    patch,
)

from sseed.exceptions import ValidationError
from sseed.validation.analysis import (
    MnemonicAnalysisResult,
    MnemonicAnalyzer,
    analyze_mnemonic_comprehensive,
)


class TestMnemonicAnalysisResult:
    """Test MnemonicAnalysisResult class."""

    def test_init_creates_instance(self):
        """Test MnemonicAnalysisResult initialization."""
        result = MnemonicAnalysisResult()

        assert result.overall_score == 0
        assert result.overall_status == "unknown"
        assert result.timestamp == ""
        assert result.analysis_duration_ms == 0.0

        # Individual check results
        assert result.format_check == {}
        assert result.language_check == {}
        assert result.checksum_check == {}
        assert result.entropy_analysis == {}
        assert result.security_analysis == {}
        assert result.weak_patterns == {}

        # Lists
        assert result.warnings == []
        assert result.recommendations == []
        assert result.security_notes == []

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        result = MnemonicAnalysisResult()
        result.overall_score = 85
        result.overall_status = "excellent"
        result.timestamp = "2023-01-01 12:00:00 UTC"
        result.analysis_duration_ms = 123.45

        result.format_check = {"status": "pass", "word_count": 12}
        result.warnings = ["test warning"]
        result.recommendations = ["test recommendation"]
        result.security_notes = ["test security note"]

        result_dict = result.to_dict()

        assert result_dict["overall_score"] == 85
        assert result_dict["overall_status"] == "excellent"
        assert result_dict["timestamp"] == "2023-01-01 12:00:00 UTC"
        assert result_dict["analysis_duration_ms"] == 123.45

        assert "checks" in result_dict
        assert result_dict["checks"]["format"] == {"status": "pass", "word_count": 12}

        assert result_dict["warnings"] == ["test warning"]
        assert result_dict["recommendations"] == ["test recommendation"]
        assert result_dict["security_notes"] == ["test security note"]

    def test_is_valid_true(self):
        """Test is_valid returns True for valid results."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "pass"}
        result.checksum_check = {"status": "pass"}
        result.overall_score = 75

        assert result.is_valid() is True

    def test_is_valid_false_format_fail(self):
        """Test is_valid returns False when format fails."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "fail"}
        result.checksum_check = {"status": "pass"}
        result.overall_score = 75

        assert result.is_valid() is False

    def test_is_valid_false_checksum_fail(self):
        """Test is_valid returns False when checksum fails."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "pass"}
        result.checksum_check = {"status": "fail"}
        result.overall_score = 75

        assert result.is_valid() is False

    def test_is_valid_false_low_score(self):
        """Test is_valid returns False when score is too low."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "pass"}
        result.checksum_check = {"status": "pass"}
        result.overall_score = 60  # Below 70 threshold

        assert result.is_valid() is False

    def test_is_high_quality_true(self):
        """Test is_high_quality returns True for high scores."""
        result = MnemonicAnalysisResult()
        result.overall_score = 90

        assert result.is_high_quality() is True

    def test_is_high_quality_false(self):
        """Test is_high_quality returns False for lower scores."""
        result = MnemonicAnalysisResult()
        result.overall_score = 80  # Below 85 threshold

        assert result.is_high_quality() is False


class TestMnemonicAnalyzer:
    """Test MnemonicAnalyzer class."""

    def setup_method(self):
        """Set up test instance."""
        with patch("sseed.validation.analysis.get_security_hardening") as mock_security:
            mock_security.return_value = Mock()
            self.analyzer = MnemonicAnalyzer()

    def test_init_creates_instance(self):
        """Test MnemonicAnalyzer initialization."""
        with patch("sseed.validation.analysis.get_security_hardening") as mock_security:
            mock_hardening = Mock()
            mock_security.return_value = mock_hardening

            analyzer = MnemonicAnalyzer()

            assert analyzer.security_hardening == mock_hardening
            mock_security.assert_called_once()

    @patch("sseed.validation.analysis.time.perf_counter")
    @patch("sseed.validation.analysis.time.strftime")
    @patch("sseed.validation.analysis.time.gmtime")
    def test_analyze_comprehensive_basic_flow(
        self, mock_gmtime, mock_strftime, mock_perf_counter
    ):
        """Test comprehensive analysis basic flow."""
        # Mock time functions
        mock_perf_counter.side_effect = [0.0, 0.123]  # start, end
        mock_strftime.return_value = "2023-01-01 12:00:00 UTC"
        mock_gmtime.return_value = time.struct_time((2023, 1, 1, 12, 0, 0, 0, 1, 0))

        # Mock all analysis methods
        with patch.object(self.analyzer, "_analyze_format") as mock_format:
            with patch.object(self.analyzer, "_analyze_language") as mock_lang:
                with patch.object(self.analyzer, "_analyze_checksum") as mock_checksum:
                    with patch.object(
                        self.analyzer, "_analyze_entropy"
                    ) as mock_entropy:
                        with patch.object(
                            self.analyzer, "_analyze_security"
                        ) as mock_security:
                            with patch.object(
                                self.analyzer, "_analyze_weak_patterns"
                            ) as mock_patterns:
                                with patch.object(
                                    self.analyzer, "_calculate_overall_assessment"
                                ) as mock_assess:
                                    with patch.object(
                                        self.analyzer, "_generate_recommendations"
                                    ) as mock_recs:

                                        # Set up format check to pass for entropy analysis
                                        def set_format_pass(mnemonic, result):
                                            result.format_check = {"status": "pass"}

                                        mock_format.side_effect = set_format_pass

                                        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
                                        result = self.analyzer.analyze_comprehensive(
                                            mnemonic
                                        )

                                        # Verify all methods were called
                                        mock_format.assert_called_once()
                                        mock_lang.assert_called_once()
                                        mock_checksum.assert_called_once()
                                        mock_entropy.assert_called_once()  # Should be called since format passes
                                        mock_security.assert_called_once()
                                        mock_patterns.assert_called_once()
                                        mock_assess.assert_called_once()
                                        mock_recs.assert_called_once()

                                        # Verify result properties
                                        assert (
                                            result.timestamp
                                            == "2023-01-01 12:00:00 UTC"
                                        )
                                        assert result.analysis_duration_ms == 123.0

    def test_analyze_comprehensive_entropy_skipped_on_format_fail(self):
        """Test entropy analysis is skipped when format fails."""
        with patch.object(self.analyzer, "_analyze_format") as mock_format:
            with patch.object(self.analyzer, "_analyze_language"):
                with patch.object(self.analyzer, "_analyze_checksum"):
                    with patch.object(
                        self.analyzer, "_analyze_entropy"
                    ) as mock_entropy:
                        with patch.object(self.analyzer, "_analyze_security"):
                            with patch.object(self.analyzer, "_analyze_weak_patterns"):
                                with patch.object(
                                    self.analyzer, "_calculate_overall_assessment"
                                ):
                                    with patch.object(
                                        self.analyzer, "_generate_recommendations"
                                    ):

                                        # Set up format check to fail
                                        def set_format_fail(mnemonic, result):
                                            result.format_check = {"status": "fail"}

                                        mock_format.side_effect = set_format_fail

                                        mnemonic = "invalid mnemonic"
                                        self.analyzer.analyze_comprehensive(mnemonic)

                                        # Entropy analysis should not be called
                                        mock_entropy.assert_not_called()

    def test_analyze_comprehensive_exception_handling(self):
        """Test exception handling in comprehensive analysis."""
        with patch.object(
            self.analyzer, "_analyze_format", side_effect=Exception("Test error")
        ):
            mnemonic = "test mnemonic"
            result = self.analyzer.analyze_comprehensive(mnemonic)

            assert result.overall_status == "error"
            assert "Analysis failed: Test error" in result.warnings

    @patch("sseed.validation.analysis.validate_mnemonic_words")
    def test_analyze_format_success(self, mock_validate):
        """Test successful format analysis."""
        mock_validate.return_value = True

        result = MnemonicAnalysisResult()
        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

        self.analyzer._analyze_format(mnemonic, result)

        assert result.format_check["status"] == "pass"
        assert result.format_check["word_count"] == 12
        assert result.format_check["unique_words"] == 12
        assert "Valid format with 12 words" in result.format_check["message"]
        assert result.format_check["details"]["has_duplicates"] is False

    @patch("sseed.validation.analysis.validate_mnemonic_words")
    def test_analyze_format_with_duplicates(self, mock_validate):
        """Test format analysis with duplicate words."""
        mock_validate.return_value = True

        result = MnemonicAnalysisResult()
        mnemonic = "abandon abandon able about above absent absorb abstract absurd abuse access accident"

        self.analyzer._analyze_format(mnemonic, result)

        assert result.format_check["status"] == "pass"
        assert result.format_check["word_count"] == 12
        assert result.format_check["unique_words"] == 11  # One duplicate
        assert result.format_check["details"]["has_duplicates"] is True

    @patch("sseed.validation.analysis.validate_mnemonic_words")
    def test_analyze_format_validation_error(self, mock_validate):
        """Test format analysis with validation error."""
        mock_validate.side_effect = ValidationError("Invalid word count")

        result = MnemonicAnalysisResult()
        mnemonic = "invalid mnemonic"

        self.analyzer._analyze_format(mnemonic, result)

        assert result.format_check["status"] == "fail"
        assert "Invalid word count" in result.format_check["error"]
        assert "Format validation failed" in result.warnings[0]

    @patch("sseed.validation.analysis.detect_mnemonic_language")
    def test_analyze_language_success(self, mock_detect):
        """Test successful language analysis."""
        mock_lang_info = Mock()
        mock_lang_info.code = "en"
        mock_lang_info.name = "English"
        mock_detect.return_value = mock_lang_info

        result = MnemonicAnalysisResult()
        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

        self.analyzer._analyze_language(mnemonic, result)

        assert result.language_check["status"] == "pass"
        assert result.language_check["detected"] == "en"
        assert result.language_check["detected_name"] == "English"
        assert result.language_check["mismatch"] is False

    @patch("sseed.validation.analysis.detect_mnemonic_language")
    @patch("sseed.validation.analysis.SUPPORTED_LANGUAGES")
    def test_analyze_language_mismatch(self, mock_supported, mock_detect):
        """Test language analysis with mismatch."""
        mock_lang_info = Mock()
        mock_lang_info.code = "en"
        mock_lang_info.name = "English"
        mock_detect.return_value = mock_lang_info

        # Mock expected language info
        mock_expected_info = Mock()
        mock_expected_info.name = "Spanish"
        mock_supported.get.return_value = mock_expected_info

        result = MnemonicAnalysisResult()
        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

        self.analyzer._analyze_language(mnemonic, result, expected_language="es")

        assert result.language_check["status"] == "warning"
        assert result.language_check["expected"] == "es"
        assert result.language_check["mismatch"] is True
        assert "Language mismatch" in result.warnings[0]

    @patch("sseed.validation.analysis.detect_mnemonic_language")
    def test_analyze_language_detection_failed(self, mock_detect):
        """Test language analysis when detection fails."""
        mock_detect.return_value = None

        result = MnemonicAnalysisResult()
        mnemonic = "invalid mnemonic"

        self.analyzer._analyze_language(mnemonic, result)

        assert result.language_check["status"] == "fail"
        assert result.language_check["detected"] is None
        assert "Language detection failed" in result.warnings

    @patch("sseed.validation.analysis.validate_mnemonic_checksum")
    def test_analyze_checksum_valid(self, mock_validate):
        """Test checksum analysis with valid checksum."""
        mock_validate.return_value = True

        result = MnemonicAnalysisResult()
        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

        self.analyzer._analyze_checksum(mnemonic, result)

        assert result.checksum_check["status"] == "pass"
        assert result.checksum_check["message"] == "Valid BIP-39 checksum"
        assert result.checksum_check["algorithm"] == "BIP-39 SHA256"

    @patch("sseed.validation.analysis.validate_mnemonic_checksum")
    def test_analyze_checksum_invalid(self, mock_validate):
        """Test checksum analysis with invalid checksum."""
        mock_validate.return_value = False

        result = MnemonicAnalysisResult()
        mnemonic = "invalid checksum mnemonic phrase here to test validation failure"

        self.analyzer._analyze_checksum(mnemonic, result)

        assert result.checksum_check["status"] == "fail"
        assert result.checksum_check["message"] == "Invalid BIP-39 checksum"
        assert "BIP-39 checksum validation failed" in result.warnings

    @patch("sseed.validation.analysis.get_mnemonic_entropy")
    @patch("sseed.validation.analysis.validate_entropy_quality")
    def test_analyze_entropy_success(self, mock_validate_quality, mock_get_entropy):
        """Test successful entropy analysis."""
        mock_get_entropy.return_value = b"x" * 16  # 16 bytes = 128 bits

        mock_quality = Mock()
        mock_quality.is_acceptable = True
        mock_quality.score = 85
        mock_quality.warnings = []
        mock_quality.recommendations = ["Use hardware RNG"]
        mock_quality.get_summary.return_value = "Good entropy quality"
        mock_quality.is_good_quality.return_value = True
        mock_validate_quality.return_value = mock_quality

        result = MnemonicAnalysisResult()
        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

        with patch.object(self.analyzer, "_calculate_byte_diversity", return_value=0.8):
            with patch.object(
                self.analyzer,
                "_analyze_entropy_patterns",
                return_value={"test": "pattern"},
            ):
                self.analyzer._analyze_entropy(mnemonic, result)

        assert result.entropy_analysis["status"] == "pass"
        assert result.entropy_analysis["score"] == 85
        assert result.entropy_analysis["is_acceptable"] is True
        assert result.entropy_analysis["entropy_bytes"] == 16
        assert result.entropy_analysis["entropy_bits"] == 128

    def test_calculate_byte_diversity(self):
        """Test byte diversity calculation."""
        # All unique bytes
        entropy1 = b"\x01\x02\x03\x04"
        diversity1 = self.analyzer._calculate_byte_diversity(entropy1)
        assert diversity1 == 1.0  # 4 unique bytes / 4 total bytes

        # Some repeated bytes
        entropy2 = b"\x01\x01\x02\x03"
        diversity2 = self.analyzer._calculate_byte_diversity(entropy2)
        assert diversity2 == 0.75  # 3 unique bytes / 4 total bytes

        # Empty bytes
        entropy3 = b""
        diversity3 = self.analyzer._calculate_byte_diversity(entropy3)
        assert diversity3 == 0.0

    def test_analyze_entropy_patterns(self):
        """Test entropy pattern analysis."""
        # All zeros
        entropy1 = b"\x00\x00\x00\x00"
        patterns1 = self.analyzer._analyze_entropy_patterns(entropy1)
        assert patterns1["all_zeros"] is True
        assert patterns1["all_ones"] is False

        # All ones
        entropy2 = b"\xff\xff\xff\xff"
        patterns2 = self.analyzer._analyze_entropy_patterns(entropy2)
        assert patterns2["all_zeros"] is False
        assert patterns2["all_ones"] is True

        # Mixed entropy
        entropy3 = b"\x01\x02\x03\x04"
        patterns3 = self.analyzer._analyze_entropy_patterns(entropy3)
        assert patterns3["all_zeros"] is False
        assert patterns3["all_ones"] is False
        assert patterns3["byte_distribution"] == "uniform"

    def test_detect_sequential_patterns(self):
        """Test sequential pattern detection."""
        # Alphabetical sequence - algorithm finds overlapping sequences
        words1 = ["apple", "banana", "cherry", "date"]
        patterns1 = self.analyzer._detect_sequential_patterns(words1)
        assert len(patterns1) == 2  # Two overlapping sequences: 0-2 and 1-3
        assert "alphabetical sequence" in patterns1[0]

        # No sequence
        words2 = ["zebra", "apple", "cherry", "banana"]
        patterns2 = self.analyzer._detect_sequential_patterns(words2)
        assert len(patterns2) == 0

    def test_detect_weak_signatures(self):
        """Test weak signature detection."""
        # Contains test pattern
        words1 = ["abandon", "ability", "test", "about"]
        signatures1 = self.analyzer._detect_weak_signatures(words1)
        assert len(signatures1) >= 1
        assert any("abandon" in sig or "test" in sig for sig in signatures1)

        # No weak patterns
        words2 = ["random", "secure", "mnemonic", "phrase"]
        signatures2 = self.analyzer._detect_weak_signatures(words2)
        assert len(signatures2) == 0

    def test_analyze_weak_patterns_success(self):
        """Test weak pattern analysis success."""
        result = MnemonicAnalysisResult()
        mnemonic = "zebra yellow xray winter victory uncle trust soldier perfect ocean"

        self.analyzer._analyze_weak_patterns(mnemonic, result)

        assert result.weak_patterns["status"] == "pass"
        assert result.weak_patterns["repeated_words"] == []
        assert "No obvious weak patterns detected" in result.weak_patterns["message"]

    def test_analyze_weak_patterns_repeated_words(self):
        """Test weak pattern analysis with repeated words."""
        result = MnemonicAnalysisResult()
        mnemonic = "word word different phrase here for testing analysis quality check"

        self.analyzer._analyze_weak_patterns(mnemonic, result)

        assert result.weak_patterns["status"] == "warning"
        assert "word" in result.weak_patterns["repeated_words"]
        assert "Repeated words" in result.weak_patterns["message"]

    def test_calculate_overall_assessment_excellent(self):
        """Test overall assessment calculation for excellent score."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "pass"}
        result.checksum_check = {"status": "pass"}
        result.language_check = {"status": "pass"}
        result.entropy_analysis = {"score": 95}
        result.security_analysis = {"meets_security_threshold": True}
        result.weak_patterns = {"status": "pass"}

        self.analyzer._calculate_overall_assessment(result)

        assert result.overall_score >= 85
        assert result.overall_status == "excellent"

    def test_calculate_overall_assessment_format_fail(self):
        """Test overall assessment with format failure."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "fail"}
        result.checksum_check = {"status": "pass"}

        self.analyzer._calculate_overall_assessment(result)

        assert result.overall_score == 0
        assert result.overall_status == "fail"

    def test_calculate_overall_assessment_checksum_fail(self):
        """Test overall assessment with checksum failure."""
        result = MnemonicAnalysisResult()
        result.format_check = {"status": "pass"}
        result.checksum_check = {"status": "fail"}

        self.analyzer._calculate_overall_assessment(result)

        assert result.overall_score == 0
        assert result.overall_status == "fail"

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        result = MnemonicAnalysisResult()
        result.overall_score = 60  # Below 70
        result.entropy_analysis = {
            "score": 70,
            "recommendations": ["Use better entropy"],
        }
        result.weak_patterns = {"repeated_words": ["word1"]}
        result.security_analysis = {"meets_security_threshold": False}
        result.language_check = {"mismatch": True}

        self.analyzer._generate_recommendations(result)

        assert "Consider regenerating mnemonic" in result.recommendations[0]
        assert "Entropy quality could be improved" in result.recommendations
        assert "Avoid using repeated words in mnemonics" in result.recommendations
        assert (
            "Use stronger entropy source for security-critical applications"
            in result.recommendations
        )
        assert (
            "Verify expected language matches detected language"
            in result.recommendations
        )
        assert "Use better entropy" in result.recommendations


class TestPublicInterface:
    """Test public interface functions."""

    @patch("sseed.validation.analysis.MnemonicAnalyzer")
    def test_analyze_mnemonic_comprehensive(self, mock_analyzer_class):
        """Test public analyze_mnemonic_comprehensive function."""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {"test": "result"}
        mock_analyzer.analyze_comprehensive.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer

        mnemonic = "test mnemonic"
        result = analyze_mnemonic_comprehensive(
            mnemonic, expected_language="en", strict_mode=True
        )

        mock_analyzer_class.assert_called_once()
        mock_analyzer.analyze_comprehensive.assert_called_once_with(
            mnemonic, "en", True
        )
        mock_result.to_dict.assert_called_once()
        assert result == {"test": "result"}


class TestIntegrationWithRealData:
    """Integration tests with real data (mocked dependencies)."""

    def setup_method(self):
        """Set up for integration tests."""
        with patch("sseed.validation.analysis.get_security_hardening") as mock_security:
            mock_security.return_value = Mock()
            self.analyzer = MnemonicAnalyzer()

    @patch("sseed.validation.analysis.validate_mnemonic_words")
    @patch("sseed.validation.analysis.detect_mnemonic_language")
    @patch("sseed.validation.analysis.validate_mnemonic_checksum")
    @patch("sseed.validation.analysis.get_mnemonic_entropy")
    @patch("sseed.validation.analysis.validate_entropy_quality")
    def test_real_mnemonic_analysis_flow(
        self,
        mock_validate_quality,
        mock_get_entropy,
        mock_validate_checksum,
        mock_detect_lang,
        mock_validate_words,
    ):
        """Test analysis flow with realistic mocked data."""
        # Set up mocks
        mock_validate_words.return_value = True

        mock_lang_info = Mock()
        mock_lang_info.code = "en"
        mock_lang_info.name = "English"
        mock_detect_lang.return_value = mock_lang_info

        mock_validate_checksum.return_value = True
        mock_get_entropy.return_value = b"x" * 16

        mock_quality = Mock()
        mock_quality.is_acceptable = True
        mock_quality.score = 85
        mock_quality.warnings = []
        mock_quality.recommendations = []
        mock_quality.get_summary.return_value = "Good quality"
        mock_quality.is_good_quality.return_value = True
        mock_validate_quality.return_value = mock_quality

        # Mock security hardening
        self.analyzer.security_hardening.validate_entropy_quality.return_value = True
        self.analyzer.security_hardening._has_weak_patterns.return_value = False
        self.analyzer.security_hardening._passes_chi_square_test.return_value = True

        mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
        result = self.analyzer.analyze_comprehensive(mnemonic)

        # Verify the analysis completed successfully
        assert result.overall_score > 0
        assert result.overall_status != "error"
        assert result.format_check["status"] == "pass"
        assert result.language_check["status"] == "pass"
        assert result.checksum_check["status"] == "pass"
        assert result.entropy_analysis["status"] == "pass"
        assert len(result.timestamp) > 0
        assert result.analysis_duration_ms >= 0
