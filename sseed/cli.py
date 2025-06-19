"""Main CLI entry point for sseed application.

Provides command-line interface for BIP39/SLIP39 operations:
- gen: Generate a 24-word BIP-39 mnemonic
- shard: Split mnemonic into SLIP-39 shards
- restore: Reconstruct mnemonic from shards
"""

import argparse
import sys

from sseed import __version__
from sseed.bip39 import generate_mnemonic
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
    sanitize_filename,
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
        description="Secure, offline BIP39/SLIP39 cryptocurrency seed management with mathematical verification",
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
For security guidelines: https://github.com/yourusername/sseed/blob/main/docs/security.md
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

    # Generate command
    gen_parser = subparsers.add_parser(
        "gen",
        help="Generate a 24-word BIP-39 mnemonic using secure entropy",
        description="Generate a cryptographically secure 24-word BIP-39 mnemonic using system entropy.",
        epilog="Example: sseed gen -o my-wallet-backup.txt",
    )
    gen_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file (default: stdout)",
    )

    # Shard command
    shard_parser = subparsers.add_parser(
        "shard",
        help="Split mnemonic into SLIP-39 shards with group/threshold configuration",
        description="Split a BIP-39 mnemonic into SLIP-39 threshold shards for secure distribution.",
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
        help="Group threshold configuration (default: 3-of-5). Examples: '3-of-5', '2:(2-of-3,3-of-5)'",
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
        help="Write each shard to a separate file (e.g., shards_01.txt, shards_02.txt)",
    )

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore",
        help="Reconstruct mnemonic from a valid set of SLIP-39 shards",
        description="Reconstruct the original mnemonic from SLIP-39 shards using Shamir's Secret Sharing.",
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

        try:
            # Output to file or stdout
            if args.output:
                # Use the proper file writing function with path sanitization
                write_mnemonic_to_file(mnemonic, args.output, include_comments=True)
                logger.info("Mnemonic written to file: %s", args.output)
                print(f"Mnemonic written to: {args.output}")
            else:
                # Output to stdout
                print(mnemonic)
                logger.info("Mnemonic written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete mnemonic from memory
            secure_delete_variable(mnemonic)

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
            return EXIT_USAGE_ERROR

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

            # Output reconstructed mnemonic
            if args.output:
                write_mnemonic_to_file(reconstructed_mnemonic, args.output)
                logger.info("Reconstructed mnemonic written to file: %s", args.output)
                print(f"Mnemonic reconstructed and written to: {args.output}")
            else:
                # Output to stdout
                print(reconstructed_mnemonic)
                logger.info("Reconstructed mnemonic written to stdout")

            return EXIT_SUCCESS

        finally:
            # Securely delete shards and mnemonic from memory
            secure_delete_variable(
                shards,
                reconstructed_mnemonic if "reconstructed_mnemonic" in locals() else "",
            )

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


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI application.

    Args:
        argv: Command-line arguments (default: sys.argv[1:]).

    Returns:
        Exit code (0=success, 1=usage error, 2=crypto error, 3=file error, 4=validation error, 130=interrupted).
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
        if args.command == "gen":
            return handle_gen_command(args)
        if args.command == "shard":
            return handle_shard_command(args)
        if args.command == "restore":
            return handle_restore_command(args)

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
