"""BIP-39 mnemonic generation and validation for sseed application.

Implements BIP-39 mnemonic operations using bip_utils.Bip39MnemonicGenerator
as specified in F-2 of the PRD. Provides 24-word mnemonic generation in English.
"""

import hashlib
import unicodedata

from bip_utils import (
    Bip39MnemonicDecoder,
    Bip39MnemonicGenerator,
    Bip39MnemonicValidator,
)

from sseed.entropy import (
    generate_entropy_bytes,
    secure_delete_variable,
)
from sseed.exceptions import (
    EntropyError,
    MnemonicError,
)
from sseed.logging_config import (
    get_logger,
    log_security_event,
)
from sseed.validation import (
    normalize_input,
    validate_mnemonic_words,
)

logger = get_logger(__name__)


def generate_mnemonic() -> str:
    """Generate a 24-word BIP-39 mnemonic using secure entropy.

    Uses bip_utils.Bip39MnemonicGenerator to generate a 24-word mnemonic
    in English as specified in F-2 of the PRD. Uses secure entropy from
    the entropy module.

    Returns:
        24-word BIP-39 mnemonic string.

    Raises:
        MnemonicError: If mnemonic generation fails.
        EntropyError: If entropy generation fails.
    """
    try:
        logger.info("Starting 24-word BIP-39 mnemonic generation")
        log_security_event("BIP-39 mnemonic generation initiated")

        # Generate 32 bytes (256 bits) of secure entropy for 24-word mnemonic
        entropy_bytes = generate_entropy_bytes(32)

        try:
            # Generate mnemonic using bip_utils
            mnemonic = Bip39MnemonicGenerator().FromEntropy(entropy_bytes)

            # Convert to string (bip_utils returns a Bip39Mnemonic object)
            mnemonic_str = str(mnemonic)

            # Validate the generated mnemonic
            words = mnemonic_str.split()
            if len(words) != 24:
                raise MnemonicError(
                    f"Generated mnemonic has {len(words)} words, expected 24",
                    context={"word_count": len(words)},
                )

            # Additional validation using our validator
            validate_mnemonic_words(words)

            # Verify the mnemonic is valid using bip_utils validator (Phase 5 requirement)
            if not Bip39MnemonicValidator().IsValid(mnemonic_str):
                raise MnemonicError(
                    "Generated mnemonic failed BIP-39 checksum validation",
                    context={"mnemonic_length": len(words)},
                )

            logger.info("Successfully generated 24-word BIP-39 mnemonic")
            log_security_event("BIP-39 mnemonic generation completed successfully")

            return mnemonic_str

        finally:
            # Securely delete entropy from memory
            secure_delete_variable(entropy_bytes)

    except EntropyError:
        # Re-raise entropy errors as-is
        raise
    except Exception as e:
        error_msg = f"Failed to generate BIP-39 mnemonic: {e}"
        logger.error(error_msg)
        log_security_event(f"BIP-39 mnemonic generation failed: {error_msg}")
        raise MnemonicError(error_msg, context={"original_error": str(e)}) from e


def validate_mnemonic(mnemonic: str) -> bool:
    """Validate a BIP-39 mnemonic string.

    Validates mnemonic checksum and format using bip_utils validator
    as specified in F-5 of the PRD.

    Args:
        mnemonic: BIP-39 mnemonic string to validate.

    Returns:
        True if mnemonic is valid, False otherwise.

    Raises:
        MnemonicError: If validation encounters an error.
    """
    try:
        # Normalize input
        normalized_mnemonic = normalize_input(mnemonic)

        if not normalized_mnemonic:
            logger.warning("Empty mnemonic provided for validation")
            return False

        # Split into words and validate format
        words = normalized_mnemonic.split()
        validate_mnemonic_words(words)

        # Use bip_utils validator for comprehensive checksum validation (Phase 5 requirement)
        is_valid: bool = bool(Bip39MnemonicValidator().IsValid(normalized_mnemonic))

        if is_valid:
            logger.info("Mnemonic validation successful (%d words)", len(words))
            log_security_event(f"Mnemonic validation: VALID ({len(words)} words)")
        else:
            logger.warning("Mnemonic validation failed (%d words)", len(words))
            log_security_event(f"Mnemonic validation: INVALID ({len(words)} words)")

        return is_valid

    except Exception as e:
        error_msg = f"Error during mnemonic validation: {e}"
        logger.error(error_msg)
        log_security_event(f"Mnemonic validation error: {error_msg}")
        raise MnemonicError(error_msg, context={"original_error": str(e)}) from e


def parse_mnemonic(mnemonic: str) -> list[str]:
    """Parse and normalize a mnemonic string into word list.

    Normalizes the mnemonic input and returns a validated list of words.

    Args:
        mnemonic: BIP-39 mnemonic string to parse.

    Returns:
        List of normalized mnemonic words.

    Raises:
        MnemonicError: If mnemonic parsing or validation fails.
    """
    try:
        # Normalize input
        normalized_mnemonic = normalize_input(mnemonic)

        if not normalized_mnemonic:
            raise MnemonicError(
                "Empty mnemonic provided",
                context={"original_length": len(mnemonic)},
            )

        # Split into words
        words = normalized_mnemonic.split()

        # Validate word list
        validate_mnemonic_words(words)

        logger.debug("Parsed mnemonic into %d words", len(words))

        return words

    except Exception as e:
        error_msg = f"Failed to parse mnemonic: {e}"
        logger.error(error_msg)
        raise MnemonicError(error_msg, context={"original_error": str(e)}) from e


def get_mnemonic_entropy(mnemonic: str) -> bytes:
    """Extract entropy bytes from a valid BIP-39 mnemonic.

    Converts a validated BIP-39 mnemonic back to its original entropy.
    This is useful for SLIP-39 operations that require the raw entropy.

    Args:
        mnemonic: Valid BIP-39 mnemonic string.

    Returns:
        Original entropy bytes.

    Raises:
        MnemonicError: If mnemonic is invalid or entropy extraction fails.
    """
    try:
        # Validate mnemonic first
        if not validate_mnemonic(mnemonic):
            raise MnemonicError(
                "Cannot extract entropy from invalid mnemonic",
                context={"mnemonic_valid": False},
            )

        # Normalize input
        normalized_mnemonic = normalize_input(mnemonic)

        # Extract entropy using bip_utils
        entropy_bytes: bytes = bytes(Bip39MnemonicDecoder().Decode(normalized_mnemonic))

        logger.info("Extracted %d bytes of entropy from mnemonic", len(entropy_bytes))
        log_security_event(f"Entropy extraction: {len(entropy_bytes)} bytes")

        return entropy_bytes

    except Exception as e:
        error_msg = f"Failed to extract entropy from mnemonic: {e}"
        logger.error(error_msg)
        log_security_event(f"Entropy extraction failed: {error_msg}")
        raise MnemonicError(error_msg, context={"original_error": str(e)}) from e


def generate_master_seed(
    mnemonic: str,
    passphrase: str = "",
    iterations: int = 2048,
) -> bytes:
    """Generate master seed from BIP-39 mnemonic using PBKDF2.

    Derives a 512-bit (64-byte) master seed from a BIP-39 mnemonic and optional
    passphrase using PBKDF2-HMAC-SHA512 as specified in BIP-39.

    This master seed can be used to derive cryptographic keys according to
    BIP-32 hierarchical deterministic (HD) wallet specification.

    Args:
        mnemonic: Valid BIP-39 mnemonic string.
        passphrase: Optional passphrase for additional security (default: "").
        iterations: PBKDF2 iteration count (default: 2048 per BIP-39).

    Returns:
        512-bit (64-byte) master seed.

    Raises:
        MnemonicError: If mnemonic is invalid or seed generation fails.

    Example:
        >>> mnemonic = generate_mnemonic()
        >>> seed = generate_master_seed(mnemonic)
        >>> len(seed)
        64
        >>> seed_with_passphrase = generate_master_seed(mnemonic, "my_passphrase")
    """
    try:
        logger.info("Starting master seed generation from BIP-39 mnemonic")
        log_security_event("Master seed generation initiated")

        # Validate mnemonic first
        if not validate_mnemonic(mnemonic):
            raise MnemonicError(
                "Cannot generate master seed from invalid mnemonic",
                context={"mnemonic_valid": False},
            )

        # Normalize mnemonic and passphrase according to BIP-39
        normalized_mnemonic = unicodedata.normalize("NFKD", mnemonic.strip())
        normalized_passphrase = unicodedata.normalize("NFKD", passphrase)

        # BIP-39 specifies: password = mnemonic, salt = "mnemonic" + passphrase
        password = normalized_mnemonic.encode("utf-8")
        salt = ("mnemonic" + normalized_passphrase).encode("utf-8")

        try:
            # Generate 512-bit (64-byte) seed using PBKDF2-HMAC-SHA512
            master_seed = hashlib.pbkdf2_hmac(
                "sha512",
                password,
                salt,
                iterations,
                dklen=64,  # 512 bits = 64 bytes
            )

            logger.info("Successfully generated 512-bit master seed")
            log_security_event("Master seed generation completed successfully")

            return master_seed

        finally:
            # Securely delete sensitive variables from memory
            secure_delete_variable(password)
            secure_delete_variable(salt)

    except Exception as e:
        error_msg = f"Failed to generate master seed: {e}"
        logger.error(error_msg)
        log_security_event(f"Master seed generation failed: {error_msg}")
        raise MnemonicError(error_msg, context={"original_error": str(e)}) from e


def mnemonic_to_hex_seed(
    mnemonic: str,
    passphrase: str = "",
) -> str:
    """Convert BIP-39 mnemonic to hexadecimal master seed string.

    Convenience function that generates the master seed and returns it as
    a hexadecimal string for easy display and storage.

    Args:
        mnemonic: Valid BIP-39 mnemonic string.
        passphrase: Optional passphrase for additional security (default: "").

    Returns:
        128-character hexadecimal string representing the 512-bit master seed.

    Raises:
        MnemonicError: If mnemonic is invalid or seed generation fails.

    Example:
        >>> mnemonic = generate_mnemonic()
        >>> hex_seed = mnemonic_to_hex_seed(mnemonic)
        >>> len(hex_seed)
        128
    """
    master_seed = None
    try:
        master_seed = generate_master_seed(mnemonic, passphrase)
        hex_seed = master_seed.hex()

        logger.debug("Converted master seed to hexadecimal format")

        return hex_seed

    finally:
        # Securely delete master seed from memory
        if master_seed is not None:
            secure_delete_variable(master_seed)
