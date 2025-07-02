"""Address generation for HD wallets.

Implements address generation for multiple cryptocurrencies and address types
using the bip-utils library with proper formatting and validation.

This module handles the conversion of derived BIP32 keys into cryptocurrency
addresses following appropriate standards for each coin and address type.
"""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
)

from bip_utils import Bip32Secp256k1

from sseed.entropy import secure_delete_variable
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

from .coins import (
    AddressTypeConfig,
    CoinConfig,
)
from .exceptions import AddressGenerationError

logger = get_logger(__name__)


@dataclass
class AddressInfo:
    """Complete address information.

    Contains all details about a generated cryptocurrency address including
    derivation information, keys, and metadata.
    """

    index: int
    derivation_path: str
    private_key: str
    public_key: str
    address: str
    address_type: str
    coin: str
    network: str

    def to_dict(self, include_private_key: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for JSON output.

        Args:
            include_private_key: Whether to include private key in output.

        Returns:
            Dictionary representation of address info.

        Example:
            >>> addr_info = AddressInfo(...)
            >>> data = addr_info.to_dict(include_private_key=False)
            >>> print("private_key" in data)  # False
        """
        data = {
            "index": self.index,
            "derivation_path": self.derivation_path,
            "public_key": self.public_key,
            "address": self.address,
            "address_type": self.address_type,
            "coin": self.coin,
            "network": self.network,
        }

        if include_private_key:
            data["private_key"] = self.private_key

        return data

    def to_csv_row(self, include_private_key: bool = True) -> List[str]:
        """Convert to CSV row format.

        Args:
            include_private_key: Whether to include private key.

        Returns:
            List of string values for CSV output.
        """
        row = [
            str(self.index),
            self.derivation_path,
            self.public_key,
            self.address,
            self.address_type,
            self.coin,
            self.network,
        ]

        if include_private_key:
            row.insert(2, self.private_key)  # Insert after derivation_path

        return row

    def __str__(self) -> str:
        """String representation of address info."""
        return f"{self.coin} {self.address_type} address {self.index}: {self.address}"


def generate_address(
    master_seed: bytes,
    coin_config: CoinConfig,
    address_config: AddressTypeConfig,
    derivation_path: str,
    index: int,
    account: int = 0,
    change: int = 0,
) -> AddressInfo:
    """Generate address using BIP context.

    Creates a cryptocurrency address using the appropriate BIP context
    (BIP44, BIP49, BIP84, BIP86) for the specified coin and address type.

    Args:
        master_seed: BIP39 master seed (512 bits).
        coin_config: Cryptocurrency configuration.
        address_config: Address type configuration.
        derivation_path: BIP32 derivation path used.
        index: Address index number.
        account: Account number.
        change: Change flag (0=external, 1=internal).

    Returns:
        AddressInfo object with complete address details.

    Raises:
        AddressGenerationError: If address generation fails.

    Example:
        >>> addr = generate_address(seed, bitcoin_config, native_segwit_config, path, 0)
        >>> print(addr.address)  # bc1q...
    """
    private_key_wif = None
    public_key_hex = None
    address = None
    bip_ctx = None

    try:
        logger.debug(
            "Generating %s %s address at index %d",
            coin_config.name,
            address_config.name,
            index,
        )

        # Create appropriate BIP context based on purpose
        if address_config.purpose == 44:
            # BIP44 - Legacy P2PKH addresses
            from bip_utils import (
                Bip44,
                Bip44Changes,
            )

            bip_ctx = Bip44.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_addr = (
                bip_ctx.Purpose()
                .Coin()
                .Account(account)
                .Change(
                    Bip44Changes.CHAIN_EXT if change == 0 else Bip44Changes.CHAIN_INT
                )
                .AddressIndex(index)
            )
        elif address_config.purpose == 49:
            # BIP49 - SegWit P2SH-P2WPKH addresses
            from bip_utils import (
                Bip44Changes,
                Bip49,
            )

            bip_ctx = Bip49.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_addr = (
                bip_ctx.Purpose()
                .Coin()
                .Account(account)
                .Change(
                    Bip44Changes.CHAIN_EXT if change == 0 else Bip44Changes.CHAIN_INT
                )
                .AddressIndex(index)
            )
        elif address_config.purpose == 84:
            # BIP84 - Native SegWit P2WPKH addresses
            from bip_utils import (
                Bip44Changes,
                Bip84,
            )

            bip_ctx = Bip84.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_addr = (
                bip_ctx.Purpose()
                .Coin()
                .Account(account)
                .Change(
                    Bip44Changes.CHAIN_EXT if change == 0 else Bip44Changes.CHAIN_INT
                )
                .AddressIndex(index)
            )
        elif address_config.purpose == 86:
            # BIP86 - Taproot P2TR addresses
            from bip_utils import (
                Bip44Changes,
                Bip86,
            )

            bip_ctx = Bip86.FromSeed(master_seed, address_config.bip_utils_coin)
            bip_addr = (
                bip_ctx.Purpose()
                .Coin()
                .Account(account)
                .Change(
                    Bip44Changes.CHAIN_EXT if change == 0 else Bip44Changes.CHAIN_INT
                )
                .AddressIndex(index)
            )
        else:
            raise AddressGenerationError(
                f"Unsupported BIP purpose: {address_config.purpose}",
                coin=coin_config.name,
                address_type=address_config.name,
                derivation_path=derivation_path,
                operation="create_bip_context",
                context={"purpose": address_config.purpose},
            )

        # Extract key material and address
        private_key_wif = bip_addr.PrivateKey().Raw().ToHex()
        public_key_hex = bip_addr.PublicKey().RawCompressed().ToHex()
        address = bip_addr.PublicKey().ToAddress()

        # Validate generated address format
        if not _validate_address_format(address, coin_config, address_config):
            logger.warning("Generated address may have unexpected format: %s", address)

        # Create AddressInfo object
        address_info = AddressInfo(
            index=index,
            derivation_path=derivation_path,
            private_key=private_key_wif,
            public_key=public_key_hex,
            address=address,
            address_type=address_config.name.lower().replace(" ", "-"),
            coin=coin_config.name,
            network=coin_config.network_name,
        )

        logger.debug("Generated %s address: %s", coin_config.name, address)
        log_security_event(
            f"HD wallet: Address generated for {coin_config.name} at index {index}"
        )

        return address_info

    except AddressGenerationError:
        # Re-raise address generation errors
        raise
    except Exception as e:
        raise AddressGenerationError(
            f"Address generation failed: {e}",
            coin=coin_config.name,
            address_type=address_config.name,
            derivation_path=derivation_path,
            operation="generate_address",
            context={"index": index},
            original_error=e,
        ) from e
    finally:
        # Secure cleanup of intermediate values
        _secure_cleanup_variables(private_key_wif, public_key_hex, bip_ctx)


def derive_address_batch(
    master_seed: bytes,
    coin_config: CoinConfig,
    address_config: AddressTypeConfig,
    account: int = 0,
    change: int = 0,
    start_index: int = 0,
    count: int = 1,
) -> List[AddressInfo]:
    """Derive multiple addresses efficiently.

    Generates multiple addresses in batch with optimized key derivation
    and comprehensive error handling.

    Args:
        master_seed: BIP39 master seed (512 bits).
        coin_config: Cryptocurrency configuration.
        address_config: Address type configuration.
        account: Account number.
        change: Change flag (0=external, 1=internal).
        start_index: Starting address index.
        count: Number of addresses to generate.

    Returns:
        List of AddressInfo objects.

    Raises:
        AddressGenerationError: If batch generation fails.

    Example:
        >>> addresses = derive_address_batch(master_seed, btc_config, segwit_config, count=10)
        >>> print(f"Generated {len(addresses)} SegWit addresses")
    """
    from .derivation import build_derivation_path  # Avoid circular import

    addresses = []

    try:
        logger.info(
            "Starting batch address derivation: %s %s (count=%d, account=%d)",
            coin_config.name,
            address_config.name,
            count,
            account,
        )

        for i in range(count):
            index = start_index + i

            try:
                # Build derivation path for this address
                path = build_derivation_path(
                    purpose=address_config.purpose,
                    coin_type=coin_config.coin_type,
                    account=account,
                    change=change,
                    address_index=index,
                )

                # Generate address using master seed and BIP context
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
                raise AddressGenerationError(
                    f"Batch generation failed at index {index}: {e}",
                    coin=coin_config.name,
                    address_type=address_config.name,
                    count=count,
                    operation="derive_address_batch",
                    context={
                        "index": index,
                        "account": account,
                        "change": change,
                        "total_count": count,
                    },
                    original_error=e,
                ) from e

        logger.info(
            "Batch address derivation completed: %d %s addresses",
            len(addresses),
            coin_config.name,
        )
        log_security_event(
            f"HD wallet: Batch derivation completed ({len(addresses)} addresses)"
        )

        return addresses

    except AddressGenerationError:
        # Re-raise address generation errors
        raise
    except Exception as e:
        raise AddressGenerationError(
            f"Batch address derivation failed: {e}",
            coin=coin_config.name,
            address_type=address_config.name,
            count=count,
            operation="derive_address_batch",
            context={"start_index": start_index, "account": account, "change": change},
            original_error=e,
        ) from e


def _derive_key_from_master(master_key: Bip32Secp256k1, path: str) -> Bip32Secp256k1:
    """Derive key from master key using derivation path.

    Internal helper function for step-by-step key derivation with
    comprehensive error handling.

    Args:
        master_key: BIP32 master key.
        path: BIP32 derivation path.

    Returns:
        Derived BIP32 key.

    Raises:
        AddressGenerationError: If key derivation fails.
    """
    from .derivation import parse_derivation_path  # Avoid circular import

    try:
        path_components = parse_derivation_path(path)
        derived_key = master_key

        for i, component in enumerate(path_components):
            try:
                derived_key = derived_key.ChildKey(component)
            except Exception as e:
                raise AddressGenerationError(
                    f"Key derivation failed at component {i}: {e}",
                    derivation_path=path,
                    operation="_derive_key_from_master",
                    context={
                        "component_index": i,
                        "component_value": component,
                        "total_components": len(path_components),
                    },
                    original_error=e,
                ) from e

        return derived_key

    except AddressGenerationError:
        # Re-raise address generation errors
        raise
    except Exception as e:
        raise AddressGenerationError(
            f"Key derivation failed for path {path}: {e}",
            derivation_path=path,
            operation="_derive_key_from_master",
            original_error=e,
        ) from e


def _validate_address_format(
    address: str, coin_config: CoinConfig, address_config: AddressTypeConfig
) -> bool:
    """Validate address format for specific coin and type.

    Performs basic format validation to ensure the generated address
    matches expected patterns for the cryptocurrency and address type.

    Args:
        address: Generated address string.
        coin_config: Cryptocurrency configuration.
        address_config: Address type configuration.

    Returns:
        True if address format appears valid, False otherwise.
    """
    try:
        if not address or not isinstance(address, str):
            return False

        # Bitcoin address validation
        if coin_config.name == "bitcoin":
            if address_config.name == "Legacy" and not address.startswith("1"):
                return False
            elif address_config.name == "SegWit" and not address.startswith("3"):
                return False
            elif address_config.name == "Native SegWit" and not address.startswith(
                "bc1q"
            ):
                return False
            elif address_config.name == "Taproot" and not address.startswith("bc1p"):
                return False

        # Ethereum address validation
        elif coin_config.name == "ethereum":
            if not (address.startswith("0x") and len(address) == 42):
                return False

        # Litecoin address validation
        elif coin_config.name == "litecoin":
            if address_config.name == "Legacy" and not address.startswith("L"):
                return False
            elif address_config.name == "SegWit" and not address.startswith("M"):
                return False
            elif address_config.name == "Native SegWit" and not address.startswith(
                "ltc1"
            ):
                return False

        return True

    except Exception as e:
        logger.warning("Address format validation failed: %s", e)
        return False


def _secure_cleanup_variables(*variables: Any) -> None:
    """Securely clean up sensitive variables.

    Uses SSeed's secure deletion patterns to clean up any sensitive
    cryptographic material from memory.

    Args:
        *variables: Variables to securely delete.
    """
    for i, var in enumerate(variables):
        if var is not None:
            try:
                # For string variables (WIF keys, hex values)
                if isinstance(var, str):
                    # Create a bytes version and securely delete it
                    var_bytes = var.encode("utf-8")
                    secure_delete_variable(var_bytes)

                # For BIP context objects, try to clean internal state
                elif hasattr(var, "_key_data"):
                    secure_delete_variable(var._key_data)
                elif hasattr(var, "_priv_key"):
                    secure_delete_variable(var._priv_key)

            except Exception as cleanup_error:
                logger.warning(
                    "Failed to securely clean up variable %d: %s", i, cleanup_error
                )


def get_csv_headers(include_private_key: bool = True) -> List[str]:
    """Get CSV headers for address information.

    Args:
        include_private_key: Whether to include private key column.

    Returns:
        List of CSV header strings.

    Example:
        >>> headers = get_csv_headers(include_private_key=False)
        >>> print(headers[0])  # "Index"
    """
    headers = [
        "Index",
        "DerivationPath",
        "PublicKey",
        "Address",
        "AddressType",
        "Coin",
        "Network",
    ]

    if include_private_key:
        headers.insert(2, "PrivateKey")  # Insert after DerivationPath

    return headers


def format_address_summary(addresses: List[AddressInfo]) -> str:
    """Format a summary of generated addresses.

    Args:
        addresses: List of AddressInfo objects.

    Returns:
        Formatted summary string.

    Example:
        >>> summary = format_address_summary(addresses)
        >>> print(summary)  # "Generated 5 Bitcoin Native SegWit addresses (bc1q...)"
    """
    if not addresses:
        return "No addresses generated"

    first_addr = addresses[0]
    count = len(addresses)

    # Group by coin and address type
    groups: Dict[str, List[AddressInfo]] = {}
    for addr in addresses:
        key = f"{addr.coin}_{addr.address_type}"
        if key not in groups:
            groups[key] = []
        groups[key].append(addr)

    summary_parts = []
    for group_addresses in groups.values():
        first = group_addresses[0]
        count = len(group_addresses)
        coin_name = first.coin.title()
        addr_type = first.address_type.replace("-", " ").title()

        # Show first and last address if multiple
        if count == 1:
            addr_range = first.address
        elif count <= 3:
            addr_list = [addr.address for addr in group_addresses]
            addr_range = ", ".join(addr_list)
        else:
            first_address = group_addresses[0].address
            last_address = group_addresses[-1].address
            addr_range = f"{first_address} ... {last_address}"

        summary_parts.append(
            f"{count} {coin_name} {addr_type} address{'es' if count > 1 else ''}: {addr_range}"
        )

    return "\n".join(summary_parts)


def validate_address_info_list(addresses: List[AddressInfo]) -> Dict[str, Any]:
    """Validate a list of AddressInfo objects.

    Performs comprehensive validation of generated addresses including
    format checks, uniqueness validation, and consistency verification.

    Args:
        addresses: List of AddressInfo objects to validate.

    Returns:
        Dictionary with validation results.

    Example:
        >>> result = validate_address_info_list(addresses)
        >>> print(result["valid"], result["unique_addresses"])  # True, 10
    """
    if not addresses:
        return {"valid": True, "errors": [], "warnings": [], "stats": {}}

    errors = []
    warnings = []
    unique_addresses = set()
    unique_private_keys = set()

    # Validate each address
    for i, addr in enumerate(addresses):
        try:
            # Check for required fields
            if not addr.address:
                errors.append(f"Address {i}: Missing address")
            if not addr.derivation_path:
                errors.append(f"Address {i}: Missing derivation path")
            if not addr.private_key:
                errors.append(f"Address {i}: Missing private key")

            # Check for duplicates
            if addr.address in unique_addresses:
                errors.append(f"Address {i}: Duplicate address {addr.address}")
            unique_addresses.add(addr.address)

            if addr.private_key in unique_private_keys:
                errors.append(f"Address {i}: Duplicate private key")
            unique_private_keys.add(addr.private_key)

            # Validate address format (basic check)
            if addr.address and not _basic_address_format_check(
                addr.address, addr.coin
            ):
                warnings.append(
                    f"Address {i}: Unexpected format for {addr.coin}: {addr.address}"
                )

        except Exception as e:
            errors.append(f"Address {i}: Validation error: {e}")

    # Compile statistics
    stats = {
        "total_addresses": len(addresses),
        "unique_addresses": len(unique_addresses),
        "unique_private_keys": len(unique_private_keys),
        "coins": list(set(addr.coin for addr in addresses)),
        "address_types": list(set(addr.address_type for addr in addresses)),
    }

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def _basic_address_format_check(address: str, coin: str) -> bool:
    """Basic address format validation.

    Args:
        address: Address string to validate.
        coin: Cryptocurrency name.

    Returns:
        True if address appears to have valid format.
    """
    try:
        if not address or len(address) < 10:
            return False

        # Basic format checks by coin
        if coin == "bitcoin":
            return address.startswith(("1", "3", "bc1")) and 25 <= len(address) <= 62
        elif coin == "ethereum":
            return address.startswith("0x") and len(address) == 42
        elif coin == "litecoin":
            return address.startswith(("L", "M", "ltc1")) and 25 <= len(address) <= 62

        return True  # Unknown coin, assume valid

    except Exception:
        return False
