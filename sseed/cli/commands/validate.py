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
import os
import sys
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from sseed.file_operations.readers import read_mnemonic_from_file

from ...entropy.custom import validate_entropy_quality
from ...exceptions import ValidationError
from ...languages import (
    SUPPORTED_LANGUAGES,
    detect_mnemonic_language,
    get_supported_language_codes,
)
from ...validation.crypto import validate_mnemonic_checksum
from ...validation.input import validate_mnemonic_words
from ..base import BaseCommand

logger = logging.getLogger(__name__)


class ValidateCommand(BaseCommand):
    """Advanced validation command with multiple validation modes."""

    def __init__(self):
        super().__init__(
            name="validate",
            help_text="Comprehensive validation of mnemonics, backups, and entropy",
            description="Advanced validation command with multiple validation modes including basic mnemonic validation, cross-tool compatibility testing, backup file integrity verification, batch validation for multiple files, and advanced entropy analysis.",
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
            help=(
                "Mnemonic phrase as string (use quotes for multi-word phrases). "
                "WARNING: Command line arguments may be logged or visible to other processes."
            ),
        )

        # Validation modes
        parser.add_argument(
            "--mode",
            type=str,
            choices=["basic", "advanced", "entropy", "compatibility", "backup"],
            default="basic",
            help=(
                "Validation mode: "
                "basic (checksum + format), "
                "advanced (deep analysis + scoring), "
                "entropy (specialized entropy analysis), "
                "compatibility (cross-tool testing), "
                "backup (backup verification)"
            ),
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

    def handle(self, args) -> int:
        """Handle the validate command execution."""
        return self.execute(args)

    def execute(self, args) -> int:
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
            logger.error(f"Validation failed: {e}")
            if args.json:
                self._output_json_error(str(e))
            else:
                self._error(f"Validation failed: {e}")
            return 1

    def _single_validation(self, args) -> int:
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

            # Output results
            self._output_results(result, args)

            # Return appropriate exit code
            return self._get_exit_code(result, args.strict)

        except Exception as e:
            logger.error("Single validation failed: %s", str(e))
            raise

    def _basic_validation(self, mnemonic: str, args) -> Dict[str, Any]:
        """Perform basic mnemonic validation."""
        try:
            from sseed.bip39 import (  # pylint: disable=import-outside-toplevel
                validate_mnemonic,
            )
            from sseed.languages import (  # pylint: disable=import-outside-toplevel
                detect_mnemonic_language,
            )

            result = {
                "mode": "basic",
                "mnemonic_provided": bool(mnemonic),
                "word_count": len(mnemonic.split()) if mnemonic else 0,
                "validation_results": {},
                "detected_language": None,
                "overall_status": "unknown",
                "timestamp": None,
            }

            if not mnemonic:
                result["validation_results"]["error"] = "No mnemonic provided"
                result["overall_status"] = "invalid"
                return result

            # Language detection
            detected_lang = detect_mnemonic_language(mnemonic)
            if detected_lang:
                result["detected_language"] = {
                    "name": detected_lang.name,
                    "code": detected_lang.code,
                }

            # Basic validation
            is_valid = validate_mnemonic(mnemonic)
            result["validation_results"]["checksum_valid"] = is_valid
            result["validation_results"]["format_valid"] = bool(
                mnemonic and len(mnemonic.split()) in [12, 15, 18, 21, 24]
            )

            # Overall status
            if is_valid and result["validation_results"]["format_valid"]:
                result["overall_status"] = "valid"
            else:
                result["overall_status"] = "invalid"

            return result

        except Exception as e:
            logger.error("Basic validation failed: %s", str(e))
            raise ValidationError(f"Basic validation error: {e}") from e

    def _advanced_validation(self, mnemonic: str, args) -> Dict[str, Any]:
        """Perform advanced mnemonic validation with comprehensive analysis."""
        try:
            from sseed.validation.analysis import (  # pylint: disable=import-outside-toplevel
                analyze_mnemonic_comprehensive,
            )

            result = analyze_mnemonic_comprehensive(mnemonic)
            result["mode"] = "advanced"
            return result

        except Exception as e:
            logger.error("Advanced validation failed: %s", str(e))
            raise ValidationError(f"Advanced validation error: {e}") from e

    def _entropy_validation(self, mnemonic: str, args) -> Dict[str, Any]:
        """Perform specialized entropy validation."""
        try:
            # Import entropy analysis
            from sseed.validation.analysis import (  # pylint: disable=import-outside-toplevel
                analyze_mnemonic_comprehensive,
            )

            # Get full analysis but focus on entropy
            full_result = analyze_mnemonic_comprehensive(mnemonic)

            # Extract entropy-specific results
            result = {
                "mode": "entropy",
                "mnemonic_provided": full_result.get("mnemonic_provided", False),
                "word_count": full_result.get("word_count", 0),
                "entropy_analysis": full_result.get("entropy_analysis", {}),
                "quality_score": full_result.get("quality_score", 0),
                "overall_status": full_result.get("overall_status", "unknown"),
                "timestamp": full_result.get("timestamp"),
            }

            return result

        except Exception as e:
            logger.error("Entropy validation failed: %s", str(e))
            raise ValidationError(f"Entropy validation error: {e}") from e

    def _compatibility_validation(self, mnemonic: str, args) -> Dict[str, Any]:
        """Perform cross-tool compatibility validation."""
        try:
            from sseed.validation.cross_tool import (  # pylint: disable=import-outside-toplevel
                get_available_tools,
                test_cross_tool_compatibility,
            )

            # Get available tools
            available_tools = get_available_tools()

            # Test compatibility
            compatibility_results = test_cross_tool_compatibility(
                mnemonic, available_tools
            )

            result = {
                "mode": "compatibility",
                "mnemonic_provided": bool(mnemonic),
                "word_count": len(mnemonic.split()) if mnemonic else 0,
                "available_tools": available_tools,
                "compatibility_results": compatibility_results,
                "overall_status": (
                    "compatible"
                    if compatibility_results.get("all_passed", False)
                    else "incompatible"
                ),
                "timestamp": None,
            }

            return result

        except Exception as e:
            logger.error("Compatibility validation failed: %s", str(e))
            raise ValidationError(f"Compatibility validation error: {e}") from e

    def _backup_validation(self, mnemonic: str, args) -> Dict[str, Any]:
        """Perform backup verification validation."""
        try:
            from sseed.validation.backup_verification import (  # pylint: disable=import-outside-toplevel
                verify_backup_integrity,
            )

            # Prepare backup verification parameters
            shard_files = args.shard_files or []
            group_config = args.group_config or "3-of-5"
            iterations = args.iterations
            stress_test = args.stress_test

            # Perform backup verification
            result = verify_backup_integrity(
                mnemonic=mnemonic,
                shard_files=shard_files,
                group_config=group_config,
                iterations=iterations,
                stress_test=stress_test,
            )

            result["mode"] = "backup"
            return result

        except Exception as e:
            logger.error("Backup validation failed: %s", str(e))
            raise ValidationError(f"Backup validation error: {e}") from e

    def _batch_validation(self, args) -> int:
        """Handle batch validation of multiple files."""
        try:
            from sseed.validation.batch import (  # pylint: disable=import-outside-toplevel
                validate_batch_files,
            )
            from sseed.validation.formatters import (  # pylint: disable=import-outside-toplevel
                format_validation_output,
            )

            if not args.batch:
                raise ValidationError("Batch pattern not specified")

            # Validate batch files
            batch_results = validate_batch_files(
                pattern=args.batch,
                mode=args.mode,
                max_workers=args.max_workers,
                strict=args.strict,
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

            # Return exit code based on results
            if batch_results.get("summary", {}).get("failed_count", 0) > 0:
                return 1
            else:
                return 0

        except Exception as e:
            logger.error("Batch validation failed: %s", str(e))
            raise ValidationError(f"Batch validation error: {e}") from e

    def _output_results(self, result: Dict[str, Any], args) -> None:
        """Output validation results in the specified format."""
        try:
            from sseed.validation.formatters import (  # pylint: disable=import-outside-toplevel
                format_validation_output,
            )

            # Add timestamp if not present
            if not result.get("timestamp"):
                from datetime import datetime  # pylint: disable=import-outside-toplevel

                result["timestamp"] = datetime.now().isoformat()

            # Format output
            if args.json:
                output = json.dumps(result, indent=2, default=str)
            else:
                output = format_validation_output(result, output_format="text")

            # Write output
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
                if not args.quiet:
                    logger.info("Validation results written to %s", args.output)
            else:
                print(output)

        except Exception as e:
            logger.error("Failed to output results: %s", str(e))
            raise ValidationError(f"Output error: {e}") from e

    def _get_exit_code(self, result: Dict[str, Any], strict: bool) -> int:
        """Get appropriate exit code based on validation results."""
        status = result.get("overall_status", "unknown")

        if status in ["valid", "excellent", "good", "compatible"]:
            return 0
        elif status in ["acceptable"] and not strict:
            return 0
        elif status in ["poor", "invalid", "incompatible", "fail"]:
            return 1
        else:
            return 1  # Unknown status, fail safe

    def handle_input(self, args: argparse.Namespace) -> str:
        """Handle input from various sources with proper validation."""
        try:
            if args.mnemonic:
                return args.mnemonic.strip()
            elif args.input:
                return read_mnemonic_from_file(args.input).strip()
            else:
                # Read from stdin
                if sys.stdin.isatty():
                    print("Enter mnemonic phrase (press Enter when done):")
                mnemonic = sys.stdin.read().strip()
                if not mnemonic:
                    raise ValidationError("No mnemonic provided")
                return mnemonic
        except Exception as e:
            logger.error("Failed to read mnemonic input: %s", str(e))
            raise ValidationError(f"Input error: {e}") from e

    def _output_json_error(self, error_message: str) -> None:
        """Output error in JSON format."""
        error_result = {
            "overall_status": "error",
            "error": error_message,
            "timestamp": self._get_timestamp(),
        }
        print(json.dumps(error_result, indent=2))

    def _error(self, message: str) -> None:
        """Output error message to stderr."""
        print(f"Error: {message}", file=sys.stderr)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()


def handle_validate_command(args: argparse.Namespace) -> int:
    """Handle validate command execution."""
    command = ValidateCommand()
    return command.execute(args)
