"""Input normalization and format validation for sseed application.

This module handles input processing, Unicode normalization, and format validation
for BIP-39 mnemonics and filenames with multi-language support.
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

# Multi-language word pattern: Unicode word characters excluding ASCII uppercase
# This pattern accepts lowercase ASCII, Unicode letters, and combining marks
# while rejecting ASCII uppercase letters (which are not in BIP-39 wordlists)
MNEMONIC_WORD_PATTERN = re.compile(r"^(?![A-Z])[\w\u0300-\u036f]+$", re.UNICODE)


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
    """Validate mnemonic word format with multi-language Unicode support.

    Validates that all words match expected BIP-39 format patterns including
    support for Unicode characters in non-Latin scripts (Chinese, Korean)
    and accented characters in Latin scripts (Spanish, French, etc.).

    Args:
        words: List of mnemonic words to validate.

    Raises:
        ValidationError: If any word fails format validation.

    Example:
        >>> # English words
        >>> validate_mnemonic_words(['abandon', 'ability', 'able'])

        >>> # Spanish words with accents
        >>> validate_mnemonic_words(['ábaco', 'abdomen', 'abeja'])

        >>> # Chinese words
        >>> validate_mnemonic_words(['的', '一', '是'])
    """
    if not words:
        raise ValidationError(
            "Empty word list provided",
            context={"word_count": 0},
        )

    for i, word in enumerate(words):
        if not isinstance(word, str):
            raise ValidationError(
                f"Word at position {i + 1} is not a string: {type(word).__name__}",
                context={"position": i + 1, "word_type": type(word).__name__},
            )

        if not word:
            raise ValidationError(
                f"Empty word at position {i + 1}",
                context={"position": i + 1},
            )

        # Normalize the word for validation (handle combining characters)
        normalized_word = unicodedata.normalize("NFKD", word.strip())

        # Check against multi-language pattern
        if not MNEMONIC_WORD_PATTERN.match(normalized_word):
            raise ValidationError(
                f"Invalid word format at position {i + 1}: '{word}'",
                context={"position": i + 1, "word": word},
            )


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
