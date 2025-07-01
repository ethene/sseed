"""Seed command implementation.
# pylint: disable=too-many-branches

Derives master seeds from mnemonics using BIP-39 with automatic language detection.
"""

import argparse
import getpass
import sys

from sseed.bip39 import generate_master_seed
from sseed.entropy import secure_delete_variable
from sseed.exceptions import MnemonicError
from sseed.languages import detect_mnemonic_language
from sseed.logging_config import get_logger
from sseed.validation import validate_mnemonic_checksum

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit code locally to avoid circular import
EXIT_SUCCESS = 0

logger = get_logger(__name__)


class SeedCommand(BaseCommand):
    """Derive BIP-32 master seed from mnemonic with optional passphrase and language detection."""

    def __init__(self) -> None:
        super().__init__(
            name="seed",
            help_text="Derive BIP-32 master seed from mnemonic with optional passphrase",
            description=(
                "Generate a BIP-32 master seed from a mnemonic phrase "
                "using PBKDF2 key derivation with optional passphrase. "
                "Automatically detects the mnemonic language."
            ),
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add seed command arguments."""
        self.add_common_io_arguments(parser)

        parser.add_argument(
            "-p",
            "--passphrase",
            action="store_true",
            help="Prompt for passphrase (empty passphrase if not specified)",
        )
        parser.add_argument(
            "--format",
            choices=["hex", "binary"],
            default="hex",
            help="Output format (default: hex)",
        )

        # Backward compatibility for tests that expect --hex flag
        parser.add_argument(
            "--hex",
            action="store_const",
            dest="format",
            const="hex",
            help="Output in hex format (backward compatibility)",
        )

        # Add epilog with examples
        parser.epilog = """
Examples:
  sseed seed -i wallet.txt                             Basic seed derivation
  sseed seed -i wallet.txt -p                         With passphrase prompt
  sseed seed -i wallet.txt --format binary            Binary output
  sseed seed -i wallet.txt --hex                      Hex output (legacy)
  echo "mnemonic words..." | sseed seed -p             From stdin with passphrase
        """

    @handle_common_errors("seed derivation")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the 'seed' command with automatic language detection.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting BIP-32 seed derivation")

        passphrase = ""
        try:
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

            # Handle passphrase
            if args.passphrase:
                passphrase = getpass.getpass("Enter passphrase (hidden): ")
                logger.info("Using passphrase for seed derivation")
            else:
                passphrase = ""
                logger.info("Using empty passphrase for seed derivation")

            # Derive BIP-32 seed using the correct function
            seed = generate_master_seed(mnemonic, passphrase)

            # Initialize output to avoid pylint warning
            output = ""

            # Format output
            if args.format == "hex":
                output = seed.hex()
            elif args.format == "binary":
                # Output binary data directly (for piping to other tools)
                if args.output:
                    # Write binary to file with language info comment
                    with open(args.output, "wb") as f:
                        # Add language info as comment at the beginning for binary files
                        f.write(f"# {language_display}\n".encode("utf-8"))
                        f.write(seed)
                    logger.info("Binary seed written to file: %s", args.output)
                    print(f"Binary seed with language info written to: {args.output}")
                    return EXIT_SUCCESS
                # Can't output binary to stdout safely, use hex instead
                logger.warning("Binary format not supported for stdout, using hex")
                output = seed.hex()
                print(
                    "Warning: Binary format not supported for stdout, using hex",
                    file=sys.stderr,
                )

            # Output seed (only for non-binary format) with language info
            if args.output:
                # Include language info in file output
                output_content = f"# {language_display}\n{output}"
                self.handle_output(
                    output_content,
                    args,
                    success_message="BIP-32 seed written to: {file}",
                )
            else:
                print(output)
                print(f"# {language_display}")
                logger.info("BIP-32 seed written to stdout with language info")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic, passphrase, and seed from memory
            secure_delete_variable(
                mnemonic if "mnemonic" in locals() else "",
                passphrase,
                seed if "seed" in locals() else b"",
                output if "output" in locals() else "",
            )


# Backward compatibility wrapper
def handle_seed_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for original handle_seed_command."""
    return SeedCommand().handle(args)
