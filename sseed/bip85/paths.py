"""BIP85 derivation path validation and formatting utilities.

Provides comprehensive validation and formatting for BIP85 derivation
parameters, following SSeed's existing validation patterns.
"""

import re
from typing import (
    Dict,
    Optional,
    Tuple,
    Union,
)

from sseed.logging_config import get_logger

from .exceptions import Bip85ValidationError

logger = get_logger(__name__)

# BIP85 application constants
BIP85_APPLICATIONS = {
    39: "BIP39 Mnemonic",
    2: "HD-Seed WIF",
    32: "XPRV",
    128: "Hex",
    9999: "Password",  # Non-standard but commonly used
}

# Valid word counts for BIP39 (application 39)
BIP39_VALID_WORD_COUNTS = {12, 15, 18, 21, 24}

# Valid entropy lengths for different applications (in bytes)
APPLICATION_ENTROPY_LENGTHS = {
    39: {12: 16, 15: 20, 18: 24, 21: 28, 24: 32},  # BIP39: word_count -> entropy_bytes
    2: {512: 64},  # HD-Seed: always 512 bits
    32: {512: 64},  # XPRV: always 512 bits
    128: list(range(16, 65)),  # Hex: 16-64 bytes
    9999: list(range(10, 129)),  # Password: 10-128 chars
}


def validate_bip85_parameters(
    application: int, length: int, index: int, strict: bool = True
) -> None:
    """Validate BIP85 derivation parameters.

    Args:
        application: BIP85 application identifier.
        length: Application-specific length parameter.
        index: Child derivation index.
        strict: Whether to enforce strict validation rules.

    Raises:
        Bip85ValidationError: If any parameter is invalid.

    Example:
        >>> validate_bip85_parameters(39, 12, 0)  # Valid BIP39
        >>> validate_bip85_parameters(39, 13, 0)  # Raises error
        Traceback (most recent call last):
        ...
        Bip85ValidationError: Invalid word count for BIP39: 13
    """
    logger.debug(
        "Validating BIP85 parameters: app=%d, length=%d, index=%d, strict=%s",
        application,
        length,
        index,
        strict,
    )

    # Validate application
    if not isinstance(application, int):
        raise Bip85ValidationError(
            f"Application must be integer, got {type(application).__name__}",
            parameter="application",
            value=application,
        )

    if not 0 <= application <= 0xFFFFFFFF:
        raise Bip85ValidationError(
            f"Application must be 0-4294967295, got {application}",
            parameter="application",
            value=application,
            valid_range="0 to 4294967295",
        )

    # Validate length
    if not isinstance(length, int):
        raise Bip85ValidationError(
            f"Length must be integer, got {type(length).__name__}",
            parameter="length",
            value=length,
        )

    if not 0 <= length <= 0xFFFFFFFF:
        raise Bip85ValidationError(
            f"Length must be 0-4294967295, got {length}",
            parameter="length",
            value=length,
            valid_range="0 to 4294967295",
        )

    # Validate index
    if not isinstance(index, int):
        raise Bip85ValidationError(
            f"Index must be integer, got {type(index).__name__}",
            parameter="index",
            value=index,
        )

    if not 0 <= index < 2**31:
        raise Bip85ValidationError(
            f"Index must be 0 to 2147483647, got {index}",
            parameter="index",
            value=index,
            valid_range="0 to 2147483647",
        )

    # Application-specific validation (only in strict mode)
    if strict:
        _validate_application_specific_parameters(application, length)

    logger.debug("BIP85 parameters validation passed")


def _validate_application_specific_parameters(application: int, length: int) -> None:
    """Validate application-specific length parameters.

    Args:
        application: BIP85 application identifier.
        length: Application-specific length parameter.

    Raises:
        Bip85ValidationError: If length is invalid for the application.
    """
    if application == 39:  # BIP39
        if length not in BIP39_VALID_WORD_COUNTS:
            raise Bip85ValidationError(
                f"Invalid word count for BIP39: {length}",
                parameter="length",
                value=length,
                valid_range=f"One of {sorted(BIP39_VALID_WORD_COUNTS)}",
            )

    elif application == 2:  # HD-Seed WIF
        if length != 512:
            raise Bip85ValidationError(
                f"HD-Seed WIF length must be 512 bits, got {length}",
                parameter="length",
                value=length,
                valid_range="512",
            )

    elif application == 32:  # XPRV
        if length != 512:
            raise Bip85ValidationError(
                f"XPRV length must be 512 bits, got {length}",
                parameter="length",
                value=length,
                valid_range="512",
            )

    elif application == 128:  # Hex
        if not 16 <= length <= 64:
            raise Bip85ValidationError(
                f"Hex length must be 16-64",
                parameter="length",
                value=length,
                valid_range="16 to 64 bytes",
            )

    elif application == 9999:  # Password (non-standard)
        if not 10 <= length <= 128:
            raise Bip85ValidationError(
                f"Password length must be 10-128 characters, got {length}",
                parameter="length",
                value=length,
                valid_range="10 to 128 characters",
            )


def format_bip85_path(application: int, length: int, index: int) -> str:
    """Format BIP85 derivation path as human-readable string.

    Args:
        application: Application identifier.
        length: Length parameter.
        index: Child index.

    Returns:
        Formatted derivation path string.

    Example:
        >>> format_bip85_path(39, 12, 0)
        "m/83696968'/39'/12'/0'"
    """
    return f"m/83696968'/{application}'/{length}'/{index}'"


def parse_bip85_path(path: str) -> Tuple[int, int, int]:
    """Parse BIP85 derivation path string into components.

    Args:
        path: BIP85 derivation path string.

    Returns:
        Tuple of (application, length, index).

    Raises:
        Bip85ValidationError: If path format is invalid.

    Example:
        >>> parse_bip85_path("m/83696968'/39'/12'/0'")
        (39, 12, 0)
    """
    logger.debug("Parsing BIP85 path: %s", path)

    # BIP85 path pattern: m/83696968'/{app}'/{length}'/{index}'
    pattern = r"^m/83696968'/(\d+)'/(\d+)'/(\d+)'$"
    match = re.match(pattern, path.strip())

    if not match:
        raise Bip85ValidationError(
            f"Invalid BIP85 path format: {path}",
            parameter="path",
            value=path,
            valid_range="m/83696968'/{app}'/{length}'/{index}'",
        )

    try:
        application = int(match.group(1))
        length = int(match.group(2))
        index = int(match.group(3))

        # Validate parsed components
        validate_bip85_parameters(application, length, index)

        logger.debug(
            "Successfully parsed BIP85 path: app=%d, length=%d, index=%d",
            application,
            length,
            index,
        )

        return application, length, index

    except ValueError as e:
        raise Bip85ValidationError(
            f"Invalid numeric values in path: {path}",
            parameter="path",
            value=path,
            context={"parse_error": str(e)},
        ) from e


def get_application_name(application: int) -> str:
    """Get human-readable name for BIP85 application.

    Args:
        application: Application identifier.

    Returns:
        Application name or "Unknown" if not recognized.

    Example:
        >>> get_application_name(39)
        'BIP39 Mnemonic'
        >>> get_application_name(999)
        'Unknown (999)'
    """
    return BIP85_APPLICATIONS.get(application, f"Unknown ({application})")


def calculate_entropy_bytes_needed(application: int, length: int) -> int:
    """Calculate how many entropy bytes are needed for given application/length.

    Args:
        application: BIP85 application identifier.
        length: Application-specific length parameter.

    Returns:
        Number of entropy bytes required.

    Raises:
        Bip85ValidationError: If application/length combination is invalid.

    Example:
        >>> calculate_entropy_bytes_needed(39, 12)  # 12-word BIP39
        16
        >>> calculate_entropy_bytes_needed(39, 24)  # 24-word BIP39
        32
    """
    if application == 39:  # BIP39
        if length not in BIP39_VALID_WORD_COUNTS:
            raise Bip85ValidationError(
                f"Invalid BIP39 word count: {length}",
                parameter="length",
                value=length,
                valid_range=f"One of {sorted(BIP39_VALID_WORD_COUNTS)}",
            )
        entropy_map = {12: 16, 15: 20, 18: 24, 21: 28, 24: 32}
        return entropy_map[length]

    elif application in [2, 32]:  # HD-Seed WIF, XPRV
        return 64  # Always 512 bits = 64 bytes

    elif application == 128:  # Hex
        if not 16 <= length <= 64:
            raise Bip85ValidationError(
                f"Invalid hex length: {length}",
                parameter="length",
                value=length,
                valid_range="16 to 64 bytes",
            )
        return length

    elif application == 9999:  # Password
        # For passwords, we need enough entropy to generate the characters
        # Use length bytes as a reasonable approximation
        if not 10 <= length <= 128:
            raise Bip85ValidationError(
                f"Invalid password length: {length}",
                parameter="length",
                value=length,
                valid_range="10 to 128 characters",
            )
        return min(length, 64)  # Cap at 64 bytes (HMAC-SHA512 output)

    else:
        # For unknown applications, assume they want the full 64 bytes
        logger.warning(
            "Unknown application %d, assuming 64-byte entropy requirement", application
        )
        return 64


def validate_derivation_index_range(
    index: int, max_index: Optional[int] = None
) -> None:
    """Validate derivation index is within acceptable range.

    Args:
        index: Derivation index to validate.
        max_index: Optional maximum index for additional validation.

    Raises:
        Bip85ValidationError: If index is out of range.
    """
    if not 0 <= index < 2**31:
        raise Bip85ValidationError(
            f"Index must be 0 to 2147483647, got {index}",
            parameter="index",
            value=index,
            valid_range="0 to 2147483647",
        )

    if max_index is not None and index > max_index:
        raise Bip85ValidationError(
            f"Index exceeds maximum allowed value: {index} > {max_index}",
            parameter="index",
            value=index,
            valid_range=f"0 to {max_index}",
        )


def format_parameter_summary(
    application: int, length: int, index: int
) -> Dict[str, Union[str, int]]:
    """Format BIP85 parameters as a summary dictionary.

    Args:
        application: Application identifier.
        length: Length parameter.
        index: Child index.

    Returns:
        Dictionary with formatted parameter information.

    Example:
        >>> summary = format_parameter_summary(39, 12, 0)
        >>> summary['application_name']
        'BIP39 Mnemonic'
        >>> summary['entropy_bytes']
        16
    """
    return {
        "application": application,
        "application_name": get_application_name(application),
        "length": length,
        "index": index,
        "derivation_path": format_bip85_path(application, length, index),
        "entropy_bytes": calculate_entropy_bytes_needed(application, length),
    }
