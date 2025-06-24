"""CLI package initialization for modular command architecture.

Provides exit codes and backward compatibility imports.
"""

from .commands import (
    handle_gen_command,
    handle_restore_command,
    handle_seed_command,
    handle_shard_command,
    handle_version_command,
)
from .examples import show_examples
from .parser import (
    create_parser,
    parse_args,
)

# Exit codes
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130  # Standard exit code for SIGINT

# Re-export everything for backward compatibility
__all__ = [
    # Exit codes
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR",
    "EXIT_CRYPTO_ERROR",
    "EXIT_FILE_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_INTERRUPTED",
    # Command handlers (backward compatibility)
    "handle_gen_command",
    "handle_shard_command",
    "handle_restore_command",
    "handle_seed_command",
    "handle_version_command",
    # Parser functions (backward compatibility)
    "create_parser",
    "parse_args",
    "show_examples",
]
