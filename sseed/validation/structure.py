"""Structure validation for sseed application.

This module handles validation of SLIP-39 structure elements including
group thresholds, shard collections, and duplicate detection.
"""

# pylint: disable=cyclic-import

import re
from typing import (
    List,
    Tuple,
)

from sseed.exceptions import ValidationError
from sseed.logging_config import get_logger
from sseed.validation.input import normalize_input

logger = get_logger(__name__)

# Regex patterns for validation
GROUP_THRESHOLD_PATTERN = re.compile(r"^(\d+)-of-(\d+)$")


def validate_group_threshold(group_config: str) -> Tuple[int, int]:
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


def detect_duplicate_shards(shards: List[str]) -> List[str]:
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


def validate_shard_integrity(shards: List[str]) -> None:
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
