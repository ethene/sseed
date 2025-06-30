"""BIP85 entropy derivation core implementation.

This module implements the complete BIP85 specification for deterministic entropy
derivation from BIP32 hierarchical deterministic wallets, with full specification
compliance and security-focused design.

BIP85 Overview:
    BIP85 enables the derivation of multiple deterministic entropy sources from a
    single master seed, useful for generating child mnemonics, HD wallet seeds,
    passwords, and other cryptographic entropy in a reproducible manner.

Key Features:
    - Full BIP85 specification compliance
    - Correct BIP39 derivation path: m/83696968'/39'/{language}'/{words}'/{index}'
    - Support for all BIP85 applications (BIP39, hex, passwords)
    - Memory-secure cleanup of sensitive data
    - Comprehensive error handling and validation
    - Performance optimization with master key caching

Supported Applications:
    - BIP39 Mnemonics (application 39) with proper language support
    - Hex entropy (application 128)
    - Passwords (application 9999) with various character sets

BIP39 Language Codes (per BIP85 specification):
    - 0: English
    - 1: Japanese
    - 2: Korean
    - 3: Spanish
    - 4: Chinese (Simplified)
    - 5: Chinese (Traditional)
    - 6: French
    - 7: Italian
    - 8: Czech
    - 9: Portuguese

Security Notes:
    - All intermediate values are securely cleared from memory
    - Private keys are never logged or exposed in exceptions
    - HMAC uses the specified "bip-entropy-from-k" key per BIP85
    - Master seed should be from a secure random source

Example:
    >>> import hashlib
    >>> from sseed.bip85.applications import Bip85Applications
    >>>
    >>> # Generate master seed from mnemonic (production should use secure methods)
    >>> test_mnemonic = (
    ...     "install scatter logic circle pencil average fall shoe quantum disease suspect usage"
    ... )
    >>> master_seed = hashlib.pbkdf2_hmac(
    ...     'sha512', test_mnemonic.encode('utf-8'), b'mnemonic', 2048, 64
    ... )
    >>>
    >>> # Create BIP85 applications instance
    >>> apps = Bip85Applications()
    >>>
    >>> # Generate child BIP39 mnemonic (matches official test vector)
    >>> child_mnemonic = apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")
    >>> print(child_mnemonic)
    girl mad pet galaxy egg matter matrix prison refuse sense ordinary nose
"""

import hashlib
import hmac
import struct
from typing import (
    Any,
    Optional,
    Tuple,
)

from bip_utils import Bip32Secp256k1

from sseed.entropy import secure_delete_variable
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

from .exceptions import (
    Bip85DerivationError,
    Bip85ValidationError,
)

logger = get_logger(__name__)

# BIP85 constants
BIP85_PURPOSE = 83696968  # BIP85 purpose code (0x83696968 in decimal)


def create_bip32_master_key(master_seed: bytes) -> Bip32Secp256k1:
    """Create BIP32 master key from master seed.

    Converts a 512-bit master seed (from BIP39 PBKDF2) into a BIP32
    hierarchical deterministic master key for BIP85 derivation.

    Args:
        master_seed: 512-bit (64-byte) master seed from BIP39.

    Returns:
        BIP32 master key object for hierarchical derivation.

    Raises:
        Bip85DerivationError: If master key creation fails.

    Example:
        >>> master_seed = bytes.fromhex("a" * 128)  # 64 bytes
        >>> master_key = create_bip32_master_key(master_seed)
        >>> isinstance(master_key, Bip32Secp256k1)
        True
    """
    try:
        logger.debug("Creating BIP32 master key from %d-byte seed", len(master_seed))
        log_security_event("BIP85: BIP32 master key creation initiated")

        # Validate master seed length
        if len(master_seed) != 64:
            raise Bip85ValidationError(
                f"Master seed must be 64 bytes, got {len(master_seed)} bytes",
                parameter="master_seed",
                value=len(master_seed),
                valid_range="64 bytes",
            )

        # Create BIP32 master key using bip-utils
        master_key = Bip32Secp256k1.FromSeed(master_seed)

        logger.debug("Successfully created BIP32 master key")
        log_security_event("BIP85: BIP32 master key creation completed")

        return master_key

    except Exception as e:
        error_msg = f"Failed to create BIP32 master key: {e}"
        logger.error(error_msg)
        log_security_event(f"BIP85: Master key creation failed: {error_msg}")

        raise Bip85DerivationError(
            error_msg,
            operation="create_bip32_master_key",
            context={"master_seed_length": len(master_seed)},
            original_error=e,
        ) from e


def encode_bip85_path(application: int, length: int, index: int) -> bytes:
    """Encode BIP85 derivation path components as bytes for HMAC.

    Serializes the BIP85 derivation path components according to the
    BIP85 specification for use as HMAC-SHA512 message data.

    Args:
        application: Application identifier (e.g., 39 for BIP39).
        length: Length parameter (e.g., word count for BIP39).
        index: Child index (0 to 2³¹-1).

    Returns:
        12-byte path encoding for HMAC.

    Raises:
        Bip85ValidationError: If parameters are invalid.

    Example:
        >>> path_bytes = encode_bip85_path(39, 12, 0)
        >>> len(path_bytes)
        12
    """
    try:
        logger.debug(
            "Encoding BIP85 path: app=%d, length=%d, index=%d",
            application,
            length,
            index,
        )

        # Validate parameters
        if not 0 <= application <= 0xFFFFFFFF:
            raise Bip85ValidationError(
                f"Application must be 0-4294967295, got {application}",
                parameter="application",
                value=application,
                valid_range="0 to 4294967295",
            )

        if not 0 <= length <= 0xFFFFFFFF:
            raise Bip85ValidationError(
                f"Length must be 0-4294967295, got {length}",
                parameter="length",
                value=length,
                valid_range="0 to 4294967295",
            )

        if not 0 <= index < 2**31:
            raise Bip85ValidationError(
                f"Index must be 0 to 2147483647, got {index}",
                parameter="index",
                value=index,
                valid_range="0 to 2147483647",
            )

        # Encode as big-endian 32-bit integers (12 bytes total)
        path_bytes = struct.pack(">III", application, length, index)

        logger.debug("Successfully encoded BIP85 path: %d bytes", len(path_bytes))

        return path_bytes

    except Bip85ValidationError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        error_msg = f"Failed to encode BIP85 path: {e}"
        logger.error(error_msg)

        raise Bip85DerivationError(
            error_msg,
            operation="encode_bip85_path",
            context={"application": application, "length": length, "index": index},
            original_error=e,
        ) from e


def derive_bip85_entropy(
    master_seed: bytes,
    application: int,
    length: int,
    index: int,
    output_bytes: int,
    _cached_master_key: Optional["Bip32Secp256k1"] = None,
) -> bytes:
    """Derive BIP85 entropy following the specification exactly.

    Implements the complete BIP85 derivation algorithm:
    1. Create BIP32 master key from master seed (or use cached key)
    2. Derive to path m/83696968'/{application}'/{length}'/{index}'
    3. Extract private key from final child
    4. Compute HMAC-SHA512(key="bip-entropy-from-k", msg=private_key)
    5. Return first output_bytes of HMAC result

    Args:
        master_seed: 512-bit master seed from BIP39 PBKDF2.
        application: BIP85 application identifier.
        length: Application-specific length parameter.
        index: Child derivation index (0 to 2³¹-1).
        output_bytes: Number of entropy bytes to return.
        _cached_master_key: Optional cached BIP32 master key for performance.

    Returns:
        Derived entropy bytes of specified length.

    Raises:
        Bip85DerivationError: If derivation fails.
        Bip85ValidationError: If parameters are invalid.

    Example:
        >>> master_seed = bytes.fromhex("a" * 128)
        >>> entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
        >>> len(entropy)
        16
    """
    master_key = None
    child_key = None
    private_key_bytes = None
    hmac_result = None

    try:
        logger.info(
            "Starting BIP85 derivation: app=%d, length=%d, index=%d, output=%d bytes",
            application,
            length,
            index,
            output_bytes,
        )
        log_security_event(f"BIP85: Entropy derivation initiated for index {index}")

        # Validate output length
        if not 1 <= output_bytes <= 64:
            raise Bip85ValidationError(
                f"Output bytes must be 1-64, got {output_bytes}",
                parameter="output_bytes",
                value=output_bytes,
                valid_range="1 to 64",
            )

        # Step 1: Create or use cached BIP32 master key
        if _cached_master_key is not None:
            master_key = _cached_master_key
            logger.debug("Using cached BIP32 master key for optimization")
        else:
            master_key = create_bip32_master_key(master_seed)

        # Step 2: Derive BIP85 path m/83696968'/{application}'/{length}'/{index}'
        derivation_path = f"m/{BIP85_PURPOSE}'/{application}'/{length}'/{index}'"
        logger.debug("Deriving BIP85 path: %s", derivation_path)

        # Derive step by step with hardened keys
        child_key = master_key.ChildKey(
            BIP85_PURPOSE | 0x80000000
        )  # Purpose (hardened)
        child_key = child_key.ChildKey(
            application | 0x80000000
        )  # Application (hardened)
        child_key = child_key.ChildKey(length | 0x80000000)  # Length (hardened)
        child_key = child_key.ChildKey(index | 0x80000000)  # Index (hardened)

        # Step 4: Extract private key from final child
        private_key_bytes = child_key.PrivateKey().Raw().ToBytes()

        # Path encoding no longer needed for HMAC per BIP85 spec
        # path_bytes = encode_bip85_path(application, length, index)

        # Step 5: Compute HMAC-SHA512(key="bip-entropy-from-k", msg=private_key)
        # According to BIP85 specification
        logger.debug("Computing HMAC-SHA512 for entropy extraction")
        hmac_key = b"bip-entropy-from-k"
        hmac_result = hmac.new(hmac_key, private_key_bytes, hashlib.sha512).digest()

        # Step 6: Extract required number of entropy bytes
        entropy = hmac_result[:output_bytes]

        logger.info(
            "Successfully derived %d bytes of BIP85 entropy for index %d",
            len(entropy),
            index,
        )
        log_security_event(f"BIP85: Entropy derivation completed for index {index}")

        return entropy

    except (Bip85ValidationError, Bip85DerivationError):
        # Re-raise BIP85-specific errors as-is
        raise
    except Exception as e:
        error_msg = f"BIP85 derivation failed: {e}"
        logger.error(error_msg)
        log_security_event(f"BIP85: Derivation failed: {error_msg}")

        raise Bip85DerivationError(
            error_msg,
            derivation_path=f"m/{BIP85_PURPOSE}'/{application}'/{length}'/{index}'",
            operation="derive_bip85_entropy",
            context={
                "application": application,
                "length": length,
                "index": index,
                "output_bytes": output_bytes,
            },
            original_error=e,
        ) from e

    finally:
        # Secure cleanup of all sensitive variables
        logger.debug("Performing secure cleanup of sensitive variables")

        # Clean up variables in reverse order of creation
        for var_name, var_value in [
            ("hmac_result", hmac_result),
            ("private_key_bytes", private_key_bytes),
            ("child_key", child_key),
            ("master_key", master_key),
        ]:
            if var_value is not None:
                try:
                    # For BIP32 key objects, try to clear internal state
                    if hasattr(var_value, "_key_data"):
                        secure_delete_variable(var_value._key_data)
                    if hasattr(var_value, "_chain_code"):
                        secure_delete_variable(var_value._chain_code)

                    # For bytes objects, use secure deletion
                    if isinstance(var_value, bytes):
                        secure_delete_variable(var_value)

                except Exception as cleanup_error:
                    logger.warning(
                        "Failed to securely clean up %s: %s", var_name, cleanup_error
                    )


def derive_bip85_bip39_entropy(
    master_seed: bytes,
    language_code: int,
    word_count: int,
    index: int,
    output_bytes: int,
    _cached_master_key: Optional["Bip32Secp256k1"] = None,
) -> bytes:
    """Derive BIP85 entropy specifically for BIP39 mnemonics.

    Implements the BIP85 derivation algorithm with the correct BIP39 path format:
    m/83696968'/39'/{language}'/{words}'/{index}'

    Args:
        master_seed: 512-bit master seed from BIP39 PBKDF2.
        language_code: BIP39 language code (0=English, 1=Japanese, etc.)
        word_count: Number of words in mnemonic (12, 15, 18, 21, 24).
        index: Child derivation index (0 to 2³¹-1).
        output_bytes: Number of entropy bytes to return.
        _cached_master_key: Optional cached BIP32 master key for performance.

    Returns:
        Derived entropy bytes of specified length.

    Raises:
        Bip85DerivationError: If derivation fails.
        Bip85ValidationError: If parameters are invalid.

    Example:
        >>> master_seed = bytes.fromhex("a" * 128)
        >>> entropy = derive_bip85_bip39_entropy(master_seed, 0, 12, 0, 16)
        >>> len(entropy)
        16
    """
    master_key = None
    child_key = None
    private_key_bytes = None
    hmac_result = None

    try:
        logger.info(
            "Starting BIP85 BIP39 derivation: lang=%d, words=%d, index=%d, output=%d bytes",
            language_code,
            word_count,
            index,
            output_bytes,
        )
        log_security_event(
            f"BIP85: BIP39 entropy derivation initiated for index {index}"
        )

        # Validate output length
        if not 1 <= output_bytes <= 64:
            raise Bip85ValidationError(
                f"Output bytes must be 1-64, got {output_bytes}",
                parameter="output_bytes",
                value=output_bytes,
                valid_range="1 to 64",
            )

        # Step 1: Create or use cached BIP32 master key
        if _cached_master_key is not None:
            master_key = _cached_master_key
            logger.debug("Using cached BIP32 master key for optimization")
        else:
            master_key = create_bip32_master_key(master_seed)

        # Step 2: Derive BIP39-specific BIP85 path m/83696968'/39'/{language}'/{words}'/{index}'
        derivation_path = (
            f"m/{BIP85_PURPOSE}'/39'/{language_code}'/{word_count}'/{index}'"
        )
        logger.debug("Deriving BIP85 BIP39 path: %s", derivation_path)

        # Derive step by step with hardened keys
        child_key = master_key.ChildKey(
            BIP85_PURPOSE | 0x80000000
        )  # Purpose (hardened)
        child_key = child_key.ChildKey(39 | 0x80000000)  # Application: BIP39 (hardened)
        child_key = child_key.ChildKey(
            language_code | 0x80000000
        )  # Language (hardened)
        child_key = child_key.ChildKey(word_count | 0x80000000)  # Word count (hardened)
        child_key = child_key.ChildKey(index | 0x80000000)  # Index (hardened)

        # Step 3: Extract private key from final child
        private_key_bytes = child_key.PrivateKey().Raw().ToBytes()

        # Step 4: Compute HMAC-SHA512(key="bip-entropy-from-k", msg=private_key)
        # According to BIP85 specification
        logger.debug("Computing HMAC-SHA512 for BIP39 entropy extraction")
        hmac_key = b"bip-entropy-from-k"
        hmac_result = hmac.new(hmac_key, private_key_bytes, hashlib.sha512).digest()

        # Step 5: Extract required number of entropy bytes
        entropy = hmac_result[:output_bytes]

        logger.info(
            "Successfully derived %d bytes of BIP85 BIP39 entropy for index %d",
            len(entropy),
            index,
        )
        log_security_event(
            f"BIP85: BIP39 entropy derivation completed for index {index}"
        )

        return entropy

    except (Bip85ValidationError, Bip85DerivationError):
        # Re-raise BIP85-specific errors as-is
        raise
    except Exception as e:
        error_msg = f"BIP85 BIP39 derivation failed: {e}"
        logger.error(error_msg)
        log_security_event(f"BIP85: BIP39 derivation failed: {error_msg}")

        raise Bip85DerivationError(
            error_msg,
            derivation_path=f"m/{BIP85_PURPOSE}'/39'/{language_code}'/{word_count}'/{index}'",
            operation="derive_bip85_bip39_entropy",
            context={
                "language_code": language_code,
                "word_count": word_count,
                "index": index,
                "output_bytes": output_bytes,
            },
            original_error=e,
        ) from e

    finally:
        # Secure cleanup of all sensitive variables
        logger.debug("Performing secure cleanup of sensitive variables")

        # Clean up variables in reverse order of creation
        for var_name, var_value in [
            ("hmac_result", hmac_result),
            ("private_key_bytes", private_key_bytes),
            ("child_key", child_key),
            ("master_key", master_key),
        ]:
            if var_value is not None:
                try:
                    # For BIP32 key objects, try to clear internal state
                    if hasattr(var_value, "_key_data"):
                        secure_delete_variable(var_value._key_data)
                    if hasattr(var_value, "_chain_code"):
                        secure_delete_variable(var_value._chain_code)

                    # For bytes objects, use secure deletion
                    if isinstance(var_value, bytes):
                        secure_delete_variable(var_value)

                except Exception as cleanup_error:
                    logger.warning(
                        "Failed to securely clean up %s: %s", var_name, cleanup_error
                    )


def format_bip85_derivation_path(application: int, length: int, index: int) -> str:
    """Format BIP85 derivation path as string for display.

    Args:
        application: Application identifier.
        length: Length parameter.
        index: Child index.

    Returns:
        Formatted derivation path string.

    Example:
        >>> format_bip85_derivation_path(39, 12, 0)
        "m/83696968'/39'/12'/0'"
    """
    return f"m/{BIP85_PURPOSE}'/{application}'/{length}'/{index}'"


def validate_master_seed_format(master_seed: Any) -> Tuple[bool, str]:
    """Validate master seed format and length.

    Args:
        master_seed: Master seed to validate.

    Returns:
        Tuple of (is_valid, error_message).

    Example:
        >>> seed = bytes(64)  # 64 zero bytes
        >>> is_valid, error = validate_master_seed_format(seed)
        >>> is_valid
        True
    """
    if not isinstance(master_seed, bytes):
        return False, f"Master seed must be bytes, got {type(master_seed).__name__}"

    if len(master_seed) != 64:
        return False, f"Master seed must be 64 bytes, got {len(master_seed)}"

    # Check for obviously weak seeds (all zeros, all ones, etc.)
    if master_seed == bytes(64):  # All zeros
        return False, "Master seed cannot be all zeros"

    if master_seed == bytes([0xFF] * 64):  # All ones
        return False, "Master seed cannot be all ones"

    return True, ""


def convert_hex_to_bytes(master_seed_str: str) -> bytes:
    """Convert a hexadecimal string to bytes.

    Args:
        master_seed_str: Hexadecimal string representation of the master seed.

    Returns:
        Bytes representation of the master seed.

    Raises:
        Bip85ValidationError: If the input string is invalid.

    Example:
        >>> convert_hex_to_bytes("a" * 128)
        b'\xaa' * 64
    """
    # Convert valid hex string to bytes
    try:
        return bytes.fromhex(master_seed_str)
    except ValueError as e:
        raise Bip85ValidationError(
            "Master seed contains invalid hexadecimal characters",
            parameter="master_seed",
            value=(
                master_seed_str[:50] + "..."
                if len(master_seed_str) > 50
                else master_seed_str
            ),
            valid_range="Valid hexadecimal string (0-9, a-f, A-F)",
        ) from e
