"""Cryptocurrency configuration for HD wallet operations.

Defines supported cryptocurrencies with their specific parameters,
derivation standards, and address types following BIP standards.

This module provides comprehensive cryptocurrency configurations that
integrate with the bip-utils library for address generation.
"""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from bip_utils import (
    Bip44Coins,
    Bip49Coins,
    Bip84Coins,
    Bip86Coins,
)

from sseed.logging_config import get_logger

from .exceptions import UnsupportedCoinError

logger = get_logger(__name__)


@dataclass
class AddressTypeConfig:
    """Configuration for specific address type.

    Defines how to generate addresses for a specific type (Legacy, SegWit, etc.)
    using the appropriate BIP standard and bip-utils configuration.
    """

    name: str
    description: str
    purpose: int  # BIP purpose (44, 49, 84, 86)
    bip_utils_coin: Any  # bip-utils coin enum
    format_example: str
    prefix_description: str

    def __str__(self) -> str:
        """String representation of address type."""
        return f"{self.name} ({self.description})"


@dataclass
class CoinConfig:
    """Cryptocurrency configuration.

    Complete configuration for a supported cryptocurrency including
    all supported address types and network parameters.
    """

    name: str
    symbol: str
    coin_type: int  # BIP44 coin type
    address_types: Dict[str, AddressTypeConfig]
    default_address_type: str
    network_name: str
    description: str

    def get_address_type(self, address_type: Optional[str] = None) -> AddressTypeConfig:
        """Get address type configuration.

        Args:
            address_type: Address type name (None for default).

        Returns:
            AddressTypeConfig for the specified type.

        Raises:
            UnsupportedCoinError: If address type is not supported.

        Example:
            >>> config = get_coin_config("bitcoin")
            >>> addr_config = config.get_address_type("native-segwit")
            >>> print(addr_config.name)  # "Native SegWit"
        """
        if address_type is None:
            address_type = self.default_address_type

        if address_type not in self.address_types:
            raise UnsupportedCoinError(
                f"Address type '{address_type}' not supported for {self.name}",
                coin=self.name,
                address_type=address_type,
                supported_types=list(self.address_types.keys()),
            )

        return self.address_types[address_type]

    def get_supported_address_types(self) -> List[str]:
        """Get list of supported address types for this coin."""
        return list(self.address_types.keys())

    def __str__(self) -> str:
        """String representation of coin configuration."""
        return f"{self.name} ({self.symbol}) - {len(self.address_types)} address types"


# Bitcoin configuration with all address types
BITCOIN_CONFIG = CoinConfig(
    name="bitcoin",
    symbol="BTC",
    coin_type=0,  # BIP44 coin type for Bitcoin
    network_name="Bitcoin Mainnet",
    description="Bitcoin with full address type support",
    default_address_type="native-segwit",
    address_types={
        "legacy": AddressTypeConfig(
            name="Legacy",
            description="P2PKH addresses",
            purpose=44,
            bip_utils_coin=Bip44Coins.BITCOIN,
            format_example="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            prefix_description="Addresses starting with '1'",
        ),
        "segwit": AddressTypeConfig(
            name="SegWit",
            description="P2SH-P2WPKH addresses",
            purpose=49,
            bip_utils_coin=Bip49Coins.BITCOIN,
            format_example="3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
            prefix_description="Addresses starting with '3'",
        ),
        "native-segwit": AddressTypeConfig(
            name="Native SegWit",
            description="P2WPKH addresses",
            purpose=84,
            bip_utils_coin=Bip84Coins.BITCOIN,
            format_example="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
            prefix_description="Addresses starting with 'bc1q'",
        ),
        "taproot": AddressTypeConfig(
            name="Taproot",
            description="P2TR addresses",
            purpose=86,
            bip_utils_coin=Bip86Coins.BITCOIN,
            format_example="bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr",
            prefix_description="Addresses starting with 'bc1p'",
        ),
    },
)

# Ethereum configuration
ETHEREUM_CONFIG = CoinConfig(
    name="ethereum",
    symbol="ETH",
    coin_type=60,  # BIP44 coin type for Ethereum
    network_name="Ethereum Mainnet",
    description="Ethereum with standard address support",
    default_address_type="standard",
    address_types={
        "standard": AddressTypeConfig(
            name="Standard",
            description="Ethereum addresses",
            purpose=44,
            bip_utils_coin=Bip44Coins.ETHEREUM,
            format_example="0x742d35cc6464706a45d3f4e5c4b19c5a6a6b5c5f",
            prefix_description="Addresses starting with '0x'",
        ),
    },
)

# Litecoin configuration
LITECOIN_CONFIG = CoinConfig(
    name="litecoin",
    symbol="LTC",
    coin_type=2,  # BIP44 coin type for Litecoin
    network_name="Litecoin Mainnet",
    description="Litecoin with SegWit support",
    default_address_type="native-segwit",
    address_types={
        "legacy": AddressTypeConfig(
            name="Legacy",
            description="P2PKH addresses",
            purpose=44,
            bip_utils_coin=Bip44Coins.LITECOIN,
            format_example="LbYALvN5LPu4bj7u4pjvwcwC7p2vb5QJv7",
            prefix_description="Addresses starting with 'L'",
        ),
        "segwit": AddressTypeConfig(
            name="SegWit",
            description="P2SH-P2WPKH addresses",
            purpose=49,
            bip_utils_coin=Bip49Coins.LITECOIN,
            format_example="MQMcJhpWHYVeQArcZR3sBgyPZxxRtnH441",
            prefix_description="Addresses starting with 'M'",
        ),
        "native-segwit": AddressTypeConfig(
            name="Native SegWit",
            description="P2WPKH addresses",
            purpose=84,
            bip_utils_coin=Bip84Coins.LITECOIN,
            format_example="ltc1qw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",
            prefix_description="Addresses starting with 'ltc1'",
        ),
    },
)

# Bitcoin Cash configuration (for future Phase 2)
BITCOIN_CASH_CONFIG = CoinConfig(
    name="bitcoin-cash",
    symbol="BCH",
    coin_type=145,  # BIP44 coin type for Bitcoin Cash
    network_name="Bitcoin Cash Mainnet",
    description="Bitcoin Cash with CashAddr support",
    default_address_type="standard",
    address_types={
        "standard": AddressTypeConfig(
            name="Standard",
            description="CashAddr format",
            purpose=44,
            bip_utils_coin=Bip44Coins.BITCOIN_CASH,
            format_example="bitcoincash:qpm2qsznhks23z7629mms6s4cwef74vcwvy22gdx6a",
            prefix_description="Addresses starting with 'bitcoincash:'",
        ),
    },
)

# Dogecoin configuration (for future Phase 2)
DOGECOIN_CONFIG = CoinConfig(
    name="dogecoin",
    symbol="DOGE",
    coin_type=3,  # BIP44 coin type for Dogecoin
    network_name="Dogecoin Mainnet",
    description="Dogecoin with standard support",
    default_address_type="standard",
    address_types={
        "standard": AddressTypeConfig(
            name="Standard",
            description="P2PKH addresses",
            purpose=44,
            bip_utils_coin=Bip44Coins.DOGECOIN,
            format_example="DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L",
            prefix_description="Addresses starting with 'D'",
        ),
    },
)

# Master coin configuration registry
COIN_CONFIGS: Dict[str, CoinConfig] = {
    "bitcoin": BITCOIN_CONFIG,
    "ethereum": ETHEREUM_CONFIG,
    "litecoin": LITECOIN_CONFIG,
    # Phase 2 additions (currently commented out)
    # "bitcoin-cash": BITCOIN_CASH_CONFIG,
    # "dogecoin": DOGECOIN_CONFIG,
}

# Supported coins list for CLI choices (Phase 1)
SUPPORTED_COINS = ["bitcoin", "ethereum", "litecoin"]

# All coins including future support (Phase 2+)
ALL_CONFIGURED_COINS = list(COIN_CONFIGS.keys())


def get_coin_config(coin_name: str) -> CoinConfig:
    """Get coin configuration by name.

    Args:
        coin_name: Cryptocurrency name.

    Returns:
        CoinConfig for the specified cryptocurrency.

    Raises:
        UnsupportedCoinError: If cryptocurrency is not supported.

    Example:
        >>> config = get_coin_config("bitcoin")
        >>> print(config.symbol, config.coin_type)  # BTC 0
    """
    if not isinstance(coin_name, str):
        raise UnsupportedCoinError(
            f"Coin name must be string, got {type(coin_name).__name__}",
            coin=str(coin_name),
            supported_coins=SUPPORTED_COINS,
        )

    coin_name = coin_name.lower().strip()

    if coin_name not in COIN_CONFIGS:
        raise UnsupportedCoinError(
            f"Cryptocurrency '{coin_name}' is not supported",
            coin=coin_name,
            supported_coins=SUPPORTED_COINS,
        )

    # Additional check for Phase 1 limitations
    if coin_name not in SUPPORTED_COINS:
        raise UnsupportedCoinError(
            f"Cryptocurrency '{coin_name}' is configured but not yet available in Phase 1",
            coin=coin_name,
            supported_coins=SUPPORTED_COINS,
        )

    config = COIN_CONFIGS[coin_name]
    logger.debug("Retrieved coin configuration: %s", config)
    return config


def get_supported_address_types(coin_name: str) -> List[str]:
    """Get supported address types for coin.

    Args:
        coin_name: Cryptocurrency name.

    Returns:
        List of supported address type names.

    Raises:
        UnsupportedCoinError: If cryptocurrency is not supported.

    Example:
        >>> types = get_supported_address_types("bitcoin")
        >>> print(types)  # ["legacy", "segwit", "native-segwit", "taproot"]
    """
    config = get_coin_config(coin_name)
    return config.get_supported_address_types()


def validate_coin_and_address_type(
    coin_name: str, address_type: Optional[str] = None
) -> tuple[CoinConfig, AddressTypeConfig]:
    """Validate coin and address type combination.

    Args:
        coin_name: Cryptocurrency name.
        address_type: Address type (None for default).

    Returns:
        Tuple of (CoinConfig, AddressTypeConfig).

    Raises:
        UnsupportedCoinError: If coin or address type is invalid.

    Example:
        >>> coin_cfg, addr_cfg = validate_coin_and_address_type("bitcoin", "native-segwit")
        >>> print(coin_cfg.name, addr_cfg.name)  # bitcoin Native SegWit
    """
    coin_config = get_coin_config(coin_name)
    address_config = coin_config.get_address_type(address_type)

    logger.debug(
        "Validated coin and address type: %s %s", coin_config.name, address_config.name
    )

    return coin_config, address_config


def get_coin_info(coin_name: str) -> Dict[str, Any]:
    """Get comprehensive coin information.

    Args:
        coin_name: Cryptocurrency name.

    Returns:
        Dictionary with complete coin information.

    Example:
        >>> info = get_coin_info("bitcoin")
        >>> print(info["symbol"], len(info["address_types"]))  # BTC 4
    """
    config = get_coin_config(coin_name)

    address_types_info = {}
    for type_name, type_config in config.address_types.items():
        address_types_info[type_name] = {
            "name": type_config.name,
            "description": type_config.description,
            "purpose": type_config.purpose,
            "format_example": type_config.format_example,
            "prefix_description": type_config.prefix_description,
        }

    return {
        "name": config.name,
        "symbol": config.symbol,
        "coin_type": config.coin_type,
        "network_name": config.network_name,
        "description": config.description,
        "default_address_type": config.default_address_type,
        "address_types": address_types_info,
        "supported_address_types": config.get_supported_address_types(),
    }


def get_all_coins_info() -> Dict[str, Dict[str, Any]]:
    """Get information for all supported coins.

    Returns:
        Dictionary mapping coin names to their information.

    Example:
        >>> all_info = get_all_coins_info()
        >>> print(list(all_info.keys()))  # ["bitcoin", "ethereum", "litecoin"]
    """
    all_info = {}
    for coin_name in SUPPORTED_COINS:
        all_info[coin_name] = get_coin_info(coin_name)

    logger.debug("Retrieved information for %d supported coins", len(all_info))
    return all_info


def get_coin_by_symbol(symbol: str) -> Optional[CoinConfig]:
    """Get coin configuration by symbol.

    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH").

    Returns:
        CoinConfig if found, None otherwise.

    Example:
        >>> config = get_coin_by_symbol("BTC")
        >>> print(config.name if config else "Not found")  # bitcoin
    """
    symbol = symbol.upper().strip()

    for coin_name in SUPPORTED_COINS:
        config = COIN_CONFIGS[coin_name]
        if config.symbol.upper() == symbol:
            logger.debug("Found coin by symbol %s: %s", symbol, config.name)
            return config

    return None


def format_supported_coins_help() -> str:
    """Format help text for supported coins.

    Returns:
        Formatted help text for CLI usage.

    Example:
        >>> help_text = format_supported_coins_help()
        >>> print(help_text[:50])  # First 50 characters
    """
    lines = ["Supported cryptocurrencies:"]

    for coin_name in SUPPORTED_COINS:
        config = COIN_CONFIGS[coin_name]
        address_types = ", ".join(config.get_supported_address_types())
        lines.append(f"  {config.name} ({config.symbol}): {address_types}")

    return "\n".join(lines)


def format_address_types_help(coin_name: str) -> str:
    """Format help text for address types of a specific coin.

    Args:
        coin_name: Cryptocurrency name.

    Returns:
        Formatted help text for address types.

    Example:
        >>> help_text = format_address_types_help("bitcoin")
        >>> print("legacy" in help_text)  # True
    """
    try:
        config = get_coin_config(coin_name)
        lines = [f"{config.name} address types:"]

        for type_name, type_config in config.address_types.items():
            default_marker = (
                " (default)" if type_name == config.default_address_type else ""
            )
            lines.append(f"  {type_name}: {type_config.description}{default_marker}")
            lines.append(f"    Example: {type_config.format_example}")

        return "\n".join(lines)

    except UnsupportedCoinError:
        return f"Cryptocurrency '{coin_name}' is not supported"


# Phase tracking for development
def get_phase_info() -> Dict[str, Any]:
    """Get implementation phase information.

    Returns:
        Dictionary with phase implementation status.
    """
    return {
        "current_phase": 1,
        "phase_1_coins": ["bitcoin", "ethereum", "litecoin"],
        "phase_2_planned": ["bitcoin-cash", "dogecoin"],
        "total_configured": len(ALL_CONFIGURED_COINS),
        "total_supported": len(SUPPORTED_COINS),
        "implementation_status": {
            "bitcoin": "Full implementation (4 address types)",
            "ethereum": "Standard implementation (1 address type)",
            "litecoin": "SegWit implementation (3 address types)",
            "bitcoin-cash": "Configured, not yet enabled",
            "dogecoin": "Configured, not yet enabled",
        },
    }
