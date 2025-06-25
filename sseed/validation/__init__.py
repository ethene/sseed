"""Validation module for sseed application.

This module provides comprehensive validation functionality organized by concern:
- Input validation and normalization
- Cryptographic validation (checksums)
- Structure validation (groups, shards)

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
