"""
Advanced validation command for comprehensive mnemonic and backup verification.

This module provides the `sseed validate` command with multiple validation modes:
- Basic mnemonic validation (checksum, wordlist, format)
- Cross-tool compatibility testing
- Backup file integrity verification
- Batch validation for multiple files
- Advanced entropy analysis
"""

import argparse
import json
import logging
import sys
from typing import (
    Any,
    Dict,
)

from sseed.file_operations.readers import read_mnemonic_from_file

from ...exceptions import ValidationError
from ..base import BaseCommand
from ..error_handling import handle_top_level_errors

logger = logging.getLogger(__name__)


class ValidateCommand(BaseCommand):
    """Advanced validation command with multiple validation modes."""

    def __init__(self) -> None:
        super().__init__(
            name="validate",
            help_text="Comprehensive validation of mnemonics, backups, and entropy",
            description="Advanced validation command with multiple validation modes.",
        )
        self.validation_results: Dict[str, Any] = {}

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        # Input methods (mutually exclusive)
        input_group = parser.add_mutually_exclusive_group(required=False)
        input_group.add_argument(
            "-i",
            "--input",
            type=str,
            metavar="FILE",
            help="Input file containing mnemonic phrase",
        )
        input_group.add_argument(
            "-m",
            "--mnemonic",
            type=str,
            metavar="PHRASE",
            help="Mnemonic phrase as string (use quotes for multi-word phrases).",
        )

        # Validation modes
        parser.add_argument(
            "--mode",
            type=str,
            choices=["basic", "advanced", "entropy", "compatibility", "backup"],
            default="basic",
            help="Validation mode",
        )

        # Output options
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            metavar="FILE",
            help="Output file (default: stdout)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format",
        )

        # Batch processing
        parser.add_argument(
            "--batch",
            type=str,
            metavar="PATTERN",
            help="Batch validate files matching glob pattern (e.g., '*.txt')",
        )
        parser.add_argument(
            "--max-workers",
            type=int,
            default=4,
            help="Maximum worker threads for batch processing (default: 4)",
        )

        # Advanced options
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Enable strict validation (fail on warnings)",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress progress output (JSON mode only)",
        )

        # Backup-specific options
        parser.add_argument(
            "--shard-files",
            type=str,
            nargs="+",
            metavar="FILE",
            help="SLIP-39 shard files for backup verification",
        )
        parser.add_argument(
            "--group-config",
            type=str,
            metavar="CONFIG",
            help="Group configuration for backup verification (e.g., '3-of-5')",
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=10,
            help="Number of iterations for stress testing (default: 10)",
        )
        parser.add_argument(
            "--stress-test",
            action="store_true",
            help="Enable stress testing for backup verification",
        )

    def handle(self, args: argparse.Namespace) -> int:
        """Handle the validate command execution."""
        return self.execute(args)

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the validate command."""
        try:
            # Handle batch processing
            if args.batch:
                return self._batch_validation(args)

            # Handle single validation
            return self._single_validation(args)

        except KeyboardInterrupt:
            logger.info("Validation interrupted by user")
            return 130  # Standard exit code for SIGINT
        except Exception as e:
            logger.error("Validation failed: %s", e)
            if args.json:
                self._output_json_error(str(e))
            else:
                self._error(f"Validation failed: {e}")
            return 1

    def _single_validation(self, args: argparse.Namespace) -> int:
        """Handle single mnemonic validation."""
        try:
            # Get mnemonic input
            mnemonic = self.handle_input(args)

            # Perform validation based on mode
            if args.mode == "basic":
                result = self._basic_validation(mnemonic, args)
            elif args.mode == "advanced":
                result = self._advanced_validation(mnemonic, args)
            elif args.mode == "entropy":
                result = self._entropy_validation(mnemonic, args)
            elif args.mode == "compatibility":
                result = self._compatibility_validation(mnemonic, args)
            elif args.mode == "backup":
                result = self._backup_validation(mnemonic, args)
            else:
                raise ValidationError(f"Unknown validation mode: {args.mode}")

            # Store results for testing
            self.validation_results = result

            # Output results
            self._output_results(result, args)

            # Return exit code
            return self._get_exit_code(result, args.strict)

        except Exception as e:
            logger.error("Single validation failed: %s", e)
            if args.json:
                self._output_json_error(str(e))
            else:
                self._error(f"Validation failed: {e}")
            return 1

    def _basic_validation(
        self, mnemonic: str, _args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Perform basic mnemonic validation."""
        try:
            from sseed.validation import validate_mnemonic_basic

            return validate_mnemonic_basic(mnemonic)
        except ImportError:
            # Fallback implementation
            from sseed.bip39 import validate_mnemonic
            from sseed.languages import detect_mnemonic_language

            detected_lang = detect_mnemonic_language(mnemonic)
            is_valid = validate_mnemonic(mnemonic)

            return {
                "is_valid": is_valid,
                "mode": "basic",
                "language": detected_lang.code if detected_lang else "unknown",
                "word_count": len(mnemonic.split()),
            }

    def _advanced_validation(
        self, mnemonic: str, args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Perform advanced mnemonic validation."""
        try:
            from sseed.validation import validate_mnemonic_advanced

            return validate_mnemonic_advanced(mnemonic)
        except ImportError:
            return self._basic_validation(mnemonic, args)

    def _entropy_validation(
        self, mnemonic: str, args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Perform entropy-focused validation."""
        try:
            from sseed.validation import validate_mnemonic_entropy

            return validate_mnemonic_entropy(mnemonic)
        except ImportError:
            return self._basic_validation(mnemonic, args)

    def _compatibility_validation(
        self, mnemonic: str, args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Perform cross-tool compatibility validation."""
        try:
            from sseed.validation import validate_mnemonic_compatibility

            return validate_mnemonic_compatibility(mnemonic)
        except ImportError:
            return self._basic_validation(mnemonic, args)

    def _backup_validation(
        self, mnemonic: str, args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Perform backup verification validation."""
        try:
            from sseed.validation.backup_verification import verify_backup_integrity

            result = verify_backup_integrity(
                mnemonic=mnemonic,
                shard_files=args.shard_files or [],
                group_config=args.group_config or "3-of-5",
                iterations=args.iterations,
                stress_test=args.stress_test,
            )
            return result

        except ImportError as e:
            logger.error("Backup verification not available: %s", e)
            return {
                "is_valid": False,
                "mode": "backup",
                "error": "Backup verification module not available",
                "message": str(e),
            }

    def _batch_validation(self, args: argparse.Namespace) -> int:
        """Handle batch validation of multiple files."""
        try:
            from sseed.validation.batch import validate_batch_files
            from sseed.validation.formatters import format_validation_output

            batch_results = validate_batch_files(
                file_patterns=[args.batch],
                expected_language=None,
                strict_mode=args.strict,
                fail_fast=False,
                include_analysis=True,
                max_workers=args.max_workers,
            )

            # Output batch results
            if args.json:
                output = json.dumps(batch_results, indent=2, default=str)
            else:
                output = format_validation_output(batch_results, output_format="text")

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
                if not args.quiet:
                    logger.info("Batch validation results written to %s", args.output)
            else:
                print(output)

            failed_count = batch_results.get("summary", {}).get("failed_count", 0)
            return 1 if failed_count > 0 else 0

        except Exception as e:
            logger.error("Batch validation failed: %s", str(e))
            raise ValidationError(f"Batch validation error: {e}") from e

    def _output_results(self, result: Dict[str, Any], args: argparse.Namespace) -> None:
        """Output validation results."""
        try:
            from sseed.validation.formatters import format_validation_output

            if args.json:
                output = json.dumps(result, indent=2, default=str)
            else:
                output = format_validation_output(result, output_format="text")

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
                if not args.quiet:
                    logger.info("Validation results written to %s", args.output)
            else:
                print(output)

        except Exception as e:
            logger.error("Failed to output results: %s", str(e))
            print(json.dumps(result, indent=2, default=str))

    def _get_exit_code(self, result: Dict[str, Any], strict: bool) -> int:
        """Get appropriate exit code based on validation result."""
        if not result.get("is_valid", False):
            return 1

        if strict and result.get("warnings"):
            return 1

        return 0

    def handle_input(self, args: argparse.Namespace, input_arg: str = "") -> str:
        """Handle input from various sources."""
        if hasattr(args, "mnemonic") and args.mnemonic:
            return str(args.mnemonic).strip()

        if hasattr(args, "input") and args.input:
            return read_mnemonic_from_file(args.input)

        # Read from stdin
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()
            if content:
                return content

        raise ValidationError("No mnemonic provided via -m, -i, or stdin")

    def _output_json_error(self, error_message: str) -> None:
        """Output error in JSON format."""
        error_result = {
            "is_valid": False,
            "error": error_message,
            "timestamp": self._get_timestamp(),
        }
        print(json.dumps(error_result, indent=2))

    def _error(self, message: str) -> None:
        """Output error message."""
        print(f"Error: {message}", file=sys.stderr)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import datetime

        return datetime.datetime.now().isoformat()


def handle_validate_command(args: argparse.Namespace) -> int:
    """Handle validate command - entry point for CLI."""
    command = ValidateCommand()
    return handle_top_level_errors(command.execute)(args)
