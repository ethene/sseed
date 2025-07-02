# HD Wallet Module - Highly Modular Architecture Design

## Executive Summary

This document defines the highly modular architecture for the HD wallet address derivation feature, following SSeed's exact patterns for small, focused files with clear separation of concerns. The design ensures seamless integration with existing SSeed infrastructure while maintaining the security-first, automation-friendly philosophy.

## Architecture Analysis: SSeed Modular Patterns

Based on comprehensive analysis of the existing SSeed codebase, here are the key patterns we must follow:

### File Size Guidelines
- **Small files**: 13-200 lines (utilities, exceptions, simple interfaces)
- **Medium files**: 200-400 lines (main implementation, business logic)
- **Large files**: 400-800 lines (complex features - avoid when possible)
- **Average**: ~300 lines per file
- **Maximum**: No file should exceed 800 lines

### Modular Organization Principles
1. **Single Responsibility**: Each file has ONE clear purpose
2. **Layered Architecture**: Core → Applications → Utilities → Interfaces
3. **Minimal Dependencies**: Modules depend only on shared utilities
4. **Rich `__init__.py`**: Export public APIs with backward compatibility
5. **Hierarchical Exceptions**: Domain-specific exception inheritance

## HD Wallet Module Structure

Following SSeed's exact patterns, here's the modular breakdown:

```
sseed/
├── hd_wallet/                          # New HD wallet module
│   ├── __init__.py                     # Public API exports & convenience functions (~150 lines)
│   ├── core.py                         # Core HD derivation logic (~350 lines)
│   ├── coins.py                        # Cryptocurrency configurations (~300 lines)
│   ├── derivation.py                   # Derivation path utilities (~250 lines)
│   ├── addresses.py                    # Address generation logic (~320 lines)
│   ├── validation.py                   # Parameter validation (~280 lines)
│   ├── formatters.py                   # Output formatting (~200 lines)
│   ├── batch.py                        # Batch operations (~350 lines)
│   ├── extended_keys.py                # xpub/xprv handling (~180 lines)
│   ├── bip85_integration.py           # BIP85 integration (~220 lines)
│   └── exceptions.py                   # HD wallet exceptions (~120 lines)
└── cli/commands/
    └── derive.py                       # CLI command implementation (~400 lines)
```

**Total**: 11 files, average 250 lines per file, following SSeed patterns exactly.

## Detailed File Specifications

### 1. `sseed/hd_wallet/__init__.py` (~150 lines)

**Responsibility**: Public API exports, convenience functions, module metadata

```python
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
"""

# Core functionality
from .core import HDWalletManager, derive_addresses_from_mnemonic
from .addresses import AddressInfo, generate_address, derive_address_batch
from .derivation import DerivationPath, build_derivation_path, validate_path
from .coins import CoinConfig, SUPPORTED_COINS, get_coin_config
from .validation import validate_derivation_parameters, validate_coin_support
from .formatters import format_addresses_json, format_addresses_csv, format_addresses_plain
from .extended_keys import ExtendedKeys, derive_extended_keys
from .bip85_integration import derive_wallet_from_bip85

# Exception hierarchy
from .exceptions import (
    HDWalletError,
    DerivationError,
    UnsupportedCoinError,
    InvalidPathError,
    AddressGenerationError,
)

# Version and metadata
__version__ = "1.0.0"
__author__ = "SSeed Development Team"
__description__ = "HD Wallet Address Derivation with Multi-Coin Support"

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
    "CoinConfig",
    "SUPPORTED_COINS",
    "get_coin_config",
    # Validation and formatting
    "validate_derivation_parameters",
    "validate_coin_support", 
    "format_addresses_json",
    "format_addresses_csv",
    "format_addresses_plain",
    "ExtendedKeys",
    "derive_extended_keys",
    # BIP85 integration
    "derive_wallet_from_bip85",
    # Exception handling
    "HDWalletError",
    "DerivationError", 
    "UnsupportedCoinError",
    "InvalidPathError",
    "AddressGenerationError",
]

# Convenience function for quick address generation
def generate_addresses(
    mnemonic: str,
    coin: str = "bitcoin",
    count: int = 1,
    account: int = 0,
    change: int = 0,
    address_type: str = None,
    start_index: int = 0
) -> List[AddressInfo]:
    """Convenience function for generating addresses."""
    manager = HDWalletManager(mnemonic)
    return manager.derive_addresses_batch(
        coin=coin, count=count, account=account, 
        change=change, address_type=address_type, start_index=start_index
    )

# Factory function for creating HD wallet managers
def create_hd_wallet(mnemonic: str, validate: bool = True) -> HDWalletManager:
    """Create HD wallet manager with optional validation."""
    return HDWalletManager(mnemonic, validate=validate)
```

### 2. `sseed/hd_wallet/core.py` (~350 lines)

**Responsibility**: Core HD derivation logic, BIP32 operations, master key management

```python
"""Core HD wallet functionality.

Implements the fundamental hierarchical deterministic wallet operations
using BIP32 key derivation with secure memory handling.
"""

import hashlib
from typing import Optional, List
from dataclasses import dataclass

from bip_utils import (
    Bip32Secp256k1,
    Bip39SeedGenerator,
    Bip39MnemonicValidator,
)

from sseed.entropy import secure_delete_variable
from sseed.logging_config import get_logger, log_security_event
from sseed.validation import normalize_mnemonic

from .exceptions import DerivationError, HDWalletError
from .coins import CoinConfig, get_coin_config
from .derivation import DerivationPath, validate_path
from .addresses import AddressInfo, generate_address

logger = get_logger(__name__)

class HDWalletManager:
    """Core HD wallet manager for address derivation."""
    
    def __init__(self, mnemonic: str, validate: bool = True):
        """Initialize HD wallet from mnemonic."""
        self._mnemonic = normalize_mnemonic(mnemonic)
        self._master_seed: Optional[bytes] = None
        self._master_key: Optional[Bip32Secp256k1] = None
        
        if validate:
            self._validate_mnemonic()
        
        logger.debug("HD wallet manager initialized")
        log_security_event("HD wallet: Manager initialization completed")
    
    def _validate_mnemonic(self) -> None:
        """Validate mnemonic using BIP39 standards."""
        try:
            if not Bip39MnemonicValidator().IsValid(self._mnemonic):
                raise HDWalletError(
                    "Invalid BIP39 mnemonic checksum",
                    context={"mnemonic_words": len(self._mnemonic.split())}
                )
        except Exception as e:
            raise DerivationError(
                f"Mnemonic validation failed: {e}",
                operation="validate_mnemonic",
                original_error=e
            ) from e
    
    def _get_master_key(self) -> Bip32Secp256k1:
        """Get or create master key with caching."""
        if self._master_key is None:
            try:
                # Generate master seed from mnemonic
                self._master_seed = Bip39SeedGenerator(self._mnemonic).Generate()
                
                # Create BIP32 master key
                self._master_key = Bip32Secp256k1.FromSeed(self._master_seed)
                
                logger.debug("Master key created from mnemonic")
                log_security_event("HD wallet: Master key derivation completed")
                
            except Exception as e:
                raise DerivationError(
                    f"Master key creation failed: {e}",
                    operation="create_master_key",
                    original_error=e
                ) from e
        
        return self._master_key
    
    def derive_key_at_path(self, derivation_path: str) -> Bip32Secp256k1:
        """Derive key at specific path."""
        try:
            validate_path(derivation_path)
            master_key = self._get_master_key()
            
            # Parse and apply derivation path
            path_components = self._parse_derivation_path(derivation_path)
            derived_key = master_key
            
            for component in path_components:
                derived_key = derived_key.ChildKey(component)
            
            logger.debug("Key derived at path: %s", derivation_path)
            return derived_key
            
        except Exception as e:
            raise DerivationError(
                f"Key derivation failed at path {derivation_path}: {e}",
                derivation_path=derivation_path,
                operation="derive_key_at_path",
                original_error=e
            ) from e
    
    def derive_addresses_batch(
        self,
        coin: str,
        count: int = 1,
        account: int = 0,
        change: int = 0,
        address_type: Optional[str] = None,
        start_index: int = 0
    ) -> List[AddressInfo]:
        """Derive multiple addresses efficiently."""
        try:
            coin_config = get_coin_config(coin)
            addresses = []
            
            for i in range(count):
                index = start_index + i
                path = build_derivation_path(
                    coin_config, account, change, index, address_type
                )
                
                derived_key = self.derive_key_at_path(path)
                address_info = generate_address(derived_key, coin_config, path, index, address_type)
                addresses.append(address_info)
            
            logger.info(f"Generated {count} addresses for {coin}")
            log_security_event(f"HD wallet: Batch address generation completed ({count} addresses)")
            
            return addresses
            
        except Exception as e:
            raise DerivationError(
                f"Batch address derivation failed: {e}",
                operation="derive_addresses_batch",
                context={
                    "coin": coin,
                    "count": count,
                    "account": account,
                    "change": change,
                    "start_index": start_index
                },
                original_error=e
            ) from e
    
    def __del__(self):
        """Secure cleanup on destruction."""
        self._secure_cleanup()
    
    def _secure_cleanup(self) -> None:
        """Securely clean up sensitive data."""
        try:
            if self._master_seed:
                secure_delete_variable(self._master_seed)
            if self._master_key:
                # Clear key material if possible
                if hasattr(self._master_key, '_key_data'):
                    secure_delete_variable(self._master_key._key_data)
        except Exception as e:
            logger.warning("Secure cleanup failed: %s", e)

# Convenience function matching SSeed patterns
def derive_addresses_from_mnemonic(
    mnemonic: str,
    coin: str,
    count: int = 1,
    **kwargs
) -> List[AddressInfo]:
    """Convenience function for direct address derivation."""
    manager = HDWalletManager(mnemonic)
    return manager.derive_addresses_batch(coin=coin, count=count, **kwargs)
```

### 3. `sseed/hd_wallet/coins.py` (~300 lines)

**Responsibility**: Cryptocurrency configurations, coin constants, supported coins

```python
"""Cryptocurrency configuration for HD wallet operations.

Defines supported cryptocurrencies with their specific parameters,
derivation standards, and address types.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from bip_utils import (
    Bip44Coins,
    Bip49Coins, 
    Bip84Coins,
    Bip86Coins,
)

from .exceptions import UnsupportedCoinError

@dataclass
class AddressTypeConfig:
    """Configuration for specific address type."""
    name: str
    description: str
    purpose: int  # BIP purpose (44, 49, 84, 86)
    bip_utils_coin: Any
    format_example: str

@dataclass  
class CoinConfig:
    """Cryptocurrency configuration."""
    name: str
    symbol: str
    coin_type: int
    address_types: Dict[str, AddressTypeConfig]
    default_address_type: str
    network_name: str
    
    def get_address_type(self, address_type: Optional[str] = None) -> AddressTypeConfig:
        """Get address type configuration."""
        if address_type is None:
            address_type = self.default_address_type
            
        if address_type not in self.address_types:
            raise UnsupportedCoinError(
                f"Address type '{address_type}' not supported for {self.name}",
                coin=self.name,
                address_type=address_type,
                supported_types=list(self.address_types.keys())
            )
        
        return self.address_types[address_type]

# Bitcoin configuration with all address types
BITCOIN_CONFIG = CoinConfig(
    name="bitcoin",
    symbol="BTC", 
    coin_type=0,
    network_name="Bitcoin Mainnet",
    default_address_type="native-segwit",
    address_types={
        "legacy": AddressTypeConfig(
            name="Legacy",
            description="P2PKH addresses (1...)",
            purpose=44,
            bip_utils_coin=Bip44Coins.BITCOIN,
            format_example="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        ),
        "segwit": AddressTypeConfig(
            name="SegWit",
            description="P2SH-P2WPKH addresses (3...)",
            purpose=49,
            bip_utils_coin=Bip49Coins.BITCOIN,
            format_example="3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
        ),
        "native-segwit": AddressTypeConfig(
            name="Native SegWit",
            description="P2WPKH addresses (bc1...)",
            purpose=84,
            bip_utils_coin=Bip84Coins.BITCOIN,
            format_example="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        ),
        "taproot": AddressTypeConfig(
            name="Taproot",
            description="P2TR addresses (bc1p...)",
            purpose=86,
            bip_utils_coin=Bip86Coins.BITCOIN,
            format_example="bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr"
        ),
    }
)

# Ethereum configuration
ETHEREUM_CONFIG = CoinConfig(
    name="ethereum",
    symbol="ETH",
    coin_type=60,
    network_name="Ethereum Mainnet", 
    default_address_type="standard",
    address_types={
        "standard": AddressTypeConfig(
            name="Standard",
            description="Ethereum addresses (0x...)",
            purpose=44,
            bip_utils_coin=Bip44Coins.ETHEREUM,
            format_example="0x742d35cc6464706a45d3f4e5c4b19c5a6a6b5c5f"
        ),
    }
)

# Litecoin configuration  
LITECOIN_CONFIG = CoinConfig(
    name="litecoin",
    symbol="LTC",
    coin_type=2,
    network_name="Litecoin Mainnet",
    default_address_type="native-segwit",
    address_types={
        "legacy": AddressTypeConfig(
            name="Legacy",
            description="P2PKH addresses (L...)",
            purpose=44,
            bip_utils_coin=Bip44Coins.LITECOIN,
            format_example="LbYALvN5LPu4bj7u4pjvwcwC7p2vb5QJv7"
        ),
        "segwit": AddressTypeConfig(
            name="SegWit", 
            description="P2SH-P2WPKH addresses (M...)",
            purpose=49,
            bip_utils_coin=Bip49Coins.LITECOIN,
            format_example="MQMcJhpWHYVeQArcZR3sBgyPZxxRtnH441"
        ),
        "native-segwit": AddressTypeConfig(
            name="Native SegWit",
            description="P2WPKH addresses (ltc1...)",
            purpose=84,
            bip_utils_coin=Bip84Coins.LITECOIN,
            format_example="ltc1qw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90"
        ),
    }
)

# Master coin configuration registry
COIN_CONFIGS: Dict[str, CoinConfig] = {
    "bitcoin": BITCOIN_CONFIG,
    "ethereum": ETHEREUM_CONFIG, 
    "litecoin": LITECOIN_CONFIG,
}

# Supported coins list for CLI choices
SUPPORTED_COINS = list(COIN_CONFIGS.keys())

def get_coin_config(coin_name: str) -> CoinConfig:
    """Get coin configuration by name."""
    if coin_name not in COIN_CONFIGS:
        raise UnsupportedCoinError(
            f"Cryptocurrency '{coin_name}' is not supported",
            coin=coin_name,
            supported_coins=SUPPORTED_COINS
        )
    
    return COIN_CONFIGS[coin_name]

def get_supported_address_types(coin_name: str) -> List[str]:
    """Get supported address types for coin."""
    config = get_coin_config(coin_name)
    return list(config.address_types.keys())

def validate_coin_and_address_type(coin_name: str, address_type: Optional[str] = None) -> tuple[CoinConfig, AddressTypeConfig]:
    """Validate coin and address type combination."""
    coin_config = get_coin_config(coin_name)
    address_config = coin_config.get_address_type(address_type)
    return coin_config, address_config
```

### 4. `sseed/hd_wallet/derivation.py` (~250 lines)

**Responsibility**: Derivation path utilities, path building, validation

```python
"""Derivation path utilities for HD wallets.

Implements BIP32 derivation path parsing, validation, and construction
following BIP44, BIP49, BIP84, and BIP86 standards.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from .exceptions import InvalidPathError
from .coins import CoinConfig, AddressTypeConfig

# BIP32 path patterns
BIP32_PATH_PATTERN = re.compile(r"^m(/\d+'?)*$")
HARDENED_MARKER = "'"

@dataclass
class DerivationPath:
    """Structured derivation path representation."""
    purpose: int
    coin_type: int
    account: int
    change: int
    address_index: int
    
    @property
    def path_string(self) -> str:
        """Get path as string."""
        return f"m/{self.purpose}'/{self.coin_type}'/{self.account}'/{self.change}/{self.address_index}"
    
    @property
    def account_path(self) -> str:
        """Get account-level path for extended keys."""
        return f"m/{self.purpose}'/{self.coin_type}'/{self.account}'"

def validate_path(path: str) -> None:
    """Validate BIP32 derivation path format."""
    if not isinstance(path, str):
        raise InvalidPathError(
            f"Derivation path must be string, got {type(path).__name__}",
            path=path
        )
    
    if not path.startswith("m/"):
        raise InvalidPathError(
            "Derivation path must start with 'm/'",
            path=path
        )
    
    if not BIP32_PATH_PATTERN.match(path):
        raise InvalidPathError(
            "Invalid BIP32 derivation path format",
            path=path,
            pattern="m/44'/0'/0'/0/0"
        )

def parse_derivation_path(path: str) -> List[int]:
    """Parse derivation path into component integers."""
    validate_path(path)
    
    components = []
    parts = path.split("/")[1:]  # Skip 'm'
    
    for part in parts:
        if part.endswith(HARDENED_MARKER):
            # Hardened derivation
            index = int(part[:-1])
            components.append(index | 0x80000000)
        else:
            # Non-hardened derivation
            components.append(int(part))
    
    return components

def build_derivation_path(
    coin_config: CoinConfig,
    account: int = 0,
    change: int = 0,
    address_index: int = 0,
    address_type: Optional[str] = None
) -> str:
    """Build derivation path for given parameters."""
    # Validate parameters
    if not 0 <= account < 2**31:
        raise InvalidPathError(
            f"Account must be 0 to 2147483647, got {account}",
            parameter="account",
            value=account
        )
    
    if change not in [0, 1]:
        raise InvalidPathError(
            f"Change must be 0 (external) or 1 (internal), got {change}",
            parameter="change", 
            value=change
        )
    
    if not 0 <= address_index < 2**31:
        raise InvalidPathError(
            f"Address index must be 0 to 2147483647, got {address_index}",
            parameter="address_index",
            value=address_index
        )
    
    # Get address type configuration
    address_config = coin_config.get_address_type(address_type)
    
    # Build path using BIP standard
    derivation = DerivationPath(
        purpose=address_config.purpose,
        coin_type=coin_config.coin_type,
        account=account,
        change=change,
        address_index=address_index
    )
    
    return derivation.path_string

def build_account_path(
    coin_config: CoinConfig,
    account: int = 0,
    address_type: Optional[str] = None
) -> str:
    """Build account-level path for extended keys."""
    address_config = coin_config.get_address_type(address_type)
    
    derivation = DerivationPath(
        purpose=address_config.purpose,
        coin_type=coin_config.coin_type,
        account=account,
        change=0,  # Not used at account level
        address_index=0  # Not used at account level
    )
    
    return derivation.account_path

def get_path_info(path: str) -> DerivationPath:
    """Extract structured info from derivation path."""
    validate_path(path)
    
    parts = path.split("/")[1:]  # Skip 'm'
    
    if len(parts) != 5:
        raise InvalidPathError(
            f"Expected 5 path components, got {len(parts)}",
            path=path
        )
    
    try:
        purpose = int(parts[0].rstrip("'"))
        coin_type = int(parts[1].rstrip("'"))
        account = int(parts[2].rstrip("'"))
        change = int(parts[3])
        address_index = int(parts[4])
        
        return DerivationPath(purpose, coin_type, account, change, address_index)
        
    except ValueError as e:
        raise InvalidPathError(
            f"Invalid path component: {e}",
            path=path
        ) from e
```

### 5. `sseed/hd_wallet/addresses.py` (~320 lines)

**Responsibility**: Address generation logic, address formatting

```python
"""Address generation for HD wallets.

Implements address generation for multiple cryptocurrencies and address types
using the bip-utils library with proper formatting and validation.
"""

from dataclasses import dataclass
from typing import Optional

from bip_utils import (
    Bip32Secp256k1,
    Bip44,
    Bip49,
    Bip84,
    Bip86,
)

from sseed.logging_config import get_logger
from .exceptions import AddressGenerationError
from .coins import CoinConfig, AddressTypeConfig

logger = get_logger(__name__)

@dataclass
class AddressInfo:
    """Complete address information."""
    index: int
    derivation_path: str
    private_key: str
    public_key: str
    address: str
    address_type: str
    coin: str
    network: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "index": self.index,
            "derivation_path": self.derivation_path,
            "private_key": self.private_key,
            "public_key": self.public_key,
            "address": self.address,
            "address_type": self.address_type,
            "coin": self.coin,
            "network": self.network
        }

def generate_address(
    derived_key: Bip32Secp256k1,
    coin_config: CoinConfig,
    derivation_path: str,
    index: int,
    address_type: Optional[str] = None
) -> AddressInfo:
    """Generate address from derived key."""
    try:
        address_config = coin_config.get_address_type(address_type)
        
        # Create appropriate BIP context based on purpose
        if address_config.purpose == 44:
            bip_ctx = Bip44.FromPrivateKey(derived_key.PrivateKey(), address_config.bip_utils_coin)
        elif address_config.purpose == 49:
            bip_ctx = Bip49.FromPrivateKey(derived_key.PrivateKey(), address_config.bip_utils_coin)
        elif address_config.purpose == 84:
            bip_ctx = Bip84.FromPrivateKey(derived_key.PrivateKey(), address_config.bip_utils_coin)
        elif address_config.purpose == 86:
            bip_ctx = Bip86.FromPrivateKey(derived_key.PrivateKey(), address_config.bip_utils_coin)
        else:
            raise AddressGenerationError(
                f"Unsupported BIP purpose: {address_config.purpose}",
                coin=coin_config.name,
                address_type=address_type or coin_config.default_address_type,
                purpose=address_config.purpose
            )
        
        # Extract key material and address
        private_key_wif = bip_ctx.PrivateKey().ToWif()
        public_key_hex = bip_ctx.PublicKey().CompressedBytes().ToHex()
        address = bip_ctx.AddressClass().ToStr()
        
        logger.debug(f"Generated {coin_config.name} {address_config.name} address at index {index}")
        
        return AddressInfo(
            index=index,
            derivation_path=derivation_path,
            private_key=private_key_wif,
            public_key=public_key_hex,
            address=address,
            address_type=address_type or coin_config.default_address_type,
            coin=coin_config.name,
            network=coin_config.network_name
        )
        
    except Exception as e:
        raise AddressGenerationError(
            f"Address generation failed: {e}",
            coin=coin_config.name,
            address_type=address_type or coin_config.default_address_type,
            derivation_path=derivation_path,
            original_error=e
        ) from e

def derive_address_batch(
    master_key: Bip32Secp256k1,
    coin_config: CoinConfig,
    account: int = 0,
    change: int = 0,
    start_index: int = 0,
    count: int = 1,
    address_type: Optional[str] = None
) -> List[AddressInfo]:
    """Derive multiple addresses efficiently."""
    from .derivation import build_derivation_path  # Avoid circular import
    
    addresses = []
    
    try:
        for i in range(count):
            index = start_index + i
            
            # Build derivation path
            path = build_derivation_path(
                coin_config, account, change, index, address_type
            )
            
            # Derive key at path
            derived_key = _derive_key_from_master(master_key, path)
            
            # Generate address
            address_info = generate_address(
                derived_key, coin_config, path, index, address_type
            )
            
            addresses.append(address_info)
        
        logger.info(f"Batch generated {count} addresses for {coin_config.name}")
        return addresses
        
    except Exception as e:
        raise AddressGenerationError(
            f"Batch address generation failed: {e}",
            coin=coin_config.name,
            count=count,
            operation="derive_address_batch",
            original_error=e
        ) from e

def _derive_key_from_master(master_key: Bip32Secp256k1, path: str) -> Bip32Secp256k1:
    """Derive key from master key using path."""
    from .derivation import parse_derivation_path  # Avoid circular import
    
    try:
        path_components = parse_derivation_path(path)
        derived_key = master_key
        
        for component in path_components:
            derived_key = derived_key.ChildKey(component)
        
        return derived_key
        
    except Exception as e:
        raise AddressGenerationError(
            f"Key derivation failed at path {path}: {e}",
            derivation_path=path,
            operation="_derive_key_from_master",
            original_error=e
        ) from e

def validate_address_format(address: str, coin_config: CoinConfig, address_type: str) -> bool:
    """Validate address format for specific coin and type."""
    try:
        address_config = coin_config.get_address_type(address_type)
        
        # Basic format validation based on address type
        if coin_config.name == "bitcoin":
            if address_type == "legacy" and not address.startswith("1"):
                return False
            elif address_type == "segwit" and not address.startswith("3"):
                return False
            elif address_type == "native-segwit" and not address.startswith("bc1q"):
                return False
            elif address_type == "taproot" and not address.startswith("bc1p"):
                return False
        elif coin_config.name == "ethereum":
            if not (address.startswith("0x") and len(address) == 42):
                return False
        elif coin_config.name == "litecoin":
            if address_type == "legacy" and not address.startswith("L"):
                return False
            elif address_type == "segwit" and not address.startswith("M"):
                return False
            elif address_type == "native-segwit" and not address.startswith("ltc1"):
                return False
        
        return True
        
    except Exception:
        return False
```

## Command Integration

### `sseed/cli/commands/derive.py` (~400 lines)

**Responsibility**: CLI command implementation with argument parsing and output handling

```python
"""Derive command implementation.

Generates cryptocurrency addresses from BIP39 mnemonics using HD wallet derivation.
"""

import argparse
from typing import List, Optional

from sseed.hd_wallet import (
    HDWalletManager,
    SUPPORTED_COINS,
    get_coin_config,
    get_supported_address_types,
    format_addresses_json,
    format_addresses_csv, 
    format_addresses_plain,
    derive_wallet_from_bip85,
    AddressInfo,
)
from sseed.validation import normalize_mnemonic
from sseed.logging_config import get_logger

from ..base import BaseCommand
from ..error_handling import handle_common_errors

EXIT_SUCCESS = 0
logger = get_logger(__name__)

class DeriveCommand(BaseCommand):
    """Derive cryptocurrency addresses from BIP39 mnemonic."""
    
    def __init__(self) -> None:
        super().__init__(
            name="derive",
            help_text="Derive cryptocurrency addresses from BIP39 mnemonic",
            description=(
                "Generate cryptocurrency addresses using hierarchical deterministic (HD) wallet "
                "derivation from BIP39 mnemonics. Supports multiple cryptocurrencies, address types, "
                "and output formats with BIP85 integration."
            ),
        )
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add derive command arguments."""
        # Input/output arguments (following SSeed patterns)
        self.add_common_io_arguments(parser)
        
        # Coin selection (mutually exclusive with multiple coins)
        coin_group = parser.add_mutually_exclusive_group(required=True)
        coin_group.add_argument(
            "--coin",
            choices=SUPPORTED_COINS,
            metavar="COIN",
            help=f"Cryptocurrency to derive addresses for. Choices: {', '.join(SUPPORTED_COINS)}"
        )
        coin_group.add_argument(
            "--coins",
            metavar="COIN,COIN,...",
            help=f"Multiple cryptocurrencies (comma-separated). Example: bitcoin,ethereum,litecoin"
        )
        
        # Derivation parameters
        parser.add_argument(
            "--count",
            type=int,
            default=1,
            metavar="N",
            help="Number of addresses to generate (default: 1, max: 1000)"
        )
        parser.add_argument(
            "--account",
            type=int,
            default=0,
            metavar="N", 
            help="Account number for derivation (default: 0)"
        )
        parser.add_argument(
            "--change",
            type=int,
            choices=[0, 1],
            default=0,
            metavar="N",
            help="Change address flag: 0=external, 1=internal (default: 0)"
        )
        parser.add_argument(
            "--start-index",
            type=int,
            default=0,
            metavar="N",
            help="Starting address index (default: 0)"
        )
        
        # Address type selection
        parser.add_argument(
            "--type",
            dest="address_type",
            metavar="TYPE",
            help=(
                "Address type to generate. Options vary by coin: "
                "Bitcoin: legacy, segwit, native-segwit, taproot; "
                "Ethereum: standard; "
                "Litecoin: legacy, segwit, native-segwit"
            )
        )
        
        # Custom derivation path
        parser.add_argument(
            "--path",
            metavar="PATH",
            help="Custom derivation path (e.g., 'm/44'/0'/0'/0/0')"
        )
        
        # Extended keys
        extended_group = parser.add_argument_group("extended keys")
        extended_group.add_argument(
            "--export-xpub",
            action="store_true",
            help="Export extended public key (xpub) for account"
        )
        extended_group.add_argument(
            "--export-xprv",
            action="store_true", 
            help="Export extended private key (xprv) - requires --unsafe flag"
        )
        extended_group.add_argument(
            "--unsafe",
            action="store_true",
            help="Allow export of private keys and xprv (DANGEROUS)"
        )
        
        # Output format
        parser.add_argument(
            "--format",
            choices=["json", "csv", "plain"],
            default="plain",
            help="Output format (default: plain)"
        )
        
        # BIP85 integration
        bip85_group = parser.add_argument_group("BIP85 integration")
        bip85_group.add_argument(
            "--bip85-source",
            metavar="FILE",
            help="BIP85 master mnemonic file (instead of --input)"
        )
        bip85_group.add_argument(
            "--bip85-index",
            type=int,
            metavar="N",
            help="BIP85 child index for deterministic derivation"
        )
    
    @handle_common_errors("address derivation")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle address derivation command."""
        try:
            # Validate arguments
            self._validate_arguments(args)
            
            # Get mnemonic (either direct input or BIP85-derived)
            mnemonic = self._get_mnemonic(args)
            
            # Parse coin list
            coins = self._parse_coins(args)
            
            # Generate addresses for all coins
            all_results = {}
            for coin in coins:
                addresses = self._derive_addresses_for_coin(mnemonic, coin, args)
                all_results[coin] = addresses
            
            # Format and output results
            self._output_results(all_results, args)
            
            return EXIT_SUCCESS
            
        except Exception as e:
            logger.error("Address derivation failed: %s", e)
            print(f"Error: {e}")
            return 1
    
    def _validate_arguments(self, args: argparse.Namespace) -> None:
        """Validate command arguments."""
        # Validate count
        if not 1 <= args.count <= 1000:
            raise ValueError("Count must be between 1 and 1000")
        
        # Validate BIP85 arguments
        if (args.bip85_source is None) != (args.bip85_index is None):
            raise ValueError("Both --bip85-source and --bip85-index are required for BIP85 mode")
        
        # Validate private key export
        if args.export_xprv and not args.unsafe:
            raise ValueError("Extended private key export requires --unsafe flag")
        
        # Validate coin and address type combinations
        if args.coin and args.address_type:
            supported_types = get_supported_address_types(args.coin)
            if args.address_type not in supported_types:
                raise ValueError(f"Address type '{args.address_type}' not supported for {args.coin}")
```

## Integration Points

### 1. Command Registration

**Update `sseed/cli/commands/__init__.py`:**

```python
def _lazy_load_derive_command() -> Type[BaseCommand]:
    """Lazy load DeriveCommand."""
    from .derive import DeriveCommand  # pylint: disable=import-outside-toplevel
    return DeriveCommand

_COMMAND_LOADERS: Dict[str, Callable[[], Type[BaseCommand]]] = {
    # ... existing commands
    "derive": _lazy_load_derive_command,
}

class LazyCommandRegistry:
    def __init__(self) -> None:
        self._loaders = {
            # ... existing loaders
            "derive": self._load_derive_command,
        }
    
    def _load_derive_command(self) -> Any:
        """Load the derive command class.""" 
        from .derive import DeriveCommand  # pylint: disable=import-outside-toplevel
        return DeriveCommand

def handle_derive_command(args: Any) -> int:
    """Lazy wrapper for derive command handler."""
    from .derive import (
        handle_derive_command as _handler,  # pylint: disable=import-outside-toplevel
    )
    return _handler(args)

__all__ = [
    # ... existing exports
    "handle_derive_command",
]
```

### 2. Exception Integration

**Update `sseed/exceptions.py`:**

```python
class HDWalletError(SseedError):
    """Base exception for HD wallet operations."""

class DerivationError(HDWalletError):
    """Address derivation failed."""
    
    def __init__(self, message: str, derivation_path: str = "", operation: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.derivation_path = derivation_path
        self.operation = operation

class UnsupportedCoinError(HDWalletError):
    """Cryptocurrency not supported."""
    
    def __init__(self, message: str, coin: str = "", supported_coins: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.coin = coin
        self.supported_coins = supported_coins or []

class InvalidPathError(HDWalletError):
    """Invalid derivation path."""

class AddressGenerationError(HDWalletError):
    """Address generation failed."""
```

## Summary

This highly modular architecture follows SSeed's exact patterns:

- **11 small, focused files** averaging 250 lines each
- **Clear separation of concerns** with single responsibility per file
- **Rich `__init__.py`** with public API exports and convenience functions
- **Hierarchical exceptions** with detailed context
- **Lazy imports** for performance optimization
- **Backward compatibility** maintained through re-exports
- **Security-first design** with secure memory cleanup
- **Integration points** clearly defined for existing SSeed infrastructure

The design ensures seamless integration while maintaining SSeed's security-first, automation-friendly philosophy in a highly modular, maintainable structure.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Deep dive into existing command patterns and file structure", "status": "completed", "priority": "high", "id": "code_analysis_1"}, {"content": "Analyze existing modular patterns in BIP85 and other modules", "status": "completed", "priority": "high", "id": "code_analysis_2"}, {"content": "Design highly modular HD wallet architecture", "status": "completed", "priority": "high", "id": "modular_design_1"}, {"content": "Create detailed module breakdown with small focused files", "status": "completed", "priority": "medium", "id": "modular_design_2"}, {"content": "Update implementation plan with actual code integration points", "status": "completed", "priority": "medium", "id": "integration_plan_1"}]