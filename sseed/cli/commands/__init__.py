"""Command registry for CLI commands.

Provides command discovery and registration system for modular CLI architecture.
Implements lazy loading to improve CLI startup performance.
"""

# pylint: disable=import-outside-toplevel

from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Tuple,
    Type,
)

from ..base import BaseCommand


def _lazy_load_gen_command() -> Type[BaseCommand]:
    """Lazy load GenCommand."""
    from .gen import GenCommand  # pylint: disable=import-outside-toplevel

    return GenCommand


def _lazy_load_shard_command() -> Type[BaseCommand]:
    """Lazy load ShardCommand."""
    from .shard import ShardCommand  # pylint: disable=import-outside-toplevel

    return ShardCommand


def _lazy_load_restore_command() -> Type[BaseCommand]:
    """Lazy load RestoreCommand."""
    from .restore import RestoreCommand  # pylint: disable=import-outside-toplevel

    return RestoreCommand


def _lazy_load_seed_command() -> Type[BaseCommand]:
    """Lazy load SeedCommand."""
    from .seed import SeedCommand  # pylint: disable=import-outside-toplevel

    return SeedCommand


def _lazy_load_version_command() -> Type[BaseCommand]:
    """Lazy load VersionCommand."""
    # pylint: disable=import-outside-toplevel
    from .version import VersionCommand

    return VersionCommand


def _lazy_load_bip85_command() -> Type[BaseCommand]:
    """Lazy load Bip85Command."""
    from .bip85 import Bip85Command  # pylint: disable=import-outside-toplevel

    return Bip85Command


def _lazy_load_validate_command() -> Type[BaseCommand]:
    """Lazy load ValidateCommand."""
    from .validate import ValidateCommand  # pylint: disable=import-outside-toplevel

    return ValidateCommand


# Command registry with lazy loaders - maps command names to loader functions
_COMMAND_LOADERS: Dict[str, Callable[[], Type[BaseCommand]]] = {
    "gen": _lazy_load_gen_command,
    "shard": _lazy_load_shard_command,
    "restore": _lazy_load_restore_command,
    "seed": _lazy_load_seed_command,
    "version": _lazy_load_version_command,
    "bip85": _lazy_load_bip85_command,
    "validate": _lazy_load_validate_command,
}

# Cache for loaded commands to avoid repeated imports
_LOADED_COMMANDS: Dict[str, Type[BaseCommand]] = {}


class LazyCommandRegistry:
    """Lazy command registry that loads commands only when needed."""

    def __init__(self) -> None:
        """Initialize the command registry."""
        self._commands: Dict[str, Any] = {}
        self._loaders = {
            "gen": self._load_gen_command,
            "shard": self._load_shard_command,
            "restore": self._load_restore_command,
            "seed": self._load_seed_command,
            "version": self._load_version_command,
            "bip85": self._load_bip85_command,
            "validate": self._load_validate_command,
        }

    def __getitem__(self, name: str) -> Any:
        """Get a command class by name with lazy loading."""
        if name not in self._commands:
            if name in self._loaders:
                self._commands[name] = self._loaders[name]()
            else:
                raise KeyError(f"Unknown command: {name}")
        return self._commands[name]

    def __contains__(self, name: str) -> bool:
        """Check if a command exists."""
        return name in self._loaders

    def keys(self) -> List[str]:
        """Get available command names."""
        return list(self._loaders.keys())

    def items(self) -> Iterator[Tuple[str, Any]]:
        """Iterate over command name-class pairs."""
        for name in self._loaders:
            yield name, self[name]

    def _load_gen_command(self) -> Any:
        """Load the gen command class."""
        from .gen import GenCommand  # pylint: disable=import-outside-toplevel

        return GenCommand

    def _load_shard_command(self) -> Any:
        """Load the shard command class."""
        from .shard import ShardCommand  # pylint: disable=import-outside-toplevel

        return ShardCommand

    def _load_restore_command(self) -> Any:
        """Load the restore command class."""
        from .restore import RestoreCommand  # pylint: disable=import-outside-toplevel

        return RestoreCommand

    def _load_seed_command(self) -> Any:
        """Load the seed command class."""
        from .seed import SeedCommand  # pylint: disable=import-outside-toplevel

        return SeedCommand

    def _load_version_command(self) -> Any:
        """Load the version command class."""
        from .version import VersionCommand  # pylint: disable=import-outside-toplevel

        return VersionCommand

    def _load_bip85_command(self) -> Any:
        """Load the bip85 command class."""
        from .bip85 import Bip85Command  # pylint: disable=import-outside-toplevel

        return Bip85Command

    def _load_validate_command(self) -> Any:
        """Load the validate command class."""
        from .validate import ValidateCommand  # pylint: disable=import-outside-toplevel

        return ValidateCommand


# Global command registry instance
COMMANDS = LazyCommandRegistry()


# Lazy loading command handlers
def handle_gen_command(args: Any) -> int:
    """Lazy wrapper for gen command handler."""
    from .gen import (
        handle_gen_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_shard_command(args: Any) -> int:
    """Lazy wrapper for shard command handler."""
    from .shard import (
        handle_shard_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_restore_command(args: Any) -> int:
    """Lazy wrapper for restore command handler."""
    from .restore import (
        handle_restore_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_seed_command(args: Any) -> int:
    """Lazy wrapper for seed command handler."""
    from .seed import (
        handle_seed_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_version_command(args: Any) -> int:
    """Lazy wrapper for version command handler."""
    from .version import (
        handle_version_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_bip85_command(args: Any) -> int:
    """Lazy wrapper for bip85 command handler."""
    from .bip85 import (
        handle_bip85_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


def handle_validate_command(args: Any) -> int:
    """Lazy wrapper for validate command handler."""
    from .validate import (
        handle_validate_command as _handler,  # pylint: disable=import-outside-toplevel
    )

    return _handler(args)


# Backward compatibility - lazy class access
def __getattr__(name: str) -> Any:
    """Support for direct class imports with lazy loading."""
    if name in COMMANDS:
        return COMMANDS[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export registry and handlers for backward compatibility
__all__ = [
    "COMMANDS",
    "handle_gen_command",
    "handle_shard_command",
    "handle_restore_command",
    "handle_seed_command",
    "handle_version_command",
    "handle_bip85_command",
    "handle_validate_command",
    # Note: Command classes are available via __getattr__ for lazy loading
    # "GenCommand", "ShardCommand", "RestoreCommand", "SeedCommand",
    # "VersionCommand", "Bip85Command"
]
