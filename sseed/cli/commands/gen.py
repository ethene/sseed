"""Generate command implementation.

Generates secure BIP-39 mnemonics with multi-language support.
"""

import argparse

from sseed.bip39 import generate_mnemonic
from sseed.entropy import secure_delete_variable
from sseed.exceptions import MnemonicError
from sseed.languages import validate_language_code
from sseed.logging_config import get_logger
from sseed.validation import validate_mnemonic_checksum

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit code locally to avoid circular import
EXIT_SUCCESS = 0

logger = get_logger(__name__)


class GenCommand(BaseCommand):
    """Generate a 24-word BIP-39 mnemonic using secure entropy with multi-language support."""

    def __init__(self) -> None:
        super().__init__(
            name="gen",
            help_text="Generate a 24-word BIP-39 mnemonic using secure entropy",
            description=(
                "Generate a cryptographically secure 24-word BIP-39 mnemonic "
                "using system entropy. Supports all 9 BIP-39 languages."
            ),
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add gen command arguments."""
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            metavar="FILE",
            help="Output file (default: stdout)",
        )

        # Add language support
        parser.add_argument(
            "-l",
            "--language",
            type=str,
            choices=["en", "es", "fr", "it", "pt", "cs", "zh-cn", "zh-tw", "ko"],
            default="en",
            metavar="LANG",
            help=(
                "Language for mnemonic generation (default: en/English). "
                "Choices: en(English), es(Spanish), fr(French), it(Italian), "
                "pt(Portuguese), cs(Czech), zh-cn(Chinese Simplified), "
                "zh-tw(Chinese Traditional), ko(Korean)"
            ),
        )

        self.add_entropy_display_argument(parser)

    @handle_common_errors("generation")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the 'gen' command with multi-language support.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting mnemonic generation (language: %s)", args.language)

        try:
            # Validate and get language information
            language_info = validate_language_code(args.language)
            logger.info(
                "Using language: %s (%s)", language_info.name, language_info.code
            )

            # Generate the mnemonic with specified language
            mnemonic = generate_mnemonic(language_info.bip_enum)

            # Validate generated mnemonic checksum (Phase 5 requirement)
            if not validate_mnemonic_checksum(mnemonic, language_info.bip_enum):
                raise MnemonicError(
                    f"Generated mnemonic failed checksum validation for {language_info.name}",
                    context={
                        "validation_type": "checksum",
                        "language": language_info.name,
                    },
                )

            # Prepare language info for verbose output
            language_display = f"Language: {language_info.name} ({language_info.code})"

            # Output mnemonic first
            if args.output:
                # Include language info in file output
                output_content = f"# {language_display}\n{mnemonic}"
                self.handle_output(
                    output_content, args, success_message="Mnemonic written to: {file}"
                )

                # Handle entropy display after file is written
                entropy_info = self.handle_entropy_display(mnemonic, args, args.output)
                if entropy_info:
                    print(
                        f"Mnemonic with language info and entropy written to: {args.output}"
                    )
                else:
                    print(f"Mnemonic with language info written to: {args.output}")
            else:
                # Output to stdout
                print(mnemonic)
                print(f"# {language_display}")

                # Handle entropy display for stdout
                entropy_info = self.handle_entropy_display(mnemonic, args)
                if entropy_info:
                    print(entropy_info)
                logger.info("Mnemonic written to stdout in %s", language_info.name)

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic from memory
            secure_delete_variable(mnemonic if "mnemonic" in locals() else "")


# Backward compatibility wrapper
def handle_gen_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for original handle_gen_command."""
    return GenCommand().handle(args)
