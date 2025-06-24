"""Main CLI entry point for sseed application.

Provides command-line interface for BIP39/SLIP39 operations:
- gen: Generate a 24-word BIP-39 mnemonic
- shard: Split mnemonic into SLIP-39 shards
- restore: Reconstruct mnemonic from shards
"""

import argparse
import json
import platform
import sys
from importlib import metadata
from typing import (
    Any,
    Dict,
)

from sseed import __version__
from sseed.bip39 import (
    generate_master_seed,
    generate_mnemonic,
    get_mnemonic_entropy,
    mnemonic_to_hex_seed,
)
from sseed.entropy import secure_delete_variable
from sseed.exceptions import (
    EntropyError,
    FileError,
    MnemonicError,
    SecurityError,
    ShardError,
    SseedError,
    ValidationError,
)
from sseed.file_operations import (
    read_from_stdin,
    read_mnemonic_from_file,
    read_shards_from_files,
    write_mnemonic_to_file,
    write_shards_to_file,
    write_shards_to_separate_files,
)
from sseed.logging_config import (
    get_logger,
    setup_logging,
)
from sseed.slip39_operations import (
    create_slip39_shards,
    parse_group_config,
    reconstruct_mnemonic_from_shards,
)
from sseed.validation import (
    validate_group_threshold,
    validate_mnemonic_checksum,
    validate_shard_integrity,
)

# Comprehensive exit codes for better script integration
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130  # Standard exit code for SIGINT

logger = get_logger(__name__)


def handle_version_command(args: argparse.Namespace) -> int:
    """Handle the version command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (always 0 for success).
    """
    try:
        # Core version information
        version_info: Dict[str, Any] = {
            "sseed": __version__,
            "python": sys.version.split()[0],
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "architecture": platform.architecture()[0],
            },
        }

        # Dependency versions
        dependencies: Dict[str, str] = {}
        try:
            dependencies["bip-utils"] = metadata.version("bip-utils")
        except metadata.PackageNotFoundError:
            dependencies["bip-utils"] = "not installed"

        try:
            dependencies["slip39"] = metadata.version("slip39")
        except metadata.PackageNotFoundError:
            dependencies["slip39"] = "not installed"

        version_info["dependencies"] = dependencies

        # Build and environment information
        version_info["build"] = {
            "python_implementation": platform.python_implementation(),
            "python_compiler": platform.python_compiler(),
        }

        if args.json:
            # JSON output for scripting
            print(json.dumps(version_info, indent=2))
        else:
            # Human-readable output
            print(f"🔐 SSeed v{version_info['sseed']}")
            print("=" * 40)
            print()
            print("📋 Core Information:")
            print(f"   Version: {version_info['sseed']}")
            python_impl = version_info["build"]["python_implementation"]
            print(f"   Python:  {version_info['python']} ({python_impl})")
            print()
            print("🖥️  System Information:")
            os_name = version_info["platform"]["system"]
            os_release = version_info["platform"]["release"]
            print(f"   OS:           {os_name} {os_release}")
            machine = version_info["platform"]["machine"]
            arch = version_info["platform"]["architecture"]
            print(f"   Architecture: {machine} ({arch})")
            print()
            print("📦 Dependencies:")
            for dep, ver in version_info["dependencies"].items():
                status = "✅" if ver != "not installed" else "❌"
                print(f"   {status} {dep}: {ver}")
            print()
            print("🔗 Links:")
            print("   Repository: https://github.com/ethene/sseed")
            print("   PyPI:       https://pypi.org/project/sseed/")
            print("   Issues:     https://github.com/ethene/sseed/issues")

    except Exception as e:
        logger.error("Error displaying version information: %s", e)
        print(f"Error: Failed to gather version information: {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    return EXIT_SUCCESS


def show_examples() -> None:
    """Display comprehensive usage examples."""
    examples = """
SSEED USAGE EXAMPLES

Basic Operations:
  # Generate a new mnemonic
  sseed gen

  # Generate and save to file
  sseed gen -o my-wallet-backup.txt

  # Split mnemonic into 3-of-5 shards
  sseed shard -i my-wallet-backup.txt -g 3-of-5

  # Split and save to separate files
  sseed shard -i seed.txt -g 3-of-5 --separate -o shards

  # Restore from any 3 shards
  sseed restore shard_01.txt shard_02.txt shard_03.txt

Advanced Workflows:
  # Generate and immediately shard (one-liner)
  sseed gen | sseed shard -g 2-of-3

  # Multi-group enterprise setup
  sseed shard -g "2:(2-of-3,3-of-5)" -i seed.txt --separate -o enterprise-shards

  # Complex multi-group with geographic distribution
  sseed shard -g "3:(3-of-5,4-of-7,2-of-3)" -i master-seed.txt --separate -o geo-dist

  # Restore and save to new file
  sseed restore shard*.txt -o restored-seed.txt

File Management:
  # Generate with timestamp
  sseed gen -o "backup-$(date +%Y%m%d-%H%M%S).txt"

  # Restore from pattern
  sseed restore /secure/location/shard_*.txt

Group Configuration Examples:
  Simple Threshold:
    3-of-5    Any 3 of 5 shards required
    2-of-3    Any 2 of 3 shards required

  Multi-Group Security:
    2:(2-of-3,3-of-5)         Need 2 groups: 2-of-3 AND 3-of-5
    3:(3-of-5,4-of-7,2-of-3)  Need all 3 groups with different thresholds

Security Best Practices:
  # Always verify generated mnemonics
  sseed gen -o backup.txt && cat backup.txt

  # Store shards in separate secure locations
  sseed shard -i seed.txt -g 3-of-5 --separate -o /secure/location1/
  cp shard_*.txt /secure/location2/ && rm shard_*.txt

  # Test restoration before relying on shards
  sseed restore /test/shard*.txt

Integration Examples:
  # Backup existing wallet
  echo "your existing mnemonic words here" | sseed shard -g 3-of-5 --separate -o backup

  # Automated backup with verification
  sseed gen -o master.txt && sseed shard -i master.txt -g 3-of-5 --separate -o shards

For more information, see: https://github.com/yourusername/sseed
"""
    print(examples)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="sseed",
        description=(
            "Secure, offline BIP39/SLIP39 cryptocurrency seed management "
            "with mathematical verification"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
QUICK EXAMPLES:
  sseed gen                              Generate secure mnemonic
  sseed gen -o backup.txt               Save mnemonic to file
  sseed shard -i seed.txt -g 3-of-5     Split into 3-of-5 threshold shards
  sseed shard -g 2-of-3 --separate      Split stdin and save to separate files
  sseed restore shard*.txt              Restore from shard files

ADVANCED CONFIGURATIONS:
  Multi-group:     sseed shard -g "2:(2-of-3,3-of-5)" -i seed.txt
  Enterprise:      sseed shard -g "3:(3-of-5,4-of-7,2-of-3)" --separate -o geo-dist
  One-liner:       sseed gen | sseed shard -g 3-of-5

EXIT CODES:
  0   Success
  1   Usage/argument error
  2   Cryptographic error (entropy, validation, reconstruction)
  3   File I/O error
  4   Validation error (checksums, format)
  130 Interrupted by user (Ctrl+C)

Use 'sseed --examples' for comprehensive usage examples and best practices.
For security guidelines:
https://github.com/yourusername/sseed/blob/main/docs/security.md
        """,
    )

    # Global options (before subcommands)
    parser.add_argument(
        "--version",
        action="version",
        version=f"sseed {__version__}",
        help="Show version information and exit",
    )

    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show comprehensive usage examples and exit",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show detailed version and system information",
        description=(
            "Display comprehensive version information including dependencies, "
            "system details, and build information"
        ),
    )
    version_parser.add_argument(
        "--json",
        action="store_true",
        help="Output version information in JSON format",
    )

    # Generate command
    gen_parser = subparsers.add_parser(
        "gen",
        help="Generate a 24-word BIP-39 mnemonic using secure entropy",
        description=(
            "Generate a cryptographically secure 24-word BIP-39 mnemonic "
            "using system entropy."
        ),
        epilog="Example: sseed gen -o my-wallet-backup.txt",
    )
    gen_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file (default: stdout)",
    )
    gen_parser.add_argument(
        "--show-entropy",
        action="store_true",
        help="Display the underlying entropy (hex) alongside the mnemonic",
    )

    # Shard command
    shard_parser = subparsers.add_parser(
        "shard",
        help="Split mnemonic into SLIP-39 shards with group/threshold configuration",
        description=(
            "Split a BIP-39 mnemonic into SLIP-39 threshold shards "
            "for secure distribution."
        ),
        epilog="""
Examples:
  sseed shard -i seed.txt -g 3-of-5                    Simple threshold
  sseed shard -g "2:(2-of-3,3-of-5)" --separate       Multi-group setup
  echo "mnemonic words..." | sseed shard -g 2-of-3     From stdin
        """,
    )
    shard_parser.add_argument(
        "-i",
        "--input",
        type=str,
        metavar="FILE",
        help="Input file containing mnemonic (default: stdin)",
    )
    shard_parser.add_argument(
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
    shard_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file for shards (default: stdout)",
    )
    shard_parser.add_argument(
        "--separate",
        action="store_true",
        help=(
            "Write each shard to a separate file "
            "(e.g., shards_01.txt, shards_02.txt)"
        ),
    )

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore",
        help="Reconstruct mnemonic from a valid set of SLIP-39 shards",
        description=(
            "Reconstruct the original mnemonic from SLIP-39 shards "
            "using Shamir's Secret Sharing."
        ),
        epilog="""
Examples:
  sseed restore shard1.txt shard2.txt shard3.txt       From specific files
  sseed restore shard*.txt                             Using shell glob
  sseed restore /backup/location/shard_*.txt           Full paths
        """,
    )
    restore_parser.add_argument(
        "shards",
        nargs="+",
        metavar="SHARD_FILE",
        help="Shard files to use for reconstruction",
    )
    restore_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file for reconstructed mnemonic (default: stdout)",
    )
    restore_parser.add_argument(
        "--show-entropy",
        action="store_true",
        help="Display the underlying entropy (hex) alongside the reconstructed mnemonic",
    )

    # Seed command
    seed_parser = subparsers.add_parser(
        "seed",
        help="Generate master seed from BIP-39 mnemonic with optional passphrase",
        description=(
            "Generate a 512-bit master seed from a BIP-39 mnemonic using PBKDF2-HMAC-SHA512. "
            "This seed can be used for cryptographic key derivation."
        ),
        epilog="""
Examples:
  sseed seed -i mnemonic.txt                           From file
  sseed seed -i mnemonic.txt -p "my_passphrase"       With passphrase
  echo "mnemonic words..." | sseed seed               From stdin
  sseed seed -i mnemonic.txt --hex                    Output as hex
        """,
    )
    seed_parser.add_argument(
        "-i",
        "--input",
        type=str,
        metavar="FILE",
        help="Input file containing mnemonic (default: stdin)",
    )
    seed_parser.add_argument(
        "-p",
        "--passphrase",
        type=str,
        default="",
        metavar="PASSPHRASE",
        help="Optional passphrase for additional security (default: none)",
    )
    seed_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file for master seed (default: stdout)",
    )
    seed_parser.add_argument(
        "--hex",
        action="store_true",
        help="Output seed as hexadecimal string (default: binary)",
    )
    seed_parser.add_argument(
        "--iterations",
        type=int,
        default=2048,
        metavar="COUNT",
        help="PBKDF2 iteration count (default: 2048)",
    )

    return parser


def handle_gen_command(args: argparse.Namespace) -> int:
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

        # Extract entropy if requested
        entropy_info = ""
        if args.show_entropy:
            try:
                entropy_bytes = get_mnemonic_entropy(mnemonic)
                entropy_hex = entropy_bytes.hex()
                entropy_info = f"# Entropy: {entropy_hex} ({len(entropy_bytes)} bytes)"
                logger.info(
                    "Extracted entropy for display: %d bytes", len(entropy_bytes)
                )
            except Exception as e:
                logger.warning("Failed to extract entropy for display: %s", e)
                entropy_info = "# Entropy: <extraction failed>"

        try:
            # Output to file or stdout
            if args.output:
                # Use the proper file writing function with path sanitization
                write_mnemonic_to_file(mnemonic, args.output, include_comments=True)

                # If showing entropy, append it to the file
                if args.show_entropy and entropy_info:
                    try:
                        with open(args.output, "a", encoding="utf-8") as f:
                            f.write("\n" + entropy_info + "\n")
                    except Exception as e:
                        logger.warning("Failed to write entropy to file: %s", e)

                logger.info("Mnemonic written to file: %s", args.output)
                if args.show_entropy:
                    print(f"Mnemonic and entropy written to: {args.output}")
                else:
                    print(f"Mnemonic written to: {args.output}")
            else:
                # Output to stdout
                print(mnemonic)
                if args.show_entropy and entropy_info:
                    print(entropy_info)
                logger.info("Mnemonic written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic and entropy from memory
            secure_delete_variable(mnemonic)
            if "entropy_bytes" in locals():
                secure_delete_variable(entropy_bytes)
            if "entropy_hex" in locals():
                secure_delete_variable(entropy_hex)

    except (EntropyError, MnemonicError, SecurityError) as e:
        logger.error("Cryptographic error during generation: %s", e)
        print(f"Cryptographic error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR
    except FileError as e:
        logger.error("File I/O error during generation: %s", e)
        print(f"File error: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    except ValidationError as e:
        logger.error("Validation error during generation: %s", e)
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except Exception as e:
        logger.error("Unexpected error during generation: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


def handle_shard_command(args: argparse.Namespace) -> int:
    """Handle the 'shard' command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    logger.info("Starting mnemonic sharding with group: %s", args.group)

    try:
        # Validate group configuration first (Phase 5 requirement)
        try:
            validate_group_threshold(args.group)
        except ValidationError as e:
            logger.error("Invalid group configuration: %s", e)
            print(f"Invalid group configuration: {e}", file=sys.stderr)
            return EXIT_VALIDATION_ERROR

        # Read mnemonic from input source
        if args.input:
            mnemonic = read_mnemonic_from_file(args.input)
            logger.info("Read mnemonic from file: %s", args.input)
        else:
            mnemonic = read_from_stdin()
            logger.info("Read mnemonic from stdin")

        # Validate mnemonic checksum (Phase 5 requirement)
        if not validate_mnemonic_checksum(mnemonic):
            raise MnemonicError(
                "Input mnemonic failed checksum validation",
                context={"validation_type": "checksum"},
            )

        try:
            # Parse group configuration
            group_threshold, groups = parse_group_config(args.group)

            # Create SLIP-39 shards
            shards = create_slip39_shards(
                mnemonic=mnemonic,
                group_threshold=group_threshold,
                groups=groups,
            )

            # Output shards
            if args.output:
                if args.separate:
                    # Write to separate files (Phase 6 feature)
                    file_paths = write_shards_to_separate_files(shards, args.output)
                    logger.info("Shards written to %d separate files", len(file_paths))
                    print(f"Shards written to {len(file_paths)} separate files:")
                    for file_path in file_paths:
                        print(f"  {file_path}")
                else:
                    # Write to single file
                    write_shards_to_file(shards, args.output)
                    logger.info("Shards written to file: %s", args.output)
                    print(f"Shards written to: {args.output}")
            else:
                if args.separate:
                    logger.warning("--separate flag ignored when outputting to stdout")
                    print(
                        "Warning: --separate flag ignored when outputting to stdout",
                        file=sys.stderr,
                    )

                # Output to stdout
                for i, shard in enumerate(shards, 1):
                    print(f"# Shard {i}")
                    print(shard)
                    print()  # Empty line between shards
                logger.info("Shards written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic and shards from memory
            secure_delete_variable(mnemonic, shards if "shards" in locals() else [])

    except (MnemonicError, ShardError, SecurityError) as e:
        logger.error("Cryptographic error during sharding: %s", e)
        print(f"Cryptographic error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR
    except FileError as e:
        logger.error("File I/O error during sharding: %s", e)
        print(f"File error: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    except ValidationError as e:
        logger.error("Validation error during sharding: %s", e)
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except Exception as e:
        logger.error("Unexpected error during sharding: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


def handle_restore_command(args: argparse.Namespace) -> int:
    """Handle the 'restore' command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    logger.info("Starting mnemonic restoration from %d shards", len(args.shards))

    try:
        # Read shards from files
        shards = read_shards_from_files(args.shards)
        logger.info("Read %d shards from files", len(shards))

        # Validate shard integrity including duplicate detection (Phase 5 requirement)
        try:
            validate_shard_integrity(shards)
        except ValidationError as e:
            logger.error("Shard integrity validation failed: %s", e)
            print(f"Shard validation error: {e}", file=sys.stderr)
            return EXIT_VALIDATION_ERROR

        try:
            # Reconstruct mnemonic from shards
            reconstructed_mnemonic = reconstruct_mnemonic_from_shards(shards)

            # Validate reconstructed mnemonic checksum (Phase 5 requirement)
            if not validate_mnemonic_checksum(reconstructed_mnemonic):
                raise MnemonicError(
                    "Reconstructed mnemonic failed checksum validation",
                    context={"validation_type": "checksum"},
                )

            # Extract entropy if requested
            entropy_info = ""
            if args.show_entropy:
                try:
                    entropy_bytes = get_mnemonic_entropy(reconstructed_mnemonic)
                    entropy_hex = entropy_bytes.hex()
                    entropy_info = (
                        f"# Entropy: {entropy_hex} ({len(entropy_bytes)} bytes)"
                    )
                    logger.info(
                        "Extracted entropy for display: %d bytes", len(entropy_bytes)
                    )
                except Exception as e:
                    logger.warning("Failed to extract entropy for display: %s", e)
                    entropy_info = "# Entropy: <extraction failed>"

            # Output reconstructed mnemonic
            if args.output:
                write_mnemonic_to_file(reconstructed_mnemonic, args.output)

                # If showing entropy, append it to the file
                if args.show_entropy and entropy_info:
                    try:
                        with open(args.output, "a", encoding="utf-8") as f:
                            f.write("\n" + entropy_info + "\n")
                    except Exception as e:
                        logger.warning("Failed to write entropy to file: %s", e)

                logger.info("Reconstructed mnemonic written to file: %s", args.output)
                if args.show_entropy:
                    print(
                        f"Mnemonic and entropy reconstructed and written to: {args.output}"
                    )
                else:
                    print(f"Mnemonic reconstructed and written to: {args.output}")
            else:
                # Output to stdout
                print(reconstructed_mnemonic)
                if args.show_entropy and entropy_info:
                    print(entropy_info)
                logger.info("Reconstructed mnemonic written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete shards, mnemonic, and entropy from memory
            secure_delete_variable(
                shards,
                reconstructed_mnemonic if "reconstructed_mnemonic" in locals() else "",
            )
            if "entropy_bytes" in locals():
                secure_delete_variable(entropy_bytes)
            if "entropy_hex" in locals():
                secure_delete_variable(entropy_hex)

    except (MnemonicError, ShardError, SecurityError) as e:
        logger.error("Cryptographic error during restoration: %s", e)
        print(f"Cryptographic error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR
    except FileError as e:
        logger.error("File I/O error during restoration: %s", e)
        print(f"File error: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    except ValidationError as e:
        logger.error("Validation error during restoration: %s", e)
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except Exception as e:
        logger.error("Unexpected error during restoration: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


def handle_seed_command(args: argparse.Namespace) -> int:
    """Handle the 'seed' command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    logger.info("Starting master seed generation from BIP-39 mnemonic")

    try:
        # Read mnemonic from input source
        if args.input:
            mnemonic = read_mnemonic_from_file(args.input)
            logger.info("Read mnemonic from file: %s", args.input)
        else:
            mnemonic = read_from_stdin()
            logger.info("Read mnemonic from stdin")

        # Validate mnemonic checksum (Phase 5 requirement)
        if not validate_mnemonic_checksum(mnemonic):
            raise MnemonicError(
                "Input mnemonic failed checksum validation",
                context={"validation_type": "checksum"},
            )

        try:
            # Generate master seed
            if args.hex:
                # Generate hexadecimal seed
                seed_output = mnemonic_to_hex_seed(mnemonic, args.passphrase)
                logger.info("Generated hexadecimal master seed")
            else:
                # Generate binary seed
                master_seed = generate_master_seed(
                    mnemonic, args.passphrase, args.iterations
                )
                seed_output = master_seed.hex()  # Convert to hex for output
                logger.info("Generated binary master seed")

            # Output seed
            if args.output:
                # Write to file
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(seed_output + "\n")
                logger.info("Master seed written to file: %s", args.output)
                print(f"Master seed written to: {args.output}")
            else:
                # Output to stdout
                print(seed_output)
                logger.info("Master seed written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic and seed from memory
            secure_delete_variable(mnemonic)
            if "master_seed" in locals():
                secure_delete_variable(master_seed)
            if "seed_output" in locals():
                secure_delete_variable(seed_output)

    except (MnemonicError, SecurityError) as e:
        logger.error("Cryptographic error during seed generation: %s", e)
        print(f"Cryptographic error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR
    except FileError as e:
        logger.error("File I/O error during seed generation: %s", e)
        print(f"File error: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    except ValidationError as e:
        logger.error("Validation error during seed generation: %s", e)
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except Exception as e:
        logger.error("Unexpected error during seed generation: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI application.

    Args:
        argv: Command-line arguments (default: sys.argv[1:]).

    Returns:
        Exit code (0=success, 1=usage error, 2=crypto error, 3=file error,
        4=validation error, 130=interrupted).
    """
    parser = create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit(), capture and convert to our exit codes
        return EXIT_USAGE_ERROR if e.code != 0 else EXIT_SUCCESS

    # Handle --examples flag
    if hasattr(args, "examples") and args.examples:
        show_examples()
        return EXIT_SUCCESS

    # Set up logging
    log_level = "DEBUG" if args.verbose else args.log_level
    setup_logging(log_level=log_level)

    logger.info("sseed CLI started with command: %s", args.command)

    try:
        # Route to appropriate command handler
        if args.command == "version":
            return handle_version_command(args)
        if args.command == "gen":
            return handle_gen_command(args)
        if args.command == "shard":
            return handle_shard_command(args)
        if args.command == "restore":
            return handle_restore_command(args)
        if args.command == "seed":
            return handle_seed_command(args)

        # No command specified - show help
        parser.print_help()
        return EXIT_USAGE_ERROR

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user (SIGINT)")
        print("\nOperation cancelled by user", file=sys.stderr)
        return EXIT_INTERRUPTED
    except FileError as e:
        logger.error("File I/O error: %s", e)
        print(f"File error: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    except ValidationError as e:
        logger.error("Validation error: %s", e)
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except (MnemonicError, ShardError, SecurityError, EntropyError) as e:
        logger.error("Cryptographic error: %s", e)
        print(f"Cryptographic error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR
    except SseedError as e:
        # Handle any other sseed-specific errors
        logger.error("sseed error: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


if __name__ == "__main__":
    sys.exit(main())
