"""BIP85 command implementation.
# pylint: disable=broad-exception-caught

Generate deterministic entropy from master seeds using BIP85 specification.
Supports BIP39 mnemonics, hex entropy, and passwords in multiple formats.
"""

import argparse

from sseed.bip39 import (
    generate_master_seed,
    validate_mnemonic,
)
from sseed.bip85 import Bip85Applications
from sseed.entropy import secure_delete_variable
from sseed.exceptions import (
    CryptoError,
    MnemonicError,
)
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_ERROR = 2

logger = get_logger(__name__)


class Bip85Command(BaseCommand):
    """Generate deterministic entropy using BIP85 from a master mnemonic."""

    def __init__(self) -> None:
        super().__init__(
            name="bip85",
            help_text="Generate deterministic entropy using BIP85 from master mnemonic",
            description=(
                "Generate deterministic child entropy from a BIP39 master mnemonic "
                "using BIP85 specification. Supports BIP39 mnemonics (all 9 languages), "
                "hex entropy, and passwords with various character sets."
            ),
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add BIP85 command arguments."""
        # Input/output arguments
        self.add_common_io_arguments(parser)

        # Subcommand for different applications
        subparsers = parser.add_subparsers(
            dest="application",
            title="BIP85 Applications",
            description="Choose the type of entropy to generate",
            help="Available BIP85 applications",
            required=True,
        )

        # BIP39 mnemonic subcommand
        bip39_parser = subparsers.add_parser(
            "bip39",
            help="Generate BIP39 mnemonic from BIP85",
            description="Generate BIP39 mnemonic phrases in multiple languages",
        )
        self._add_bip39_arguments(bip39_parser)

        # Hex entropy subcommand
        hex_parser = subparsers.add_parser(
            "hex",
            help="Generate hex entropy from BIP85",
            description="Generate raw entropy as hexadecimal strings",
        )
        self._add_hex_arguments(hex_parser)

        # Password subcommand
        password_parser = subparsers.add_parser(
            "password",
            help="Generate password from BIP85",
            description="Generate passwords with configurable character sets",
        )
        self._add_password_arguments(password_parser)

    def _add_bip39_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add BIP39-specific arguments."""
        parser.add_argument(
            "-w",
            "--words",
            type=int,
            choices=[12, 15, 18, 21, 24],
            default=12,
            metavar="COUNT",
            help="Number of words in generated mnemonic (default: 12)",
        )

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

        parser.add_argument(
            "-n",
            "--index",
            type=int,
            default=0,
            metavar="INDEX",
            help="Child derivation index (0 to 2147483647, default: 0)",
        )

        parser.add_argument(
            "-p",
            "--passphrase",
            type=str,
            default="",
            metavar="PASS",
            help="Optional passphrase for master seed derivation (default: empty)",
        )

    def _add_hex_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add hex entropy-specific arguments."""
        parser.add_argument(
            "-b",
            "--bytes",
            type=int,
            default=32,
            metavar="COUNT",
            help="Number of entropy bytes to generate (16-64, default: 32)",
        )

        parser.add_argument(
            "-u",
            "--uppercase",
            action="store_true",
            help="Output hex in uppercase (default: lowercase)",
        )

        parser.add_argument(
            "-n",
            "--index",
            type=int,
            default=0,
            metavar="INDEX",
            help="Child derivation index (0 to 2147483647, default: 0)",
        )

        parser.add_argument(
            "-p",
            "--passphrase",
            type=str,
            default="",
            metavar="PASS",
            help="Optional passphrase for master seed derivation (default: empty)",
        )

    def _add_password_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add password-specific arguments."""
        parser.add_argument(
            "-l",
            "--length",
            type=int,
            default=20,
            metavar="LENGTH",
            help="Password length in characters (10-128, default: 20)",
        )

        parser.add_argument(
            "-c",
            "--charset",
            type=str,
            choices=["base64", "base85", "alphanumeric", "ascii"],
            default="base64",
            metavar="SET",
            help=(
                "Character set for password generation (default: base64). "
                "Choices: base64, base85, alphanumeric, ascii"
            ),
        )

        parser.add_argument(
            "-n",
            "--index",
            type=int,
            default=0,
            metavar="INDEX",
            help="Child derivation index (0 to 2147483647, default: 0)",
        )

        parser.add_argument(
            "-p",
            "--passphrase",
            type=str,
            default="",
            metavar="PASS",
            help="Optional passphrase for master seed derivation (default: empty)",
        )

    @handle_common_errors("BIP85 generation")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the BIP85 command.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        logger.info("Starting BIP85 %s generation", args.application)
        log_security_event(f"BIP85: {args.application} generation initiated")

        master_seed = None
        result = None

        try:
            # Get master mnemonic from input
            master_mnemonic = self.handle_input(args).strip()

            # Validate master mnemonic
            if not validate_mnemonic(master_mnemonic):
                logger.error("Invalid master mnemonic provided")
                print(
                    "Error: Invalid master mnemonic. Please provide a valid BIP39 mnemonic."
                )
                return EXIT_VALIDATION_ERROR

            # Generate master seed from mnemonic
            passphrase = getattr(args, "passphrase", "")
            master_seed = generate_master_seed(master_mnemonic, passphrase)
            logger.info("Master seed generated from mnemonic")

            # Create BIP85 applications instance
            apps = Bip85Applications()

            # Handle different applications
            if args.application == "bip39":
                result = self._handle_bip39(apps, master_seed, args)
            elif args.application == "hex":
                result = self._handle_hex(apps, master_seed, args)
            elif args.application == "password":
                result = self._handle_password(apps, master_seed, args)
            else:
                raise ValueError(f"Unknown application: {args.application}")

            # Output result
            if args.output:
                # Add metadata comment for file output
                metadata = self._generate_metadata_comment(args)
                output_content = f"{metadata}\n{result}"
                self.handle_output(
                    output_content,
                    args,
                    success_message=f"BIP85 {args.application} written to: {{file}}",
                )
            else:
                print(result)
                # Show metadata for stdout
                metadata = self._generate_metadata_comment(args, include_hash=False)
                print(metadata)

            logger.info("BIP85 %s generation completed successfully", args.application)
            log_security_event(f"BIP85: {args.application} generation completed")

            return EXIT_SUCCESS

        except (MnemonicError, CryptoError) as e:
            logger.error("BIP85 generation failed: %s", e)
            print(f"Error: {e}")
            return EXIT_VALIDATION_ERROR

        except Exception as e:
            logger.error("Unexpected error during BIP85 generation: %s", e)
            print(f"Unexpected error: {e}")
            return EXIT_VALIDATION_ERROR

        finally:
            # Securely delete sensitive data from memory
            if master_seed:
                secure_delete_variable(master_seed)
            if result and isinstance(result, str):
                secure_delete_variable(result)
            secure_delete_variable(
                master_mnemonic if "master_mnemonic" in locals() else ""
            )

    def _handle_bip39(
        self, apps: Bip85Applications, master_seed: bytes, args: argparse.Namespace
    ) -> str:
        """Handle BIP39 mnemonic generation."""
        try:
            mnemonic = apps.derive_bip39_mnemonic(
                master_seed=master_seed,
                word_count=args.words,
                index=args.index,
                language=args.language,
            )

            logger.info(
                "Generated BIP39 mnemonic: %d words, language %s, index %d",
                args.words,
                args.language,
                args.index,
            )

            return mnemonic

        except Exception as e:
            raise CryptoError(f"BIP39 generation failed: {e}") from e

    def _handle_hex(
        self, apps: Bip85Applications, master_seed: bytes, args: argparse.Namespace
    ) -> str:
        """Handle hex entropy generation."""
        try:
            # Validate byte count
            if not 16 <= args.bytes <= 64:
                raise ValueError("Byte count must be between 16 and 64")

            hex_entropy = apps.derive_hex_entropy(
                master_seed=master_seed,
                byte_length=args.bytes,
                index=args.index,
                uppercase=args.uppercase,
            )

            logger.info(
                "Generated hex entropy: %d bytes, index %d, uppercase %s",
                args.bytes,
                args.index,
                args.uppercase,
            )

            return hex_entropy

        except Exception as e:
            raise CryptoError(f"Hex entropy generation failed: {e}") from e

    def _handle_password(
        self, apps: Bip85Applications, master_seed: bytes, args: argparse.Namespace
    ) -> str:
        """Handle password generation."""
        try:
            # Validate password length
            if not 10 <= args.length <= 128:
                raise ValueError("Password length must be between 10 and 128")

            password = apps.derive_password(
                master_seed=master_seed,
                length=args.length,
                index=args.index,
                character_set=args.charset,
            )

            logger.info(
                "Generated password: %d characters, charset %s, index %d",
                args.length,
                args.charset,
                args.index,
            )

            return password

        except Exception as e:
            raise CryptoError(f"Password generation failed: {e}") from e

    def _generate_metadata_comment(
        self, args: argparse.Namespace, include_hash: bool = True
    ) -> str:
        """Generate metadata comment for output."""
        metadata_lines = []

        if include_hash:
            metadata_lines.append("#")

        metadata_lines.append(f"# BIP85 {args.application.upper()} Generation")
        metadata_lines.append(f"# Application: {args.application}")
        metadata_lines.append(f"# Index: {getattr(args, 'index', 0)}")

        if args.application == "bip39":
            metadata_lines.append(f"# Words: {args.words}")
            metadata_lines.append(f"# Language: {args.language}")
        elif args.application == "hex":
            metadata_lines.append(f"# Bytes: {args.bytes}")
            metadata_lines.append(
                f"# Format: {'uppercase' if args.uppercase else 'lowercase'}"
            )
        elif args.application == "password":
            metadata_lines.append(f"# Length: {args.length}")
            metadata_lines.append(f"# Character Set: {args.charset}")

        passphrase_info = "yes" if getattr(args, "passphrase", "") else "no"
        metadata_lines.append(f"# Passphrase: {passphrase_info}")

        if include_hash:
            metadata_lines.append("#")

        return "\n".join(metadata_lines)

    def get_application_info(self) -> str:
        """Get information about supported BIP85 applications."""
        apps = Bip85Applications()
        supported = apps.list_supported_applications()

        info_lines = ["Supported BIP85 Applications:"]
        for app_info in supported:
            info_lines.append(
                f"  {app_info['application']}: {app_info['name']} - {app_info['description']}"
            )

        return "\n".join(info_lines)


# Backward compatibility wrapper
def handle_bip85_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for BIP85 command handler."""
    return Bip85Command().handle(args)
