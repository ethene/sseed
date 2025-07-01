"""Error handling decorators and utilities for CLI commands.

Provides standardized error handling patterns for all CLI operations.
"""

import sys
from functools import wraps
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

# Define exit codes locally to avoid circular imports
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130

logger = get_logger(__name__)


def handle_common_errors(
    operation_name: str,
) -> Callable[[Callable[..., int]], Callable[..., int]]:
    """Decorator for standardized error handling across all commands.

    Args:
        operation_name: Name of the operation for logging (e.g., "generation", "sharding")

    Returns:
        Decorator function that wraps command handlers with error handling.
    """

    def decorator(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> int:
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
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Unexpected error during %s: %s", operation_name, e)
                print(f"Unexpected error: {e}", file=sys.stderr)
                return EXIT_CRYPTO_ERROR

        return wrapper

    return decorator


def handle_top_level_errors(func: Callable[..., int]) -> Callable[..., int]:
    """Decorator for top-level error handling in main function.

    Handles KeyboardInterrupt and other top-level exceptions.
    """

    @wraps(func)
    def wrapper(  # pylint: disable=too-many-return-statements
        *args: Any, **kwargs: Any
    ) -> int:
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
        except (MnemonicError, SecurityError) as e:
            logger.error("Cryptographic error: %s", e)
            print(f"Cryptographic error: {e}", file=sys.stderr)
            return EXIT_CRYPTO_ERROR
        except SseedError as e:
            # Handle any other sseed-specific errors
            logger.error("sseed error: %s", e)
            print(f"Error: {e}", file=sys.stderr)
            return EXIT_USAGE_ERROR
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Unexpected error: %s", e)
            print(f"Unexpected error: {e}", file=sys.stderr)
            return EXIT_CRYPTO_ERROR

    return wrapper
