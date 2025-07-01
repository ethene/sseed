"""Shard command implementation.
# pylint: disable=too-many-branches

Splits BIP-39 mnemonics into SLIP-39 threshold shards with automatic language detection.
"""

import argparse
import sys

from sseed.entropy import secure_delete_variable
from sseed.exceptions import MnemonicError
from sseed.file_operations import (
    write_shards_to_file,
    write_shards_to_separate_files,
)
from sseed.languages import detect_mnemonic_language
from sseed.logging_config import get_logger
from sseed.slip39_operations import (
    create_slip39_shards,
    parse_group_config,
)
from sseed.validation import (
    validate_group_threshold,
    validate_mnemonic_checksum,
)

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit code locally to avoid circular import
EXIT_SUCCESS = 0

logger = get_logger(__name__)


class ShardCommand(BaseCommand):
    """Split mnemonic into SLIP-39 shards with group/threshold config and language detection."""

    def __init__(self) -> None:
        super().__init__(
            name="shard",
            help_text="Split mnemonic into SLIP-39 shards with group/threshold configuration",
            description=(
                "Split a BIP-39 mnemonic into SLIP-39 threshold shards "
                "for secure distribution. Automatically detects and "
                "preserves the mnemonic language."
            ),
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add shard command arguments."""
        self.add_common_io_arguments(parser)

        parser.add_argument(
            "-g",
            "--group",
            type=str,
            default="3-of-5",
            metavar="CONFIG",
            help=(
                "Group threshold configuration (default: 3-of-5). "
                "Examples: '3-of-5', '2:(2-of-3,3-of-5)'"
            ),
        )
        parser.add_argument(
            "--separate",
            action="store_true",
            help=(
                "Write each shard to a separate file "
                "(e.g., shards_01.txt, shards_02.txt)"
            ),
        )

        # Add epilog with examples
        parser.epilog = """
Examples:
  sseed shard -i seed.txt -g 3-of-5                    Simple threshold
  sseed shard -g "2:(2-of-3,3-of-5)" --separate       Multi-group setup
  echo "mnemonic words..." | sseed shard -g 2-of-3     From stdin
        """

    @handle_common_errors("sharding")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the 'shard' command with automatic language detection.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting mnemonic sharding with group: %s", args.group)

        try:
            # Validate group configuration first (Phase 5 requirement)
            validate_group_threshold(args.group)

            # Read mnemonic from input source
            mnemonic = self.handle_input(args)

            # Auto-detect language of input mnemonic
            detected_lang = detect_mnemonic_language(mnemonic)
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
                if not validate_mnemonic_checksum(mnemonic, detected_lang.bip_enum):
                    logger.warning(
                        "Checksum validation failed for detected language %s",
                        detected_lang.name,
                    )
                    # Fall back to general validation
                    if not validate_mnemonic_checksum(mnemonic):
                        raise MnemonicError(
                            "Input mnemonic failed checksum validation",
                            context={"validation_type": "checksum"},
                        )
                else:
                    logger.info("Checksum validation passed for %s", detected_lang.name)
            else:
                logger.warning("Could not detect mnemonic language, assuming English")
                language_display = "Language: English (en) - assumed"

                # Validate with default (English) validation
                if not validate_mnemonic_checksum(mnemonic):
                    raise MnemonicError(
                        "Input mnemonic failed checksum validation",
                        context={"validation_type": "checksum"},
                    )

            # Parse group configuration
            group_threshold, groups = parse_group_config(args.group)

            # Create SLIP-39 shards
            shards = create_slip39_shards(
                mnemonic=mnemonic,
                group_threshold=group_threshold,
                groups=groups,
            )

            # Output shards with language information
            if args.output:
                if args.separate:
                    # Write to separate files (Phase 6 feature) with language info
                    shards_with_header = [
                        f"# {language_display}\n{shard}" for shard in shards
                    ]
                    file_paths = write_shards_to_separate_files(
                        shards_with_header, args.output
                    )
                    logger.info(
                        "Shards written to %d separate files with language info",
                        len(file_paths),
                    )
                    print(
                        f"Shards with language info written to {len(file_paths)} separate files:"
                    )
                    for file_path in file_paths:
                        print(f"  {file_path}")
                else:
                    # Write to single file with language info
                    shards_with_header = [f"# {language_display}"] + shards
                    write_shards_to_file(shards_with_header, args.output)
                    logger.info("Shards written to file: %s", args.output)
                    print(f"Shards with language info written to: {args.output}")
            else:
                if args.separate:
                    logger.warning("--separate flag ignored when outputting to stdout")
                    print(
                        "Warning: --separate flag ignored when outputting to stdout",
                        file=sys.stderr,
                    )

                # Output to stdout with language info
                print(f"# {language_display}")
                for i, shard in enumerate(shards, 1):
                    print(f"# Shard {i}")
                    print(shard)
                    print()  # Empty line between shards
                logger.info("Shards written to stdout with language info")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic and shards from memory
            secure_delete_variable(
                mnemonic if "mnemonic" in locals() else "",
                shards if "shards" in locals() else [],
            )


# Backward compatibility wrapper
def handle_shard_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for original handle_shard_command."""
    return ShardCommand().handle(args)
