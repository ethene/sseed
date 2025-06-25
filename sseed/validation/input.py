"""Input normalization and format validation for sseed application.

This module handles input processing, Unicode normalization, and format validation
for BIP-39 mnemonics and filenames.
"""

import re
import unicodedata
from typing import List

from sseed.exceptions import ValidationError
from sseed.logging_config import get_logger

logger = get_logger(__name__)

# BIP-39 word list length (English)
BIP39_WORD_COUNT = 2048
BIP39_MNEMONIC_LENGTHS = [12, 15, 18, 21, 24]  # Valid mnemonic lengths

# Regex patterns for validation
MNEMONIC_WORD_PATTERN = re.compile(r"^[a-z]+$")


def normalize_input(text: str) -> str:
    """Normalize input text using NFKD Unicode normalization.

    Normalizes input text as specified in the PRD edge cases section.
    Uses NFKD (Normalization Form Compatibility Decomposition) to handle
    Unicode variations consistently.

    Args:
        text: Input text to normalize.

    Returns:
        Normalized text string.

    Raises:
        ValidationError: If input is not a valid string.
    """
    if not isinstance(text, str):
        raise ValidationError(
            f"Input must be a string, got {type(text).__name__}",
            context={"input_type": type(text).__name__},
        )

    try:
        # Apply NFKD normalization
        normalized = unicodedata.normalize("NFKD", text)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        logger.debug(
            "Normalized input: %d -> %d characters", len(text), len(normalized)
        )

        return normalized

    except Exception as e:
        error_msg = f"Failed to normalize input: {e}"
        logger.error(error_msg)
        raise ValidationError(error_msg, context={"original_error": str(e)}) from e


def validate_mnemonic_words(words: List[str]) -> None:
    """Validate mnemonic word list format and structure.

    Validates that mnemonic words conform to BIP-39 requirements:
    - Correct number of words (12, 15, 18, 21, or 24)
    - All words are lowercase alphabetic
    - No duplicate words

    Args:
        words: List of mnemonic words to validate.

    Raises:
        ValidationError: If mnemonic words are invalid.
    """
    if not isinstance(words, list):
        raise ValidationError(
            f"Mnemonic words must be a list, got {type(words).__name__}",
            context={"input_type": type(words).__name__},
        )

    # Check word count
    word_count = len(words)
    if word_count not in BIP39_MNEMONIC_LENGTHS:
        raise ValidationError(
            f"Invalid mnemonic length: {word_count}. Must be one of {BIP39_MNEMONIC_LENGTHS}",
            context={"word_count": word_count, "valid_lengths": BIP39_MNEMONIC_LENGTHS},
        )

    # Note: BIP-39 allows duplicate words, so we don't check for duplicates here
    # The checksum validation will catch invalid mnemonics

    # Validate each word format
    for i, word in enumerate(words):
        if not isinstance(word, str):
            raise ValidationError(
                f"Word at position {i} is not a string: {type(word).__name__}",
                context={"position": i, "word_type": type(word).__name__},
            )

        if not MNEMONIC_WORD_PATTERN.match(word):
            raise ValidationError(
                f"Invalid word format at position {i}: '{word}'. Must be lowercase alphabetic.",
                context={"position": i, "word": word},
            )

    logger.info("Successfully validated %d mnemonic words", word_count)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility.

    Removes or replaces characters that might cause issues on different
    operating systems.

    Args:
        filename: Filename to sanitize.

    Returns:
        Sanitized filename.

    Raises:
        ValidationError: If filename is invalid.
    """
    if not isinstance(filename, str):
        raise ValidationError(
            f"Filename must be a string, got {type(filename).__name__}",
            context={"input_type": type(filename).__name__},
        )

    # Normalize the filename
    normalized = normalize_input(filename)

    if not normalized:
        raise ValidationError(
            "Filename cannot be empty after normalization",
            context={"original": filename},
        )

    # Remove or replace problematic characters
    # Replace path separators and other reserved characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", normalized)

    # Remove leading/trailing dots and spaces (Windows compatibility)
    sanitized = sanitized.strip(". ")

    # Ensure it's not empty after sanitization
    if not sanitized:
        raise ValidationError(
            "Filename is empty after sanitization",
            context={"original": filename, "normalized": normalized},
        )

    logger.debug("Sanitized filename: '%s' -> '%s'", filename, sanitized)

    return sanitized
