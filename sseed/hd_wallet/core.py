"""Core HD wallet functionality.

Implements the fundamental hierarchical deterministic wallet operations
using BIP32 key derivation with secure memory handling.

This module provides the main HDWalletManager class that coordinates
all HD wallet operations while leveraging existing SSeed infrastructure.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
)

from bip_utils import (
    Bip32Secp256k1,
    Bip39MnemonicValidator,
    Bip39SeedGenerator,
)

from sseed.bip85.core import create_bip32_master_key  # Reuse existing infrastructure
from sseed.entropy import secure_delete_variable
from sseed.logging_config import (
    get_logger,
    log_security_event,
)
from sseed.validation import normalize_input

from .derivation import (
    build_derivation_path,
    parse_derivation_path,
    validate_path,
)
from .exceptions import (
    DerivationError,
    HDWalletError,
)

if TYPE_CHECKING:
    from .addresses import AddressInfo
    from .extended_keys import ExtendedKeyInfo

logger = get_logger(__name__)


class HDWalletManager:
    """Core HD wallet manager for address derivation.

    Provides comprehensive hierarchical deterministic wallet functionality
    with secure memory management and performance optimization through caching.

    This class integrates with existing SSeed infrastructure while providing
    new HD wallet capabilities for multiple cryptocurrencies.
    """

    def __init__(self, mnemonic: str, validate: bool = True):
        """Initialize HD wallet from mnemonic.

        Args:
            mnemonic: BIP39 mnemonic phrase.
            validate: Whether to validate mnemonic checksum.

        Raises:
            HDWalletError: If mnemonic is invalid or initialization fails.

        Example:
            >>> manager = HDWalletManager("word1 word2 ... word24")
            >>> addresses = manager.derive_addresses_batch("bitcoin", 5)
        """
        # Store normalized mnemonic
        self._mnemonic = normalize_input(mnemonic)

        # Initialize cached components
        self._master_seed: Optional[bytes] = None
        self._master_key: Optional[Bip32Secp256k1] = None
        self._derived_keys_cache: Dict[str, Bip32Secp256k1] = {}

        # Track initialization status
        self._initialized = False

        # Validate mnemonic if requested
        if validate:
            self._validate_mnemonic()

        self._initialized = True
        logger.debug(
            "HD wallet manager initialized with %d-word mnemonic",
            len(self._mnemonic.split()),
        )
        log_security_event("HD wallet: Manager initialization completed")

    def _validate_mnemonic(self) -> None:
        """Validate mnemonic using BIP39 standards.

        Raises:
            HDWalletError: If mnemonic validation fails.
        """
        try:
            if not Bip39MnemonicValidator().IsValid(self._mnemonic):
                raise HDWalletError(
                    "Invalid BIP39 mnemonic checksum",
                    operation="validate_mnemonic",
                    context={"mnemonic_words": len(self._mnemonic.split())},
                )
            logger.debug("Mnemonic validation successful")
        except Exception as e:
            raise DerivationError(
                f"Mnemonic validation failed: {e}",
                operation="validate_mnemonic",
                context={"mnemonic_words": len(self._mnemonic.split())},
                original_error=e,
            ) from e

    def _get_master_seed(self) -> bytes:
        """Get or create master seed with caching.

        Returns:
            512-bit master seed from BIP39 PBKDF2.

        Raises:
            DerivationError: If master seed generation fails.
        """
        if self._master_seed is None:
            try:
                # Generate 512-bit master seed from mnemonic using BIP39 PBKDF2
                self._master_seed = Bip39SeedGenerator(self._mnemonic).Generate()

                logger.debug("Master seed generated (%d bytes)", len(self._master_seed))
                log_security_event("HD wallet: Master seed generation completed")

            except Exception as e:
                raise DerivationError(
                    f"Master seed generation failed: {e}",
                    operation="generate_master_seed",
                    original_error=e,
                ) from e

        return self._master_seed

    def _get_master_key(self) -> Bip32Secp256k1:
        """Get or create master key with caching.

        Reuses existing create_bip32_master_key() from BIP85 module
        to maintain consistency with existing SSeed infrastructure.

        Returns:
            BIP32 master key for hierarchical derivation.

        Raises:
            DerivationError: If master key creation fails.
        """
        if self._master_key is None:
            try:
                # Get master seed first
                master_seed = self._get_master_seed()

                # Use existing SSeed function for BIP32 master key creation
                self._master_key = create_bip32_master_key(master_seed)

                logger.debug("Master key created using existing SSeed infrastructure")
                log_security_event("HD wallet: Master key derivation completed")

            except Exception as e:
                raise DerivationError(
                    f"Master key creation failed: {e}",
                    operation="create_master_key",
                    original_error=e,
                ) from e

        return self._master_key

    def derive_key_at_path(
        self, derivation_path: str, use_cache: bool = True
    ) -> Bip32Secp256k1:
        """Derive key at specific path with optional caching.

        Args:
            derivation_path: BIP32 derivation path (e.g., "m/44'/0'/0'/0/0").
            use_cache: Whether to use key caching for performance.

        Returns:
            Derived BIP32 key at specified path.

        Raises:
            DerivationError: If key derivation fails.

        Example:
            >>> key = manager.derive_key_at_path("m/84'/0'/0'/0/5")
            >>> address = generate_address_from_key(key, "bitcoin", "native-segwit")
        """
        try:
            # Validate path format
            validate_path(derivation_path)

            # Check cache first if enabled
            if use_cache and derivation_path in self._derived_keys_cache:
                logger.debug("Using cached key for path: %s", derivation_path)
                return self._derived_keys_cache[derivation_path]

            # Get master key
            master_key = self._get_master_key()

            # Parse derivation path into components
            path_components = parse_derivation_path(derivation_path)

            # Derive key step by step
            derived_key = master_key
            for i, component in enumerate(path_components):
                try:
                    derived_key = derived_key.ChildKey(component)
                except Exception as e:
                    raise DerivationError(
                        f"Key derivation failed at component {i} (value: {component})",
                        derivation_path=derivation_path,
                        operation="derive_child_key",
                        context={"component_index": i, "component_value": component},
                        original_error=e,
                    ) from e

            # Cache the derived key if caching is enabled
            if use_cache:
                self._derived_keys_cache[derivation_path] = derived_key

            logger.debug("Key derived at path: %s", derivation_path)
            log_security_event(
                f"HD wallet: Key derivation completed for path {derivation_path}"
            )

            return derived_key

        except (DerivationError, HDWalletError):
            # Re-raise HD wallet specific errors
            raise
        except Exception as e:
            raise DerivationError(
                f"Unexpected error during key derivation: {e}",
                derivation_path=derivation_path,
                operation="derive_key_at_path",
                original_error=e,
            ) from e

    def derive_addresses_batch(
        self,
        coin: str,
        count: int = 1,
        account: int = 0,
        change: int = 0,
        address_type: Optional[str] = None,
        start_index: int = 0,
        custom_path_template: Optional[str] = None,
    ) -> List["AddressInfo"]:
        """Derive multiple addresses efficiently.

        Generates multiple cryptocurrency addresses using batch optimization
        with comprehensive parameter validation.

        Args:
            coin: Cryptocurrency name (bitcoin, ethereum, litecoin).
            count: Number of addresses to generate (1-1000).
            account: Account number for derivation.
            change: Change flag (0=external, 1=internal).
            address_type: Address type (legacy, segwit, native-segwit, taproot).
            start_index: Starting address index.
            custom_path_template: Custom derivation path template.

        Returns:
            List of AddressInfo objects with derivation details.

        Raises:
            DerivationError: If address derivation fails.
            HDWalletError: If parameters are invalid.

        Example:
            >>> addresses = manager.derive_addresses_batch("bitcoin", 10, address_type="native-segwit")
            >>> for addr in addresses:
            ...     print(f"{addr.index}: {addr.address}")
        """
        # Import here to avoid circular imports
        from .addresses import generate_address
        from .coins import get_coin_config
        from .validation import validate_derivation_parameters

        try:
            # Validate parameters
            validate_derivation_parameters(
                coin=coin,
                count=count,
                account=account,
                change=change,
                start_index=start_index,
                address_type=address_type,
            )

            # Get coin configuration
            coin_config = get_coin_config(coin)

            # Get address type configuration
            address_config = coin_config.get_address_type(address_type)

            addresses = []

            logger.info(
                "Starting batch address derivation: %s %s addresses (count=%d, account=%d)",
                coin,
                address_config.name,
                count,
                account,
            )

            for i in range(count):
                index = start_index + i

                try:
                    if custom_path_template:
                        # Use custom path template
                        path = custom_path_template.format(
                            purpose=address_config.purpose,
                            coin_type=coin_config.coin_type,
                            account=account,
                            change=change,
                            index=index,
                        )
                    else:
                        # Build standard derivation path
                        path = build_derivation_path(
                            purpose=address_config.purpose,
                            coin_type=coin_config.coin_type,
                            account=account,
                            change=change,
                            address_index=index,
                        )

                    # Generate address using master seed
                    master_seed = self._get_master_seed()
                    address_info = generate_address(
                        master_seed=master_seed,
                        coin_config=coin_config,
                        address_config=address_config,
                        derivation_path=path,
                        index=index,
                        account=account,
                        change=change,
                    )

                    addresses.append(address_info)

                except Exception as e:
                    raise DerivationError(
                        f"Address generation failed at index {index}: {e}",
                        operation="derive_addresses_batch",
                        context={
                            "coin": coin,
                            "index": index,
                            "account": account,
                            "change": change,
                            "address_type": address_type
                            or coin_config.default_address_type,
                        },
                        original_error=e,
                    ) from e

            logger.info(
                "Batch address derivation completed: %d %s addresses generated",
                len(addresses),
                coin,
            )
            log_security_event(
                f"HD wallet: Batch derivation completed ({len(addresses)} addresses)"
            )

            return addresses

        except (DerivationError, HDWalletError):
            # Re-raise HD wallet specific errors
            raise
        except Exception as e:
            raise DerivationError(
                f"Batch address derivation failed: {e}",
                operation="derive_addresses_batch",
                context={
                    "coin": coin,
                    "count": count,
                    "account": account,
                    "change": change,
                    "start_index": start_index,
                },
                original_error=e,
            ) from e

    def get_extended_keys(
        self,
        coin: str,
        account: int = 0,
        address_type: Optional[str] = None,
        include_private: bool = False,
    ) -> "ExtendedKeyInfo":
        """Get extended keys (xpub/xprv) for account level.

        Args:
            coin: Cryptocurrency name.
            account: Account number.
            address_type: Address type.
            include_private: Whether to include private keys (requires explicit flag).

        Returns:
            ExtendedKeyInfo object with extended key information.

        Raises:
            DerivationError: If extended key derivation fails.
        """
        # Import here to avoid circular imports
        from .coins import get_coin_config
        from .extended_keys import derive_extended_keys

        try:
            coin_config = get_coin_config(coin)
            address_config = coin_config.get_address_type(address_type)

            return derive_extended_keys(
                wallet_manager=self,
                coin_config=coin_config,
                address_config=address_config,
                account=account,
                include_private=include_private,
            )

        except Exception as e:
            raise DerivationError(
                f"Extended key derivation failed: {e}",
                operation="get_extended_keys",
                context={
                    "coin": coin,
                    "account": account,
                    "address_type": address_type,
                },
                original_error=e,
            ) from e

    def get_extended_keys_batch(
        self,
        coin: str,
        accounts: List[int],
        address_type: Optional[str] = None,
        include_private: bool = False,
    ) -> List["ExtendedKeyInfo"]:
        """Get extended keys for multiple accounts efficiently.

        Args:
            coin: Cryptocurrency name.
            accounts: List of account numbers.
            address_type: Address type.
            include_private: Whether to include private keys.

        Returns:
            List of ExtendedKeyInfo objects.

        Raises:
            DerivationError: If extended key derivation fails.
        """
        # Import here to avoid circular imports
        from .coins import get_coin_config
        from .extended_keys import derive_extended_keys_batch

        try:
            coin_config = get_coin_config(coin)
            address_config = coin_config.get_address_type(address_type)

            return derive_extended_keys_batch(
                wallet_manager=self,
                coin_config=coin_config,
                address_config=address_config,
                accounts=accounts,
                include_private=include_private,
            )

        except Exception as e:
            raise DerivationError(
                f"Batch extended key derivation failed: {e}",
                operation="get_extended_keys_batch",
                context={
                    "coin": coin,
                    "accounts": accounts,
                    "address_type": address_type,
                },
                original_error=e,
            ) from e

    def clear_cache(self) -> None:
        """Clear derived key cache to free memory."""
        cache_size = len(self._derived_keys_cache)
        self._derived_keys_cache.clear()
        logger.debug("Cleared derived key cache (%d entries)", cache_size)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "derived_keys_cached": len(self._derived_keys_cache),
            "cache_paths": list(self._derived_keys_cache.keys()),
            "master_key_cached": self._master_key is not None,
            "master_seed_cached": self._master_seed is not None,
        }

    def __del__(self) -> None:
        """Secure cleanup on destruction."""
        if hasattr(self, "_initialized") and self._initialized:
            self._secure_cleanup()

    def _secure_cleanup(self) -> None:
        """Securely clean up sensitive data.

        Uses existing SSeed secure deletion patterns to clean up
        all sensitive cryptographic material.
        """
        try:
            # Clear derived key cache
            self.clear_cache()

            # Secure deletion of master seed
            if self._master_seed:
                secure_delete_variable(self._master_seed)
                self._master_seed = None

            # Secure deletion of master key (if possible)
            if self._master_key:
                # Try to clear internal key data if accessible
                try:
                    if hasattr(self._master_key, "_key_data"):
                        secure_delete_variable(self._master_key._key_data)
                    if hasattr(self._master_key, "_chain_code"):
                        secure_delete_variable(self._master_key._chain_code)
                except Exception as cleanup_error:
                    logger.warning(
                        "Could not securely clean master key internals: %s",
                        cleanup_error,
                    )

                self._master_key = None

            logger.debug("HD wallet secure cleanup completed")
            log_security_event("HD wallet: Secure cleanup completed")

        except Exception as e:
            logger.warning("Secure cleanup failed: %s", e)


# Convenience function matching SSeed patterns
def derive_addresses_from_mnemonic(
    mnemonic: str,
    coin: str,
    count: int = 1,
    validate_mnemonic: bool = True,
    **kwargs: Any,
) -> List["AddressInfo"]:
    """Convenience function for direct address derivation.

    Creates a temporary HDWalletManager and derives addresses,
    following SSeed's pattern of providing convenience functions.

    Args:
        mnemonic: BIP39 mnemonic phrase.
        coin: Cryptocurrency name.
        count: Number of addresses to generate.
        validate_mnemonic: Whether to validate mnemonic checksum.
        **kwargs: Additional arguments for derive_addresses_batch.

    Returns:
        List of AddressInfo objects.

    Raises:
        HDWalletError: If address derivation fails.

    Example:
        >>> addresses = derive_addresses_from_mnemonic(
        ...     "word1 word2 ...", "bitcoin", 5, address_type="native-segwit"
        ... )
    """
    manager = HDWalletManager(mnemonic, validate=validate_mnemonic)
    try:
        return manager.derive_addresses_batch(coin=coin, count=count, **kwargs)
    finally:
        # Ensure cleanup happens
        manager._secure_cleanup()
