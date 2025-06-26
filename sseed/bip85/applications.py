"""BIP85 application-specific formatters.

Converts BIP85-derived entropy into various application formats including:
- BIP39 mnemonics (all 9 supported languages)
- Hexadecimal strings
- Passwords with various character sets

Leverages existing SSeed infrastructure for multi-language support
and follows SSeed patterns for error handling and validation.
"""

import string

from sseed.bip39 import entropy_to_mnemonic
from sseed.languages import (
    get_supported_language_codes,
    validate_language_code,
)
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

from .core import (
    derive_bip85_bip39_entropy,
    derive_bip85_entropy,
)
from .exceptions import (
    Bip85ApplicationError,
    Bip85ValidationError,
)
from .paths import (
    calculate_entropy_bytes_needed,
    get_application_name,
    validate_bip85_parameters,
)

logger = get_logger(__name__)

# BIP85 language codes according to the specification
BIP85_LANGUAGE_CODES = {
    "en": 0,  # English
    "ja": 1,  # Japanese (SSeed doesn't support this yet)
    "ko": 2,  # Korean
    "es": 3,  # Spanish
    "zh-cn": 4,  # Chinese (Simplified) - SSeed uses zh-cn
    "zh-Hans": 4,  # Chinese (Simplified) - Alternative code
    "zh-tw": 5,  # Chinese (Traditional) - SSeed uses zh-tw
    "zh-Hant": 5,  # Chinese (Traditional) - Alternative code
    "fr": 6,  # French
    "it": 7,  # Italian
    "cs": 8,  # Czech
    "pt": 9,  # Portuguese
}


class Bip85Applications:
    """Convert BIP85 entropy to various application formats."""

    def __init__(self) -> None:
        """Initialize BIP85 applications formatter."""
        logger.debug("Initializing BIP85 applications formatter")

    def derive_bip39_mnemonic(
        self, master_seed: bytes, word_count: int, index: int = 0, language: str = "en"
    ) -> str:
        """Generate BIP39 mnemonic from BIP85 entropy."""
        try:
            logger.info(
                "Generating BIP39 mnemonic: %d words, index %d, language %s",
                word_count,
                index,
                language,
            )
            log_security_event(
                f"BIP85: BIP39 mnemonic generation initiated (index {index})"
            )

            # Validate language
            try:
                lang_info = validate_language_code(language)
            except Exception:
                available = ", ".join(get_supported_language_codes())
                raise Bip85ValidationError(
                    f"Invalid language code: {language}",
                    parameter="language",
                    value=language,
                    valid_range=f"One of: {available}",
                )

            # Get BIP85 language code
            if language not in BIP85_LANGUAGE_CODES:
                raise Bip85ValidationError(
                    f"Language not supported by BIP85: {language}",
                    parameter="language",
                    value=language,
                    valid_range=f"One of: {', '.join(BIP85_LANGUAGE_CODES.keys())}",
                )

            language_code = BIP85_LANGUAGE_CODES[language]

            # Validate BIP85 parameters
            validate_bip85_parameters(39, word_count, index, strict=True)

            # Calculate required entropy bytes
            entropy_bytes = calculate_entropy_bytes_needed(39, word_count)

            # Derive BIP85 entropy using the correct BIP39 path format
            # m/83696968'/39'/{language}'/{words}'/{index}'
            entropy = derive_bip85_bip39_entropy(
                master_seed=master_seed,
                language_code=language_code,
                word_count=word_count,
                index=index,
                output_bytes=entropy_bytes,
            )

            # Convert entropy to BIP39 mnemonic using existing infrastructure
            mnemonic = entropy_to_mnemonic(entropy, language)

            logger.info(
                "Successfully generated BIP39 mnemonic: %d words in %s",
                len(mnemonic.split()),
                language,
            )
            log_security_event(
                f"BIP85: BIP39 mnemonic generation completed (index {index})"
            )

            return mnemonic

        except (Bip85ValidationError, Bip85ApplicationError):
            # Re-raise BIP85-specific errors as-is
            raise
        except Exception as e:
            error_msg = f"BIP39 mnemonic generation failed: {e}"
            logger.error(error_msg)
            log_security_event(f"BIP85: BIP39 generation failed: {error_msg}")

            raise Bip85ApplicationError(
                error_msg,
                application="BIP39",
                entropy_length=entropy_bytes if "entropy_bytes" in locals() else None,
                context={
                    "word_count": word_count,
                    "index": index,
                    "language": language,
                },
                original_error=e,
            ) from e

    def derive_hex_entropy(
        self,
        master_seed: bytes,
        byte_length: int,
        index: int = 0,
        uppercase: bool = False,
    ) -> str:
        """Generate hexadecimal entropy from BIP85."""
        try:
            logger.info(
                "Generating hex entropy: %d bytes, index %d, uppercase %s",
                byte_length,
                index,
                uppercase,
            )
            log_security_event(
                f"BIP85: Hex entropy generation initiated (index {index})"
            )

            # Validate BIP85 parameters
            validate_bip85_parameters(128, byte_length, index, strict=True)

            # Derive BIP85 entropy
            entropy = derive_bip85_entropy(
                master_seed=master_seed,
                application=128,  # Hex application
                length=byte_length,
                index=index,
                output_bytes=byte_length,
            )

            # Format as hexadecimal
            hex_string = entropy.hex()
            if uppercase:
                hex_string = hex_string.upper()

            logger.info(
                "Successfully generated hex entropy: %d characters", len(hex_string)
            )
            log_security_event(
                f"BIP85: Hex entropy generation completed (index {index})"
            )

            return hex_string

        except (Bip85ValidationError, Bip85ApplicationError):
            # Re-raise BIP85-specific errors as-is
            raise
        except Exception as e:
            error_msg = f"Hex entropy generation failed: {e}"
            logger.error(error_msg)
            log_security_event(f"BIP85: Hex generation failed: {error_msg}")

            raise Bip85ApplicationError(
                error_msg,
                application="Hex",
                entropy_length=byte_length,
                context={
                    "byte_length": byte_length,
                    "index": index,
                    "uppercase": uppercase,
                },
                original_error=e,
            ) from e

    def derive_password(
        self,
        master_seed: bytes,
        length: int,
        index: int = 0,
        character_set: str = "base64",
    ) -> str:
        """Generate password from BIP85 entropy."""
        try:
            logger.info(
                "Generating password: %d chars, index %d, charset %s",
                length,
                index,
                character_set,
            )
            log_security_event(f"BIP85: Password generation initiated (index {index})")

            # Validate BIP85 parameters
            validate_bip85_parameters(9999, length, index, strict=True)

            # Validate character set
            valid_charsets = ["base64", "base85", "alphanumeric", "ascii"]
            if character_set not in valid_charsets:
                raise Bip85ValidationError(
                    f"Invalid character set: {character_set}",
                    parameter="character_set",
                    value=character_set,
                    valid_range=f"One of: {', '.join(valid_charsets)}",
                )

            # Calculate entropy bytes needed (cap at 64 for HMAC-SHA512)
            entropy_bytes = min(length, 64)

            # Derive BIP85 entropy
            entropy = derive_bip85_entropy(
                master_seed=master_seed,
                application=9999,  # Password application (non-standard)
                length=length,
                index=index,
                output_bytes=entropy_bytes,
            )

            # Convert entropy to password using specified character set
            password = self._entropy_to_password(entropy, length, character_set)

            logger.info(
                "Successfully generated password: %d characters using %s charset",
                len(password),
                character_set,
            )
            log_security_event(f"BIP85: Password generation completed (index {index})")

            return password

        except (Bip85ValidationError, Bip85ApplicationError):
            # Re-raise BIP85-specific errors as-is
            raise
        except Exception as e:
            error_msg = f"Password generation failed: {e}"
            logger.error(error_msg)
            log_security_event(f"BIP85: Password generation failed: {error_msg}")

            raise Bip85ApplicationError(
                error_msg,
                application="Password",
                entropy_length=entropy_bytes if "entropy_bytes" in locals() else None,
                context={
                    "length": length,
                    "index": index,
                    "character_set": character_set,
                },
                original_error=e,
            ) from e

    def _entropy_to_password(
        self, entropy: bytes, length: int, character_set: str
    ) -> str:
        """Convert entropy bytes to password using specified character set."""
        try:
            # Define character sets
            charsets = {
                "base64": string.ascii_letters + string.digits + "+/",
                "base85": string.ascii_letters
                + string.digits
                + "!#$%&()*+-;<=>?@^_`{|}~",
                "alphanumeric": string.ascii_letters + string.digits,
                "ascii": string.ascii_letters + string.digits + string.punctuation,
            }

            charset = charsets[character_set]
            charset_size = len(charset)

            # Use entropy to select characters deterministically
            password_chars = []
            entropy_int = int.from_bytes(entropy, byteorder="big")

            for i in range(length):
                # Use modular arithmetic to select character
                char_index = entropy_int % charset_size
                password_chars.append(charset[char_index])

                # Shift entropy for next character
                entropy_int //= charset_size

                # If we run out of entropy, hash current state
                if entropy_int == 0 and i < length - 1:
                    import hashlib

                    new_entropy = hashlib.sha256(
                        entropy + i.to_bytes(4, "big")
                    ).digest()
                    entropy_int = int.from_bytes(new_entropy, byteorder="big")

            return "".join(password_chars)

        except Exception as e:
            raise Bip85ApplicationError(
                f"Character set conversion failed: {e}",
                application="Password",
                context={"character_set": character_set, "target_length": length},
                original_error=e,
            ) from e

    def get_application_info(self, application: int) -> dict:
        """Get information about a BIP85 application."""
        return {
            "application": application,
            "name": get_application_name(application),
            "supported": application in [39, 128, 9999],
            "description": self._get_application_description(application),
        }

    def _get_application_description(self, application: int) -> str:
        """Get description for BIP85 application."""
        descriptions = {
            39: "Generate BIP39 mnemonic phrases in multiple languages",
            128: "Generate raw entropy as hexadecimal strings",
            9999: "Generate passwords with configurable character sets",
            2: "Generate HD wallet seeds (future implementation)",
            32: "Generate extended private keys (future implementation)",
        }

        return descriptions.get(application, f"Unknown application ({application})")

    def list_supported_applications(self) -> list:
        """List all currently supported BIP85 applications."""
        supported_apps = [39, 128, 9999]
        return [self.get_application_info(app) for app in supported_apps]
