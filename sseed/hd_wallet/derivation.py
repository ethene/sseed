"""Derivation path utilities for HD wallets.

Implements BIP32 derivation path parsing, validation, and construction
following BIP44, BIP49, BIP84, and BIP86 standards.

This module provides utilities for working with hierarchical deterministic
wallet derivation paths in a secure and validated manner.
"""

import re
from dataclasses import dataclass
from typing import (
    List,
    Tuple,
)

from sseed.logging_config import get_logger

from .exceptions import InvalidPathError

logger = get_logger(__name__)

# BIP32 path patterns and constants
BIP32_PATH_PATTERN = re.compile(r"^m(/\d+'?)*$")
HARDENED_MARKER = "'"
HARDENED_OFFSET = 0x80000000

# BIP purpose constants
BIP44_PURPOSE = 44  # Legacy addresses
BIP49_PURPOSE = 49  # SegWit P2SH-P2WPKH
BIP84_PURPOSE = 84  # Native SegWit P2WPKH
BIP86_PURPOSE = 86  # Taproot P2TR

# Standard derivation path components
MAX_HARDENED_INDEX = 2**31 - 1
MAX_NON_HARDENED_INDEX = 2**31 - 1


@dataclass
class DerivationPath:
    """Structured derivation path representation.

    Represents a BIP32 hierarchical deterministic derivation path
    with structured access to all components.
    """

    purpose: int
    coin_type: int
    account: int
    change: int
    address_index: int

    @property
    def path_string(self) -> str:
        """Get path as BIP32 string format.

        Returns:
            Formatted derivation path (e.g., "m/84'/0'/0'/0/0").
        """
        return f"m/{self.purpose}'/{self.coin_type}'/{self.account}'/{self.change}/{self.address_index}"

    @property
    def account_path(self) -> str:
        """Get account-level path for extended keys.

        Returns:
            Account-level path (e.g., "m/84'/0'/0'").
        """
        return f"m/{self.purpose}'/{self.coin_type}'/{self.account}'"

    @property
    def purpose_name(self) -> str:
        """Get human-readable purpose name.

        Returns:
            Purpose name (e.g., "BIP84 Native SegWit").
        """
        purpose_names = {
            BIP44_PURPOSE: "BIP44 Legacy",
            BIP49_PURPOSE: "BIP49 SegWit",
            BIP84_PURPOSE: "BIP84 Native SegWit",
            BIP86_PURPOSE: "BIP86 Taproot",
        }
        return purpose_names.get(self.purpose, f"BIP{self.purpose}")

    def __str__(self) -> str:
        """String representation of derivation path."""
        return self.path_string


def validate_path(path: str) -> None:
    """Validate BIP32 derivation path format.

    Validates that the provided path follows BIP32 standard format
    and contains valid component values.

    Args:
        path: Derivation path to validate.

    Raises:
        InvalidPathError: If path format is invalid.

    Example:
        >>> validate_path("m/44'/0'/0'/0/0")  # Valid
        >>> validate_path("invalid")  # Raises InvalidPathError
    """
    if not isinstance(path, str):
        raise InvalidPathError(
            f"Derivation path must be string, got {type(path).__name__}", path=str(path)
        )

    if not path.startswith("m/"):
        raise InvalidPathError(
            "Derivation path must start with 'm/'", path=path, pattern="m/44'/0'/0'/0/0"
        )

    if not BIP32_PATH_PATTERN.match(path):
        raise InvalidPathError(
            "Invalid BIP32 derivation path format", path=path, pattern="m/44'/0'/0'/0/0"
        )

    logger.debug("Validated derivation path: %s", path)


def parse_derivation_path(path: str) -> List[int]:
    """Parse derivation path into component integers.

    Converts a BIP32 derivation path string into a list of integer
    components suitable for BIP32 key derivation.

    Args:
        path: BIP32 derivation path string.

    Returns:
        List of derivation component integers with hardened flag applied.

    Raises:
        InvalidPathError: If path format is invalid.

    Example:
        >>> parse_derivation_path("m/44'/0'/0'/0/0")
        [2147483692, 2147483648, 2147483648, 0, 0]
    """
    validate_path(path)

    components = []
    parts = path.split("/")[1:]  # Skip 'm'

    for i, part in enumerate(parts):
        try:
            if part.endswith(HARDENED_MARKER):
                # Hardened derivation
                index = int(part[:-1])
                if not 0 <= index <= MAX_HARDENED_INDEX:
                    raise InvalidPathError(
                        f"Hardened index must be 0 to {MAX_HARDENED_INDEX}, got {index}",
                        path=path,
                        parameter=f"component_{i}",
                        value=index,
                        valid_range=f"0 to {MAX_HARDENED_INDEX}",
                    )
                components.append(index | HARDENED_OFFSET)
            else:
                # Non-hardened derivation
                index = int(part)
                if not 0 <= index <= MAX_NON_HARDENED_INDEX:
                    raise InvalidPathError(
                        f"Non-hardened index must be 0 to {MAX_NON_HARDENED_INDEX}, got {index}",
                        path=path,
                        parameter=f"component_{i}",
                        value=index,
                        valid_range=f"0 to {MAX_NON_HARDENED_INDEX}",
                    )
                components.append(index)
        except ValueError as e:
            raise InvalidPathError(
                f"Invalid path component '{part}': must be integer",
                path=path,
                parameter=f"component_{i}",
                value=part,
            ) from e

    logger.debug("Parsed derivation path %s into %d components", path, len(components))
    return components


def build_derivation_path(
    purpose: int,
    coin_type: int,
    account: int = 0,
    change: int = 0,
    address_index: int = 0,
) -> str:
    """Build derivation path for given parameters.

    Constructs a BIP32 derivation path from individual components
    with comprehensive validation.

    Args:
        purpose: BIP purpose (44, 49, 84, 86).
        coin_type: Cryptocurrency coin type.
        account: Account number (default: 0).
        change: Change flag (0=external, 1=internal).
        address_index: Address index.

    Returns:
        Formatted BIP32 derivation path.

    Raises:
        InvalidPathError: If parameters are invalid.

    Example:
        >>> build_derivation_path(84, 0, 0, 0, 5)
        "m/84'/0'/0'/0/5"
    """
    # Validate purpose
    valid_purposes = [BIP44_PURPOSE, BIP49_PURPOSE, BIP84_PURPOSE, BIP86_PURPOSE]
    if purpose not in valid_purposes:
        raise InvalidPathError(
            f"Purpose must be one of {valid_purposes}, got {purpose}",
            parameter="purpose",
            value=purpose,
            valid_range=f"One of {valid_purposes}",
        )

    # Validate coin type
    if not 0 <= coin_type <= MAX_HARDENED_INDEX:
        raise InvalidPathError(
            f"Coin type must be 0 to {MAX_HARDENED_INDEX}, got {coin_type}",
            parameter="coin_type",
            value=coin_type,
            valid_range=f"0 to {MAX_HARDENED_INDEX}",
        )

    # Validate account
    if not 0 <= account <= MAX_HARDENED_INDEX:
        raise InvalidPathError(
            f"Account must be 0 to {MAX_HARDENED_INDEX}, got {account}",
            parameter="account",
            value=account,
            valid_range=f"0 to {MAX_HARDENED_INDEX}",
        )

    # Validate change
    if change not in [0, 1]:
        raise InvalidPathError(
            f"Change must be 0 (external) or 1 (internal), got {change}",
            parameter="change",
            value=change,
            valid_range="0 or 1",
        )

    # Validate address index
    if not 0 <= address_index <= MAX_NON_HARDENED_INDEX:
        raise InvalidPathError(
            f"Address index must be 0 to {MAX_NON_HARDENED_INDEX}, got {address_index}",
            parameter="address_index",
            value=address_index,
            valid_range=f"0 to {MAX_NON_HARDENED_INDEX}",
        )

    # Build path using DerivationPath dataclass
    derivation = DerivationPath(
        purpose=purpose,
        coin_type=coin_type,
        account=account,
        change=change,
        address_index=address_index,
    )

    logger.debug("Built derivation path: %s", derivation.path_string)
    return derivation.path_string


def build_account_path(purpose: int, coin_type: int, account: int = 0) -> str:
    """Build account-level path for extended keys.

    Creates an account-level derivation path for xpub/xprv generation.

    Args:
        purpose: BIP purpose (44, 49, 84, 86).
        coin_type: Cryptocurrency coin type.
        account: Account number (default: 0).

    Returns:
        Account-level derivation path.

    Raises:
        InvalidPathError: If parameters are invalid.

    Example:
        >>> build_account_path(84, 0, 0)
        "m/84'/0'/0'"
    """
    # Validate using same logic as build_derivation_path
    derivation = DerivationPath(
        purpose=purpose,
        coin_type=coin_type,
        account=account,
        change=0,  # Not used at account level
        address_index=0,  # Not used at account level
    )

    # Validate parameters (reuse validation from build_derivation_path)
    validate_derivation_parameters(purpose, coin_type, account, 0, 0)

    logger.debug("Built account path: %s", derivation.account_path)
    return derivation.account_path


def get_path_info(path: str) -> DerivationPath:
    """Extract structured info from derivation path.

    Parses a BIP32 derivation path and returns structured information
    about all components.

    Args:
        path: BIP32 derivation path string.

    Returns:
        DerivationPath object with parsed components.

    Raises:
        InvalidPathError: If path format is invalid.

    Example:
        >>> info = get_path_info("m/84'/0'/0'/0/5")
        >>> print(info.purpose, info.address_index)  # 84, 5
    """
    validate_path(path)

    parts = path.split("/")[1:]  # Skip 'm'

    if len(parts) != 5:
        raise InvalidPathError(
            f"Expected 5 path components, got {len(parts)}",
            path=path,
            pattern="m/purpose'/coin'/account'/change/index",
        )

    try:
        purpose = int(parts[0].rstrip("'"))
        coin_type = int(parts[1].rstrip("'"))
        account = int(parts[2].rstrip("'"))
        change = int(parts[3])
        address_index = int(parts[4])

        derivation = DerivationPath(purpose, coin_type, account, change, address_index)
        logger.debug("Extracted path info: %s", derivation)
        return derivation

    except ValueError as e:
        raise InvalidPathError(f"Invalid path component: {e}", path=path) from e


def validate_derivation_parameters(
    purpose: int, coin_type: int, account: int, change: int, address_index: int
) -> None:
    """Validate individual derivation parameters.

    Comprehensive validation of all derivation path components.

    Args:
        purpose: BIP purpose.
        coin_type: Cryptocurrency coin type.
        account: Account number.
        change: Change flag.
        address_index: Address index.

    Raises:
        InvalidPathError: If any parameter is invalid.
    """
    # This function encapsulates the validation logic used in build_derivation_path
    # to avoid code duplication
    build_derivation_path(purpose, coin_type, account, change, address_index)


def get_standard_purposes() -> List[Tuple[int, str]]:
    """Get list of standard BIP purposes.

    Returns:
        List of (purpose_number, description) tuples.
    """
    return [
        (BIP44_PURPOSE, "Legacy P2PKH addresses"),
        (BIP49_PURPOSE, "SegWit P2SH-P2WPKH addresses"),
        (BIP84_PURPOSE, "Native SegWit P2WPKH addresses"),
        (BIP86_PURPOSE, "Taproot P2TR addresses"),
    ]


def format_path_description(path: str) -> str:
    """Format human-readable path description.

    Args:
        path: BIP32 derivation path.

    Returns:
        Human-readable description.

    Example:
        >>> format_path_description("m/84'/0'/0'/0/5")
        "BIP84 Native SegWit: Account 0, External Address 5"
    """
    try:
        info = get_path_info(path)
        change_desc = "External" if info.change == 0 else "Internal"
        return f"{info.purpose_name}: Account {info.account}, {change_desc} Address {info.address_index}"
    except InvalidPathError:
        return f"Custom path: {path}"
