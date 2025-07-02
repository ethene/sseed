"""HD wallet specific exception classes.

Provides hierarchical exception types for HD wallet operations following
SSeed's exception patterns and design principles.
"""

from typing import (
    Any,
    List,
    Optional,
)

from sseed.exceptions import SseedError


class HDWalletError(SseedError):
    """Base exception for HD wallet operations.

    Inherits from SseedError to maintain consistency with existing
    SSeed exception hierarchy.
    """

    def __init__(
        self,
        message: str,
        coin: str = "",
        operation: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize HD wallet error.

        Args:
            message: Error message.
            coin: Cryptocurrency name (if applicable).
            operation: Operation that failed (if applicable).
            context: Additional context information.
        """
        super().__init__(message, context)
        self.coin = coin
        self.operation = operation


class DerivationError(HDWalletError):
    """Address derivation failed.

    Raised when BIP32 key derivation or address generation fails.
    """

    def __init__(
        self,
        message: str,
        derivation_path: str = "",
        operation: str = "",
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize derivation error.

        Args:
            message: Error message.
            derivation_path: BIP32 derivation path that failed.
            operation: Specific operation that failed.
            context: Additional context information.
            original_error: Original exception that caused this error.
        """
        super().__init__(message, operation=operation, context=context)
        self.derivation_path = derivation_path
        self.original_error = original_error


class UnsupportedCoinError(HDWalletError):
    """Cryptocurrency not supported.

    Raised when attempting operations on unsupported cryptocurrencies
    or invalid coin configurations.
    """

    def __init__(
        self,
        message: str,
        coin: str = "",
        address_type: str = "",
        supported_coins: Optional[List[str]] = None,
        supported_types: Optional[List[str]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize unsupported coin error.

        Args:
            message: Error message.
            coin: Unsupported cryptocurrency name.
            address_type: Unsupported address type (if applicable).
            supported_coins: List of supported cryptocurrencies.
            supported_types: List of supported address types.
            context: Additional context information.
        """
        super().__init__(message, coin=coin, context=context)
        self.address_type = address_type
        self.supported_coins = supported_coins or []
        self.supported_types = supported_types or []


class InvalidPathError(HDWalletError):
    """Invalid derivation path.

    Raised when BIP32 derivation path format is invalid or
    contains invalid components.
    """

    def __init__(
        self,
        message: str,
        path: str = "",
        parameter: str = "",
        value: Any = None,
        valid_range: str = "",
        pattern: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize invalid path error.

        Args:
            message: Error message.
            path: Invalid derivation path.
            parameter: Invalid parameter name.
            value: Invalid parameter value.
            valid_range: Valid range description.
            pattern: Expected path pattern.
            context: Additional context information.
        """
        super().__init__(message, context=context)
        self.path = path
        self.parameter = parameter
        self.value = value
        self.valid_range = valid_range
        self.pattern = pattern


class AddressGenerationError(HDWalletError):
    """Address generation failed.

    Raised when cryptocurrency address generation fails due to
    invalid keys, unsupported formats, or other issues.
    """

    def __init__(
        self,
        message: str,
        coin: str = "",
        address_type: str = "",
        derivation_path: str = "",
        count: int = 0,
        operation: str = "",
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize address generation error.

        Args:
            message: Error message.
            coin: Cryptocurrency name.
            address_type: Address type being generated.
            derivation_path: Derivation path being used.
            count: Number of addresses being generated.
            operation: Specific operation that failed.
            context: Additional context information.
            original_error: Original exception that caused this error.
        """
        super().__init__(message, coin=coin, operation=operation, context=context)
        self.address_type = address_type
        self.derivation_path = derivation_path
        self.count = count
        self.original_error = original_error


class ExtendedKeyError(HDWalletError):
    """Extended key operation failed.

    Raised when xpub/xprv generation, parsing, or export fails.
    """

    def __init__(
        self,
        message: str,
        key_type: str = "",
        coin: str = "",
        account: int = 0,
        operation: str = "",
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize extended key error.

        Args:
            message: Error message.
            key_type: Type of extended key (xpub/xprv).
            coin: Cryptocurrency name.
            account: Account number.
            operation: Specific operation that failed.
            context: Additional context information.
            original_error: Original exception that caused this error.
        """
        super().__init__(message, coin=coin, operation=operation, context=context)
        self.key_type = key_type
        self.account = account
        self.original_error = original_error
