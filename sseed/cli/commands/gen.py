"""Generate command implementation.

Handles mnemonic generation with secure entropy.
"""

import argparse

from sseed.bip39 import generate_mnemonic
from sseed.entropy import secure_delete_variable
from sseed.exceptions import MnemonicError
from sseed.logging_config import get_logger
from sseed.validation import validate_mnemonic_checksum

from ..base import BaseCommand
from ..error_handling import handle_common_errors
from .. import EXIT_SUCCESS

logger = get_logger(__name__)


class GenCommand(BaseCommand):
    """Generate a 24-word BIP-39 mnemonic using secure entropy."""

    def __init__(self):
        super().__init__(
            name="gen",
            help_text="Generate a 24-word BIP-39 mnemonic using secure entropy",
            description=(
                "Generate a cryptographically secure 24-word BIP-39 mnemonic "
                "using system entropy."
            )
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
        self.add_entropy_display_argument(parser)

    @handle_common_errors("generation")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the 'gen' command.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting mnemonic generation")

        try:
            # Generate the mnemonic
            mnemonic = generate_mnemonic()

            # Validate generated mnemonic checksum (Phase 5 requirement)
            if not validate_mnemonic_checksum(mnemonic):
                raise MnemonicError(
                    "Generated mnemonic failed checksum validation",
                    context={"validation_type": "checksum"},
                )

            # Handle entropy display if requested
            entropy_info = self.handle_entropy_display(mnemonic, args, args.output)

            # Output mnemonic
            if args.output:
                self.handle_output(
                    mnemonic, 
                    args, 
                    success_message="Mnemonic written to: {file}"
                )
                
                # Display entropy info if showing entropy
                if entropy_info:
                    print(f"Mnemonic and entropy written to: {args.output}")
            else:
                # Output to stdout
                print(mnemonic)
                if entropy_info:
                    print(entropy_info)
                logger.info("Mnemonic written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic from memory
            secure_delete_variable(mnemonic if "mnemonic" in locals() else "")


# Backward compatibility wrapper
def handle_gen_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for original handle_gen_command."""
    return GenCommand().handle(args) 