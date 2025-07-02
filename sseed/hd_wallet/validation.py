"""Parameter validation for HD wallet operations.

Provides comprehensive validation for all HD wallet parameters including
cryptocurrencies, addresses types, derivation parameters, and security checks.

This module follows SSeed's validation patterns while providing HD wallet
specific validation logic.
"""

from typing import (
    Any,
    Dict,
    Optional,
)

from sseed.logging_config import get_logger

from .derivation import (
    get_path_info,
    validate_path,
)
from .exceptions import (
    HDWalletError,
    InvalidPathError,
    UnsupportedCoinError,
)

logger = get_logger(__name__)

# Validation constants
MIN_ADDRESS_COUNT = 1
MAX_ADDRESS_COUNT = 1000
MIN_ACCOUNT_NUMBER = 0
MAX_ACCOUNT_NUMBER = 2**31 - 1
MIN_ADDRESS_INDEX = 0
MAX_ADDRESS_INDEX = 2**31 - 1

# Valid change values
VALID_CHANGE_VALUES = [0, 1]  # 0=external, 1=internal

# Supported coin validation will be imported from coins module
# to avoid circular imports


def validate_coin_support(coin: str) -> None:
    """Validate that cryptocurrency is supported.

    Args:
        coin: Cryptocurrency name to validate.

    Raises:
        UnsupportedCoinError: If cryptocurrency is not supported.

    Example:
        >>> validate_coin_support("bitcoin")  # Valid
        >>> validate_coin_support("dogecoin")  # May raise UnsupportedCoinError
    """
    # Import here to avoid circular imports
    from .coins import (
        SUPPORTED_COINS,
        get_coin_config,
    )

    if not isinstance(coin, str):
        raise UnsupportedCoinError(
            f"Coin name must be string, got {type(coin).__name__}",
            coin=str(coin),
            supported_coins=SUPPORTED_COINS,
        )

    coin = coin.lower().strip()

    if not coin:
        raise UnsupportedCoinError(
            "Coin name cannot be empty", coin=coin, supported_coins=SUPPORTED_COINS
        )

    if coin not in SUPPORTED_COINS:
        raise UnsupportedCoinError(
            f"Cryptocurrency '{coin}' is not supported",
            coin=coin,
            supported_coins=SUPPORTED_COINS,
        )

    # Additional validation - ensure coin configuration exists
    try:
        get_coin_config(coin)
    except Exception as e:
        raise UnsupportedCoinError(
            f"Coin configuration error for '{coin}': {e}",
            coin=coin,
            supported_coins=SUPPORTED_COINS,
        ) from e

    logger.debug("Coin validation successful: %s", coin)


def validate_address_type(coin: str, address_type: Optional[str] = None) -> str:
    """Validate address type for specific cryptocurrency.

    Args:
        coin: Cryptocurrency name.
        address_type: Address type to validate (optional).

    Returns:
        Validated address type (default if None provided).

    Raises:
        UnsupportedCoinError: If address type is not supported.

    Example:
        >>> validate_address_type("bitcoin", "native-segwit")
        "native-segwit"
        >>> validate_address_type("bitcoin", None)  # Returns default
        "native-segwit"
    """
    # Import here to avoid circular imports
    from .coins import (
        get_coin_config,
        get_supported_address_types,
    )

    # Validate coin first
    validate_coin_support(coin)

    # Get coin configuration
    coin_config = get_coin_config(coin)

    # Use default if no address type specified
    if address_type is None:
        address_type = coin_config.default_address_type
        logger.debug("Using default address type for %s: %s", coin, address_type)
        return address_type

    # Validate address type format
    if not isinstance(address_type, str):
        raise UnsupportedCoinError(
            f"Address type must be string, got {type(address_type).__name__}",
            coin=coin,
            address_type=str(address_type),
            supported_types=get_supported_address_types(coin),
        )

    address_type = address_type.lower().strip()

    if not address_type:
        raise UnsupportedCoinError(
            "Address type cannot be empty",
            coin=coin,
            address_type=address_type,
            supported_types=get_supported_address_types(coin),
        )

    # Check if address type is supported for this coin
    supported_types = get_supported_address_types(coin)
    if address_type not in supported_types:
        raise UnsupportedCoinError(
            f"Address type '{address_type}' not supported for {coin}",
            coin=coin,
            address_type=address_type,
            supported_types=supported_types,
        )

    logger.debug("Address type validation successful: %s %s", coin, address_type)
    return address_type


def validate_address_count(count: int) -> None:
    """Validate address count parameter.

    Args:
        count: Number of addresses to generate.

    Raises:
        HDWalletError: If count is invalid.

    Example:
        >>> validate_address_count(10)  # Valid
        >>> validate_address_count(0)   # Raises HDWalletError
    """
    if not isinstance(count, int):
        raise HDWalletError(
            f"Address count must be integer, got {type(count).__name__}",
            operation="validate_address_count",
            context={"count": count},
        )

    if not MIN_ADDRESS_COUNT <= count <= MAX_ADDRESS_COUNT:
        raise HDWalletError(
            f"Address count must be {MIN_ADDRESS_COUNT} to {MAX_ADDRESS_COUNT}, got {count}",
            operation="validate_address_count",
            context={
                "count": count,
                "min_count": MIN_ADDRESS_COUNT,
                "max_count": MAX_ADDRESS_COUNT,
            },
        )

    logger.debug("Address count validation successful: %d", count)


def validate_account_number(account: int) -> None:
    """Validate account number parameter.

    Args:
        account: Account number for derivation.

    Raises:
        InvalidPathError: If account number is invalid.

    Example:
        >>> validate_account_number(0)    # Valid
        >>> validate_account_number(-1)   # Raises InvalidPathError
    """
    if not isinstance(account, int):
        raise InvalidPathError(
            f"Account number must be integer, got {type(account).__name__}",
            parameter="account",
            value=account,
        )

    if not MIN_ACCOUNT_NUMBER <= account <= MAX_ACCOUNT_NUMBER:
        raise InvalidPathError(
            f"Account number must be {MIN_ACCOUNT_NUMBER} to {MAX_ACCOUNT_NUMBER}, got {account}",
            parameter="account",
            value=account,
            valid_range=f"{MIN_ACCOUNT_NUMBER} to {MAX_ACCOUNT_NUMBER}",
        )

    logger.debug("Account number validation successful: %d", account)


def validate_change_flag(change: int) -> None:
    """Validate change flag parameter.

    Args:
        change: Change flag (0=external, 1=internal).

    Raises:
        InvalidPathError: If change flag is invalid.

    Example:
        >>> validate_change_flag(0)  # Valid (external)
        >>> validate_change_flag(1)  # Valid (internal)
        >>> validate_change_flag(2)  # Raises InvalidPathError
    """
    if not isinstance(change, int):
        raise InvalidPathError(
            f"Change flag must be integer, got {type(change).__name__}",
            parameter="change",
            value=change,
        )

    if change not in VALID_CHANGE_VALUES:
        raise InvalidPathError(
            f"Change flag must be 0 (external) or 1 (internal), got {change}",
            parameter="change",
            value=change,
            valid_range="0 or 1",
        )

    logger.debug("Change flag validation successful: %d", change)


def validate_address_index(index: int) -> None:
    """Validate address index parameter.

    Args:
        index: Address index for derivation.

    Raises:
        InvalidPathError: If address index is invalid.

    Example:
        >>> validate_address_index(0)    # Valid
        >>> validate_address_index(100)  # Valid
        >>> validate_address_index(-1)   # Raises InvalidPathError
    """
    if not isinstance(index, int):
        raise InvalidPathError(
            f"Address index must be integer, got {type(index).__name__}",
            parameter="address_index",
            value=index,
        )

    if not MIN_ADDRESS_INDEX <= index <= MAX_ADDRESS_INDEX:
        raise InvalidPathError(
            f"Address index must be {MIN_ADDRESS_INDEX} to {MAX_ADDRESS_INDEX}, got {index}",
            parameter="address_index",
            value=index,
            valid_range=f"{MIN_ADDRESS_INDEX} to {MAX_ADDRESS_INDEX}",
        )

    logger.debug("Address index validation successful: %d", index)


def validate_derivation_parameters(
    coin: str,
    count: int = 1,
    account: int = 0,
    change: int = 0,
    start_index: int = 0,
    address_type: Optional[str] = None,
    custom_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Comprehensive validation of all derivation parameters.

    Validates all parameters for HD wallet address derivation and returns
    normalized values for use in derivation operations.

    Args:
        coin: Cryptocurrency name.
        count: Number of addresses to generate.
        account: Account number.
        change: Change flag.
        start_index: Starting address index.
        address_type: Address type (optional).
        custom_path: Custom derivation path (optional).

    Returns:
        Dictionary with validated and normalized parameters.

    Raises:
        HDWalletError: If any parameter is invalid.
        UnsupportedCoinError: If coin or address type is unsupported.
        InvalidPathError: If derivation parameters are invalid.

    Example:
        >>> params = validate_derivation_parameters("bitcoin", 5, address_type="native-segwit")
        >>> print(params["coin"], params["address_type"])
        bitcoin native-segwit
    """
    logger.debug(
        "Validating derivation parameters: coin=%s, count=%d, account=%d",
        coin,
        count,
        account,
    )

    # Validate individual parameters
    validate_coin_support(coin)
    validated_address_type = validate_address_type(coin, address_type)
    validate_address_count(count)
    validate_account_number(account)
    validate_change_flag(change)
    validate_address_index(start_index)

    # Validate address range
    max_end_index = start_index + count - 1
    if max_end_index > MAX_ADDRESS_INDEX:
        raise InvalidPathError(
            f"Address range exceeds maximum index: start={start_index}, count={count}, max_end={max_end_index}",
            parameter="address_range",
            value=max_end_index,
            valid_range=f"0 to {MAX_ADDRESS_INDEX}",
        )

    # Validate custom path if provided
    if custom_path:
        validate_custom_path(custom_path, coin, validated_address_type)

    # Return normalized parameters
    validated_params = {
        "coin": coin.lower().strip(),
        "address_type": validated_address_type,
        "count": count,
        "account": account,
        "change": change,
        "start_index": start_index,
        "end_index": max_end_index,
        "custom_path": custom_path,
    }

    logger.debug("Parameter validation successful: %s", validated_params)
    return validated_params


def validate_custom_path(custom_path: str, coin: str, address_type: str) -> None:
    """Validate custom derivation path.

    Args:
        custom_path: Custom BIP32 derivation path.
        coin: Cryptocurrency name.
        address_type: Address type.

    Raises:
        InvalidPathError: If custom path is invalid.

    Example:
        >>> validate_custom_path("m/84'/0'/0'/0/0", "bitcoin", "native-segwit")
        >>> validate_custom_path("invalid", "bitcoin", "legacy")  # Raises error
    """
    # Validate basic path format
    validate_path(custom_path)

    # Extract path information
    try:
        path_info = get_path_info(custom_path)
    except Exception as e:
        raise InvalidPathError(
            f"Failed to parse custom path: {e}", path=custom_path
        ) from e

    # Import here to avoid circular imports
    from .coins import get_coin_config

    # Get expected configuration
    coin_config = get_coin_config(coin)
    address_config = coin_config.get_address_type(address_type)

    # Validate purpose matches address type
    if path_info.purpose != address_config.purpose:
        logger.warning(
            "Custom path purpose (%d) doesn't match address type purpose (%d) for %s %s",
            path_info.purpose,
            address_config.purpose,
            coin,
            address_type,
        )

    # Validate coin type matches
    if path_info.coin_type != coin_config.coin_type:
        logger.warning(
            "Custom path coin type (%d) doesn't match expected coin type (%d) for %s",
            path_info.coin_type,
            coin_config.coin_type,
            coin,
        )

    logger.debug("Custom path validation completed: %s", custom_path)


def validate_extended_key_request(
    coin: str,
    account: int = 0,
    address_type: Optional[str] = None,
    include_private: bool = False,
    unsafe_flag: bool = False,
) -> Dict[str, Any]:
    """Validate extended key derivation request.

    Args:
        coin: Cryptocurrency name.
        account: Account number.
        address_type: Address type.
        include_private: Whether to include private keys.
        unsafe_flag: Whether --unsafe flag was provided.

    Returns:
        Dictionary with validated parameters.

    Raises:
        HDWalletError: If private keys requested without unsafe flag.

    Example:
        >>> validate_extended_key_request("bitcoin", 0, "native-segwit", False)
        >>> validate_extended_key_request("bitcoin", 0, "legacy", True, True)  # With unsafe
    """
    # Validate basic parameters
    validate_coin_support(coin)
    validated_address_type = validate_address_type(coin, address_type)
    validate_account_number(account)

    # Security check for private key export
    if include_private and not unsafe_flag:
        raise HDWalletError(
            "Private key export requires --unsafe flag for security",
            operation="validate_extended_key_request",
            context={"include_private": include_private, "unsafe_flag": unsafe_flag},
        )

    validated_params = {
        "coin": coin.lower().strip(),
        "address_type": validated_address_type,
        "account": account,
        "include_private": include_private,
        "unsafe_flag": unsafe_flag,
    }

    if include_private:
        logger.warning("Private key export requested with --unsafe flag")
        log_security_event = __import__(
            "sseed.logging_config", fromlist=["log_security_event"]
        ).log_security_event
        log_security_event("HD wallet: Private key export requested")

    logger.debug("Extended key request validation successful: %s", validated_params)
    return validated_params


def validate_output_format(format_type: str) -> str:
    """Validate output format parameter.

    Args:
        format_type: Output format (json, csv, plain).

    Returns:
        Validated format type.

    Raises:
        HDWalletError: If format is invalid.

    Example:
        >>> validate_output_format("json")
        "json"
        >>> validate_output_format("invalid")  # Raises HDWalletError
    """
    VALID_FORMATS = ["json", "csv", "plain"]

    if not isinstance(format_type, str):
        raise HDWalletError(
            f"Output format must be string, got {type(format_type).__name__}",
            operation="validate_output_format",
            context={"format": format_type},
        )

    format_type = format_type.lower().strip()

    if format_type not in VALID_FORMATS:
        raise HDWalletError(
            f"Output format must be one of {VALID_FORMATS}, got '{format_type}'",
            operation="validate_output_format",
            context={"format": format_type, "valid_formats": VALID_FORMATS},
        )

    logger.debug("Output format validation successful: %s", format_type)
    return format_type


def validate_bip85_parameters(
    bip85_source: Optional[str] = None, bip85_index: Optional[int] = None
) -> Dict[str, Any]:
    """Validate BIP85 integration parameters.

    Args:
        bip85_source: BIP85 master mnemonic file.
        bip85_index: BIP85 child index.

    Returns:
        Dictionary with validated BIP85 parameters.

    Raises:
        HDWalletError: If BIP85 parameters are invalid.

    Example:
        >>> validate_bip85_parameters("master.txt", 0)
        >>> validate_bip85_parameters(None, None)  # Both None is valid
        >>> validate_bip85_parameters("master.txt", None)  # Raises error
    """
    # Both None is valid (no BIP85 integration)
    if bip85_source is None and bip85_index is None:
        return {"bip85_enabled": False}

    # Both must be provided if either is provided
    if (bip85_source is None) != (bip85_index is None):
        raise HDWalletError(
            "Both --bip85-source and --bip85-index are required for BIP85 mode",
            operation="validate_bip85_parameters",
            context={"bip85_source": bip85_source, "bip85_index": bip85_index},
        )

    # Validate BIP85 index
    if not isinstance(bip85_index, int):
        raise HDWalletError(
            f"BIP85 index must be integer, got {type(bip85_index).__name__}",
            operation="validate_bip85_parameters",
            context={"bip85_index": bip85_index},
        )

    if not 0 <= bip85_index <= MAX_ACCOUNT_NUMBER:
        raise HDWalletError(
            f"BIP85 index must be 0 to {MAX_ACCOUNT_NUMBER}, got {bip85_index}",
            operation="validate_bip85_parameters",
            context={"bip85_index": bip85_index, "max_index": MAX_ACCOUNT_NUMBER},
        )

    validated_params = {
        "bip85_enabled": True,
        "bip85_source": bip85_source,
        "bip85_index": bip85_index,
    }

    logger.debug("BIP85 parameter validation successful: %s", validated_params)
    return validated_params
