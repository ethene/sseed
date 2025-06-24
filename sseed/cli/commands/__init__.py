"""Command registry for CLI commands.

Provides command discovery and registration system for modular CLI architecture.
"""

from typing import (
    Dict,
    Type,
)

from ..base import BaseCommand

# Import all command classes
from .gen import GenCommand
from .restore import RestoreCommand
from .seed import SeedCommand
from .shard import ShardCommand
from .version import VersionCommand

# Command registry - maps command names to command classes
COMMANDS: Dict[str, Type[BaseCommand]] = {
    "gen": GenCommand,
    "shard": ShardCommand,
    "restore": RestoreCommand,
    "seed": SeedCommand,
    "version": VersionCommand,
}

# Backward compatibility exports
from .gen import handle_gen_command
from .restore import handle_restore_command
from .seed import handle_seed_command
from .shard import handle_shard_command
from .version import handle_version_command

__all__ = [
    "COMMANDS",
    "BaseCommand",
    "GenCommand",
    "ShardCommand",
    "RestoreCommand",
    "SeedCommand",
    "VersionCommand",
    # Backward compatibility
    "handle_gen_command",
    "handle_shard_command",
    "handle_restore_command",
    "handle_seed_command",
    "handle_version_command",
]
