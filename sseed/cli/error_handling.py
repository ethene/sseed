"""Standardized error handling for CLI commands.

Provides decorators and utilities to eliminate error handling duplication
across command handlers.
"""

import functools
import sys
from typing import (
    Any,
    Callable,
)

from sseed.exceptions import (
    EntropyError,
    FileError,
    MnemonicError,
    SecurityError,
    ShardError,
    SseedError,
    ValidationError,
)
from sseed.logging_config import get_logger

from . import (
    EXIT_CRYPTO_ERROR,
    EXIT_FILE_ERROR,
    EXIT_INTERRUPTED,
    EXIT_USAGE_ERROR,
    EXIT_VALIDATION_ERROR,
)

logger = get_logger(__name__)


def handle_common_errors(operation_name: str) -> Callable:
    """Decorator for standardized error handling across all commands.

    Args:
        operation_name: Name of the operation for logging (e.g., "generation", "sharding")

    Returns:
        Decorator function that wraps command handlers with error handling.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> int:
            try:
                return func(*args, **kwargs)
            except (EntropyError, MnemonicError, SecurityError, ShardError) as e:
                logger.error("Cryptographic error during %s: %s", operation_name, e)
                print(f"Cryptographic error: {e}", file=sys.stderr)
                return EXIT_CRYPTO_ERROR
            except FileError as e:
                logger.error("File I/O error during %s: %s", operation_name, e)
                print(f"File error: {e}", file=sys.stderr)
                return EXIT_FILE_ERROR
            except ValidationError as e:
                logger.error("Validation error during %s: %s", operation_name, e)
                print(f"Validation error: {e}", file=sys.stderr)
                return EXIT_VALIDATION_ERROR
            except Exception as e:
                logger.error("Unexpected error during %s: %s", operation_name, e)
                print(f"Unexpected error: {e}", file=sys.stderr)
                return EXIT_CRYPTO_ERROR

        return wrapper

    return decorator


def handle_top_level_errors(func: Callable) -> Callable:
    """Decorator for top-level error handling in main function.

    Handles KeyboardInterrupt and other top-level exceptions.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> int:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user (SIGINT)")
            print("\nOperation cancelled by user", file=sys.stderr)
            return EXIT_INTERRUPTED
        except FileError as e:
            logger.error("File I/O error: %s", e)
            print(f"File error: {e}", file=sys.stderr)
            return EXIT_FILE_ERROR
        except ValidationError as e:
            logger.error("Validation error: %s", e)
            print(f"Validation error: {e}", file=sys.stderr)
            return EXIT_VALIDATION_ERROR
        except (MnemonicError, ShardError, SecurityError, EntropyError) as e:
            logger.error("Cryptographic error: %s", e)
            print(f"Cryptographic error: {e}", file=sys.stderr)
            return EXIT_CRYPTO_ERROR
        except SseedError as e:
            # Handle any other sseed-specific errors
            logger.error("sseed error: %s", e)
            print(f"Error: {e}", file=sys.stderr)
            return EXIT_USAGE_ERROR
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            print(f"Unexpected error: {e}", file=sys.stderr)
            return EXIT_CRYPTO_ERROR

    return wrapper
