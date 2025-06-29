"""Validation module for sseed application.

This module provides comprehensive validation functionality organized by concern:
- Input validation and normalization
- Cryptographic validation (checksums)
- Structure validation (groups, shards)
- Advanced analysis and cross-tool compatibility (Phase 2)

All functions are re-exported for backward compatibility with existing code.
"""

from typing import (
    Any,
    Dict,
)

# Import all functions from the modular structure
from sseed.validation.crypto import validate_mnemonic_checksum
from sseed.validation.input import (
    BIP39_MNEMONIC_LENGTHS,
    BIP39_WORD_COUNT,
    MNEMONIC_WORD_PATTERN,
    normalize_input,
    sanitize_filename,
    validate_mnemonic_words,
)
from sseed.validation.structure import (
    GROUP_THRESHOLD_PATTERN,
    detect_duplicate_shards,
    validate_group_threshold,
    validate_shard_integrity,
)

# Phase 2 modules - Advanced validation features
try:
    from sseed.validation.analysis import (
        MnemonicAnalysisResult,
        MnemonicAnalyzer,
        analyze_mnemonic_comprehensive,
    )

    _ANALYSIS_AVAILABLE = True
except ImportError:
    _ANALYSIS_AVAILABLE = False

try:
    from sseed.validation.cross_tool import (
        CrossToolCompatibilityResult,
        CrossToolTester,
        get_available_tools,
        is_tool_available,
        test_cross_tool_compatibility,
    )

    _CROSS_TOOL_AVAILABLE = True
except ImportError:
    _CROSS_TOOL_AVAILABLE = False

# Phase 3 modules - Batch processing and advanced formatting
try:
    from sseed.validation.batch import (
        BatchValidationResult,
        BatchValidator,
        validate_batch_files,
    )

    _BATCH_AVAILABLE = True
except ImportError:
    _BATCH_AVAILABLE = False

try:
    from sseed.validation.formatters import (
        ValidationFormatter,
        format_validation_output,
    )

    _FORMATTERS_AVAILABLE = True
except ImportError:
    _FORMATTERS_AVAILABLE = False

# Phase 4 modules - Backup verification
try:
    from sseed.validation.backup_verification import (
        BackupVerificationResult,
        BackupVerifier,
        verify_backup_integrity,
    )

    _BACKUP_VERIFICATION_AVAILABLE = True
except ImportError:
    _BACKUP_VERIFICATION_AVAILABLE = False

# Re-export all public functions for backward compatibility
__all__ = [
    # Constants
    "BIP39_WORD_COUNT",
    "BIP39_MNEMONIC_LENGTHS",
    "MNEMONIC_WORD_PATTERN",
    "GROUP_THRESHOLD_PATTERN",
    # Input validation functions
    "normalize_input",
    "validate_mnemonic_words",
    "sanitize_filename",
    # Cryptographic validation functions
    "validate_mnemonic_checksum",
    # Structure validation functions
    "validate_group_threshold",
    "detect_duplicate_shards",
    "validate_shard_integrity",
    # Convenience CLI validation functions
    "validate_mnemonic_basic",
    "validate_mnemonic_advanced",
    "validate_mnemonic_entropy",
    "validate_mnemonic_compatibility",
]

# Add Phase 2 functions if available
if _ANALYSIS_AVAILABLE:
    __all__.extend(
        [
            "analyze_mnemonic_comprehensive",
            "MnemonicAnalysisResult",
            "MnemonicAnalyzer",
        ]
    )

if _CROSS_TOOL_AVAILABLE:
    __all__.extend(
        [
            "test_cross_tool_compatibility",
            "get_available_tools",
            "is_tool_available",
            "CrossToolCompatibilityResult",
            "CrossToolTester",
        ]
    )

# Add Phase 3 functions if available
if _BATCH_AVAILABLE:
    __all__.extend(
        [
            "validate_batch_files",
            "BatchValidator",
            "BatchValidationResult",
        ]
    )

if _FORMATTERS_AVAILABLE:
    __all__.extend(
        [
            "format_validation_output",
            "ValidationFormatter",
        ]
    )

# Add Phase 4 functions if available
if _BACKUP_VERIFICATION_AVAILABLE:
    __all__.extend(
        [
            "verify_backup_integrity",
            "BackupVerifier",
            "BackupVerificationResult",
        ]
    )


# Convenience validation functions for CLI
def validate_mnemonic_basic(mnemonic: str) -> Dict[str, Any]:
    """Basic mnemonic validation."""
    from ..bip39 import validate_mnemonic
    from ..languages import detect_mnemonic_language

    detected_lang = detect_mnemonic_language(mnemonic)
    is_valid = validate_mnemonic(mnemonic)

    return {
        "is_valid": is_valid,
        "mode": "basic",
        "language": detected_lang.code if detected_lang else "unknown",
        "word_count": len(mnemonic.split()),
    }


def validate_mnemonic_advanced(mnemonic: str) -> Dict[str, Any]:
    """Advanced mnemonic validation with analysis."""
    if _ANALYSIS_AVAILABLE:
        return analyze_mnemonic_comprehensive(mnemonic)
    else:
        return validate_mnemonic_basic(mnemonic)


def validate_mnemonic_entropy(mnemonic: str) -> Dict[str, Any]:
    """Entropy-focused validation."""
    from ..bip39 import get_mnemonic_entropy
    from ..entropy.custom import validate_entropy_quality

    basic_result = validate_mnemonic_basic(mnemonic)
    if basic_result["is_valid"]:
        try:
            entropy_bytes = get_mnemonic_entropy(mnemonic)
            entropy_result = validate_entropy_quality(entropy_bytes)
            basic_result.update(
                {
                    "mode": "entropy",
                    "entropy_analysis": (
                        entropy_result.to_dict()
                        if hasattr(entropy_result, "to_dict")
                        else {}
                    ),
                }
            )
        except Exception as e:
            basic_result["warnings"] = [f"Entropy analysis failed: {e}"]

    return basic_result


def validate_mnemonic_compatibility(mnemonic: str) -> Dict[str, Any]:
    """Cross-tool compatibility validation."""
    if _CROSS_TOOL_AVAILABLE:
        return test_cross_tool_compatibility(mnemonic)
    else:
        result = validate_mnemonic_basic(mnemonic)
        result["mode"] = "compatibility"
        result["warnings"] = ["Cross-tool compatibility testing not available"]
        return result


# Module availability flags
ANALYSIS_AVAILABLE = _ANALYSIS_AVAILABLE
CROSS_TOOL_AVAILABLE = _CROSS_TOOL_AVAILABLE
BATCH_AVAILABLE = _BATCH_AVAILABLE
FORMATTERS_AVAILABLE = _FORMATTERS_AVAILABLE
BACKUP_VERIFICATION_AVAILABLE = _BACKUP_VERIFICATION_AVAILABLE
