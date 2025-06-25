"""Argument parser creation for CLI.

Creates the main argument parser and subparsers for all commands.
"""

import argparse
import sys
from typing import (
    List,
    NoReturn,
    Optional,
)

from sseed import __version__

from .base import BaseCommand
from .commands import COMMANDS
from .examples import show_examples

# Define exit code locally to avoid circular import
EXIT_USAGE_ERROR = 1


class SSeedArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that uses SSeed exit codes."""

    def error(self, message: str) -> NoReturn:
        """Override error method to use our exit code."""
        self.print_usage(sys.stderr)
        args = {"prog": self.prog, "message": message}
        self.exit(EXIT_USAGE_ERROR, "%(prog)s: error: %(message)s\n" % args)


def create_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Create the main argument parser.

    Args:
        prog: Program name override (default: None uses sys.argv[0]).

    Returns:
        Configured ArgumentParser instance.
    """
    parser = SSeedArgumentParser(
        prog=prog or "sseed",
        description=(
            "🔐 SSeed: Professional BIP-39/SLIP-39 mnemonic toolkit. "
            "Generate, shard, and restore cryptographic mnemonics with enterprise-grade security."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sseed gen -o wallet.txt                    Generate new mnemonic
  sseed shard -i wallet.txt -g 3-of-5       Create threshold shards
  sseed restore shard*.txt                   Reconstruct from shards
  sseed examples                             Show comprehensive examples

For detailed command help: sseed <command> --help
Repository: https://github.com/ethene/sseed
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )

    # Add global logging argument that tests expect
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    # Create subparser for commands
    subparsers = parser.add_subparsers(
        dest="command",
        title="Commands",
        description="Available commands for mnemonic operations",
        help="Run 'sseed <command> --help' for detailed help",
        metavar="<command>",
    )

    # Add special 'examples' command
    examples_parser = subparsers.add_parser(
        "examples",
        help="Show comprehensive usage examples",
        description="Display detailed usage examples for all commands",
        parents=[],  # Use SSeedArgumentParser for subparsers too
    )
    examples_parser.set_defaults(func=show_examples)

    # Add all registered commands
    for command_name, command_class in COMMANDS.items():
        command_instance: BaseCommand = command_class()

        # Create subparser for this command using our custom parser class
        cmd_parser = subparsers.add_parser(
            command_name,
            help=command_instance.help_text,
            description=command_instance.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add command-specific arguments
        command_instance.add_arguments(cmd_parser)

        # Set the command handler function
        cmd_parser.set_defaults(func=command_instance.handle)

    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Arguments to parse (default: None uses sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = create_parser()

    # Parse arguments
    if args is None:
        args = sys.argv[1:]

    parsed_args = parser.parse_args(args)

    # Handle case where no command was specified
    if not hasattr(parsed_args, "func"):
        parser.print_help()
        sys.exit(EXIT_USAGE_ERROR)

    return parsed_args
