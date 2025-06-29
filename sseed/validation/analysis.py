"""Unified mnemonic analysis engine for comprehensive validation.

This module provides comprehensive mnemonic analysis by integrating existing
validation components into a unified analysis engine with scoring and reporting.
"""

import logging
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from ..bip39 import get_mnemonic_entropy
from ..bip85.security import get_security_hardening
from ..entropy.custom import validate_entropy_quality
from ..exceptions import ValidationError
from ..languages import (
    SUPPORTED_LANGUAGES,
    detect_mnemonic_language,
)
from ..validation.crypto import validate_mnemonic_checksum
from ..validation.input import validate_mnemonic_words

logger = logging.getLogger(__name__)


class MnemonicAnalysisResult:
    """Results of comprehensive mnemonic analysis."""

    def __init__(self) -> None:
        self.overall_score: int = 0
        self.overall_status: str = "unknown"
        self.timestamp: str = ""
        self.analysis_duration_ms: float = 0.0

        # Individual check results
        self.format_check: Dict[str, Any] = {}
        self.language_check: Dict[str, Any] = {}
        self.checksum_check: Dict[str, Any] = {}
        self.entropy_analysis: Dict[str, Any] = {}
        self.security_analysis: Dict[str, Any] = {}
        self.weak_patterns: Dict[str, Any] = {}

        # Recommendations and warnings
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.security_notes: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary."""
        return {
            "overall_score": self.overall_score,
            "overall_status": self.overall_status,
            "timestamp": self.timestamp,
            "analysis_duration_ms": self.analysis_duration_ms,
            "checks": {
                "format": self.format_check,
                "language": self.language_check,
                "checksum": self.checksum_check,
                "entropy_analysis": self.entropy_analysis,
                "security_analysis": self.security_analysis,
                "weak_patterns": self.weak_patterns,
            },
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "security_notes": self.security_notes,
        }

    def is_valid(self) -> bool:
        """Check if mnemonic passes all critical validations."""
        return (
            self.format_check.get("status") == "pass"
            and self.checksum_check.get("status") == "pass"
            and self.overall_score >= 70
        )

    def is_high_quality(self) -> bool:
        """Check if mnemonic is high quality (score >= 85)."""
        return self.overall_score >= 85


class MnemonicAnalyzer:
    """Comprehensive mnemonic analyzer integrating all validation components."""

    def __init__(self) -> None:
        self.security_hardening = get_security_hardening()

    def analyze_comprehensive(
        self,
        mnemonic: str,
        expected_language: Optional[str] = None,
        strict_mode: bool = False,
    ) -> MnemonicAnalysisResult:
        """Perform comprehensive mnemonic analysis.

        Args:
            mnemonic: The mnemonic phrase to analyze
            expected_language: Expected language code (optional)
            strict_mode: Enable strict validation mode

        Returns:
            MnemonicAnalysisResult with comprehensive analysis
        """
        start_time = time.perf_counter()
        result = MnemonicAnalysisResult()
        result.timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        try:
            logger.info("Starting comprehensive mnemonic analysis")

            # 1. Format validation
            self._analyze_format(mnemonic, result)

            # 2. Language detection and validation
            self._analyze_language(mnemonic, result, expected_language)

            # 3. Checksum validation
            self._analyze_checksum(mnemonic, result)

            # 4. Entropy analysis (if format is valid)
            if result.format_check.get("status") == "pass":
                self._analyze_entropy(mnemonic, result)

            # 5. Security analysis
            self._analyze_security(mnemonic, result, strict_mode)

            # 6. Weak pattern detection
            self._analyze_weak_patterns(mnemonic, result)

            # 7. Calculate overall score and status
            self._calculate_overall_assessment(result)

            # 8. Generate recommendations
            self._generate_recommendations(result)

            # Record analysis duration
            end_time = time.perf_counter()
            result.analysis_duration_ms = (end_time - start_time) * 1000

            logger.info(
                "Comprehensive analysis completed: score=%d, status=%s, duration=%.2fms",
                result.overall_score,
                result.overall_status,
                result.analysis_duration_ms,
            )

            return result

        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            result.overall_status = "error"
            result.warnings.append(f"Analysis failed: {str(e)}")
            return result

    def _analyze_format(self, mnemonic: str, result: MnemonicAnalysisResult) -> None:
        """Analyze mnemonic format and structure."""
        try:
            words = mnemonic.strip().split()
            word_count = len(words)

            # Use existing validation
            validate_mnemonic_words(words)

            result.format_check = {
                "status": "pass",
                "word_count": word_count,
                "unique_words": len(set(words)),
                "message": f"Valid format with {word_count} words",
                "details": {
                    "has_duplicates": len(words) != len(set(words)),
                    "empty_words": any(not word.strip() for word in words),
                    "word_lengths": [len(word) for word in words],
                },
            }

        except ValidationError as e:
            result.format_check = {
                "status": "fail",
                "error": str(e),
                "message": "Invalid mnemonic format",
                "word_count": len(mnemonic.strip().split()) if mnemonic.strip() else 0,
            }
            result.warnings.append(f"Format validation failed: {str(e)}")

    def _analyze_language(
        self,
        mnemonic: str,
        result: MnemonicAnalysisResult,
        expected_language: Optional[str] = None,
    ) -> None:
        """Analyze language detection and validation."""
        try:
            detected_lang_info = detect_mnemonic_language(mnemonic)

            if detected_lang_info:
                detected_lang = detected_lang_info.code

                result.language_check = {
                    "status": "pass",
                    "detected": detected_lang,
                    "detected_name": detected_lang_info.name,
                    "confidence": getattr(detected_lang_info, "confidence", "high"),
                    "message": f"Language: {detected_lang_info.name} ({detected_lang})",
                }

                # Check for language mismatch
                if expected_language and detected_lang != expected_language:
                    expected_lang_info = SUPPORTED_LANGUAGES.get(expected_language)
                    result.language_check["status"] = "warning"
                    result.language_check["expected"] = expected_language
                    result.language_check["expected_name"] = (
                        expected_lang_info.name if expected_lang_info else "Unknown"
                    )
                    result.language_check["mismatch"] = True
                    result.warnings.append(
                        f"Language mismatch: detected {detected_lang_info.name}, "
                        f"expected {expected_lang_info.name if expected_lang_info else expected_language}"
                    )
                else:
                    result.language_check["mismatch"] = False

            else:
                result.language_check = {
                    "status": "fail",
                    "message": "Could not detect language",
                    "detected": None,
                }
                result.warnings.append("Language detection failed")

        except Exception as e:
            result.language_check = {
                "status": "error",
                "error": str(e),
                "message": "Language analysis failed",
            }
            result.warnings.append(f"Language analysis error: {str(e)}")

    def _analyze_checksum(self, mnemonic: str, result: MnemonicAnalysisResult) -> None:
        """Analyze BIP-39 checksum validation."""
        try:
            # Use existing validation
            is_valid = validate_mnemonic_checksum(mnemonic)

            if is_valid:
                result.checksum_check = {
                    "status": "pass",
                    "message": "Valid BIP-39 checksum",
                    "algorithm": "BIP-39 SHA256",
                }
            else:
                result.checksum_check = {
                    "status": "fail",
                    "message": "Invalid BIP-39 checksum",
                    "algorithm": "BIP-39 SHA256",
                }
                result.warnings.append("BIP-39 checksum validation failed")

        except Exception as e:
            result.checksum_check = {
                "status": "error",
                "error": str(e),
                "message": "Checksum validation failed",
            }
            result.warnings.append(f"Checksum validation error: {str(e)}")

    def _analyze_entropy(self, mnemonic: str, result: MnemonicAnalysisResult) -> None:
        """Analyze entropy quality of the mnemonic."""
        try:
            # Extract entropy from mnemonic
            entropy_bytes = get_mnemonic_entropy(mnemonic)

            # Use existing entropy quality validation
            entropy_quality = validate_entropy_quality(entropy_bytes)

            result.entropy_analysis = {
                "status": "pass" if entropy_quality.is_acceptable else "warning",
                "score": entropy_quality.score,
                "is_acceptable": entropy_quality.is_acceptable,
                "is_good_quality": entropy_quality.is_good_quality(),
                "entropy_bytes": len(entropy_bytes),
                "entropy_bits": len(entropy_bytes) * 8,
                "message": entropy_quality.get_summary(),
                "warnings": entropy_quality.warnings,
                "recommendations": entropy_quality.recommendations,
                "details": {
                    "byte_diversity": self._calculate_byte_diversity(entropy_bytes),
                    "pattern_analysis": self._analyze_entropy_patterns(entropy_bytes),
                },
            }

            # Add entropy warnings to overall warnings
            if entropy_quality.warnings:
                result.warnings.extend(
                    [f"Entropy: {w}" for w in entropy_quality.warnings]
                )

        except Exception as e:
            result.entropy_analysis = {
                "status": "error",
                "error": str(e),
                "message": "Entropy analysis failed",
            }
            result.warnings.append(f"Entropy analysis error: {str(e)}")

    def _analyze_security(
        self, mnemonic: str, result: MnemonicAnalysisResult, strict_mode: bool = False
    ) -> None:
        """Analyze security aspects using BIP85 security hardening."""
        try:
            # Extract entropy for security analysis
            entropy_bytes = get_mnemonic_entropy(mnemonic)

            # Use BIP85 security hardening for validation
            security_valid = self.security_hardening.validate_entropy_quality(
                entropy_bytes, min_entropy_bits=128
            )

            result.security_analysis = {
                "status": "pass" if security_valid else "fail",
                "entropy_bits": len(entropy_bytes) * 8,
                "min_required_bits": 128,
                "meets_security_threshold": security_valid,
                "strict_mode": strict_mode,
                "message": (
                    "Meets security requirements"
                    if security_valid
                    else "Below security threshold"
                ),
                "details": {
                    "has_weak_patterns": self.security_hardening._has_weak_patterns(
                        entropy_bytes
                    ),
                    "passes_randomness_test": self.security_hardening._passes_chi_square_test(
                        entropy_bytes
                    ),
                },
            }

            if not security_valid:
                result.warnings.append("Entropy does not meet security requirements")
                result.security_notes.append(
                    "Consider regenerating with system entropy"
                )

        except Exception as e:
            result.security_analysis = {
                "status": "error",
                "error": str(e),
                "message": "Security analysis failed",
            }
            result.warnings.append(f"Security analysis error: {str(e)}")

    def _analyze_weak_patterns(
        self, mnemonic: str, result: MnemonicAnalysisResult
    ) -> None:
        """Analyze for weak mnemonic patterns."""
        try:
            words = mnemonic.strip().split()

            # Check for repeated words
            word_counts: Dict[str, int] = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            repeated_words = [word for word, count in word_counts.items() if count > 1]

            # Check for sequential patterns
            sequential_patterns = self._detect_sequential_patterns(words)

            # Check for common weak mnemonics
            weak_signatures = self._detect_weak_signatures(words)

            status = "pass"
            issues = []

            if repeated_words:
                status = "warning"
                issues.append(f"Repeated words: {', '.join(repeated_words)}")

            if sequential_patterns:
                status = "warning"
                issues.append(f"Sequential patterns detected: {sequential_patterns}")

            if weak_signatures:
                status = "warning"
                issues.append(f"Weak signatures: {', '.join(weak_signatures)}")

            result.weak_patterns = {
                "status": status,
                "repeated_words": repeated_words,
                "sequential_patterns": sequential_patterns,
                "weak_signatures": weak_signatures,
                "message": (
                    "; ".join(issues) if issues else "No obvious weak patterns detected"
                ),
                "details": {
                    "word_frequency": word_counts,
                    "unique_word_ratio": len(set(words)) / len(words),
                },
            }

            if issues:
                result.warnings.extend([f"Weak pattern: {issue}" for issue in issues])

        except Exception as e:
            result.weak_patterns = {
                "status": "error",
                "error": str(e),
                "message": "Weak pattern analysis failed",
            }
            result.warnings.append(f"Weak pattern analysis error: {str(e)}")

    def _calculate_overall_assessment(self, result: MnemonicAnalysisResult) -> None:
        """Calculate overall score and status."""
        score = 100

        # Format check (critical)
        if result.format_check.get("status") == "fail":
            score = 0
            result.overall_status = "fail"
            return
        elif result.format_check.get("status") == "error":
            score -= 50

        # Checksum check (critical)
        if result.checksum_check.get("status") == "fail":
            score = 0
            result.overall_status = "fail"
            return
        elif result.checksum_check.get("status") == "error":
            score -= 50

        # Language check (moderate impact)
        if result.language_check.get("status") == "warning":
            score -= 10
        elif result.language_check.get("status") in ["fail", "error"]:
            score -= 20

        # Entropy analysis (high impact)
        entropy_score = result.entropy_analysis.get("score", 100)
        if entropy_score < 100:
            score -= (100 - entropy_score) * 0.3  # 30% weight

        # Security analysis (high impact)
        if not result.security_analysis.get("meets_security_threshold", True):
            score -= 30

        # Weak patterns (moderate impact)
        if result.weak_patterns.get("status") == "warning":
            score -= 15

        # Ensure score is within bounds
        score = max(0, min(100, int(score)))
        result.overall_score = score

        # Determine status
        if score >= 85:
            result.overall_status = "excellent"
        elif score >= 70:
            result.overall_status = "good"
        elif score >= 50:
            result.overall_status = "acceptable"
        elif score >= 30:
            result.overall_status = "poor"
        else:
            result.overall_status = "fail"

    def _generate_recommendations(self, result: MnemonicAnalysisResult) -> None:
        """Generate recommendations based on analysis results."""
        recommendations = []

        if result.overall_score < 70:
            recommendations.append("Consider regenerating mnemonic with system entropy")

        if result.entropy_analysis.get("score", 100) < 80:
            recommendations.append("Entropy quality could be improved")

        if result.weak_patterns.get("repeated_words"):
            recommendations.append("Avoid using repeated words in mnemonics")

        if not result.security_analysis.get("meets_security_threshold", True):
            recommendations.append(
                "Use stronger entropy source for security-critical applications"
            )

        if result.language_check.get("mismatch"):
            recommendations.append("Verify expected language matches detected language")

        # Add entropy-specific recommendations
        entropy_recs = result.entropy_analysis.get("recommendations", [])
        recommendations.extend(entropy_recs)

        result.recommendations = recommendations

    def _calculate_byte_diversity(self, entropy_bytes: bytes) -> float:
        """Calculate byte diversity ratio."""
        if len(entropy_bytes) == 0:
            return 0.0
        unique_bytes = len(set(entropy_bytes))
        return unique_bytes / min(len(entropy_bytes), 256)

    def _analyze_entropy_patterns(self, entropy_bytes: bytes) -> Dict[str, Any]:
        """Analyze entropy for patterns."""
        return {
            "all_zeros": entropy_bytes == b"\x00" * len(entropy_bytes),
            "all_ones": entropy_bytes == b"\xff" * len(entropy_bytes),
            "has_repeating_bytes": len(set(entropy_bytes)) < len(entropy_bytes) / 4,
            "byte_distribution": (
                "uniform"
                if len(set(entropy_bytes)) > len(entropy_bytes) / 2
                else "skewed"
            ),
        }

    def _detect_sequential_patterns(self, words: List[str]) -> List[str]:
        """Detect sequential patterns in word list."""
        patterns = []

        # Check for alphabetical sequences
        for i in range(len(words) - 2):
            if words[i] < words[i + 1] < words[i + 2]:
                patterns.append(f"alphabetical sequence at positions {i}-{i+2}")

        return patterns

    def _detect_weak_signatures(self, words: List[str]) -> List[str]:
        """Detect known weak mnemonic signatures."""
        signatures = []

        # Check for common test mnemonics
        test_patterns = [
            "abandon",
            "test",
            "example",
            "sample",
        ]

        for pattern in test_patterns:
            if any(pattern in word.lower() for word in words):
                signatures.append(f"contains test pattern: {pattern}")

        return signatures


def analyze_mnemonic_comprehensive(
    mnemonic: str, expected_language: Optional[str] = None, strict_mode: bool = False
) -> Dict[str, Any]:
    """Public interface for comprehensive mnemonic analysis.

    Args:
        mnemonic: The mnemonic phrase to analyze
        expected_language: Expected language code (optional)
        strict_mode: Enable strict validation mode

    Returns:
        Dictionary containing comprehensive analysis results
    """
    analyzer = MnemonicAnalyzer()
    result = analyzer.analyze_comprehensive(mnemonic, expected_language, strict_mode)
    return result.to_dict()
