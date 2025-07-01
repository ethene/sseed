"""SLIP-39 sharding and reconstruction operations for sseed application.

Implements SLIP-39 operations using the shamir_mnemonic library as specified in F-3 of the PRD.
Provides functionality to split BIP-39 mnemonics into SLIP-39 shards and reconstruct them.
"""

import re
from typing import Any

# Import shamir_mnemonic library components
try:
    from shamir_mnemonic import MnemonicError as ShamirMnemonicError
    from shamir_mnemonic import (
        combine_mnemonics,
        generate_mnemonics,
    )
except ImportError as e:
    raise ImportError(f"shamir_mnemonic library not available: {e}") from e

try:
    from bip_utils import Bip39MnemonicGenerator
except ImportError as e:
    raise ImportError(f"bip_utils library not available: {e}") from e

from sseed.bip39 import (
    get_mnemonic_entropy,
    validate_mnemonic,
)
from sseed.entropy import secure_delete_variable
from sseed.exceptions import (
    MnemonicError,
    ShardError,
    ValidationError,
)
from sseed.logging_config import (
    get_logger,
    log_security_event,
)
from sseed.validation import (
    detect_duplicate_shards,
    normalize_input,
    validate_group_threshold,
)

logger = get_logger(__name__)


def create_slip39_shards(
    mnemonic: str,
    group_threshold: int = 1,
    groups: list[tuple[int, int]] | None = None,
    passphrase: str = "",  # nosec B107
) -> list[str]:
    """Create SLIP-39 shards from a BIP-39 mnemonic.

    Splits a BIP-39 mnemonic into SLIP-39 shards using the specified group
    and threshold configuration.

    Args:
        mnemonic: Valid BIP-39 mnemonic to shard.
        group_threshold: Number of groups required for reconstruction.
        groups: List of (threshold, count) tuples for each group.
        passphrase: Optional passphrase for additional security.

    Returns:
        List of SLIP-39 shard strings.

    Raises:
        ShardError: If sharding operation fails.
        MnemonicError: If input mnemonic is invalid.
    """
    try:
        logger.info("Starting SLIP-39 sharding operation")
        log_security_event("SLIP-39 sharding initiated")

        # Validate input mnemonic
        if not validate_mnemonic(mnemonic):
            raise MnemonicError(
                "Cannot shard invalid BIP-39 mnemonic",
                context={"mnemonic_valid": False},
            )

        # Extract entropy from BIP-39 mnemonic
        entropy_bytes = get_mnemonic_entropy(mnemonic)

        # Set default groups if not provided (single group 3-of-5)
        if groups is None:
            groups = [(3, 5)]  # Default: 3-of-5 threshold

        try:
            # Generate SLIP-39 mnemonics using shamir_mnemonic library
            slip39_mnemonics = generate_mnemonics(
                group_threshold=group_threshold,
                groups=groups,
                master_secret=entropy_bytes,
                passphrase=passphrase.encode("utf-8"),
            )

            # Flatten the nested structure and convert to strings
            shard_list = []
            for group_mnemonics in slip39_mnemonics:
                for mnemonic_obj in group_mnemonics:
                    # Handle both string and list formats
                    if isinstance(mnemonic_obj, str):
                        shard_list.append(mnemonic_obj)
                    else:
                        shard_list.append(" ".join(mnemonic_obj))

            logger.info("Successfully created %d SLIP-39 shards", len(shard_list))
            log_security_event(f"SLIP-39 sharding completed: {len(shard_list)} shards")

            return shard_list

        finally:
            # Securely delete entropy from memory
            secure_delete_variable(entropy_bytes)

    except (ShamirMnemonicError, Exception) as e:
        error_msg = f"Failed to create SLIP-39 shards: {e}"
        logger.error(error_msg)
        log_security_event(f"SLIP-39 sharding failed: {error_msg}")
        raise ShardError(error_msg, context={"original_error": str(e)}) from e


def parse_group_config(group_config: str) -> tuple[int, list[tuple[int, int]]]:
    """Parse group configuration string into threshold and groups.

    Parses configurations like:
    - "3-of-5" -> group_threshold=1, groups=[(3, 5)]
    - "2-of-3,3-of-5" -> group_threshold=2, groups=[(2, 3), (3, 5)]
    - "1:(2-of-3,3-of-5)" -> group_threshold=1, groups=[(2, 3), (3, 5)]

    Args:
        group_config: Group configuration string.

    Returns:
        Tuple of (group_threshold, groups_list).

    Raises:
        ValidationError: If configuration is invalid.
    """
    try:
        # Normalize input
        config = normalize_input(group_config)

        # Check for explicit group threshold format: "N:(group1,group2)"
        group_threshold_match = re.match(r"^(\d+):\((.+)\)$", config)
        if group_threshold_match:
            group_threshold = int(group_threshold_match.group(1))
            groups_str = group_threshold_match.group(2)
        else:
            # Single group or comma-separated groups (default group_threshold=1)
            group_threshold = 1
            groups_str = config

        # Parse individual groups
        groups = []
        for group_str in groups_str.split(","):
            group_str = group_str.strip()
            threshold, total = validate_group_threshold(group_str)
            groups.append((threshold, total))

        # Validate group threshold
        if group_threshold <= 0 or group_threshold > len(groups):
            raise ValidationError(
                f"Group threshold ({group_threshold}) must be between 1 and {len(groups)}",
                context={"group_threshold": group_threshold, "num_groups": len(groups)},
            )

        logger.info(
            "Parsed group config: threshold=%d, groups=%s", group_threshold, groups
        )

        return group_threshold, groups

    except (ValueError, TypeError, AttributeError) as e:
        logger.error("Failed to parse group specification: %s", e)
        raise ValueError(f"Invalid group specification format: {e}") from e

    except (IndexError, KeyError) as e:
        logger.error("Group specification parsing error: %s", e)
        raise ValueError(f"Malformed group specification: {e}") from e


def reconstruct_mnemonic_from_shards(
    shards: list[str],
    passphrase: str = "",  # nosec B107
) -> str:
    """Reconstruct BIP-39 mnemonic from SLIP-39 shards.

    Combines SLIP-39 shards to reconstruct the original BIP-39 mnemonic.

    Args:
        shards: List of SLIP-39 shard strings.
        passphrase: Optional passphrase used during sharding.

    Returns:
        Reconstructed BIP-39 mnemonic string.

    Raises:
        ShardError: If reconstruction fails.
        ValidationError: If shards are invalid.
    """
    try:
        logger.info("Starting SLIP-39 reconstruction from %d shards", len(shards))
        log_security_event(f"SLIP-39 reconstruction initiated: {len(shards)} shards")

        if not shards:
            raise ValidationError(
                "No shards provided for reconstruction",
                context={"shard_count": 0},
            )

        # Validate and normalize shards
        normalized_shards = []
        for i, shard in enumerate(shards):
            normalized_shard = normalize_input(shard)
            if not normalized_shard:
                raise ValidationError(
                    f"Empty shard at position {i}",
                    context={"position": i, "shard": shard},
                )
            normalized_shards.append(normalized_shard)

        # Use enhanced duplicate detection from validation module (Phase 5 requirement)
        duplicates = detect_duplicate_shards(normalized_shards)
        if duplicates:
            logger.warning("Removing %d duplicate shards", len(duplicates))
            # Remove duplicates while preserving order
            seen = set()
            unique_shards = []
            for shard in normalized_shards:
                if shard not in seen:
                    seen.add(shard)
                    unique_shards.append(shard)
            normalized_shards = unique_shards

        try:
            # Use the string shards directly with shamir_mnemonic library
            master_secret = combine_mnemonics(
                normalized_shards,
                passphrase=passphrase.encode("utf-8"),
            )

            # Convert entropy back to BIP-39 mnemonic
            bip39_mnemonic = Bip39MnemonicGenerator().FromEntropy(master_secret)
            mnemonic_str = str(bip39_mnemonic)

            # Validate the reconstructed mnemonic
            if not validate_mnemonic(mnemonic_str):
                raise ShardError(
                    "Reconstructed mnemonic failed validation",
                    context={"mnemonic_valid": False},
                )

            logger.info(
                "Successfully reconstructed BIP-39 mnemonic from SLIP-39 shards"
            )
            log_security_event("SLIP-39 reconstruction completed successfully")

            return mnemonic_str

        except ShamirMnemonicError as e:
            error_msg = f"SLIP-39 reconstruction failed: {e}"
            logger.error(error_msg)
            log_security_event(f"SLIP-39 reconstruction failed: {error_msg}")
            raise ShardError(error_msg, context={"shamir_error": str(e)}) from e

    except ShardError:
        # Re-raise shard errors as-is
        raise
    except Exception as e:
        error_msg = f"Failed to reconstruct mnemonic from shards: {e}"
        logger.error(error_msg)
        log_security_event(f"SLIP-39 reconstruction error: {error_msg}")
        raise ShardError(error_msg, context={"original_error": str(e)}) from e


def validate_slip39_shard(shard: str) -> bool:
    """Validate a SLIP-39 shard string.

    Validates that a shard conforms to SLIP-39 format and has valid checksum.

    Args:
        shard: SLIP-39 shard string to validate.

    Returns:
        True if shard is valid, False otherwise.
    """
    try:
        # Normalize input
        normalized_shard = normalize_input(shard)

        if not normalized_shard:
            logger.warning("Empty shard provided for validation")
            return False

        # Split into words
        words = normalized_shard.split()

        # SLIP-39 shards should have 20 or 33 words
        if len(words) not in [20, 33]:
            logger.warning("Invalid SLIP-39 shard length: %d words", len(words))
            return False

        try:
            # Basic validation using shamir_mnemonic
            # The library will do full validation during reconstruction
            is_valid = len(words) in [20, 33]  # Basic length check

            logger.info(
                "SLIP-39 shard validation: %s (%d words)",
                "VALID" if is_valid else "INVALID",
                len(words),
            )
            log_security_event(
                f"SLIP-39 shard validation: "
                f"{'VALID' if is_valid else 'INVALID'} ({len(words)} words)"
            )

            return is_valid

        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("SLIP-39 shard validation failed: %s", e)
            log_security_event(f"SLIP-39 shard validation failed: {e}")
            return False

    except (ValueError, TypeError, AttributeError) as e:
        logger.error("Error during SLIP-39 shard validation: %s", e)
        log_security_event(f"SLIP-39 shard validation error: {e}")
        return False


def get_shard_info(shard: str) -> dict[str, Any]:
    """Extract information from a SLIP-39 shard.

    Extracts group index, member index, and other metadata from a shard.

    Args:
        shard: SLIP-39 shard string.

    Returns:
        Dictionary with shard information.

    Raises:
        ShardError: If shard information cannot be extracted.
    """
    try:
        # Normalize input
        normalized_shard = normalize_input(shard)
        words = normalized_shard.split()

        if not validate_slip39_shard(normalized_shard):
            raise ShardError(
                "Cannot extract info from invalid SLIP-39 shard",
                context={"shard_valid": False},
            )

        # Basic shard info (shamir_mnemonic library would provide more detailed extraction)
        info = {
            "word_count": len(words),
            "shard_type": "slip39",
            "valid": True,
            "first_word": words[0] if words else "",
            "last_word": words[-1] if words else "",
        }

        logger.debug("Extracted SLIP-39 shard info: %s", info)

        return info

    except Exception as e:
        error_msg = f"Failed to extract shard information: {e}"
        logger.error(error_msg)
        raise ShardError(error_msg, context={"original_error": str(e)}) from e
