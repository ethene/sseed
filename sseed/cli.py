"""Main CLI entry point for sseed application.

Provides command-line interface for BIP39/SLIP39 operations:
- gen: Generate a 24-word BIP-39 mnemonic
- shard: Split mnemonic into SLIP-39 shards
- restore: Reconstruct mnemonic from shards
"""

import argparse
import sys

from sseed.exceptions import (
    EntropyError,
    FileError,
    MnemonicError,
    SecurityError,
    ShardError,
    SseedError,
    ValidationError,
)
from sseed.logging_config import get_logger, setup_logging

# Exit codes as specified in PRD
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="sseed",
        description="Offline BIP39/SLIP39 CLI Tool for secure cryptocurrency seed management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sseed gen                           # Generate mnemonic to stdout
  sseed gen -o seed.txt              # Generate mnemonic to file
  sseed shard -i seed.txt -g 3-of-5  # Shard with 3-of-5 threshold
  sseed restore shard1.txt shard2.txt shard3.txt  # Restore from shards
        """,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser(
        "gen",
        help="Generate a 24-word BIP-39 mnemonic using secure entropy",
    )
    gen_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file (default: stdout)",
    )

    # Shard command
    shard_parser = subparsers.add_parser(
        "shard",
        help="Split mnemonic into SLIP-39 shards with group/threshold configuration",
    )
    shard_parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Input file containing mnemonic (default: stdin)",
    )
    shard_parser.add_argument(
        "-g",
        "--group",
        type=str,
        default="3-of-5",
        help="Group threshold configuration (default: 3-of-5)",
    )
    shard_parser.add_argument(
        "-o",
        "--output",
        type=str,
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
    )
    restore_parser.add_argument(
        "shards",
        nargs="+",
        help="Shard files to use for reconstruction",
    )
    restore_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for reconstructed mnemonic (default: stdout)",
    )

    # Global options
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
        # Import here to avoid circular imports
        from sseed.bip39 import generate_mnemonic
        from sseed.entropy import secure_delete_variable
        from sseed.validation import sanitize_filename, validate_mnemonic_checksum

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
                # Sanitize filename (Phase 5 requirement)
                safe_filename = sanitize_filename(args.output)

                # Write to file
                with open(safe_filename, "w", encoding="utf-8") as f:
                    f.write(mnemonic + "\n")

                logger.info("Mnemonic written to file: %s", safe_filename)
                print(f"Mnemonic written to: {safe_filename}")
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
    except (ValidationError, FileError) as e:
        logger.error("Validation/file error during generation: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR
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
        # Import here to avoid circular imports
        from sseed.entropy import secure_delete_variable
        from sseed.file_operations import (
            read_from_stdin,
            read_mnemonic_from_file,
            write_shards_to_file,
            write_shards_to_separate_files,
        )
        from sseed.slip39_operations import create_slip39_shards, parse_group_config
        from sseed.validation import validate_group_threshold, validate_mnemonic_checksum

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
    except (ValidationError, FileError) as e:
        logger.error("Validation/file error during sharding: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR
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
        # Import here to avoid circular imports
        from sseed.entropy import secure_delete_variable
        from sseed.file_operations import read_shards_from_files, write_mnemonic_to_file
        from sseed.slip39_operations import reconstruct_mnemonic_from_shards
        from sseed.validation import validate_mnemonic_checksum, validate_shard_integrity

        # Read shards from files
        shards = read_shards_from_files(args.shards)
        logger.info("Read %d shards from files", len(shards))

        # Validate shard integrity including duplicate detection (Phase 5 requirement)
        try:
            validate_shard_integrity(shards)
        except ValidationError as e:
            logger.error("Shard integrity validation failed: %s", e)
            print(f"Shard validation error: {e}", file=sys.stderr)
            return EXIT_USAGE_ERROR

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
                shards, reconstructed_mnemonic if "reconstructed_mnemonic" in locals() else ""
            )

    except (MnemonicError, ShardError, SecurityError) as e:
        logger.error("Cryptographic error during restoration: %s", e)
        print(f"Cryptographic error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR
    except (ValidationError, FileError) as e:
        logger.error("Validation/file error during restoration: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    except Exception as e:
        logger.error("Unexpected error during restoration: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI application.

    Args:
        argv: Command-line arguments (default: sys.argv[1:]).

    Returns:
        Exit code.
    """
    parser = create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit(), capture and convert to our exit codes
        return EXIT_USAGE_ERROR if e.code != 0 else EXIT_SUCCESS

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
        parser.print_help()
        return EXIT_USAGE_ERROR

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("Operation cancelled by user", file=sys.stderr)
        return EXIT_USAGE_ERROR
    except SseedError as e:
        # Handle all sseed-specific errors
        logger.error("sseed error: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        # Determine exit code based on error type
        if isinstance(e, (MnemonicError, ShardError, SecurityError, EntropyError)):
            return EXIT_CRYPTO_ERROR
        return EXIT_USAGE_ERROR
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_CRYPTO_ERROR


if __name__ == "__main__":
    sys.exit(main())
