"""CLI package with lazy loading for better performance."""

# pylint: disable=import-outside-toplevel

import argparse
from typing import (
    Any,
    Optional,
)

# Exit codes
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130  # Standard exit code for SIGINT


# Lazy loading functions for backward compatibility
def handle_gen_command(args: Any) -> int:
    """Lazy wrapper for gen command handler."""
    from .commands import (
        handle_gen_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_shard_command(args: Any) -> int:
    """Lazy wrapper for shard command handler."""
    from .commands import (
        handle_shard_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_restore_command(args: Any) -> int:
    """Lazy wrapper for restore command handler."""
    from .commands import (
        handle_restore_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_seed_command(args: Any) -> int:
    """Lazy wrapper for seed command handler."""
    from .commands import (
        handle_seed_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_version_command(args: Any) -> int:
    """Lazy wrapper for version command handler."""
    from .commands import (
        handle_version_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def show_examples(args: Any) -> int:
    """Lazy wrapper for examples function."""
    from .examples import (
        show_examples as _show_examples,  # pylint: disable=import-outside-toplevel
    )

    return _show_examples(args)


def create_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Lazy wrapper for parser creation."""
    from .parser import (
        create_parser as _create_parser,  # pylint: disable=import-outside-toplevel
    )

    return _create_parser(prog)


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Lazy wrapper for argument parsing."""
    from .parser import (
        parse_args as _parse_args,  # pylint: disable=import-outside-toplevel
    )

    return _parse_args(args)


# Export constants and functions
__all__ = [
    # Exit codes
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR",
    "EXIT_CRYPTO_ERROR",
    "EXIT_FILE_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_INTERRUPTED",
    # Command handlers
    "handle_gen_command",
    "handle_shard_command",
    "handle_restore_command",
    "handle_seed_command",
    "handle_version_command",
    # Parser functions (backward compatibility)
    "create_parser",
    "parse_args",
    # Examples
    "show_examples",
]
