"""Restore command implementation.

Reconstructs BIP-39 mnemonics from SLIP-39 shards.
"""

import argparse

from sseed.entropy import secure_delete_variable
from sseed.file_operations import read_shards_from_files
from sseed.logging_config import get_logger
from sseed.slip39_operations import reconstruct_mnemonic_from_shards
from sseed.validation import validate_shard_integrity

from .. import EXIT_SUCCESS
from ..base import BaseCommand
from ..error_handling import handle_common_errors

logger = get_logger(__name__)


class RestoreCommand(BaseCommand):
    """Reconstruct mnemonic from a valid set of SLIP-39 shards."""

    def __init__(self):
        super().__init__(
            name="restore",
            help_text="Reconstruct mnemonic from a valid set of SLIP-39 shards",
            description=(
                "Reconstruct the original mnemonic from SLIP-39 shards "
                "using Shamir's Secret Sharing."
            ),
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add restore command arguments."""
        parser.add_argument(
            "shards",
            nargs="+",
            metavar="SHARD_FILE",
            help="Shard files to use for reconstruction",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            metavar="FILE",
            help="Output file for reconstructed mnemonic (default: stdout)",
        )
        self.add_entropy_display_argument(parser)

        # Add epilog with examples
        parser.epilog = """
Examples:
  sseed restore shard1.txt shard2.txt shard3.txt       From specific files
  sseed restore shard*.txt                             Using shell glob
  sseed restore /backup/location/shard_*.txt           Full paths
        """

    @handle_common_errors("restoration")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the 'restore' command.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting mnemonic restoration from %d shards", len(args.shards))

        try:
            # Read shards from files (Phase 5 requirement)
            shards = read_shards_from_files(args.shards)

            # Validate shard integrity (Phase 5 requirement)
            validate_shard_integrity(shards)

            # Reconstruct mnemonic from shards
            reconstructed_mnemonic = reconstruct_mnemonic_from_shards(shards)

            # Handle entropy display if requested
            entropy_info = self.handle_entropy_display(
                reconstructed_mnemonic, args, args.output
            )

            # Output reconstructed mnemonic
            if args.output:
                self.handle_output(
                    reconstructed_mnemonic,
                    args,
                    success_message="Mnemonic reconstructed and written to: {file}",
                )

                # Display entropy info if showing entropy
                if entropy_info:
                    print(
                        f"Mnemonic and entropy reconstructed and written to: {args.output}"
                    )
            else:
                # Output to stdout
                print(reconstructed_mnemonic)
                if entropy_info:
                    print(entropy_info)
                logger.info("Reconstructed mnemonic written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete shards, mnemonic, and entropy from memory
            secure_delete_variable(
                shards if "shards" in locals() else [],
                reconstructed_mnemonic if "reconstructed_mnemonic" in locals() else "",
            )


# Backward compatibility wrapper
def handle_restore_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for original handle_restore_command."""
    return RestoreCommand().handle(args)
