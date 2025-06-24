"""CLI package for sseed application.

Provides command-line interface with modular command architecture.
Maintains backward compatibility with the original monolithic CLI.
"""

# Exit codes (moved from cli.py)
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130  # Standard exit code for SIGINT

# Core imports for backward compatibility - import at module level to avoid cycles
from . import (
    commands,
    examples,
    parser,
)

# Expose command handlers for backward compatibility
from .commands import (
    handle_gen_command,
    handle_restore_command,
    handle_seed_command,
    handle_shard_command,
    handle_version_command,
)

# Parser functions for backward compatibility
from .examples import show_examples

# Main entry point
from .main import main
from .parser import (
    create_parser,
    parse_args,
)

__all__ = [
    "main",
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR",
    "EXIT_CRYPTO_ERROR",
    "EXIT_FILE_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_INTERRUPTED",
    "handle_gen_command",
    "handle_shard_command",
    "handle_restore_command",
    "handle_seed_command",
    "handle_version_command",
    "create_parser",
    "parse_args",
    "show_examples",
]
