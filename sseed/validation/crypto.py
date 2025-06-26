"""Cryptographic validation for BIP-39 and SLIP-39 operations.

This module provides validation functions for cryptographic operations including
checksum validation, entropy verification, and mnemonic integrity checks.
"""

import logging
from typing import Optional

from bip_utils import (
    Bip39Languages,
    Bip39MnemonicValidator,
)

from sseed.languages import (
    detect_mnemonic_language,
    get_language_by_bip_enum,
)

logger = logging.getLogger(__name__)


def validate_mnemonic_checksum(
    mnemonic: str, language: Optional[Bip39Languages] = None
) -> bool:
    """Validate BIP-39 mnemonic checksum with language support.

    Validates that a mnemonic has a correct BIP-39 checksum using the specified
    or auto-detected language.

    Args:
        mnemonic: BIP-39 mnemonic string to validate.
        language: Optional language. If None, language will be auto-detected.

    Returns:
        True if checksum is valid, False otherwise.

    Example:
        >>> # Auto-detection
        >>> validate_mnemonic_checksum("abandon ability able about above absent")
        True

        >>> # Explicit language
        >>> from bip_utils import Bip39Languages
        >>> validate_mnemonic_checksum("abandon ability", Bip39Languages.ENGLISH)
        False
    """
    try:
        if not isinstance(mnemonic, str) or not mnemonic.strip():
            logger.warning("Invalid mnemonic input for checksum validation")
            return False

        # Normalize mnemonic
        normalized_mnemonic = mnemonic.strip().lower()

        # Language detection and validation
        lang_info = None
        if language is None:
            # Attempt automatic language detection
            detected_lang_info = detect_mnemonic_language(normalized_mnemonic)
            if detected_lang_info:
                language = detected_lang_info.bip_enum
                lang_info = detected_lang_info
                logger.debug(
                    "Auto-detected language for checksum validation: %s",
                    detected_lang_info.name,
                )
            else:
                # Fall back to English if detection fails
                language = Bip39Languages.ENGLISH
                logger.warning(
                    "Language detection failed for checksum validation, using English"
                )
        else:
            # Get language info for explicit language
            try:
                lang_info = get_language_by_bip_enum(language)
                logger.debug(
                    "Using explicit language for checksum validation: %s",
                    lang_info.name,
                )
            except Exception as lang_error:  # pylint: disable=broad-exception-caught
                logger.debug("Could not get language info: %s", lang_error)

        # Validate checksum using BIP-39 library
        validator = Bip39MnemonicValidator(language)
        is_valid: bool = bool(validator.IsValid(normalized_mnemonic))

        if is_valid:
            lang_name = lang_info.name if lang_info else str(language)
            logger.debug("Checksum validation successful for %s mnemonic", lang_name)
        else:
            lang_name = lang_info.name if lang_info else str(language)
            logger.debug("Checksum validation failed for %s mnemonic", lang_name)

        return is_valid

    except Exception as error:
        logger.warning("Error during checksum validation: %s", error)
        return False


def validate_entropy_length(entropy: bytes) -> bool:
    """Validate that entropy has correct length for BIP-39.

    Args:
        entropy: Entropy bytes to validate.

    Returns:
        True if entropy length is valid for BIP-39.
    """
    if not isinstance(entropy, bytes):
        return False  # type: ignore[unreachable]

    # BIP-39 supports entropy lengths: 128, 160, 192, 224, 256 bits
    valid_lengths = {16, 20, 24, 28, 32}  # bytes
    return len(entropy) in valid_lengths
