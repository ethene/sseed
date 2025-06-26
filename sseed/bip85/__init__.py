"""BIP85 Deterministic Entropy Generation.

Implementation of BIP85 (Deterministic Entropy From BIP32 Keychains)
for generating child entropy from master seeds in a deterministic manner.

This module provides:
- BIP85 core derivation using BIP32 + HMAC-SHA512
- Path validation and encoding
- Application-specific formatters (BIP39, Hex, Password)
- Complete error handling and security infrastructure

Integrates seamlessly with existing SSeed infrastructure including
multi-language support, file operations, and validation patterns.

Key Features:
- Full BIP85 specification compliance
- Multiple application support (BIP39, hex, passwords)
- Secure memory management and cleanup
- Integration with existing SSeed infrastructure

References:
- BIP85 Specification: https://github.com/bitcoin/bips/blob/master/bip-0085.mediawiki
- SSeed Documentation: https://github.com/ethene/sseed
"""

from .core import (
    derive_bip85_entropy,
    create_bip32_master_key,
    encode_bip85_path,
)
from .exceptions import (
    Bip85Error,
    Bip85ValidationError,
    Bip85DerivationError,
    Bip85ApplicationError,
)
from .paths import (
    validate_bip85_parameters,
    calculate_entropy_bytes_needed,
    format_bip85_path,
    get_application_name,
    format_parameter_summary
)
from .applications import Bip85Applications

# Version information
__version__ = "1.0.0"
__author__ = "SSeed Development Team"

# Public API exports
__all__ = [
    # Core functionality
    "derive_bip85_entropy",
    "create_bip32_master_key", 
    "encode_bip85_path",
    # Exception classes
    "Bip85Error",
    "Bip85ValidationError",
    "Bip85DerivationError",
    "Bip85ApplicationError",
    # Path utilities
    "validate_bip85_parameters",
    "calculate_entropy_bytes_needed",
    "format_bip85_path",
    "get_application_name",
    "format_parameter_summary",
    # Applications
    "Bip85Applications",
] 

# Convenience function for common usage pattern
def generate_bip39_mnemonic(
    master_seed: bytes,
    word_count: int = 12,
    index: int = 0,
    language: str = "en"
) -> str:
    """Convenience function to generate BIP39 mnemonic from BIP85.
    
    Args:
        master_seed: 512-bit master seed from BIP39 PBKDF2.
        word_count: Number of words (12, 15, 18, 21, or 24).
        index: Child derivation index (0 to 2³¹-1).
        language: BIP39 language code.
        
    Returns:
        BIP39 mnemonic string.
        
    Example:
        >>> import sseed.bip85 as bip85
        >>> master_seed = bytes.fromhex("a" * 128)
        >>> mnemonic = bip85.generate_bip39_mnemonic(master_seed, 12)
        >>> len(mnemonic.split())
        12
    """
    apps = Bip85Applications()
    return apps.derive_bip39_mnemonic(master_seed, word_count, index, language)


def generate_hex_entropy(
    master_seed: bytes,
    byte_length: int = 32,
    index: int = 0,
    uppercase: bool = False
) -> str:
    """Convenience function to generate hex entropy from BIP85.
    
    Args:
        master_seed: 512-bit master seed from BIP39 PBKDF2.
        byte_length: Number of entropy bytes (16-64).
        index: Child derivation index (0 to 2³¹-1).
        uppercase: Return uppercase hex.
        
    Returns:
        Hexadecimal entropy string.
        
    Example:
        >>> import sseed.bip85 as bip85
        >>> master_seed = bytes.fromhex("b" * 128)
        >>> hex_str = bip85.generate_hex_entropy(master_seed, 32)
        >>> len(hex_str)
        64
    """
    apps = Bip85Applications()
    return apps.derive_hex_entropy(master_seed, byte_length, index, uppercase)


def generate_password(
    master_seed: bytes,
    length: int = 20,
    index: int = 0,
    character_set: str = "base64"
) -> str:
    """Convenience function to generate password from BIP85.
    
    Args:
        master_seed: 512-bit master seed from BIP39 PBKDF2.
        length: Password length in characters (10-128).
        index: Child derivation index (0 to 2³¹-1).
        character_set: Character set (base64, base85, alphanumeric, ascii).
        
    Returns:
        Generated password string.
        
    Example:
        >>> import sseed.bip85 as bip85
        >>> master_seed = bytes.fromhex("c" * 128)
        >>> password = bip85.generate_password(master_seed, 20)
        >>> len(password)
        20
    """
    apps = Bip85Applications()
    return apps.derive_password(master_seed, length, index, character_set)


# Add convenience functions to __all__
__all__.extend([
    "generate_bip39_mnemonic",
    "generate_hex_entropy", 
    "generate_password"
]) 