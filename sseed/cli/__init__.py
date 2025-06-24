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

# Import core functions that tests expect to mock
# These need to be imported to this level for backward compatibility
from sseed.bip39 import generate_mnemonic
from sseed.file_operations import (
    read_from_stdin,
    read_mnemonic_from_file,
    read_shards_from_files,
    write_mnemonic_to_file,
    write_shards_to_file,
    write_shards_to_separate_files,
)
from sseed.slip39_operations import (
    create_slip39_shards,
    parse_group_config,
    reconstruct_mnemonic_from_shards,
)
from sseed.validation import (
    validate_group_threshold,
    validate_mnemonic_checksum,
    validate_shard_integrity,
)

# Backward compatibility exports for tests and existing code
from .commands import (
    handle_gen_command,
    handle_restore_command,
    handle_seed_command,
    handle_shard_command,
    handle_version_command,
)
from .examples import show_examples

# Main entry point
from .main import main

# Parser functions for backward compatibility
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
    # Backward compatibility command handlers
    "handle_gen_command",
    "handle_shard_command",
    "handle_restore_command",
    "handle_seed_command",
    "handle_version_command",
    # Parser functions
    "create_parser",
    "parse_args",
    "show_examples",
    # Core functions for test mocking
    "generate_mnemonic",
    "validate_mnemonic_checksum",
    "validate_group_threshold",
    "validate_shard_integrity",
    "read_mnemonic_from_file",
    "write_mnemonic_to_file",
    "read_from_stdin",
    "read_shards_from_files",
    "write_shards_to_file",
    "write_shards_to_separate_files",
    "parse_group_config",
    "create_slip39_shards",
    "reconstruct_mnemonic_from_shards",
]
