"""BIP-39 mnemonic operations with multi-language support.

This module provides comprehensive BIP-39 mnemonic generation, validation,
and processing capabilities with support for all 9 BIP-39 languages.
Enhanced for multi-language support while maintaining 100% backward compatibility.
"""

import hashlib
import logging
import unicodedata
from typing import (
    List,
    Optional,
)

from bip_utils import (
    Bip39Languages,
    Bip39MnemonicDecoder,
    Bip39MnemonicGenerator,
    Bip39MnemonicValidator,
)

from sseed.entropy import secure_delete_variable
from sseed.exceptions import (
    CryptoError,
    MnemonicError,
)
from sseed.languages import (
    detect_mnemonic_language,
    get_language_by_bip_enum,
    validate_language_code,
)
from sseed.logging_config import log_security_event

logger = logging.getLogger(__name__)


def _normalize_mnemonic(mnemonic: str) -> str:
    """Normalize mnemonic string for processing.

    Args:
        mnemonic: Raw mnemonic string.

    Returns:
        Normalized mnemonic string.
    """
    if not isinstance(mnemonic, str):
        raise MnemonicError(f"Mnemonic must be a string, got {type(mnemonic).__name__}")

    # Apply Unicode normalization and basic cleaning
    normalized = unicodedata.normalize("NFKD", mnemonic.strip().lower())

    if not normalized:
        raise MnemonicError("Mnemonic cannot be empty")

    return normalized


def generate_mnemonic(language: Optional[Bip39Languages] = None) -> str:
    """Generate a BIP-39 mnemonic with optional language support.

    Args:
        language: Optional BIP-39 language. Defaults to English for backward compatibility.

    Returns:
        Generated BIP-39 mnemonic string (24 words).

    Raises:
        CryptoError: If mnemonic generation fails.

    Example:
        >>> # English (default)
        >>> mnemonic_en = generate_mnemonic()
        >>> len(mnemonic_en.split())
        24

        >>> # Spanish
        >>> from bip_utils import Bip39Languages
        >>> mnemonic_es = generate_mnemonic(Bip39Languages.SPANISH)
        >>> len(mnemonic_es.split())
        24
    """
    try:
        # Use English as default for backward compatibility
        if language is None:
            language = Bip39Languages.ENGLISH

        logger.debug("Generating mnemonic in language: %s", language)

        # Create language-specific generator
        generator = Bip39MnemonicGenerator(language)

        # Generate with high entropy (256 bits = 24 words)
        mnemonic = str(generator.FromWordsNumber(24))

        if not mnemonic:
            raise CryptoError("Generated mnemonic is empty")

        # Get language info for logging
        try:
            lang_info = get_language_by_bip_enum(language)
            logger.info("Successfully generated %s mnemonic", lang_info.name)
        except Exception as lang_error:  # pylint: disable=broad-exception-caught
            logger.debug("Could not get language info: %s", lang_error)
            logger.info("Successfully generated mnemonic")

        return mnemonic

    except Exception as error:
        logger.error("Failed to generate mnemonic: %s", error)
        raise CryptoError(f"Failed to generate mnemonic: {error}") from error


def validate_mnemonic(mnemonic: str, language: Optional[Bip39Languages] = None) -> bool:
    """Validate a BIP-39 mnemonic with automatic or explicit language detection.

    Performs comprehensive validation including:
    - Format and structure validation
    - Language detection (if not specified)
    - BIP-39 checksum validation
    - Word list validation

    Args:
        mnemonic: BIP-39 mnemonic string to validate.
        language: Optional explicit language. If None, language will be auto-detected.

    Returns:
        True if mnemonic is valid, False otherwise.

    Example:
        >>> # Auto-detection (new feature)
        >>> validate_mnemonic("abandon ability able about above absent absorb abstract")
        True

        >>> # Explicit language validation
        >>> from bip_utils import Bip39Languages
        >>> validate_mnemonic("abandon ability able about above absent", Bip39Languages.ENGLISH)
        True
    """
    try:
        # Normalize input
        normalized_mnemonic = _normalize_mnemonic(mnemonic)

        # Language detection and validation
        lang_info = None
        if language is None:
            # Attempt automatic language detection
            detected_lang_info = detect_mnemonic_language(normalized_mnemonic)
            if detected_lang_info:
                language = detected_lang_info.bip_enum
                lang_info = detected_lang_info
                logger.debug("Auto-detected language: %s", detected_lang_info.name)
            else:
                logger.warning("Language detection failed, falling back to English")
                language = Bip39Languages.ENGLISH
        else:
            # Get language info for explicit language
            try:
                lang_info = get_language_by_bip_enum(language)
                logger.debug("Using explicit language: %s", lang_info.name)
            except Exception as lang_error:  # pylint: disable=broad-exception-caught
                logger.debug("Could not get language info: %s", lang_error)

        # Validate using BIP-39 library
        validator = Bip39MnemonicValidator(language)
        is_valid = bool(validator.IsValid(normalized_mnemonic))

        if is_valid:
            lang_name = lang_info.name if lang_info else str(language)
            logger.debug("Mnemonic validated successfully as %s", lang_name)
        else:
            lang_name = lang_info.name if lang_info else str(language)
            logger.debug("Mnemonic validation failed for %s", lang_name)

        return is_valid

    except Exception as error:
        logger.debug("Mnemonic validation error: %s", error)
        return False


def parse_mnemonic(
    mnemonic: str, language: Optional[Bip39Languages] = None
) -> List[str]:
    """Parse and validate a BIP-39 mnemonic into individual words.

    Args:
        mnemonic: BIP-39 mnemonic string to parse.
        language: Optional language for validation. Auto-detected if not provided.

    Returns:
        List of validated mnemonic words.

    Raises:
        MnemonicError: If mnemonic is invalid or cannot be parsed.

    Example:
        >>> words = parse_mnemonic("abandon ability able about above absent")
        >>> len(words)
        6
        >>> words[0]
        'abandon'
    """
    try:
        # Normalize and validate input
        normalized_mnemonic = _normalize_mnemonic(mnemonic)

        # Language detection for validation
        if language is None:
            detected_lang_info = detect_mnemonic_language(normalized_mnemonic)
            if detected_lang_info:
                language = detected_lang_info.bip_enum
                logger.debug(
                    "Auto-detected language for parsing: %s",
                    detected_lang_info.name,
                )
            else:
                logger.warning("Could not detect language, assuming English")
                language = Bip39Languages.ENGLISH

        # Validate mnemonic structure
        if not validate_mnemonic(normalized_mnemonic, language):
            raise MnemonicError(
                "Invalid mnemonic structure or checksum",
                context={"mnemonic_length": len(normalized_mnemonic.split())},
            )

        # Parse words
        words = normalized_mnemonic.split()
        logger.debug("Successfully parsed mnemonic into %d words", len(words))

        return words

    except MnemonicError:
        raise
    except Exception as error:
        logger.error("Failed to parse mnemonic: %s", error)
        raise MnemonicError(f"Failed to parse mnemonic: {error}") from error


def get_mnemonic_entropy(
    mnemonic: str, language: Optional[Bip39Languages] = None
) -> bytes:
    """Extract entropy from a BIP-39 mnemonic with multi-language support.

    Args:
        mnemonic: Valid BIP-39 mnemonic string.
        language: Optional language specification. Auto-detected if not provided.

    Returns:
        Raw entropy bytes from the mnemonic.

    Raises:
        MnemonicError: If mnemonic is invalid or entropy extraction fails.

    Example:
        >>> entropy = get_mnemonic_entropy("abandon ability able about above absent")
        >>> len(entropy)  # Length depends on mnemonic word count
        32  # 256 bits for 24-word mnemonic
        >>> isinstance(entropy, bytes)
        True
    """
    try:
        # Normalize input
        normalized_mnemonic = _normalize_mnemonic(mnemonic)

        # Language detection if not provided
        if language is None:
            detected_lang_info = detect_mnemonic_language(normalized_mnemonic)
            if detected_lang_info:
                language = detected_lang_info.bip_enum
                logger.debug(
                    "Auto-detected language for entropy extraction: %s",
                    detected_lang_info.name,
                )
            else:
                logger.warning("Could not detect language, assuming English")
                language = Bip39Languages.ENGLISH

        # Validate before entropy extraction
        if not validate_mnemonic(normalized_mnemonic, language):
            raise MnemonicError(
                "Cannot extract entropy from invalid mnemonic",
                context={"language": str(language)},
            )

        # Extract entropy using BIP-39 decoder
        decoder = Bip39MnemonicDecoder(language)
        entropy_bytes = decoder.Decode(normalized_mnemonic)

        # Cast to bytes since we know the decoder returns bytes but MyPy sees Any
        entropy: bytes = bytes(entropy_bytes)

        logger.debug("Successfully extracted %d bytes of entropy", len(entropy))
        return entropy

    except MnemonicError:
        raise
    except Exception as error:
        logger.error("Failed to extract entropy: %s", error)
        raise MnemonicError(f"Failed to extract entropy: {error}") from error


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


def entropy_to_mnemonic(entropy: bytes, language: str = "en") -> str:
    """Convert raw entropy bytes to BIP39 mnemonic.
    
    Args:
        entropy: Raw entropy bytes (16, 20, 24, 28, or 32 bytes).
        language: Language code (en, es, fr, it, pt, cs, zh-cn, zh-tw, ko).
        
    Returns:
        BIP39 mnemonic string in the specified language.
        
    Raises:
        MnemonicError: If entropy is invalid or conversion fails.
        
    Example:
        >>> entropy = bytes.fromhex("a" * 32)  # 16 bytes
        >>> mnemonic = entropy_to_mnemonic(entropy, "en")
        >>> len(mnemonic.split())
        12
    """
    try:
        # Validate entropy length
        if len(entropy) not in [16, 20, 24, 28, 32]:
            raise MnemonicError(
                f"Invalid entropy length: {len(entropy)} bytes. "
                "Must be 16, 20, 24, 28, or 32 bytes."
            )
        
        # Convert language code to BIP39Languages enum
        lang_info = validate_language_code(language)
        bip_language = lang_info.bip_enum
        
        # Create language-specific generator
        generator = Bip39MnemonicGenerator(bip_language)
        
        # Generate mnemonic from entropy
        mnemonic = str(generator.FromEntropy(entropy))
        
        if not mnemonic:
            raise MnemonicError("Generated mnemonic is empty")
        
        logger.debug(
            "Successfully converted %d bytes of entropy to %s mnemonic",
            len(entropy), lang_info.name
        )
        
        return mnemonic
        
    except Exception as error:
        logger.error("Failed to convert entropy to mnemonic: %s", error)
        if isinstance(error, MnemonicError):
            raise
        raise MnemonicError(f"Failed to convert entropy to mnemonic: {error}") from error
