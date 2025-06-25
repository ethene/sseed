"""Cryptographic validation for sseed application.

This module handles cryptographic validation operations, primarily BIP-39
mnemonic checksum validation using the bip_utils library.
"""

from bip_utils import Bip39MnemonicValidator

from sseed.exceptions import ValidationError
from sseed.logging_config import get_logger
from sseed.validation.input import (
    normalize_input,
    validate_mnemonic_words,
)

logger = get_logger(__name__)


def validate_mnemonic_checksum(mnemonic: str) -> bool:
    """Validate BIP-39 mnemonic checksum using bip_utils validator.

    Implements comprehensive mnemonic checksum validation as required
    in Phase 5, step 19. Uses the bip_utils library for checksum verification.

    Args:
        mnemonic: BIP-39 mnemonic string to validate.

    Returns:
        True if checksum is valid, False otherwise.

    Raises:
        ValidationError: If validation encounters an error.
    """
    try:
        # Normalize input
        normalized_mnemonic = normalize_input(mnemonic)

        if not normalized_mnemonic:
            logger.warning("Empty mnemonic provided for checksum validation")
            return False

        # Parse words and validate format first
        words = normalized_mnemonic.split()
        validate_mnemonic_words(words)

        # Use bip_utils validator for comprehensive checksum validation
        validator = Bip39MnemonicValidator()
        is_valid: bool = bool(validator.IsValid(normalized_mnemonic))

        if is_valid:
            logger.info("Mnemonic checksum validation: VALID (%d words)", len(words))
        else:
            logger.warning(
                "Mnemonic checksum validation: INVALID (%d words)", len(words)
            )

        return is_valid

    except Exception as e:
        error_msg = f"Error during mnemonic checksum validation: {e}"
        logger.error(error_msg)
        raise ValidationError(error_msg, context={"original_error": str(e)}) from e
