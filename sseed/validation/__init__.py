"""Validation module for sseed application.

This module provides comprehensive validation functionality organized by concern:
- Input validation and normalization
- Cryptographic validation (checksums)
- Structure validation (groups, shards)
- Advanced analysis and cross-tool compatibility (Phase 2)

All functions are re-exported for backward compatibility with existing code.
"""

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
        analyze_mnemonic_comprehensive,
        MnemonicAnalysisResult,
        SecurityAnalyzer,
    )
    _ANALYSIS_AVAILABLE = True
except ImportError:
    _ANALYSIS_AVAILABLE = False

try:
    from sseed.validation.cross_tool import (
        test_cross_tool_compatibility,
        get_available_tools,
        is_tool_available,
        CrossToolCompatibilityResult,
        CrossToolTester,
    )
    _CROSS_TOOL_AVAILABLE = True
except ImportError:
    _CROSS_TOOL_AVAILABLE = False

# Phase 3 modules - Batch processing and advanced formatting
try:
    from sseed.validation.batch import (
        validate_batch_files,
        BatchValidator,
        BatchValidationResult,
    )
    _BATCH_AVAILABLE = True
except ImportError:
    _BATCH_AVAILABLE = False

try:
    from sseed.validation.formatters import (
        format_validation_output,
        ValidationFormatter,
    )
    _FORMATTERS_AVAILABLE = True
except ImportError:
    _FORMATTERS_AVAILABLE = False

# Phase 4 modules - Backup verification
try:
    from sseed.validation.backup_verification import (
        verify_backup_integrity,
        BackupVerifier,
        BackupVerificationResult,
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
]

# Add Phase 2 functions if available
if _ANALYSIS_AVAILABLE:
    __all__.extend([
        "analyze_mnemonic_comprehensive",
        "MnemonicAnalysisResult",
        "SecurityAnalyzer",
    ])

if _CROSS_TOOL_AVAILABLE:
    __all__.extend([
        "test_cross_tool_compatibility",
        "get_available_tools",
        "is_tool_available",
        "CrossToolCompatibilityResult",
        "CrossToolTester",
    ])

# Add Phase 3 functions if available
if _BATCH_AVAILABLE:
    __all__.extend([
        "validate_batch_files",
        "BatchValidator",
        "BatchValidationResult",
    ])

if _FORMATTERS_AVAILABLE:
    __all__.extend([
        "format_validation_output",
        "ValidationFormatter",
    ])

# Add Phase 4 functions if available
if _BACKUP_VERIFICATION_AVAILABLE:
    __all__.extend([
        "verify_backup_integrity",
        "BackupVerifier",
        "BackupVerificationResult",
    ])

# Module availability flags
ANALYSIS_AVAILABLE = _ANALYSIS_AVAILABLE
CROSS_TOOL_AVAILABLE = _CROSS_TOOL_AVAILABLE
BATCH_AVAILABLE = _BATCH_AVAILABLE
FORMATTERS_AVAILABLE = _FORMATTERS_AVAILABLE
BACKUP_VERIFICATION_AVAILABLE = _BACKUP_VERIFICATION_AVAILABLE
