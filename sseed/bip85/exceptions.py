"""BIP85-specific exception classes.

Provides specialized exception handling for BIP85 operations, following
SSeed's existing exception patterns and providing detailed error context.
"""

from typing import (
    Any,
    Dict,
    Optional,
)

from sseed.exceptions import SseedError


class Bip85Error(SseedError):
    """Base exception for all BIP85-related errors.

    Inherits from SseedError to maintain consistency with existing
    SSeed exception hierarchy and error handling patterns.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize BIP85 error.

        Args:
            message: Human-readable error description.
            context: Additional error context for debugging.
            original_error: Original exception that caused this error.
        """
        super().__init__(message, context)
        self.original_error = original_error


class Bip85ValidationError(Bip85Error):
    """Exception raised for BIP85 parameter validation errors.

    Raised when BIP85 derivation parameters are invalid, such as:
    - Invalid application codes
    - Out-of-range length parameters
    - Invalid derivation indices
    - Malformed derivation paths
    """

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        value: Optional[Any] = None,
        valid_range: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error with parameter details.

        Args:
            message: Error description.
            parameter: Name of the invalid parameter.
            value: Invalid value that was provided.
            valid_range: Description of valid parameter range.
            context: Additional error context.
        """
        # Build enhanced context
        error_context = context or {}
        if parameter:
            error_context["parameter"] = parameter
        if value is not None:
            error_context["invalid_value"] = value
        if valid_range:
            error_context["valid_range"] = valid_range

        super().__init__(message, error_context)
        self.parameter = parameter
        self.value = value
        self.valid_range = valid_range


class Bip85DerivationError(Bip85Error):
    """Exception raised for BIP85 key derivation failures.

    Raised when BIP85 cryptographic operations fail, such as:
    - BIP32 key derivation failures
    - HMAC-SHA512 computation errors
    - Invalid master seed format
    - Cryptographic library errors
    """

    def __init__(
        self,
        message: str,
        derivation_path: Optional[str] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize derivation error with operation details.

        Args:
            message: Error description.
            derivation_path: BIP85 derivation path that failed.
            operation: Specific operation that failed.
            context: Additional error context.
            original_error: Original cryptographic exception.
        """
        # Build enhanced context
        error_context = context or {}
        if derivation_path:
            error_context["derivation_path"] = derivation_path
        if operation:
            error_context["failed_operation"] = operation
        if original_error:
            error_context["original_error"] = str(original_error)

        super().__init__(message, error_context, original_error)
        self.derivation_path = derivation_path
        self.operation = operation


class Bip85ApplicationError(Bip85Error):
    """Exception raised for BIP85 application-specific errors.

    Raised when application formatters encounter errors, such as:
    - Invalid entropy length for BIP39 word counts
    - Unsupported language codes
    - Invalid password length parameters
    - Format conversion failures
    """

    def __init__(
        self,
        message: str,
        application: Optional[str] = None,
        entropy_length: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize application error with format details.

        Args:
            message: Error description.
            application: Application type that failed.
            entropy_length: Entropy length that caused the error.
            context: Additional error context.
            original_error: Original formatting exception.
        """
        # Build enhanced context
        error_context = context or {}
        if application:
            error_context["application"] = application
        if entropy_length is not None:
            error_context["entropy_length"] = entropy_length

        super().__init__(message, error_context, original_error)
        self.application = application
        self.entropy_length = entropy_length
