"""Input validation and normalization for sseed application.

Implements input validation and Unicode normalization (NFKD) as specified
in step 8 of Phase 2 and edge cases section of the PRD.
"""

import re
import unicodedata

from bip_utils import Bip39MnemonicValidator

from sseed.exceptions import ValidationError
from sseed.logging_config import get_logger

logger = get_logger(__name__)

# BIP-39 word list length (English)
BIP39_WORD_COUNT = 2048
BIP39_MNEMONIC_LENGTHS = [12, 15, 18, 21, 24]  # Valid mnemonic lengths

# Regex patterns for validation
MNEMONIC_WORD_PATTERN = re.compile(r"^[a-z]+$")
GROUP_THRESHOLD_PATTERN = re.compile(r"^(\d+)-of-(\d+)$")


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


def validate_mnemonic_words(words: list[str]) -> None:
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


def validate_group_threshold(group_config: str) -> tuple[int, int]:
    """Validate and parse group threshold configuration.

    Validates group/threshold configuration string in format "M-of-N"
    where M is the threshold and N is the total number of shares.
    Implements threshold logic validation as required in Phase 5, step 20.

    Args:
        group_config: Group configuration string (e.g., "3-of-5").

    Returns:
        Tuple of (threshold, total_shares).

    Raises:
        ValidationError: If group configuration is invalid.
    """
    if not isinstance(group_config, str):
        raise ValidationError(
            f"Group configuration must be a string, got {type(group_config).__name__}",
            context={"input_type": type(group_config).__name__},
        )

    # Normalize the input
    normalized_config = normalize_input(group_config)

    # Match the pattern
    match = GROUP_THRESHOLD_PATTERN.match(normalized_config)
    if not match:
        raise ValidationError(
            f"Invalid group configuration format: '{group_config}'. Expected 'M-of-N' format.",
            context={"config": group_config},
        )

    try:
        threshold = int(match.group(1))
        total_shares = int(match.group(2))
    except ValueError as e:
        raise ValidationError(
            f"Invalid numbers in group configuration: '{group_config}'",
            context={"config": group_config, "error": str(e)},
        ) from e

    # Validate threshold logic - Phase 5 requirement
    if threshold <= 0:
        raise ValidationError(
            f"Threshold must be positive, got: {threshold}",
            context={"threshold": threshold, "total_shares": total_shares},
        )

    if total_shares <= 0:
        raise ValidationError(
            f"Total shares must be positive, got: {total_shares}",
            context={"threshold": threshold, "total_shares": total_shares},
        )

    if threshold > total_shares:
        raise ValidationError(
            f"Threshold ({threshold}) cannot be greater than total shares ({total_shares})",
            context={"threshold": threshold, "total_shares": total_shares},
        )

    # Reasonable limits for SLIP-39
    if total_shares > 16:
        raise ValidationError(
            f"Total shares ({total_shares}) exceeds maximum of 16",
            context={"threshold": threshold, "total_shares": total_shares},
        )

    # Minimum threshold should be meaningful
    if threshold == 1 and total_shares > 1:
        logger.warning(
            "Threshold of 1 provides no security benefit with multiple shares"
        )

    logger.info("Validated group configuration: %d-of-%d", threshold, total_shares)

    return threshold, total_shares


def detect_duplicate_shards(shards: list[str]) -> list[str]:
    """Detect duplicate shards in a list.

    Implements duplicate shard detection as required in Phase 5, step 21.
    Returns a list of duplicate shards found.

    Args:
        shards: List of shard strings to check.

    Returns:
        List of duplicate shard strings.

    Raises:
        ValidationError: If input validation fails.
    """
    if not isinstance(shards, list):
        raise ValidationError(
            f"Shards must be a list, got {type(shards).__name__}",
            context={"input_type": type(shards).__name__},
        )

    if not shards:
        return []

    # Normalize all shards
    normalized_shards = []
    for i, shard in enumerate(shards):
        if not isinstance(shard, str):
            raise ValidationError(
                f"Shard at position {i} is not a string: {type(shard).__name__}",
                context={"position": i, "shard_type": type(shard).__name__},
            )

        normalized_shard = normalize_input(shard)
        if not normalized_shard:
            raise ValidationError(
                f"Empty shard at position {i}",
                context={"position": i},
            )

        normalized_shards.append(normalized_shard)

    # Find duplicates
    seen: set[str] = set()
    duplicates: set[str] = set()

    for shard in normalized_shards:
        if shard in seen:
            duplicates.add(shard)
        else:
            seen.add(shard)

    duplicate_list = list(duplicates)

    if duplicate_list:
        logger.warning("Detected %d duplicate shards", len(duplicate_list))
    else:
        logger.debug("No duplicate shards detected")

    return duplicate_list


def validate_shard_integrity(shards: list[str]) -> None:
    """Validate integrity of shard collection.

    Performs comprehensive validation of a collection of shards:
    - Checks for duplicates
    - Validates each shard format
    - Ensures minimum threshold requirements

    Args:
        shards: List of shard strings to validate.

    Raises:
        ValidationError: If shard integrity validation fails.
    """
    if not isinstance(shards, list):
        raise ValidationError(
            f"Shards must be a list, got {type(shards).__name__}",
            context={"input_type": type(shards).__name__},
        )

    if not shards:
        raise ValidationError(
            "No shards provided for validation",
            context={"shard_count": 0},
        )

    # Check for duplicates
    duplicates = detect_duplicate_shards(shards)
    if duplicates:
        raise ValidationError(
            f"Duplicate shards detected: {len(duplicates)} duplicates found",
            context={
                "duplicate_count": len(duplicates),
                "duplicates": duplicates[:3],
            },  # Show first 3
        )

    # Validate minimum number of shards
    if len(shards) < 2:
        raise ValidationError(
            f"Insufficient shards: {len(shards)}. At least 2 shards required for reconstruction.",
            context={"shard_count": len(shards)},
        )

    # Basic format validation for each shard
    for i, shard in enumerate(shards):
        normalized_shard = normalize_input(shard)
        words = normalized_shard.split()

        # SLIP-39 shards should have 20 or 33 words
        if len(words) not in [20, 33]:
            raise ValidationError(
                f"Invalid shard format at position {i}: {len(words)} words. "
                f"Expected 20 or 33 words.",
                context={"position": i, "word_count": len(words)},
            )

    logger.info("Shard integrity validation passed: %d shards", len(shards))


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
