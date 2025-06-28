"""BIP85 optimized applications with caching.

High-performance BIP85 derivation with intelligent caching and optimization.
Provides the same interface as the standard applications but with better
performance for batch operations and repeated derivations.
"""

import string
from typing import (
    Any,
    Dict,
    List,
)

from sseed.languages import (
    get_supported_language_codes,
    validate_language_code,
)

from ..bip39 import entropy_to_mnemonic
from ..logging_config import (
    get_logger,
    log_security_event,
)
from .cache import (
    OptimizedBip32KeyManager,
    get_global_cache,
)
from .core import derive_bip85_entropy
from .exceptions import (
    Bip85ApplicationError,
    Bip85ValidationError,
)
from .paths import (
    calculate_entropy_bytes_needed,
    validate_bip85_parameters,
)

logger = get_logger(__name__)


class OptimizedBip85Applications:
    """Optimized BIP85 applications with caching and batch processing support."""

    def __init__(self, enable_caching: bool = True):
        """Initialize optimized BIP85 applications.

        Args:
            enable_caching: Enable performance caching (default: True)
        """
        self._enable_caching = enable_caching
        self._cache = get_global_cache() if enable_caching else None
        self._key_manager = (
            OptimizedBip32KeyManager(self._cache) if enable_caching else None
        )

        logger.debug(
            "Initialized optimized BIP85 applications (caching: %s)", enable_caching
        )

    def derive_bip39_mnemonic(
        self, master_seed: bytes, word_count: int, index: int = 0, language: str = "en"
    ) -> str:
        """Generate BIP39 mnemonic with optimization."""
        try:
            logger.debug(
                "Optimized BIP39 generation: %d words, index %d, language %s",
                word_count,
                index,
                language,
            )
            log_security_event(
                f"BIP85: Optimized BIP39 generation initiated (index {index})"
            )

            # Fast path validation with caching
            if self._cache:
                cached_valid = self._cache.get_validation_result(39, word_count, index)
                if cached_valid is None:
                    validate_bip85_parameters(39, word_count, index, strict=True)
                    self._cache.cache_validation_result(39, word_count, index, True)
            else:
                validate_bip85_parameters(39, word_count, index, strict=True)

            # Language validation (typically fast, minimal caching benefit)
            try:
                _lang_info = validate_language_code(language)
            except Exception:
                available = ", ".join(get_supported_language_codes())
                raise Bip85ValidationError(
                    f"Invalid language code: {language}",
                    parameter="language",
                    value=language,
                    valid_range=f"One of: {available}",
                )

            # Optimized entropy bytes calculation with caching
            if self._cache:
                entropy_bytes = self._cache.get_entropy_bytes_needed(39, word_count)
                if entropy_bytes is None:
                    entropy_bytes = calculate_entropy_bytes_needed(39, word_count)
                    self._cache.cache_entropy_bytes_needed(
                        39, word_count, entropy_bytes
                    )
            else:
                entropy_bytes = calculate_entropy_bytes_needed(39, word_count)

            # Optimized entropy derivation (uses cached master key if available)
            if self._key_manager:
                master_key = self._key_manager.get_master_key(master_seed)
                entropy = derive_bip85_entropy(
                    master_seed=master_seed,
                    application=39,
                    length=word_count,
                    index=index,
                    output_bytes=entropy_bytes,
                    _cached_master_key=master_key,  # Pass cached key if available
                )
            else:
                entropy = derive_bip85_entropy(
                    master_seed=master_seed,
                    application=39,
                    length=word_count,
                    index=index,
                    output_bytes=entropy_bytes,
                )

            # Convert entropy to mnemonic
            mnemonic = entropy_to_mnemonic(entropy, language)

            logger.debug(
                "Optimized BIP39 generation completed: %d words in %s",
                len(mnemonic.split()),
                language,
            )
            log_security_event(
                f"BIP85: Optimized BIP39 generation completed (index {index})"
            )

            return mnemonic

        except (Bip85ValidationError, Bip85ApplicationError):
            raise
        except Exception as e:
            error_msg = f"Optimized BIP39 generation failed: {e}"
            logger.error(error_msg)
            log_security_event(f"BIP85: Optimized BIP39 generation failed: {error_msg}")

            raise Bip85ApplicationError(
                error_msg,
                application="BIP39",
                entropy_length=entropy_bytes if "entropy_bytes" in locals() else None,
                context={
                    "word_count": word_count,
                    "index": index,
                    "language": language,
                    "optimized": True,
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
        """Generate hex entropy with optimization."""
        try:
            logger.debug(
                "Optimized hex generation: %d bytes, index %d, uppercase %s",
                byte_length,
                index,
                uppercase,
            )
            log_security_event(
                f"BIP85: Optimized hex generation initiated (index {index})"
            )

            # Fast path validation with caching
            if self._cache:
                cached_valid = self._cache.get_validation_result(
                    128, byte_length, index
                )
                if cached_valid is None:
                    validate_bip85_parameters(128, byte_length, index, strict=True)
                    self._cache.cache_validation_result(128, byte_length, index, True)
            else:
                validate_bip85_parameters(128, byte_length, index, strict=True)

            # Optimized entropy derivation
            if self._key_manager:
                master_key = self._key_manager.get_master_key(master_seed)
                entropy = derive_bip85_entropy(
                    master_seed=master_seed,
                    application=128,
                    length=byte_length,
                    index=index,
                    output_bytes=byte_length,
                    _cached_master_key=master_key,
                )
            else:
                entropy = derive_bip85_entropy(
                    master_seed=master_seed,
                    application=128,
                    length=byte_length,
                    index=index,
                    output_bytes=byte_length,
                )

            # Format as hexadecimal
            hex_string = entropy.hex()
            if uppercase:
                hex_string = hex_string.upper()

            logger.debug(
                "Optimized hex generation completed: %d characters", len(hex_string)
            )
            log_security_event(
                f"BIP85: Optimized hex generation completed (index {index})"
            )

            return hex_string

        except (Bip85ValidationError, Bip85ApplicationError):
            raise
        except Exception as e:
            error_msg = f"Optimized hex generation failed: {e}"
            logger.error(error_msg)
            log_security_event(f"BIP85: Optimized hex generation failed: {error_msg}")

            raise Bip85ApplicationError(
                error_msg,
                application="Hex",
                entropy_length=byte_length,
                context={
                    "byte_length": byte_length,
                    "index": index,
                    "uppercase": uppercase,
                    "optimized": True,
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
        """Generate password with optimization."""
        try:
            logger.debug(
                "Optimized password generation: %d chars, index %d, charset %s",
                length,
                index,
                character_set,
            )
            log_security_event(
                f"BIP85: Optimized password generation initiated (index {index})"
            )

            # Fast path validation with caching
            if self._cache:
                cached_valid = self._cache.get_validation_result(9999, length, index)
                if cached_valid is None:
                    validate_bip85_parameters(9999, length, index, strict=True)
                    self._cache.cache_validation_result(9999, length, index, True)
            else:
                validate_bip85_parameters(9999, length, index, strict=True)

            # Character set validation
            valid_charsets = ["base64", "base85", "alphanumeric", "ascii"]
            if character_set not in valid_charsets:
                raise Bip85ValidationError(
                    f"Invalid character set: {character_set}",
                    parameter="character_set",
                    value=character_set,
                    valid_range=f"One of: {', '.join(valid_charsets)}",
                )

            # Calculate entropy bytes needed
            entropy_bytes = min(length, 64)

            # Optimized entropy derivation
            if self._key_manager:
                master_key = self._key_manager.get_master_key(master_seed)
                entropy = derive_bip85_entropy(
                    master_seed=master_seed,
                    application=9999,
                    length=length,
                    index=index,
                    output_bytes=entropy_bytes,
                    _cached_master_key=master_key,
                )
            else:
                entropy = derive_bip85_entropy(
                    master_seed=master_seed,
                    application=9999,
                    length=length,
                    index=index,
                    output_bytes=entropy_bytes,
                )

            # Convert to password
            password = self._entropy_to_password(entropy, length, character_set)

            logger.debug(
                "Optimized password generation completed: %d characters", len(password)
            )
            log_security_event(
                f"BIP85: Optimized password generation completed (index {index})"
            )

            return password

        except (Bip85ValidationError, Bip85ApplicationError):
            raise
        except Exception as e:
            error_msg = f"Optimized password generation failed: {e}"
            logger.error(error_msg)
            log_security_event(
                f"BIP85: Optimized password generation failed: {error_msg}"
            )

            raise Bip85ApplicationError(
                error_msg,
                application="Password",
                entropy_length=entropy_bytes if "entropy_bytes" in locals() else None,
                context={
                    "length": length,
                    "index": index,
                    "character_set": character_set,
                    "optimized": True,
                },
                original_error=e,
            ) from e

    def _entropy_to_password(
        self, entropy: bytes, length: int, character_set: str
    ) -> str:
        """Convert entropy to password using specified character set."""
        # Define character sets
        charsets = {
            "base64": string.ascii_letters + string.digits + "+/",
            "base85": string.ascii_letters + string.digits + "!#$%&()*+-;<=>?@^_`{|}~",
            "alphanumeric": string.ascii_letters + string.digits,
            "ascii": string.printable[:-6],  # Exclude whitespace chars
        }

        charset = charsets[character_set]
        charset_size = len(charset)

        # Generate password by mapping entropy bytes to charset
        password = ""
        for i in range(length):
            # Use modular arithmetic to map entropy to character
            entropy_index = i % len(entropy)
            char_index = entropy[entropy_index] % charset_size
            password += charset[char_index]

            # Mix in position for additional randomness
            if i < len(entropy) - 1:
                next_byte = (entropy[entropy_index] + i + 1) % 256
                entropy = (
                    entropy[:entropy_index]
                    + bytes([next_byte])
                    + entropy[entropy_index + 1 :]
                )

        return password

    def derive_batch_bip39(
        self,
        master_seed: bytes,
        word_count: int,
        indices: List[int],
        language: str = "en",
    ) -> List[str]:
        """Generate multiple BIP39 mnemonics efficiently in batch."""
        try:
            logger.info(
                "Batch BIP39 generation: %d words, %d indices, language %s",
                word_count,
                len(indices),
                language,
            )
            log_security_event(
                f"BIP85: Batch BIP39 generation initiated ({len(indices)} indices)"
            )

            results = []

            # Pre-validate once for the batch
            validate_bip85_parameters(
                39, word_count, 0, strict=True
            )  # Use index 0 for validation

            # Pre-calculate entropy bytes needed
            entropy_bytes = calculate_entropy_bytes_needed(39, word_count)

            # Validate language once
            try:
                _lang_info = validate_language_code(language)
            except Exception:
                available = ", ".join(get_supported_language_codes())
                raise Bip85ValidationError(
                    f"Invalid language code: {language}",
                    parameter="language",
                    value=language,
                    valid_range=f"One of: {available}",
                )

            # Optimize master key creation for batch
            if self._key_manager:
                master_key = self._key_manager.get_master_key(master_seed)
            else:
                master_key = None

            # Generate all mnemonics
            for index in indices:
                if self._key_manager and master_key:
                    entropy = derive_bip85_entropy(
                        master_seed=master_seed,
                        application=39,
                        length=word_count,
                        index=index,
                        output_bytes=entropy_bytes,
                        _cached_master_key=master_key,
                    )
                else:
                    entropy = derive_bip85_entropy(
                        master_seed=master_seed,
                        application=39,
                        length=word_count,
                        index=index,
                        output_bytes=entropy_bytes,
                    )

                mnemonic = entropy_to_mnemonic(entropy, language)
                results.append(mnemonic)

            logger.info("Batch BIP39 generation completed: %d mnemonics", len(results))
            log_security_event(
                f"BIP85: Batch BIP39 generation completed ({len(results)} mnemonics)"
            )

            return results

        except Exception as e:
            error_msg = f"Batch BIP39 generation failed: {e}"
            logger.error(error_msg)
            log_security_event(f"BIP85: Batch BIP39 generation failed: {error_msg}")

            raise Bip85ApplicationError(
                error_msg,
                application="Batch BIP39",
                context={
                    "word_count": word_count,
                    "indices": indices,
                    "language": language,
                    "batch_size": len(indices),
                },
                original_error=e,
            ) from e

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the optimized applications."""
        if self._cache:
            cache_stats = self._cache.get_stats()
            cache_stats["caching_enabled"] = True
        else:
            cache_stats = {"caching_enabled": False}

        return {
            "optimization_enabled": True,
            "cache_stats": cache_stats,
            "features": {
                "master_key_caching": self._key_manager is not None,
                "validation_caching": self._cache is not None,
                "entropy_bytes_caching": self._cache is not None,
                "batch_processing": True,
            },
        }

    def clear_cache(self) -> None:
        """Clear performance cache."""
        if self._cache:
            self._cache.clear()
            logger.info("Cleared optimized BIP85 cache")
