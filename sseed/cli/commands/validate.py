"""
Advanced validation command for comprehensive mnemonic and backup verification.

This module provides the `sseed validate` command with multiple validation modes:
- Basic mnemonic validation (checksum, wordlist, format)
- Cross-tool compatibility testing 
- Backup file integrity verification
- Batch validation for multiple files
- Advanced entropy analysis
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import sys

from ..base import BaseCommand
from ...validation.crypto import validate_mnemonic_checksum
from ...validation.input import validate_mnemonic_words
from ...languages import detect_mnemonic_language, SUPPORTED_LANGUAGES, get_supported_language_codes
from ...entropy.custom import validate_entropy_quality
from ...exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidateCommand(BaseCommand):
    """Advanced validation command with multiple validation modes."""
    
    def __init__(self):
        super().__init__(
            name="validate",
            help_text="Comprehensive validation of mnemonics, backups, and entropy",
            description="Advanced validation command with multiple validation modes including basic mnemonic validation, cross-tool compatibility testing, backup file integrity verification, batch validation for multiple files, and advanced entropy analysis."
        )
        self.validation_results: Dict[str, Any] = {}
        
    def add_arguments(self, parser) -> None:
        """Add command-specific arguments."""
        # Input sources (mutually exclusive group)
        input_group = parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument(
            "-m", "--mnemonic",
            help="Mnemonic phrase to validate (quoted string)"
        )
        input_group.add_argument(
            "-i", "--input-file",
            type=Path,
            help="File containing mnemonic or backup data"
        )
        input_group.add_argument(
            "--batch",
            type=Path,
            help="Directory or pattern for batch validation"
        )
        
        # Validation modes
        parser.add_argument(
            "--mode",
            choices=["basic", "advanced", "compatibility", "entropy", "backup"],
            default="basic",
            help="Validation mode (default: basic)"
        )
        
        # Output options
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Verbose output with detailed analysis"
        )
        parser.add_argument(
            "--quiet", "-q",
            action="store_true",
            help="Quiet mode - only show pass/fail status"
        )
        
        # Validation options
        parser.add_argument(
            "--language", "-l",
            choices=get_supported_language_codes(),
            help="Expected language (auto-detect if not specified)"
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Strict validation mode with enhanced checks"
        )
        parser.add_argument(
            "--check-entropy",
            action="store_true",
            help="Include entropy quality analysis"
        )
        
        # Backup verification options
        parser.add_argument(
            "--shard-files",
            nargs="*",
            help="Existing shard files to test for backup verification"
        )
        parser.add_argument(
            "--group-config",
            default="3-of-5",
            help="Group configuration for backup testing (default: 3-of-5)"
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=1,
            help="Number of round-trip iterations for backup testing (default: 1)"
        )
        parser.add_argument(
            "--stress-test",
            action="store_true",
            help="Enable stress testing with multiple iterations"
        )
        
    def handle(self, args) -> int:
        """Handle the validate command execution."""
        return self.execute(args)
        
    def execute(self, args) -> int:
        """Execute the validate command."""
        try:
            # Check which input mode to use
            if hasattr(args, 'batch') and args.batch:
                return self._batch_validate(args)
            elif hasattr(args, 'input_file') and args.input_file:
                return self._validate_file(args)
            elif hasattr(args, 'mnemonic') and args.mnemonic:
                return self._validate_mnemonic(args)
            else:
                raise ValueError("No valid input provided (mnemonic, input_file, or batch)")
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            if hasattr(args, 'json') and args.json:
                self._output_json_error(str(e))
            else:
                self._error(f"Validation failed: {e}")
            return 1
            
    def _validate_mnemonic(self, args) -> int:
        """Validate a single mnemonic phrase."""
        mnemonic = args.mnemonic.strip()
        
        # Initialize validation results
        self.validation_results = {
            "input": mnemonic,
            "input_type": "mnemonic",
            "mode": args.mode,
            "timestamp": self._get_timestamp(),
            "checks": {},
            "overall_status": "unknown"
        }
        
        # Perform validation based on mode
        if args.mode == "basic":
            success = self._basic_validation(mnemonic, args)
        elif args.mode == "advanced":
            success = self._advanced_validation(mnemonic, args)
        elif args.mode == "compatibility":
            success = self._compatibility_validation(mnemonic, args)
        elif args.mode == "entropy":
            success = self._entropy_validation(mnemonic, args)
        elif args.mode == "backup":
            success = self._backup_validation(mnemonic, args)
        else:
            raise ValueError(f"Unknown validation mode: {args.mode}")
            
        # Set overall status if not already set by comprehensive analysis
        if self.validation_results.get("overall_status") == "unknown":
            self.validation_results["overall_status"] = "pass" if success else "fail"
        
        # Output results
        self._output_results(args)
        
        return 0 if success else 1
        
    def _basic_validation(self, mnemonic: str, args) -> bool:
        """Perform basic mnemonic validation."""
        checks = self.validation_results["checks"]
        overall_success = True
        
        # 1. Format validation (parse into words)
        try:
            words = mnemonic.strip().split()
            word_count = len(words)
            
            # Validate word format and count
            validate_mnemonic_words(words)
            checks["format"] = {
                "status": "pass",
                "word_count": word_count,
                "message": f"Valid format with {word_count} words"
            }
        except ValidationError as e:
            checks["format"] = {
                "status": "fail",
                "error": str(e),
                "message": "Invalid mnemonic format"
            }
            overall_success = False
            
        # 2. Language detection
        try:
            detected_lang_info = detect_mnemonic_language(mnemonic)
            if detected_lang_info:
                detected_lang = detected_lang_info.code
                expected_lang = args.language or detected_lang
                
                checks["language"] = {
                    "status": "pass",
                    "detected": detected_lang,
                    "expected": expected_lang,
                    "match": detected_lang == expected_lang,
                    "message": f"Language: {detected_lang_info.name}"
                }
                
                if args.language and detected_lang != args.language:
                    expected_lang_info = SUPPORTED_LANGUAGES.get(args.language)
                    expected_name = expected_lang_info.name if expected_lang_info else args.language
                    checks["language"]["status"] = "warning"
                    checks["language"]["message"] += f" (expected {expected_name})"
            else:
                checks["language"] = {
                    "status": "fail",
                    "error": "Language detection failed",
                    "message": "Could not detect mnemonic language"
                }
                overall_success = False
                
        except Exception as e:
            checks["language"] = {
                "status": "fail",
                "error": str(e),
                "message": "Language detection failed"
            }
            overall_success = False
            
        # 3. Checksum validation
        if "language" in checks and checks["language"]["status"] in ["pass", "warning"]:
            try:
                # Use BIP utils enum for checksum validation
                detected_lang_info = detect_mnemonic_language(mnemonic)
                if detected_lang_info:
                    is_valid = validate_mnemonic_checksum(mnemonic, detected_lang_info.bip_enum)
                else:
                    # Fallback to auto-detection in the function
                    is_valid = validate_mnemonic_checksum(mnemonic)
                    
                checks["checksum"] = {
                    "status": "pass" if is_valid else "fail",
                    "message": "Valid BIP-39 checksum" if is_valid else "Invalid BIP-39 checksum"
                }
                if not is_valid:
                    overall_success = False
            except Exception as e:
                checks["checksum"] = {
                    "status": "fail",
                    "error": str(e),
                    "message": "Checksum validation failed"
                }
                overall_success = False
                
        return overall_success
        
    def _advanced_validation(self, mnemonic: str, args) -> bool:
        """Perform advanced validation with comprehensive analysis."""
        try:
            # Use the new unified analysis engine
            from ...validation.analysis import analyze_mnemonic_comprehensive
            
            expected_language = getattr(args, 'language', None)
            strict_mode = getattr(args, 'strict', False)
            
            # Perform comprehensive analysis
            analysis_result = analyze_mnemonic_comprehensive(
                mnemonic, 
                expected_language=expected_language,
                strict_mode=strict_mode
            )
            
            # Update validation results with comprehensive analysis
            self.validation_results.update(analysis_result)
            
            # Determine success based on comprehensive analysis
            return analysis_result.get("overall_score", 0) >= 70
            
        except Exception as e:
            logger.error(f"Advanced validation failed: {e}")
            # Fallback to basic validation
            success = self._basic_validation(mnemonic, args)
            
            checks = self.validation_results["checks"]
            
            # Additional advanced checks
            if args.strict:
                # Check for common weak patterns
                self._check_weak_patterns(mnemonic, checks)
                
            if args.check_entropy:
                # Analyze entropy quality
                self._analyze_mnemonic_entropy(mnemonic, checks)
                
            return success and all(
                check.get("status") != "fail" 
                for check in checks.values()
            )
        
    def _compatibility_validation(self, mnemonic: str, args) -> bool:
        """Perform cross-tool compatibility validation."""
        # Start with basic validation
        success = self._basic_validation(mnemonic, args)
        
        try:
            # Use the new cross-tool compatibility testing
            from ...validation.cross_tool import test_cross_tool_compatibility, get_available_tools
            
            checks = self.validation_results["checks"]
            
            # Check if any external tools are available
            available_tools = get_available_tools()
            
            if not available_tools:
                checks["compatibility"] = {
                    "status": "warning",
                    "message": "No external tools available for compatibility testing",
                    "recommendation": "Install external tools like 'shamir-mnemonic[cli]' for comprehensive testing"
                }
            else:
                # Perform cross-tool compatibility testing
                compatibility_result = test_cross_tool_compatibility(mnemonic)
                
                # Add compatibility results to validation
                checks["compatibility"] = {
                    "status": "pass" if compatibility_result.get("compatibility_score", 0) >= 80 else "warning",
                    "compatibility_score": compatibility_result.get("compatibility_score", 0),
                    "tools_tested": compatibility_result.get("tools_tested", []),
                    "overall_status": compatibility_result.get("overall_status", "unknown"),
                    "message": f"Compatibility score: {compatibility_result.get('compatibility_score', 0)}% ({compatibility_result.get('overall_status', 'unknown')})"
                }
                
                # Add detailed results if verbose
                if getattr(args, 'verbose', False):
                    checks["compatibility"]["detailed_results"] = compatibility_result
                    
        except Exception as e:
            logger.error(f"Compatibility validation failed: {e}")
            checks = self.validation_results["checks"]
            checks["compatibility"] = {
                "status": "error",
                "error": str(e),
                "message": f"Cross-tool compatibility testing failed: {e}"
            }
        
        return success
        
    def _entropy_validation(self, mnemonic: str, args) -> bool:
        """Perform entropy-focused validation."""
        # Start with basic validation
        success = self._basic_validation(mnemonic, args)
        
        try:
            # Use the new unified analysis engine for detailed entropy analysis
            from ...validation.analysis import analyze_mnemonic_comprehensive
            
            # Perform comprehensive analysis with focus on entropy
            analysis_result = analyze_mnemonic_comprehensive(
                mnemonic, 
                expected_language=getattr(args, 'language', None),
                strict_mode=True  # Use strict mode for entropy analysis
            )
            
            # Extract entropy-specific results
            checks = self.validation_results["checks"]
            if "entropy_analysis" in analysis_result.get("checks", {}):
                checks["entropy_analysis"] = analysis_result["checks"]["entropy_analysis"]
            else:
                # Fallback to basic entropy analysis
                self._analyze_mnemonic_entropy(mnemonic, checks)
                
        except Exception as e:
            logger.error(f"Entropy validation failed: {e}")
            # Fallback to basic entropy analysis
            checks = self.validation_results["checks"]
            self._analyze_mnemonic_entropy(mnemonic, checks)
        
        return success
        
    def _backup_validation(self, mnemonic: str, args) -> bool:
        """Perform comprehensive backup validation."""
        try:
            from ...validation.backup_verification import verify_backup_integrity
            
            # Perform backup verification
            backup_results = verify_backup_integrity(
                mnemonic=mnemonic,
                shard_files=getattr(args, 'shard_files', None),
                group_config=getattr(args, 'group_config', '3-of-5'),
                iterations=getattr(args, 'iterations', 1),
                stress_test=getattr(args, 'stress_test', False),
            )
            
            # Update validation results with backup verification data
            self.validation_results.update({
                "backup_verification": backup_results,
                "overall_status": backup_results.get("overall_status", "unknown"),
                "overall_score": backup_results.get("overall_score", 0),
                "checks": {
                    "backup_integrity": {
                        "status": backup_results.get("overall_status", "unknown"),
                        "score": backup_results.get("overall_score", 0),
                        "tests_performed": backup_results.get("tests_performed", []),
                        "duration_ms": backup_results.get("total_duration_ms", 0),
                        "message": f"Backup verification: {backup_results.get('overall_status', 'unknown')} ({backup_results.get('overall_score', 0)}/100)"
                    }
                }
            })
            
            # Add errors and warnings if any
            if backup_results.get("errors"):
                self.validation_results["errors"] = backup_results["errors"]
                
            if backup_results.get("warnings"):
                self.validation_results["warnings"] = backup_results["warnings"]
                
            if backup_results.get("recommendations"):
                self.validation_results["recommendations"] = backup_results["recommendations"]
            
            # Return success based on overall score
            return backup_results.get("overall_score", 0) >= 70
            
        except ImportError:
            # Backup verification module not available
            self.validation_results["checks"]["backup_verification"] = {
                "status": "error",
                "error": "Backup verification module not available",
                "message": "Install backup verification dependencies"
            }
            return False
            
        except Exception as e:
            logger.error(f"Backup validation failed: {e}")
            self.validation_results["checks"]["backup_verification"] = {
                "status": "error",
                "error": str(e),
                "message": "Backup validation failed"
            }
            return False
        
    def _check_weak_patterns(self, mnemonic: str, checks: Dict[str, Any]) -> None:
        """Check for weak mnemonic patterns."""
        words = mnemonic.split()
        
        # Check for repeated words
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
            
        repeated_words = [word for word, count in word_counts.items() if count > 1]
        
        if repeated_words:
            checks["weak_patterns"] = {
                "status": "warning",
                "repeated_words": repeated_words,
                "message": f"Contains repeated words: {', '.join(repeated_words)}"
            }
        else:
            checks["weak_patterns"] = {
                "status": "pass",
                "message": "No obvious weak patterns detected"
            }
            
    def _analyze_mnemonic_entropy(self, mnemonic: str, checks: Dict[str, Any]) -> None:
        """Analyze entropy quality of the mnemonic."""
        try:
            # For this basic implementation, provide simplified entropy metrics
            # In a full implementation, we'd convert the mnemonic back to entropy
            words = mnemonic.split()
            
            # Basic entropy metrics
            checks["entropy_analysis"] = {
                "status": "info",
                "word_count": len(words),
                "unique_words": len(set(words)),
                "estimated_bits": len(words) * 11,  # Each BIP-39 word represents ~11 bits
                "message": f"Estimated entropy: {len(words) * 11} bits from {len(words)} words"
            }
            
        except Exception as e:
            checks["entropy_analysis"] = {
                "status": "error",
                "error": str(e),
                "message": "Entropy analysis failed"
            }
            
    def _validate_file(self, args) -> int:
        """Validate a file containing mnemonic or backup data."""
        try:
            content = args.input_file.read_text().strip()
            
            # Update args to validate the file content
            args.mnemonic = content
            
            # Add file info to results
            self.validation_results = {
                "input_file": str(args.input_file),
                "input_type": "file",
                "file_size": args.input_file.stat().st_size
            }
            
            return self._validate_mnemonic(args)
            
        except Exception as e:
            logger.error(f"Failed to read file {args.input_file}: {e}")
            if args.json:
                self._output_json_error(f"File read error: {e}")
            else:
                self._error(f"Failed to read file: {e}")
            return 1
            
    def _batch_validate(self, args) -> int:
        """Perform batch validation on multiple files."""
        try:
            from ...validation.batch import validate_batch_files
            from ...validation.formatters import format_validation_output
            
            # Convert batch path to file patterns
            batch_path = str(args.batch)
            
            # Determine file patterns based on input
            if Path(batch_path).is_dir():
                # Directory - look for common mnemonic file patterns
                file_patterns = [
                    f"{batch_path}/*.txt",
                    f"{batch_path}/*.mnemonic",
                    f"{batch_path}/*.seed",
                ]
            else:
                # Assume it's a glob pattern
                file_patterns = [batch_path]
            
            logger.info(f"Starting batch validation with patterns: {file_patterns}")
            
            # Perform batch validation
            batch_results = validate_batch_files(
                file_patterns=file_patterns,
                expected_language=getattr(args, 'language', None),
                strict_mode=getattr(args, 'strict', False),
                fail_fast=False,  # Don't fail fast for batch operations
                include_analysis=(args.mode != "basic"),  # Include full analysis for advanced modes
                max_workers=None,  # Use default worker count
            )
            
            # Output results based on format
            if args.json:
                print(json.dumps(batch_results, indent=2))
            elif args.quiet:
                # Just show summary in quiet mode
                summary = batch_results.get("summary", {})
                success_rate = summary.get("success_rate", 0)
                status = "PASS" if success_rate >= 90 else "PARTIAL" if success_rate >= 50 else "FAIL"
                print(f"{status} ({success_rate:.1f}%)")
            else:
                # Use the new formatter for human-readable output
                formatted_output = format_validation_output(
                    batch_results,
                    output_format="text",
                    verbose=getattr(args, 'verbose', False),
                    use_colors=True,
                    use_symbols=True,
                )
                print(formatted_output)
            
            # Determine exit code based on results
            summary = batch_results.get("summary", {})
            success_rate = summary.get("success_rate", 0)
            
            if success_rate >= 90:
                return 0  # All good
            elif success_rate >= 50:
                return 2  # Partial success
            else:
                return 1  # Mostly failed
                
        except Exception as e:
            logger.error(f"Batch validation failed: {e}")
            if args.json:
                self._output_json_error(f"Batch validation error: {e}")
            else:
                self._error(f"Batch validation failed: {e}")
            return 1
        
    def _output_results(self, args) -> None:
        """Output validation results in the requested format."""
        if args.json:
            print(json.dumps(self.validation_results, indent=2))
        elif args.quiet:
            status = self.validation_results.get("overall_status", "unknown")
            print(status.upper())
        else:
            # Use the new formatter for enhanced human-readable output
            try:
                from ...validation.formatters import format_validation_output
                formatted_output = format_validation_output(
                    self.validation_results,
                    output_format="text",
                    verbose=getattr(args, 'verbose', False),
                    use_colors=True,
                    use_symbols=True,
                )
                print(formatted_output)
            except ImportError:
                # Fallback to original formatting if formatters not available
                self._format_human_readable_output(args)
            
    def _format_human_readable_output(self, args) -> None:
        """Format human-readable validation output."""
        results = self.validation_results
        
        # Header
        print(f"\n🔍 SSeed Validation Report")
        print(f"{'=' * 50}")
        print(f"Mode: {results.get('mode', 'unknown').title()}")
        print(f"Timestamp: {results.get('timestamp', 'unknown')}")
        
        if 'input_file' in results:
            print(f"Input File: {results['input_file']}")
            
        print()
        
        # Check results
        checks = results.get("checks", {})
        for check_name, check_data in checks.items():
            status = check_data.get("status", "unknown")
            message = check_data.get("message", "No message")
            
            # Status icon
            if status == "pass":
                icon = "✅"
            elif status == "fail":
                icon = "❌"
            elif status == "warning":
                icon = "⚠️"
            elif status == "info":
                icon = "ℹ️"
            else:
                icon = "❓"
                
            print(f"{icon} {check_name.replace('_', ' ').title()}: {message}")
            
            # Show additional details in verbose mode
            if args.verbose and "error" in check_data:
                print(f"   Error: {check_data['error']}")
                
        # Overall status
        print()
        overall_status = results.get("overall_status", "unknown")
        if overall_status == "pass":
            print("🎉 Overall Status: PASS")
        elif overall_status == "fail":
            print("💥 Overall Status: FAIL")
        else:
            print(f"❓ Overall Status: {overall_status.upper()}")
            
    def _output_json_error(self, error_message: str) -> None:
        """Output error in JSON format."""
        error_result = {
            "overall_status": "error",
            "error": error_message,
            "timestamp": self._get_timestamp()
        }
        print(json.dumps(error_result, indent=2))
        
    def _error(self, message: str) -> None:
        """Output error message to stderr."""
        print(f"Error: {message}", file=sys.stderr)
        
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat() 