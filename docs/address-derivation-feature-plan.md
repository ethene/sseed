# Address Derivation Feature Development Plan

## Executive Summary

This document outlines the development plan for adding comprehensive HD wallet address derivation capabilities to SSeed. The feature will provide a new `derive` command that generates cryptocurrency addresses from BIP39 mnemonics and BIP85 entropy, supporting multiple cryptocurrencies, address types, and output formats.

**UPDATED**: This plan has been refined based on comprehensive code analysis to follow SSeed's exact modular architecture patterns with small, focused files and seamless integration points.

## Code-Based Architecture Analysis

### Existing SSeed Patterns (Analyzed from Actual Code)

**Command Structure Analysis:**
- **BaseCommand Pattern**: All commands inherit from `BaseCommand` in `sseed/cli/base.py`
- **Lazy Loading Registry**: Dual registration in `LazyCommandRegistry` and `_COMMAND_LOADERS`
- **File Sizes**: Commands range 132-791 lines (average ~400 lines)
- **Argument Patterns**: Standard `-i/--input`, `-o/--output`, `--format`, language/word count patterns

**Modular Organization (Actual Analysis):**
- **BIP85 Module**: 8 files, 160-617 lines each, clear separation (core→applications→paths→cache→exceptions)
- **Validation Module**: 9 files, modular by concern (input→crypto→structure→analysis→formatters)
- **File Operations**: 4 focused files (37-251 lines), clear I/O separation (readers→writers→formatters→validators)
- **Average File Size**: ~300 lines, with rich `__init__.py` files (35-235 lines)

**Integration Infrastructure:**
- **BIP32 Foundation**: `create_bip32_master_key()` in `sseed/bip85/core.py` (617 lines)
- **Security Patterns**: `secure_delete_variable()` from `sseed/entropy`, comprehensive logging
- **Exception Hierarchy**: `SseedError` base with domain-specific inheritance
- **Crypto Library**: `bip-utils>=2.9.3` with `Bip32Secp256k1`, `Bip44/49/84/86` support

### Proven Modular Principles
1. **Small Focused Files**: Most files 200-400 lines, clear single responsibility
2. **Rich `__init__.py`**: Public API exports, convenience functions, backward compatibility
3. **Hierarchical Exceptions**: Domain-specific errors with detailed context
4. **Layered Architecture**: Core→Applications→Utilities→Interfaces
5. **Minimal Dependencies**: Modules only depend on shared utilities (logging, exceptions)

## Feature Requirements

### 1. CLI Interface Design

```bash
# Basic address derivation
sseed derive -i wallet.txt --coin bitcoin --count 10
sseed derive -i wallet.txt --coin ethereum --count 5 --account 1

# Multiple coins with same mnemonic
sseed derive -i wallet.txt --coins bitcoin,ethereum,litecoin --count 5

# Specific derivation paths
sseed derive -i wallet.txt --path "m/44'/0'/0'/0/0" --coin bitcoin
sseed derive -i wallet.txt --path "m/44'/60'/0'/0/0" --coin ethereum

# Address type selection (Bitcoin)
sseed derive -i wallet.txt --coin bitcoin --type legacy --count 5
sseed derive -i wallet.txt --coin bitcoin --type segwit --count 5
sseed derive -i wallet.txt --coin bitcoin --type native-segwit --count 5
sseed derive -i wallet.txt --coin bitcoin --type taproot --count 5

# Account and change address derivation
sseed derive -i wallet.txt --coin bitcoin --account 0 --change 0 --count 10
sseed derive -i wallet.txt --coin bitcoin --account 0 --change 1 --count 5  # Change addresses

# Extended key export
sseed derive -i wallet.txt --coin bitcoin --export-xpub --account 0
sseed derive -i wallet.txt --coin bitcoin --export-xprv --account 0 --unsafe

# Output formats
sseed derive -i wallet.txt --coin bitcoin --format json --count 5
sseed derive -i wallet.txt --coin bitcoin --format csv --count 10
sseed derive -i wallet.txt --coin bitcoin --format plain --count 3

# BIP85 integration
sseed derive --bip85-source master.txt --index 0 --coin bitcoin --count 5
sseed bip85 -i master.txt --app bip39 --index 0 | sseed derive --coin ethereum
```

### 2. Supported Cryptocurrencies (Phase 1)

**High Priority:**
- **Bitcoin** (BTC) - All address types: Legacy, SegWit, Native SegWit, Taproot
- **Ethereum** (ETH) - Standard Ethereum addresses
- **Litecoin** (LTC) - Legacy and SegWit support

**Medium Priority:**
- Bitcoin Cash (BCH)
- Dogecoin (DOGE)
- Cardano (ADA)
- Polkadot (DOT)

### 3. Derivation Path Standards

**Supported Standards:**
- **BIP44**: `m/44'/coin'/account'/change/address` - Legacy addresses
- **BIP49**: `m/49'/coin'/account'/change/address` - SegWit (P2SH-P2WPKH)
- **BIP84**: `m/84'/coin'/account'/change/address` - Native SegWit (P2WPKH)
- **BIP86**: `m/86'/coin'/account'/change/address` - Taproot (P2TR)

**Coin Type Constants:**
- Bitcoin (BTC): 0
- Ethereum (ETH): 60
- Litecoin (LTC): 2
- Bitcoin Cash (BCH): 145
- Dogecoin (DOGE): 3

### 4. Output Format Specifications

#### JSON Format
```json
{
  "mnemonic_info": {
    "word_count": 24,
    "language": "english",
    "checksum_valid": true
  },
  "derivation": {
    "coin": "bitcoin",
    "address_type": "native-segwit",
    "derivation_path_template": "m/84'/0'/0'/0/{index}",
    "account": 0,
    "change": 0
  },
  "addresses": [
    {
      "index": 0,
      "derivation_path": "m/84'/0'/0'/0/0",
      "private_key": "L1234...",
      "public_key": "03abc123...",
      "address": "bc1q...",
      "address_type": "native-segwit"
    }
  ],
  "extended_keys": {
    "xpub": "xpub6789...",
    "xprv": "xprv9876..."
  },
  "metadata": {
    "generated_at": "2024-01-01T12:00:00Z",
    "total_addresses": 10,
    "generator": "sseed v1.11.5"
  }
}
```

#### CSV Format
```csv
Index,DerivationPath,PrivateKey,PublicKey,Address,AddressType
0,m/84'/0'/0'/0/0,L1234...,03abc123...,bc1q...,native-segwit
1,m/84'/0'/0'/0/1,L5678...,03def456...,bc1q...,native-segwit
```

#### Plain Text Format
```
Bitcoin Native SegWit Addresses (m/84'/0'/0'/0/{index})
================================================================
0: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
1: bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4
2: bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3

Extended Public Key (Account 0): xpub6CUGRUonZSQ4TWtTMmzXdrXDtypWKiKrhko4egpiMZbpiaQL...
```

## Highly Modular Implementation Architecture

### 1. Module Structure (Following SSeed Patterns)

```
sseed/
├── hd_wallet/                          # New HD wallet module (11 files)
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

**Architecture Principles:**
- **11 small, focused files** averaging 250 lines each (follows SSeed patterns exactly)
- **Clear separation of concerns** with single responsibility per file
- **No file exceeds 400 lines** (following SSeed's largest file of 791 lines)
- **Rich `__init__.py`** with public API exports and convenience functions
- **Modular by responsibility**: Core→Coins→Derivation→Addresses→Validation→Formatters

### 2. Detailed File Specifications (Based on SSeed Patterns)

#### `sseed/hd_wallet/__init__.py` (~150 lines)
**Responsibility**: Public API exports, convenience functions, module metadata (following BIP85 patterns)

```python
"""HD Wallet Address Derivation for SSeed.

This module implements hierarchical deterministic wallet functionality
following BIP32, BIP44, BIP49, BIP84, and BIP86 standards.
"""

# Core functionality exports (following file_operations/__init__.py pattern)
from .core import HDWalletManager, derive_addresses_from_mnemonic
from .addresses import AddressInfo, generate_address, derive_address_batch
from .derivation import DerivationPath, build_derivation_path, validate_path
from .coins import CoinConfig, SUPPORTED_COINS, get_coin_config
from .exceptions import HDWalletError, DerivationError, UnsupportedCoinError

# Convenience functions (following BIP85/__init__.py pattern)
def generate_addresses(mnemonic: str, coin: str = "bitcoin", count: int = 1) -> List[AddressInfo]:
    """Convenience function for generating addresses."""
    manager = HDWalletManager(mnemonic)
    return manager.derive_addresses_batch(coin=coin, count=count)

__all__ = [
    "HDWalletManager", "derive_addresses_from_mnemonic", "AddressInfo",
    "generate_address", "derive_address_batch", "DerivationPath",
    "build_derivation_path", "CoinConfig", "SUPPORTED_COINS",
    "HDWalletError", "DerivationError", "UnsupportedCoinError",
    "generate_addresses"  # Convenience function
]
```

#### `sseed/hd_wallet/core.py` (~350 lines)
**Responsibility**: Core HD derivation logic, BIP32 operations, master key management

```python
"""Core HD wallet functionality."""

class HDWalletManager:
    """Core HD wallet manager for address derivation."""
    
    def __init__(self, mnemonic: str, validate: bool = True):
        """Initialize HD wallet from mnemonic (following BIP85 patterns)."""
        self._mnemonic = normalize_mnemonic(mnemonic)
        self._master_seed: Optional[bytes] = None
        self._master_key: Optional[Bip32Secp256k1] = None
        
    def _get_master_key(self) -> Bip32Secp256k1:
        """Get or create master key with caching (following BIP85 caching patterns)."""
        # Reuse existing create_bip32_master_key() from sseed/bip85/core.py
        
    def derive_addresses_batch(self, coin: str, count: int = 1, **kwargs) -> List[AddressInfo]:
        """Derive multiple addresses efficiently."""
        # Implementation using existing BIP32 infrastructure
```

#### `sseed/hd_wallet/coins.py` (~300 lines)
**Responsibility**: Cryptocurrency configurations, coin constants, supported coins

```python
"""Cryptocurrency configuration for HD wallet operations."""

@dataclass
class CoinConfig:
    """Cryptocurrency configuration (following validation module patterns)."""
    name: str
    symbol: str
    coin_type: int
    address_types: Dict[str, AddressTypeConfig]
    default_address_type: str

# Configuration instances
BITCOIN_CONFIG = CoinConfig(
    name="bitcoin", symbol="BTC", coin_type=0,
    default_address_type="native-segwit",
    address_types={
        "legacy": AddressTypeConfig(purpose=44, bip_utils_coin=Bip44Coins.BITCOIN),
        "segwit": AddressTypeConfig(purpose=49, bip_utils_coin=Bip49Coins.BITCOIN),
        "native-segwit": AddressTypeConfig(purpose=84, bip_utils_coin=Bip84Coins.BITCOIN),
        "taproot": AddressTypeConfig(purpose=86, bip_utils_coin=Bip86Coins.BITCOIN),
    }
)

SUPPORTED_COINS = ["bitcoin", "ethereum", "litecoin"]  # For CLI choices
```

#### `sseed/hd_wallet/addresses.py` (~320 lines)
**Responsibility**: Address generation logic, address formatting

```python
"""Address generation for HD wallets."""

@dataclass
class AddressInfo:
    """Complete address information (following validation patterns)."""
    index: int
    derivation_path: str
    private_key: str
    public_key: str
    address: str
    address_type: str
    coin: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""

def generate_address(derived_key: Bip32Secp256k1, coin_config: CoinConfig, 
                    derivation_path: str, index: int) -> AddressInfo:
    """Generate address from derived key using bip-utils."""
    # Implementation using Bip44/49/84/86 from bip-utils
```

### 3. Command Implementation (Following SSeed Command Patterns)

#### `sseed/cli/commands/derive.py` (~400 lines)
**Responsibility**: CLI command implementation with argument parsing and output handling

```python
"""Derive command implementation.

Generates cryptocurrency addresses from BIP39 mnemonics using HD wallet derivation.
"""

from sseed.hd_wallet import (
    HDWalletManager, SUPPORTED_COINS, get_coin_config,
    format_addresses_json, format_addresses_csv, format_addresses_plain,
    derive_wallet_from_bip85, AddressInfo,
)
from ..base import BaseCommand
from ..error_handling import handle_common_errors

class DeriveCommand(BaseCommand):
    """Derive cryptocurrency addresses from BIP39 mnemonic (following existing patterns)."""
    
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
        """Add derive command arguments (following gen.py patterns)."""
        # Standard I/O arguments (following BaseCommand patterns)
        self.add_common_io_arguments(parser)
        
        # Coin selection (mutually exclusive group like entropy sources in gen.py)
        coin_group = parser.add_mutually_exclusive_group(required=True)
        coin_group.add_argument("--coin", choices=SUPPORTED_COINS, metavar="COIN")
        coin_group.add_argument("--coins", metavar="COIN,COIN,...", help="Multiple coins")
        
        # Derivation parameters (following BIP85 parameter patterns)
        parser.add_argument("--count", type=int, default=1, metavar="N", help="Number of addresses")
        parser.add_argument("--account", type=int, default=0, metavar="N", help="Account number")
        parser.add_argument("--change", type=int, choices=[0, 1], default=0, help="Change flag")
        
        # Address type (following gen.py language choice patterns)
        parser.add_argument("--type", dest="address_type", metavar="TYPE", 
                          help="Address type (legacy, segwit, native-segwit, taproot)")
        
        # Extended keys (following BIP85 application patterns)
        extended_group = parser.add_argument_group("extended keys")
        extended_group.add_argument("--export-xpub", action="store_true")
        extended_group.add_argument("--export-xprv", action="store_true")
        extended_group.add_argument("--unsafe", action="store_true", help="Allow private key export")
        
        # Output format (following validation command patterns)
        parser.add_argument("--format", choices=["json", "csv", "plain"], default="plain")
        
        # BIP85 integration (following existing BIP85 argument patterns)
        bip85_group = parser.add_argument_group("BIP85 integration")
        bip85_group.add_argument("--bip85-source", metavar="FILE", help="BIP85 master mnemonic")
        bip85_group.add_argument("--bip85-index", type=int, metavar="N", help="BIP85 child index")
        
    @handle_common_errors("address derivation")  # Following existing error handling patterns
    def handle(self, args: argparse.Namespace) -> int:
        """Handle address derivation command (following existing command patterns)."""
        # Implementation following gen.py and bip85.py patterns
        # 1. Validate arguments
        # 2. Get mnemonic (direct input or BIP85-derived)
        # 3. Parse coin list
        # 4. Generate addresses using HDWalletManager
        # 5. Format and output results using formatters
        return EXIT_SUCCESS
```

## Exact Integration with Existing SSeed Architecture

### 1. Leveraging Existing BIP85 Infrastructure (Code-Based)

**Direct Reuse of Existing Functions:**
```python
# In sseed/hd_wallet/core.py - reuse existing BIP32 infrastructure
from sseed.bip85.core import create_bip32_master_key  # EXISTING function (line 92)
from sseed.entropy import secure_delete_variable     # EXISTING function
from sseed.logging_config import get_logger, log_security_event  # EXISTING

class HDWalletManager:
    def _get_master_key(self) -> Bip32Secp256k1:
        """Reuse existing BIP32 master key creation."""
        if self._master_key is None:
            # Use EXISTING function from BIP85 module
            self._master_key = create_bip32_master_key(self._master_seed)
        return self._master_key
```

**BIP85 Integration (New File):**
```python
# In sseed/hd_wallet/bip85_integration.py (~220 lines)
from sseed.bip85 import Bip85Applications  # EXISTING class

def derive_wallet_from_bip85(master_seed: bytes, bip85_index: int) -> str:
    """Generate HD wallet mnemonic from BIP85 child entropy."""
    apps = Bip85Applications()  # Use EXISTING BIP85 infrastructure
    child_mnemonic = apps.derive_bip39_mnemonic(master_seed, 24, bip85_index)
    return child_mnemonic
```

### 2. Command Registration (Exact Patterns from __init__.py)

**Update `sseed/cli/commands/__init__.py` (following EXACT patterns):**
```python
# Add lazy loader function (following lines 22-62 pattern)
def _lazy_load_derive_command() -> Type[BaseCommand]:
    """Lazy load DeriveCommand."""
    from .derive import DeriveCommand  # pylint: disable=import-outside-toplevel
    return DeriveCommand

# Add to command registry (line 73-81 pattern)
_COMMAND_LOADERS: Dict[str, Callable[[], Type[BaseCommand]]] = {
    "gen": _lazy_load_gen_command,
    "shard": _lazy_load_shard_command,
    # ... existing commands
    "derive": _lazy_load_derive_command,  # NEW
}

# Add to LazyCommandRegistry class (lines 87-166 pattern)
class LazyCommandRegistry:
    def __init__(self) -> None:
        self._loaders = {
            # ... existing loaders
            "derive": self._load_derive_command,  # NEW
        }
    
    def _load_derive_command(self) -> Any:
        """Load the derive command class."""
        from .derive import DeriveCommand  # pylint: disable=import-outside-toplevel
        return DeriveCommand

# Add handler function (lines 172-233 pattern)
def handle_derive_command(args: Any) -> int:
    """Lazy wrapper for derive command handler."""
    from .derive import (
        handle_derive_command as _handler,  # pylint: disable=import-outside-toplevel
    )
    return _handler(args)

# Add to exports (lines 245-257)
__all__ = [
    # ... existing exports
    "handle_derive_command",  # NEW
]
```

### 3. Exception Integration (Exact Patterns from exceptions.py)

**Extend `sseed/exceptions.py` (following existing hierarchy):**
```python
# Add to existing exception hierarchy (following SseedError patterns)
class HDWalletError(SseedError):
    """Base exception for HD wallet operations."""
    
    def __init__(self, message: str, coin: str = "", operation: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.coin = coin
        self.operation = operation

class DerivationError(HDWalletError):
    """Address derivation failed."""
    
    def __init__(self, message: str, derivation_path: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.derivation_path = derivation_path

class UnsupportedCoinError(HDWalletError):
    """Cryptocurrency not supported."""
    
    def __init__(self, message: str, supported_coins: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.supported_coins = supported_coins or []

class InvalidPathError(HDWalletError):
    """Invalid derivation path."""

class AddressGenerationError(HDWalletError):
    """Address generation failed."""
```

## Security Considerations

### 1. Private Key Handling
- **Default Behavior**: Never expose private keys unless `--unsafe` flag is used
- **Memory Security**: Implement secure cleanup for all private key material
- **Logging**: Never log private keys, only derivation paths and public information

### 2. Extended Key Export
- **xpub Export**: Safe by default, contains no private information
- **xprv Export**: Requires `--unsafe` flag and user confirmation
- **Account Level**: Only export account-level keys (m/44'/0'/0') not master keys

### 3. Derivation Path Validation
- **Path Sanitization**: Validate all custom derivation paths
- **Range Checking**: Ensure indices are within valid BIP32 ranges
- **Hardened Keys**: Use hardened derivation for account/coin levels

## Testing Strategy

### 1. Test Vector Validation
- **BIP44/49/84 Test Vectors**: Validate against official test vectors
- **Cross-Tool Compatibility**: Test against Ian Coleman's tool, Electrum, etc.
- **Multi-Language**: Test with all 9 supported BIP39 languages

### 2. Security Testing
- **Memory Leaks**: Verify secure cleanup of sensitive data
- **Error Conditions**: Test invalid inputs, malformed mnemonics
- **Fuzzing**: Test with random/malformed derivation paths

### 3. Performance Testing
- **Batch Operations**: Test large address generation (1000+ addresses)
- **Memory Usage**: Monitor memory consumption during batch operations
- **Caching Effectiveness**: Verify BIP32 key caching improves performance

## Updated Implementation Phases (Based on Modular Architecture)

### Phase 1: Core Modular Infrastructure (Week 1)
**Focus: Foundation modules following SSeed patterns exactly**

1. **Module Structure Setup** (Days 1-2)
   - Create `sseed/hd_wallet/` directory with 11 modular files
   - Implement `exceptions.py` (~120 lines) - HD wallet specific exceptions
   - Implement `__init__.py` (~150 lines) - Public API exports and convenience functions
   - Set up proper imports and module structure

2. **Core HD Functionality** (Days 3-4)
   - Implement `core.py` (~350 lines) - HDWalletManager with BIP32 integration
   - Implement `derivation.py` (~250 lines) - Path utilities and validation
   - Reuse existing `create_bip32_master_key()` from BIP85 module
   - Implement secure memory cleanup patterns

3. **Bitcoin Foundation** (Days 5-7)
   - Implement `coins.py` (~300 lines) - Bitcoin configuration with all address types
   - Implement `addresses.py` (~320 lines) - Address generation using bip-utils
   - Implement `validation.py` (~280 lines) - Parameter validation
   - Basic Bitcoin Legacy/SegWit/Native SegWit/Taproot support

### Phase 2: CLI and Output Systems (Week 2)
**Focus: Command implementation and formatting systems**

1. **CLI Command Implementation** (Days 1-3)
   - Implement `derive.py` (~400 lines) following exact SSeed command patterns
   - Add command registration to `__init__.py` using lazy loading patterns
   - Implement argument parsing following gen.py and bip85.py patterns
   - Add error handling using existing `@handle_common_errors` decorator

2. **Output Formatting** (Days 4-5)
   - Implement `formatters.py` (~200 lines) - JSON, CSV, plain text output
   - Follow existing formatting patterns from validation module
   - Implement rich metadata and structured output

3. **Extended Key Support** (Days 6-7)
   - Implement `extended_keys.py` (~180 lines) - xpub/xprv handling
   - Add security safeguards for private key export
   - Implement account-level key derivation

### Phase 3: Multi-Coin and Advanced Features (Week 3)
**Focus: Additional cryptocurrencies and advanced functionality**

1. **Multi-Coin Support** (Days 1-3)
   - Extend `coins.py` with Ethereum and Litecoin configurations
   - Update `addresses.py` for multi-coin address generation
   - Test cross-cryptocurrency functionality

2. **BIP85 Integration** (Days 4-5)
   - Implement `bip85_integration.py` (~220 lines) - BIP85 to HD wallet bridge
   - Leverage existing BIP85 infrastructure from `sseed.bip85`
   - Add BIP85 CLI arguments and processing

3. **Batch Operations** (Days 6-7)
   - Implement `batch.py` (~350 lines) - Optimized batch address generation
   - Add performance caching following BIP85 cache patterns
   - Implement large-scale address generation (1000+ addresses)

### Phase 4: Testing and Integration Polish (Week 4)
**Focus: Comprehensive testing and documentation**

1. **Test Suite Implementation** (Days 1-3)
   - Create test files for each module following SSeed test patterns
   - Implement BIP44/49/84/86 test vector validation
   - Add cross-tool compatibility tests
   - Performance benchmarking for batch operations

2. **Documentation and Examples** (Days 4-5)
   - Update CLI help text and examples
   - Add HD wallet examples to `cli/examples.py`
   - Create comprehensive usage documentation
   - Update future enhancements document

3. **Final Integration** (Days 6-7)
   - Integration testing with existing SSeed functionality
   - Performance optimization and memory usage validation
   - Final security review and code cleanup
   - Prepare for release integration

## Updated Success Metrics (Based on Modular Design)

### Modular Architecture Goals
- **File Count**: Exactly 11 small, focused files averaging 250 lines each
- **Module Separation**: Clear single responsibility per file
- **Integration Quality**: Seamless reuse of existing SSeed infrastructure
- **Code Reuse**: Maximum leverage of BIP85, entropy, and validation modules

### Functionality Targets
- **Address Generation**: 100% compatibility with BIP44/49/84/86 derivation paths  
- **Multi-Coin Support**: Bitcoin (4 address types), Ethereum, Litecoin working correctly
- **Output Formats**: JSON, CSV, plain text with rich metadata
- **Performance**: Generate 1000 addresses in <5 seconds using batch operations
- **BIP85 Integration**: Direct derivation from BIP85 child mnemonics

### Security Compliance
- **Private Key Protection**: Zero private key exposure without explicit `--unsafe` flag
- **Memory Security**: All sensitive data cleaned using existing `secure_delete_variable()`
- **Path Validation**: 100% validation using structured derivation path utilities
- **Error Context**: Rich exception context following SSeed patterns

### Integration Standards
- **CLI Consistency**: Follows exact patterns from gen.py, bip85.py, validate.py
- **Command Registration**: Uses existing lazy loading patterns from `__init__.py`
- **Error Handling**: Uses existing `@handle_common_errors` decorator
- **Import Patterns**: Follows existing module dependency structure
- **Exception Hierarchy**: Extends existing `SseedError` with proper inheritance

## Updated Risk Mitigation (Architecture-Focused)

### Technical Implementation Risks
- **Module Dependencies**: Minimize cross-dependencies, only use shared utilities
- **File Size Control**: Monitor file sizes to stay within 200-400 line range
- **Performance Isolation**: Keep batch operations in separate module for optimization
- **bip-utils Integration**: Extensive testing with Bip44/49/84/86 classes

### Security Architecture Risks  
- **Private Key Scope**: Isolate private key handling to specific modules
- **Memory Management**: Use existing security patterns across all modules
- **Validation Boundaries**: Clear validation at module interfaces
- **Error Information**: Ensure exceptions don't leak sensitive data

### Integration Risks
- **Command Conflicts**: Follow exact command registration patterns
- **Import Cycles**: Careful module layering to avoid circular dependencies
- **Backward Compatibility**: All changes additive, no modifications to existing code
- **Documentation Consistency**: Follow existing help text and example patterns

## Summary: Code-Based Modular Architecture

This refined plan is based on comprehensive analysis of the actual SSeed codebase and follows its exact modular patterns:

**Key Advantages:**
1. **Perfect Integration**: Leverages existing BIP32 infrastructure from BIP85 module
2. **Proven Patterns**: Uses exact command, exception, and module patterns from codebase
3. **Small Focused Files**: 11 files averaging 250 lines each, following SSeed standards
4. **Security Continuity**: Uses existing security patterns and memory management
5. **Performance Foundation**: Builds on existing caching and optimization patterns

**Direct Code Reuse:**
- `create_bip32_master_key()` from `sseed/bip85/core.py` (line 92)
- `secure_delete_variable()` from `sseed/entropy`
- `@handle_common_errors` from `sseed/cli/error_handling.py`
- Command registration patterns from `sseed/cli/commands/__init__.py`
- Exception patterns from `sseed/exceptions.py`

This architecture ensures the HD wallet feature integrates seamlessly while maintaining SSeed's security-first, automation-friendly design philosophy through proven modular patterns.