"""Extended key functionality for HD wallets.

Implements extended public key (xpub) and extended private key (xprv) generation
for hierarchical deterministic wallets following BIP32 standards.

This module provides secure extended key derivation for account-level keys
that can be used for watch-only wallets and address generation.
"""

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
)

if TYPE_CHECKING:
    from .core import HDWalletManager

from bip_utils import (
    Bip44,
    Bip49,
    Bip84,
    Bip86,
)

from sseed.entropy import secure_delete_variable
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

from .coins import (
    AddressTypeConfig,
    CoinConfig,
)
from .derivation import build_account_path
from .exceptions import ExtendedKeyError

logger = get_logger(__name__)


@dataclass
class ExtendedKeyInfo:
    """Extended key information container.

    Contains both extended public and private keys with metadata
    for hierarchical deterministic wallet operations.
    """

    coin: str
    address_type: str
    account: int
    network: str
    derivation_path: str
    xpub: str
    xprv: Optional[str] = None  # Only included if explicitly requested
    fingerprint: str = ""
    depth: int = 3  # Account level is depth 3 in BIP32

    def to_dict(self, include_private: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON output.

        Args:
            include_private: Whether to include extended private key.

        Returns:
            Dictionary representation of extended key info.

        Example:
            >>> ext_key_info = ExtendedKeyInfo(...)
            >>> data = ext_key_info.to_dict(include_private=False)
            >>> print("xprv" in data)  # False
        """
        data = {
            "coin": self.coin,
            "address_type": self.address_type,
            "account": self.account,
            "network": self.network,
            "derivation_path": self.derivation_path,
            "xpub": self.xpub,
            "fingerprint": self.fingerprint,
            "depth": self.depth,
        }

        if include_private and self.xprv:
            data["xprv"] = self.xprv

        return data

    def __str__(self) -> str:
        """String representation of extended key info."""
        return f"{self.coin} {self.address_type} account {self.account}: {self.xpub[:20]}..."


def derive_extended_keys(
    wallet_manager: "HDWalletManager",
    coin_config: CoinConfig,
    address_config: AddressTypeConfig,
    account: int = 0,
    include_private: bool = False,
) -> ExtendedKeyInfo:
    """Derive extended keys for account level.

    Generates extended public key (xpub) and optionally extended private key (xprv)
    for the specified account level following BIP32 standards.

    Args:
        wallet_manager: HDWalletManager instance.
        coin_config: Cryptocurrency configuration.
        address_config: Address type configuration.
        account: Account number for key derivation.
        include_private: Whether to include extended private key (security warning).

    Returns:
        ExtendedKeyInfo object with derived keys and metadata.

    Raises:
        ExtendedKeyError: If extended key derivation fails.

    Example:
        >>> ext_keys = derive_extended_keys(manager, btc_config, segwit_config, 0)
        >>> print(ext_keys.xpub)  # xpub6D4BDPcP2GT579...
    """
    xpub = None
    xprv = None
    bip_account = None

    try:
        logger.debug(
            "Deriving extended keys for %s %s account %d",
            coin_config.name,
            address_config.name,
            account,
        )

        # Get master seed from wallet manager
        master_seed = wallet_manager._get_master_seed()

        # Create appropriate BIP context based on purpose
        if address_config.purpose == 44:
            # BIP44 - Legacy P2PKH addresses
            bip_ctx = Bip44.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_account = bip_ctx.Purpose().Coin().Account(account)
        elif address_config.purpose == 49:
            # BIP49 - SegWit P2SH-P2WPKH addresses
            bip_ctx = Bip49.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_account = bip_ctx.Purpose().Coin().Account(account)
        elif address_config.purpose == 84:
            # BIP84 - Native SegWit P2WPKH addresses
            bip_ctx = Bip84.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_account = bip_ctx.Purpose().Coin().Account(account)
        elif address_config.purpose == 86:
            # BIP86 - Taproot P2TR addresses
            bip_ctx = Bip86.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_account = bip_ctx.Purpose().Coin().Account(account)
        else:
            raise ExtendedKeyError(
                f"Unsupported BIP purpose for extended keys: {address_config.purpose}",
                coin=coin_config.name,
                account=account,
                operation="create_bip_context",
                context={"purpose": address_config.purpose, "account": account},
            )

        # Extract extended keys using correct bip-utils API
        xpub = bip_account.PublicKey().ToExtended()
        if include_private:
            xprv = bip_account.PrivateKey().ToExtended()

        # Get key metadata
        fingerprint = bip_account.Bip32Object().FingerPrint().ToHex()

        # Build account-level derivation path
        derivation_path = build_account_path(
            purpose=address_config.purpose,
            coin_type=coin_config.coin_type,
            account=account,
        )

        # Create ExtendedKeyInfo object
        extended_key_info = ExtendedKeyInfo(
            coin=coin_config.name,
            address_type=address_config.name.lower().replace(" ", "-"),
            account=account,
            network=coin_config.network_name,
            derivation_path=derivation_path,
            xpub=xpub,
            xprv=xprv,
            fingerprint=fingerprint,
            depth=3,  # Account level is depth 3
        )

        logger.debug(
            "Extended keys derived for %s account %d", coin_config.name, account
        )
        log_security_event(
            f"HD wallet: Extended keys derived for {coin_config.name} account {account}"
        )

        return extended_key_info

    except ExtendedKeyError:
        # Re-raise extended key errors
        raise
    except Exception as e:
        raise ExtendedKeyError(
            f"Extended key derivation failed: {e}",
            coin=coin_config.name,
            account=account,
            operation="derive_extended_keys",
            context={"account": account, "include_private": include_private},
            original_error=e,
        ) from e
    finally:
        # Secure cleanup of intermediate values
        _secure_cleanup_extended_key_variables(xpub, xprv, bip_account)


def derive_extended_keys_batch(
    wallet_manager: "HDWalletManager",
    coin_config: CoinConfig,
    address_config: AddressTypeConfig,
    accounts: list[int],
    include_private: bool = False,
) -> list[ExtendedKeyInfo]:
    """Derive extended keys for multiple accounts efficiently.

    Generates extended keys for multiple account numbers in batch
    with optimized error handling and secure cleanup.

    Args:
        wallet_manager: HDWalletManager instance.
        coin_config: Cryptocurrency configuration.
        address_config: Address type configuration.
        accounts: List of account numbers.
        include_private: Whether to include extended private keys.

    Returns:
        List of ExtendedKeyInfo objects.

    Raises:
        ExtendedKeyError: If batch derivation fails.

    Example:
        >>> ext_keys = derive_extended_keys_batch(manager, btc_config, segwit_config, [0, 1, 2])
        >>> print(f"Generated {len(ext_keys)} extended keys")
    """
    extended_keys = []

    try:
        logger.info(
            "Starting batch extended key derivation for %d accounts", len(accounts)
        )

        for account in accounts:
            try:
                extended_key = derive_extended_keys(
                    wallet_manager=wallet_manager,
                    coin_config=coin_config,
                    address_config=address_config,
                    account=account,
                    include_private=include_private,
                )
                extended_keys.append(extended_key)

            except Exception as e:
                raise ExtendedKeyError(
                    f"Batch extended key derivation failed at account {account}: {e}",
                    coin=coin_config.name,
                    account=account,
                    operation="derive_extended_keys_batch",
                    context={
                        "account": account,
                        "total_accounts": len(accounts),
                        "include_private": include_private,
                    },
                    original_error=e,
                ) from e

        logger.info(
            "Batch extended key derivation completed: %d keys generated",
            len(extended_keys),
        )
        log_security_event(
            f"HD wallet: Batch extended key derivation completed ({len(extended_keys)} keys)"
        )

        return extended_keys

    except ExtendedKeyError:
        # Re-raise extended key errors
        raise
    except Exception as e:
        raise ExtendedKeyError(
            f"Batch extended key derivation failed: {e}",
            coin=coin_config.name,
            operation="derive_extended_keys_batch",
            context={"accounts": accounts, "include_private": include_private},
            original_error=e,
        ) from e


def validate_extended_key(extended_key: str, key_type: str = "auto") -> Dict[str, Any]:
    """Validate an extended key format and extract information.

    Validates the format of an extended public or private key
    and extracts metadata for verification.

    Args:
        extended_key: Extended key string (xpub/xprv/ypub/zpub/etc).
        key_type: Expected key type ("xpub", "xprv", "auto").

    Returns:
        Dictionary with validation results and extracted information.

    Raises:
        ExtendedKeyError: If validation fails.

    Example:
        >>> result = validate_extended_key("xpub6D4BDPcP2GT579...")
        >>> print(result["valid"], result["key_type"])  # True, "xpub"
    """
    try:
        from bip_utils import (  # pylint: disable=import-outside-toplevel
            Bip32KeyDeserializer,
        )

        logger.debug("Validating extended key format")

        # Attempt to deserialize the extended key
        try:
            deserialized_key = Bip32KeyDeserializer.DeserializeKey(extended_key)

            # Extract key information
            is_public = deserialized_key.IsPublic()
            key_type_detected = "xpub" if is_public else "xprv"

            # Validate key type if specified
            if key_type != "auto" and key_type != key_type_detected:
                raise ExtendedKeyError(
                    f"Key type mismatch: expected {key_type}, got {key_type_detected}",
                    operation="validate_extended_key",
                    context={"expected": key_type, "detected": key_type_detected},
                )

            # Extract metadata
            result = {
                "valid": True,
                "key_type": key_type_detected,
                "is_public": is_public,
                "depth": deserialized_key.Depth(),
                "fingerprint": deserialized_key.FingerPrint().ToHex(),
                "child_index": deserialized_key.ChildIndex(),
                "chain_code": deserialized_key.ChainCode().ToHex(),
            }

            logger.debug("Extended key validation successful: %s", key_type_detected)
            return result

        except Exception as e:
            raise ExtendedKeyError(
                f"Invalid extended key format: {e}",
                operation="validate_extended_key",
                context={"key_type": key_type},
                original_error=e,
            ) from e

    except ExtendedKeyError:
        # Re-raise extended key errors
        raise
    except Exception as e:
        raise ExtendedKeyError(
            f"Extended key validation failed: {e}",
            operation="validate_extended_key",
            original_error=e,
        ) from e


def get_extended_key_info(extended_key: str) -> Dict[str, Any]:
    """Get comprehensive information about an extended key.

    Extracts and formats all available information from an extended key
    including derivation details and key material.

    Args:
        extended_key: Extended key string.

    Returns:
        Dictionary with comprehensive key information.

    Example:
        >>> info = get_extended_key_info("xpub6D4BDPcP2GT579...")
        >>> print(info["depth"], info["fingerprint"])
    """
    try:
        # Validate and get basic info
        validation_result = validate_extended_key(extended_key)

        # Add additional analysis
        key_prefix = extended_key[:4]
        prefix_info = _get_key_prefix_info(key_prefix)

        # Combine all information
        comprehensive_info = {
            **validation_result,
            "key_prefix": key_prefix,
            "network": prefix_info.get("network", "unknown"),
            "purpose_description": prefix_info.get("purpose", "unknown"),
            "raw_key": extended_key,
            "key_length": len(extended_key),
        }

        logger.debug(
            "Extended key info extracted for %s key", validation_result["key_type"]
        )
        return comprehensive_info

    except Exception as e:
        raise ExtendedKeyError(
            f"Failed to get extended key info: {e}",
            operation="get_extended_key_info",
            original_error=e,
        ) from e


def _get_key_prefix_info(prefix: str) -> Dict[str, str]:
    """Get information about extended key prefix.

    Args:
        prefix: First 4 characters of extended key.

    Returns:
        Dictionary with prefix information.
    """
    prefix_map = {
        "xpub": {"network": "Bitcoin Mainnet", "purpose": "Multi-purpose public"},
        "xprv": {"network": "Bitcoin Mainnet", "purpose": "Multi-purpose private"},
        "ypub": {"network": "Bitcoin Mainnet", "purpose": "P2SH-SegWit public (BIP49)"},
        "yprv": {
            "network": "Bitcoin Mainnet",
            "purpose": "P2SH-SegWit private (BIP49)",
        },
        "zpub": {
            "network": "Bitcoin Mainnet",
            "purpose": "Native SegWit public (BIP84)",
        },
        "zprv": {
            "network": "Bitcoin Mainnet",
            "purpose": "Native SegWit private (BIP84)",
        },
        "tpub": {"network": "Bitcoin Testnet", "purpose": "Multi-purpose public"},
        "tprv": {"network": "Bitcoin Testnet", "purpose": "Multi-purpose private"},
        "upub": {"network": "Bitcoin Testnet", "purpose": "P2SH-SegWit public (BIP49)"},
        "uprv": {
            "network": "Bitcoin Testnet",
            "purpose": "P2SH-SegWit private (BIP49)",
        },
        "vpub": {
            "network": "Bitcoin Testnet",
            "purpose": "Native SegWit public (BIP84)",
        },
        "vprv": {
            "network": "Bitcoin Testnet",
            "purpose": "Native SegWit private (BIP84)",
        },
    }

    return prefix_map.get(prefix, {"network": "unknown", "purpose": "unknown"})


def _secure_cleanup_extended_key_variables(*variables: Any) -> None:
    """Securely clean up extended key variables.

    Uses SSeed's secure deletion patterns to clean up any sensitive
    extended key material from memory.

    Args:
        *variables: Variables to securely delete.
    """
    for i, var in enumerate(variables):
        if var is not None:
            try:
                # For string variables (extended keys)
                if isinstance(var, str):
                    # Create a bytes version and securely delete it
                    var_bytes = var.encode("utf-8")
                    secure_delete_variable(var_bytes)

                # For BIP objects, try to clean internal state
                elif hasattr(var, "_key_data"):
                    secure_delete_variable(var._key_data)
                elif hasattr(var, "_priv_key"):
                    secure_delete_variable(var._priv_key)
                elif hasattr(var, "_chain_code"):
                    secure_delete_variable(var._chain_code)

            except Exception as cleanup_error:
                logger.warning(
                    "Failed to securely clean up extended key variable %d: %s",
                    i,
                    cleanup_error,
                )


def format_extended_key_summary(extended_keys: list[ExtendedKeyInfo]) -> str:
    """Format a summary of generated extended keys.

    Args:
        extended_keys: List of ExtendedKeyInfo objects.

    Returns:
        Formatted summary string.

    Example:
        >>> summary = format_extended_key_summary(ext_keys)
        >>> print(summary)  # "Generated 3 Bitcoin Native SegWit extended keys"
    """
    if not extended_keys:
        return "No extended keys generated"

    first_key = extended_keys[0]
    count = len(extended_keys)

    # Group by coin and address type
    groups: Dict[str, list[ExtendedKeyInfo]] = {}
    for key in extended_keys:
        group_key = f"{key.coin}_{key.address_type}"
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(key)

    summary_parts = []
    for group_keys in groups.values():
        first = group_keys[0]
        group_count = len(group_keys)
        coin_name = first.coin.title()
        addr_type = first.address_type.replace("-", " ").title()

        summary_parts.append(
            f"{group_count} {coin_name} {addr_type} extended key{'s' if group_count > 1 else ''}"
        )

    return "Generated " + ", ".join(summary_parts)


def get_extended_key_csv_headers(include_private: bool = False) -> list[str]:
    """Get CSV headers for extended key information.

    Args:
        include_private: Whether to include private key column.

    Returns:
        List of CSV header strings.

    Example:
        >>> headers = get_extended_key_csv_headers(include_private=False)
        >>> print(headers[0])  # "Coin"
    """
    headers = [
        "Coin",
        "AddressType",
        "Account",
        "Network",
        "DerivationPath",
        "Xpub",
        "Fingerprint",
        "Depth",
    ]

    if include_private:
        headers.insert(-2, "Xprv")  # Insert before Fingerprint

    return headers
