"""Batch validation functionality for processing multiple files concurrently.

This module provides efficient batch processing capabilities for validating
multiple mnemonic files with configurable concurrency and error handling.
"""

import glob
import logging
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from ..exceptions import (
    FileError,
    ValidationError,
)
from ..file_operations.readers import read_mnemonic_from_file
from .analysis import analyze_mnemonic_comprehensive

logger = logging.getLogger(__name__)


class BatchValidationResult:
    """Results of batch validation operation."""

    def __init__(self) -> None:
        self.total_files: int = 0
        self.processed_files: int = 0
        self.passed_files: int = 0
        self.failed_files: int = 0
        self.error_files: int = 0
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.total_duration_ms: float = 0.0
        self.average_score: float = 0.0
        self.file_results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.summary_stats: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch result to dictionary."""
        return {
            "summary": {
                "total_files": self.total_files,
                "processed_files": self.processed_files,
                "passed_files": self.passed_files,
                "failed_files": self.failed_files,
                "error_files": self.error_files,
                "success_rate": self.get_success_rate(),
                "average_score": self.average_score,
                "total_duration_ms": self.total_duration_ms,
            },
            "statistics": self.summary_stats,
            "file_results": self.file_results,
            "errors": self.errors,
        }

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.processed_files == 0:
            return 0.0
        return (self.passed_files / self.processed_files) * 100.0

    def add_file_result(self, file_path: str, analysis_result: Dict[str, Any]) -> None:
        """Add a file validation result."""
        file_result = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "analysis": analysis_result,
            "passed": analysis_result.get("overall_score", 0) >= 70,
        }
        self.file_results.append(file_result)

        if file_result["passed"]:
            self.passed_files += 1
        else:
            self.failed_files += 1

    def add_error(self, file_path: str, error: str) -> None:
        """Add a file processing error."""
        error_result = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "error": error,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        self.errors.append(error_result)
        self.error_files += 1

    def calculate_statistics(self) -> None:
        """Calculate summary statistics from file results."""
        if not self.file_results:
            return

        scores = [
            r["analysis"]["overall_score"]
            for r in self.file_results
            if "overall_score" in r["analysis"]
        ]

        if scores:
            self.average_score = sum(scores) / len(scores)

            self.summary_stats = {
                "score_distribution": {
                    "min": min(scores),
                    "max": max(scores),
                    "average": self.average_score,
                    "median": sorted(scores)[len(scores) // 2],
                },
                "quality_distribution": {
                    "excellent": len([s for s in scores if s >= 90]),
                    "good": len([s for s in scores if 80 <= s < 90]),
                    "acceptable": len([s for s in scores if 70 <= s < 80]),
                    "poor": len([s for s in scores if 50 <= s < 70]),
                    "fail": len([s for s in scores if s < 50]),
                },
                "language_distribution": {},
                "word_count_distribution": {},
            }

            # Language distribution
            languages = [
                r["analysis"]["checks"]["language"]["detected"]
                for r in self.file_results
                if "language" in r["analysis"]["checks"]
                and "detected" in r["analysis"]["checks"]["language"]
            ]

            for lang in set(languages):
                self.summary_stats["language_distribution"][lang] = languages.count(
                    lang
                )

            # Word count distribution
            word_counts = [
                r["analysis"]["checks"]["format"]["word_count"]
                for r in self.file_results
                if "format" in r["analysis"]["checks"]
                and "word_count" in r["analysis"]["checks"]["format"]
            ]

            for count in set(word_counts):
                self.summary_stats["word_count_distribution"][str(count)] = (
                    word_counts.count(count)
                )


class BatchValidator:
    """Efficient batch validation with concurrent processing."""

    def __init__(self, max_workers: Optional[int] = None):
        """Initialize batch validator.

        Args:
            max_workers: Maximum number of concurrent workers (default: CPU count)
        """
        self.max_workers = max_workers or min(32, (Path.cwd().stat().st_dev or 1) + 4)

    def validate_files(
        self,
        file_patterns: List[str],
        expected_language: Optional[str] = None,
        strict_mode: bool = False,
        fail_fast: bool = False,
        include_analysis: bool = True,
    ) -> BatchValidationResult:
        """Validate multiple files using patterns.

        Args:
            file_patterns: List of file patterns (glob supported)
            expected_language: Expected language for all files
            strict_mode: Enable strict validation mode
            fail_fast: Stop on first error
            include_analysis: Include full analysis in results

        Returns:
            BatchValidationResult with aggregated results
        """
        result = BatchValidationResult()
        result.start_time = time.perf_counter()

        try:
            # Expand file patterns
            file_paths = self._expand_file_patterns(file_patterns)
            result.total_files = len(file_paths)

            if not file_paths:
                logger.warning("No files found matching patterns: %s", file_patterns)
                return result

            logger.info("Starting batch validation of %d files", len(file_paths))

            # Process files concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all validation tasks
                future_to_file = {
                    executor.submit(
                        self._validate_single_file,
                        file_path,
                        expected_language,
                        strict_mode,
                        include_analysis,
                    ): file_path
                    for file_path in file_paths
                }

                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    result.processed_files += 1

                    try:
                        file_result = future.result()
                        if file_result["success"]:
                            result.add_file_result(file_path, file_result["analysis"])
                        else:
                            result.add_error(file_path, file_result["error"])

                    except Exception as e:
                        logger.error("Unexpected error processing %s: %s", file_path, e)
                        result.add_error(file_path, f"Unexpected error: {str(e)}")

                    # Fail fast if requested
                    if fail_fast and result.error_files > 0:
                        logger.warning(
                            "Stopping batch validation due to fail_fast mode"
                        )
                        break

            # Calculate final statistics
            result.calculate_statistics()

            result.end_time = time.perf_counter()
            result.total_duration_ms = (result.end_time - result.start_time) * 1000

            logger.info(
                "Batch validation completed: %d/%d files processed, %.1f%% success rate, %.2fms total",
                result.processed_files,
                result.total_files,
                result.get_success_rate(),
                result.total_duration_ms,
            )

            return result

        except Exception as e:
            logger.error("Batch validation failed: %s", e)
            result.add_error("batch_operation", f"Batch validation failed: {str(e)}")
            return result

    def _expand_file_patterns(self, patterns: List[str]) -> List[str]:
        """Expand file patterns using glob."""
        file_paths = []

        for pattern in patterns:
            try:
                # Handle both absolute and relative paths
                if Path(pattern).is_absolute():
                    matches = glob.glob(pattern)
                else:
                    matches = glob.glob(pattern, recursive=True)

                # Filter to only include files (not directories)
                file_matches = [p for p in matches if Path(p).is_file()]
                file_paths.extend(file_matches)

                logger.debug(
                    "Pattern '%s' matched %d files", pattern, len(file_matches)
                )

            except Exception as e:
                logger.warning("Error expanding pattern '%s': %s", pattern, e)

        # Remove duplicates and sort
        unique_paths = sorted(set(file_paths))
        logger.debug("Total unique files found: %d", len(unique_paths))

        return unique_paths

    def _validate_single_file(
        self,
        file_path: str,
        expected_language: Optional[str],
        strict_mode: bool,
        include_analysis: bool,
    ) -> Dict[str, Any]:
        """Validate a single file.

        Returns:
            Dict with success flag, analysis result or error message
        """
        try:
            logger.debug("Validating file: %s", file_path)

            # Read mnemonic from file
            mnemonic = read_mnemonic_from_file(file_path)

            if not mnemonic or not mnemonic.strip():
                return {
                    "success": False,
                    "error": "File is empty or contains no valid mnemonic",
                }

            # Perform comprehensive analysis
            if include_analysis:
                analysis_result = analyze_mnemonic_comprehensive(
                    mnemonic.strip(),
                    expected_language=expected_language,
                    strict_mode=strict_mode,
                )
            else:
                # Basic validation only
                from ..bip39 import validate_mnemonic

                try:
                    validate_mnemonic(mnemonic.strip())
                    analysis_result = {
                        "overall_score": 80,  # Basic pass score
                        "overall_status": "pass",
                        "checks": {
                            "format": {"status": "pass"},
                            "checksum": {"status": "pass"},
                        },
                    }
                except Exception:
                    analysis_result = {
                        "overall_score": 0,
                        "overall_status": "fail",
                        "checks": {
                            "format": {"status": "fail"},
                            "checksum": {"status": "fail"},
                        },
                    }

            return {"success": True, "analysis": analysis_result}

        except FileError as e:
            return {"success": False, "error": f"File read error: {str(e)}"}
        except ValidationError as e:
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


def validate_batch_files(
    file_patterns: List[str],
    expected_language: Optional[str] = None,
    strict_mode: bool = False,
    fail_fast: bool = False,
    include_analysis: bool = True,
    max_workers: Optional[int] = None,
) -> Dict[str, Any]:
    """Public interface for batch validation.

    Args:
        file_patterns: List of file patterns (glob supported)
        expected_language: Expected language for all files
        strict_mode: Enable strict validation mode
        fail_fast: Stop on first error
        include_analysis: Include full analysis in results
        max_workers: Maximum concurrent workers

    Returns:
        Dictionary with batch validation results
    """
    validator = BatchValidator(max_workers=max_workers)
    result = validator.validate_files(
        file_patterns=file_patterns,
        expected_language=expected_language,
        strict_mode=strict_mode,
        fail_fast=fail_fast,
        include_analysis=include_analysis,
    )
    return result.to_dict()
