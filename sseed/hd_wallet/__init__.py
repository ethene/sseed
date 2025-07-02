"""HD Wallet Address Derivation for SSeed.

This module implements hierarchical deterministic wallet functionality
following BIP32, BIP44, BIP49, BIP84, and BIP86 standards.

Key Features:
- Multi-cryptocurrency support (Bitcoin, Ethereum, Litecoin, etc.)
- All Bitcoin address types (Legacy, SegWit, Native SegWit, Taproot)
- Batch address generation with performance optimization
- Extended key (xpub/xprv) export capabilities
- BIP85 integration for deterministic child wallets
- Rich output formatting (JSON, CSV, plain text)
- Security-first design with memory cleanup

Supported Cryptocurrencies:
- Bitcoin (BTC): Legacy, SegWit, Native SegWit, Taproot
- Ethereum (ETH): Standard addresses
- Litecoin (LTC): Legacy, SegWit, Native SegWit

Example Usage:
    >>> from sseed.hd_wallet import generate_addresses
    >>> addresses = generate_addresses("word1 word2 ...", "bitcoin", count=5)
    >>> for addr in addresses:
    ...     print(f"{addr.index}: {addr.address}")

    >>> from sseed.hd_wallet import HDWalletManager
    >>> manager = HDWalletManager("word1 word2 ...")
    >>> btc_addresses = manager.derive_addresses_batch("bitcoin", count=10)
    >>> eth_addresses = manager.derive_addresses_batch("ethereum", count=5)
"""

# Core functionality - now with real implementations
from typing import (
    List,
    Optional,
)

from .addresses import (
    AddressInfo,
    derive_address_batch,
    format_address_summary,
    generate_address,
    get_csv_headers,
)
from .coins import (
    SUPPORTED_COINS,
    CoinConfig,
    get_coin_config,
    get_coin_info,
    get_supported_address_types,
)
from .core import (
    HDWalletManager,
    derive_addresses_from_mnemonic,
)
from .derivation import (
    DerivationPath,
    build_derivation_path,
    get_path_info,
    validate_path,
)

# Exception hierarchy
from .exceptions import (
    AddressGenerationError,
    DerivationError,
    ExtendedKeyError,
    HDWalletError,
    InvalidPathError,
    UnsupportedCoinError,
)
from .extended_keys import (
    ExtendedKeyInfo,
    derive_extended_keys,
    derive_extended_keys_batch,
    format_extended_key_summary,
    get_extended_key_csv_headers,
    get_extended_key_info,
    validate_extended_key,
)
from .validation import (
    validate_address_type,
    validate_coin_support,
    validate_derivation_parameters,
)

# Version and metadata
__version__ = "1.0.0"
__author__ = "SSeed Development Team"
__description__ = "HD Wallet Address Derivation with Multi-Coin Support"


# Convenience function for quick address generation
def generate_addresses(
    mnemonic: str,
    coin: str = "bitcoin",
    count: int = 1,
    account: int = 0,
    change: int = 0,
    address_type: Optional[str] = None,
    start_index: int = 0,
) -> List[AddressInfo]:
    """Convenience function for generating addresses.

    Generates cryptocurrency addresses from a BIP39 mnemonic using
    hierarchical deterministic wallet derivation.

    Args:
        mnemonic: BIP39 mnemonic phrase.
        coin: Cryptocurrency name (bitcoin, ethereum, litecoin).
        count: Number of addresses to generate.
        account: Account number for derivation.
        change: Change flag (0=external, 1=internal).
        address_type: Address type (legacy, segwit, native-segwit, taproot).
        start_index: Starting address index.

    Returns:
        List of AddressInfo objects with derivation details.

    Raises:
        HDWalletError: If address generation fails.
        UnsupportedCoinError: If cryptocurrency is not supported.

    Example:
        >>> addresses = generate_addresses("word1 word2 ...", "bitcoin", 5)
        >>> print(f"Generated {len(addresses)} Bitcoin addresses")
    """
    # Implementation using HDWalletManager
    manager = HDWalletManager(mnemonic, validate=True)
    try:
        return manager.derive_addresses_batch(
            coin=coin,
            count=count,
            account=account,
            change=change,
            address_type=address_type,
            start_index=start_index,
        )
    finally:
        # Ensure cleanup happens
        manager._secure_cleanup()


# Factory function for creating HD wallet managers
def create_hd_wallet(mnemonic: str, validate: bool = True) -> HDWalletManager:
    """Create HD wallet manager with optional validation.

    Args:
        mnemonic: BIP39 mnemonic phrase.
        validate: Whether to validate mnemonic checksum.

    Returns:
        HDWalletManager instance.

    Raises:
        HDWalletError: If wallet creation fails.

    Example:
        >>> wallet = create_hd_wallet("word1 word2 ...")
        >>> addresses = wallet.derive_addresses_batch("bitcoin", 10)
    """
    return HDWalletManager(mnemonic, validate=validate)


# Get module information
def get_hd_wallet_info() -> dict:
    """Get comprehensive HD wallet implementation information.

    Returns detailed information about the HD wallet implementation including
    supported features, cryptocurrencies, and version info.

    Returns:
        Dictionary with implementation details.
    """
    return {
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "features": {
            "cryptocurrencies": {
                "bitcoin": {
                    "supported": True,
                    "address_types": ["legacy", "segwit", "native-segwit", "taproot"],
                    "coin_type": 0,
                    "description": "Bitcoin with all address types",
                },
                "ethereum": {
                    "supported": True,
                    "address_types": ["standard"],
                    "coin_type": 60,
                    "description": "Ethereum standard addresses",
                },
                "litecoin": {
                    "supported": True,
                    "address_types": ["legacy", "segwit", "native-segwit"],
                    "coin_type": 2,
                    "description": "Litecoin with SegWit support",
                },
            },
            "derivation": {
                "standards": ["BIP32", "BIP44", "BIP49", "BIP84", "BIP86"],
                "custom_paths": True,
                "batch_generation": True,
                "extended_keys": True,
                "description": "Full BIP standard compliance",
            },
            "output_formats": {
                "json": True,
                "csv": True,
                "plain_text": True,
                "metadata": True,
                "description": "Rich output formatting options",
            },
            "integration": {
                "bip85": True,
                "existing_sseed": True,
                "cli_command": True,
                "api_access": True,
                "description": "Seamless SSeed integration",
            },
        },
        "security": {
            "private_key_protection": "Requires --unsafe flag",
            "memory_cleanup": "Secure variable deletion",
            "path_validation": "Comprehensive validation",
            "error_handling": "Rich exception context",
        },
    }


# Public API exports
__all__ = [
    # Core functionality
    "HDWalletManager",
    "derive_addresses_from_mnemonic",
    "AddressInfo",
    "generate_address",
    "derive_address_batch",
    "DerivationPath",
    "build_derivation_path",
    "validate_path",
    "get_path_info",
    "CoinConfig",
    "SUPPORTED_COINS",
    "get_coin_config",
    "get_supported_address_types",
    "get_coin_info",
    "validate_derivation_parameters",
    "validate_coin_support",
    "validate_address_type",
    # Utility functions
    "generate_addresses",
    "create_hd_wallet",
    "get_hd_wallet_info",
    "get_csv_headers",
    "format_address_summary",
    # Extended key functions
    "ExtendedKeyInfo",
    "derive_extended_keys",
    "derive_extended_keys_batch",
    "validate_extended_key",
    "get_extended_key_info",
    "format_extended_key_summary",
    "get_extended_key_csv_headers",
    # Exception handling
    "HDWalletError",
    "DerivationError",
    "UnsupportedCoinError",
    "InvalidPathError",
    "AddressGenerationError",
    "ExtendedKeyError",
    # Future Phase 2 implementations:
    # "format_addresses_json",
    # "format_addresses_csv",
    # "format_addresses_plain",
    # "ExtendedKeys",
    # "derive_extended_keys",
    # "derive_wallet_from_bip85",
]
