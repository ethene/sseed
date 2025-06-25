"""Custom exception classes for sseed application.

Provides specific exception types for different error conditions as specified
in the user rules for comprehensive error handling.
"""

from typing import Any


class SseedError(Exception):
    """Base exception class for all sseed-related errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            context: Additional context information.
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


class EntropyError(SseedError):
    """Exception raised when entropy generation fails."""


class CryptoError(SseedError):
    """Exception raised for cryptographic operation failures."""


class MnemonicError(SseedError):
    """Exception raised for mnemonic-related errors."""


class ValidationError(SseedError):
    """Exception raised for input validation failures."""


class FileError(SseedError):
    """Exception raised for file I/O operations."""


class ShardError(SseedError):
    """Exception raised for SLIP-39 shard operations."""


class SecurityError(SseedError):
    """Exception raised for security-related issues."""
