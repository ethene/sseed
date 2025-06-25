"""File I/O operations for sseed application.

Provides comprehensive file operations with UTF-8 encoding, comment support,
and secure file handling for BIP39/SLIP39 operations.

This module maintains backward compatibility while providing modular architecture.
All original function imports continue to work identically.
"""

# Import all public functions to maintain backward compatibility
from .readers import (
    read_from_stdin,
    read_mnemonic_from_file,
    read_shard_from_file,
    read_shards_from_files,
)
from .writers import (
    write_mnemonic_to_file,
    write_shards_to_file,
    write_shards_to_separate_files,
    write_to_stdout,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Reading operations
    "read_mnemonic_from_file",
    "read_shard_from_file",
    "read_shards_from_files",
    "read_from_stdin",
    # Writing operations
    "write_mnemonic_to_file",
    "write_shards_to_file",
    "write_shards_to_separate_files",
    "write_to_stdout",
]
