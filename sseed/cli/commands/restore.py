"""Restore command implementation.
# pylint: disable=too-many-locals,import-outside-toplevel

Restores mnemonics from SLIP-39 shards with automatic language detection.
"""

import argparse

from sseed.entropy import secure_delete_variable
from sseed.exceptions import MnemonicError
from sseed.languages import detect_mnemonic_language
from sseed.logging_config import get_logger
from sseed.slip39_operations import reconstruct_mnemonic_from_shards
from sseed.validation import validate_mnemonic_checksum

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit code locally to avoid circular import
EXIT_SUCCESS = 0

logger = get_logger(__name__)


class RestoreCommand(BaseCommand):
    """Reconstruct mnemonic from a valid set of SLIP-39 shards with automatic language detection."""

    def __init__(self) -> None:
        super().__init__(
            name="restore",
            help_text="Reconstruct mnemonic from a valid set of SLIP-39 shards",
            description=(
                "Reconstruct the original mnemonic from SLIP-39 shards "
                "using Shamir's Secret Sharing. Automatically detects "
                "the mnemonic language."
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
        """Handle the 'restore' command with automatic language detection.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting mnemonic restoration from %d shards", len(args.shards))

        try:
            # Read shards from files
            shards = []
            for shard_file in args.shards:
                try:
                    with open(shard_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        # Extract actual shard lines (ignore comments)
                        shard_lines = [
                            line.strip()
                            for line in content.split("\n")
                            if line.strip() and not line.strip().startswith("#")
                        ]
                        shards.extend(shard_lines)
                except Exception as e:
                    raise MnemonicError(
                        f"Failed to read shard file {shard_file}: {e}",
                        context={"file": shard_file, "error": str(e)},
                    ) from e

            logger.info("Read %d shards from %d files", len(shards), len(args.shards))

            # Reconstruct mnemonic from shards using SLIP-39
            reconstructed_mnemonic = reconstruct_mnemonic_from_shards(shards)

            # Auto-detect language of reconstructed mnemonic
            detected_lang = detect_mnemonic_language(reconstructed_mnemonic)
            if detected_lang:
                logger.info(
                    "Detected mnemonic language: %s (%s)",
                    detected_lang.name,
                    detected_lang.code,
                )
                language_display = (
                    f"Language: {detected_lang.name} ({detected_lang.code})"
                )

                # Validate with detected language
                if not validate_mnemonic_checksum(
                    reconstructed_mnemonic, detected_lang.bip_enum
                ):
                    logger.warning(
                        "Checksum validation failed for detected language %s",
                        detected_lang.name,
                    )
                    # Fall back to general validation
                    if not validate_mnemonic_checksum(reconstructed_mnemonic):
                        raise MnemonicError(
                            "Reconstructed mnemonic failed checksum validation",
                            context={"validation_type": "checksum"},
                        )
                else:
                    logger.info("Checksum validation passed for %s", detected_lang.name)
            else:
                logger.warning("Could not detect mnemonic language, assuming English")
                language_display = "Language: English (en) - assumed"

                # Validate with default (English) validation
                if not validate_mnemonic_checksum(reconstructed_mnemonic):
                    raise MnemonicError(
                        "Reconstructed mnemonic failed checksum validation",
                        context={"validation_type": "checksum"},
                    )

            # Handle entropy display if requested
            entropy_info = self.handle_entropy_display(
                reconstructed_mnemonic, args, args.output
            )

            # Output reconstructed mnemonic with language information
            if args.output:
                # Create custom content that includes language info in the header
                import datetime

                from sseed.file_operations.formatters import format_file_with_comments

                # Generate custom header with language information
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                header_lines = [
                    "# BIP-39 Mnemonic File",
                    f"# Generated by sseed on {timestamp}",
                    "#",
                    "# This file contains a BIP-39 mnemonic for cryptocurrency wallet recovery.",
                    "# Keep this file extremely secure and consider splitting into SLIP-39 shards.",
                    "# Anyone with access to this mnemonic can access your funds.",
                    "#",
                    "# File format: Plain text UTF-8",
                    "# Lines starting with '#' are comments and will be ignored.",
                    "#",
                    f"# {language_display}",
                ]

                # Format the content with the custom header
                output_content = format_file_with_comments(
                    reconstructed_mnemonic, header_lines
                )

                # Write directly to file instead of using handle_output to avoid double headers
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output_content)

                # Display entropy info if showing entropy
                if entropy_info:
                    print(
                        f"Mnemonic with language info and entropy reconstructed "
                        f"and written to: {args.output}"
                    )
                else:
                    print(
                        f"Mnemonic with language info reconstructed and written to: {args.output}"
                    )
            else:
                # Output to stdout
                print(reconstructed_mnemonic)
                print(f"# {language_display}")
                if entropy_info:
                    print(entropy_info)
                logger.info(
                    "Reconstructed mnemonic written to stdout with language info"
                )

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
