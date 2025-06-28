"""Backup verification module for comprehensive SLIP-39 backup testing."""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from sseed.bip39 import validate_mnemonic
from sseed.file_operations.readers import read_mnemonic_from_file
from sseed.file_operations.writers import write_mnemonic_to_file
from sseed.slip39_operations import (
    create_slip39_shards,
    reconstruct_mnemonic_from_shards,
)

logger = logging.getLogger(__name__)


class BackupVerificationResult:
    """Container for backup verification results with comprehensive analysis."""

    def __init__(self):
        """Initialize backup verification result."""
        self.tests_performed: List[str] = []
        self.test_results: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.performance_metrics: Dict[str, float] = {}
        self.overall_score: int = 0
        self.total_duration_ms: float = 0.0
        self.timestamp: Optional[str] = None

    def add_test_result(
        self, test_name: str, success: bool, details: Dict[str, Any]
    ) -> None:
        """Add a test result to the verification."""
        self.tests_performed.append(test_name)
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": time.time(),
        }

    def add_error(self, error: str) -> None:
        """Add an error to the results."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the results."""
        self.warnings.append(warning)

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation to the results."""
        self.recommendations.append(recommendation)

    def calculate_score(self) -> int:
        """Calculate overall score based on test results."""
        if not self.test_results:
            return 0

        total_tests = len(self.test_results)
        successful_tests = sum(
            1 for result in self.test_results.values() if result["success"]
        )

        # Base score from test success rate
        base_score = int((successful_tests / total_tests) * 100)

        # Deduct points for errors and warnings
        error_penalty = min(len(self.errors) * 10, 30)
        warning_penalty = min(len(self.warnings) * 5, 20)

        final_score = max(0, base_score - error_penalty - warning_penalty)
        self.overall_score = final_score
        return final_score

    def get_status(self) -> str:
        """Get overall status based on score."""
        score = self.overall_score if self.overall_score > 0 else self.calculate_score()

        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "acceptable"
        elif score >= 50:
            return "poor"
        else:
            return "fail"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "tests_performed": self.tests_performed,
            "test_results": self.test_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "performance_metrics": self.performance_metrics,
            "overall_score": self.overall_score,
            "overall_status": self.get_status(),
            "total_duration_ms": self.total_duration_ms,
            "timestamp": self.timestamp or time.time(),
        }


class BackupVerifier:
    """Context manager for backup verification operations."""

    def __init__(
        self,
        mnemonic: str,
        shard_files: Optional[List[str]] = None,
        group_config: str = "3-of-5",
        iterations: int = 10,
        stress_test: bool = False,
    ):
        """Initialize backup verifier."""
        self.mnemonic = mnemonic
        self.shard_files = shard_files or []
        self.group_config = group_config
        self.iterations = iterations
        self.stress_test = stress_test
        self.temp_dir: Optional[str] = None
        self.result = BackupVerificationResult()

    def __enter__(self):
        """Enter context manager."""
        import shutil  # pylint: disable=import-outside-toplevel

        self.temp_dir = tempfile.mkdtemp(prefix="sseed_backup_verification_")
        logger.debug("Created temporary directory: %s", self.temp_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil  # pylint: disable=import-outside-toplevel

            shutil.rmtree(self.temp_dir)
            logger.debug("Cleaned up temporary directory: %s", self.temp_dir)

    def verify_backup_integrity(
        self,
        mnemonic: str,
        shard_files: Optional[List[str]] = None,
        group_config: str = "3-of-5",
        iterations: int = 10,
        stress_test: bool = False,
    ) -> BackupVerificationResult:
        """Perform comprehensive backup verification."""
        start_time = time.time()

        try:
            # Test 1: Validate original mnemonic
            self._test_original_mnemonic_validation()

            # Test 2: Validate existing shard files (if provided)
            if shard_files:
                self._test_existing_shard_files()

            # Test 3: Round-trip backup verification
            self._test_round_trip_backup()

            # Test 4: Multiple iteration testing
            if iterations > 1:
                self._test_multiple_iterations()

            # Test 5: Shard combination testing
            self._test_shard_combinations()

            # Test 6: Entropy consistency verification
            self._test_entropy_consistency()

            # Calculate final score and status
            self.result.calculate_score()

            # Add performance metrics
            self.result.total_duration_ms = (time.time() - start_time) * 1000

            # Generate recommendations
            self._generate_recommendations()

            return self.result

        except Exception as e:
            logger.error("Backup verification failed: %s", str(e))
            self.result.add_error(f"Verification failed: {e}")
            self.result.total_duration_ms = (time.time() - start_time) * 1000
            return self.result

    def _test_original_mnemonic_validation(self) -> None:
        """Test original mnemonic validation."""
        test_name = "original_mnemonic_validation"
        start_time = time.time()

        try:
            # Validate the original mnemonic
            is_valid = validate_mnemonic(self.mnemonic)

            details = {
                "mnemonic_valid": is_valid,
                "word_count": len(self.mnemonic.split()),
                "duration_ms": (time.time() - start_time) * 1000,
            }

            if is_valid:
                self.result.add_test_result(test_name, True, details)
            else:
                self.result.add_test_result(test_name, False, details)
                self.result.add_error("Original mnemonic failed validation")

        except Exception as e:
            details = {
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }
            self.result.add_test_result(test_name, False, details)
            self.result.add_error(f"Original mnemonic validation failed: {e}")

    def _test_existing_shard_files(self) -> None:
        """Test existing shard files if provided."""
        test_name = "existing_shard_files"
        start_time = time.time()

        try:
            if not self.shard_files:
                self.result.add_warning("No existing shard files provided for testing")
                return

            # Read and validate each shard file
            valid_shards = []
            for shard_file in self.shard_files:
                try:
                    shard_content = read_mnemonic_from_file(shard_file)
                    if shard_content:
                        valid_shards.append(shard_content)
                except Exception as e:
                    self.result.add_error(
                        f"Failed to read shard file {shard_file}: {e}"
                    )

            # Test reconstruction from existing shards
            if len(valid_shards) >= 3:  # Minimum threshold for typical SLIP-39
                try:
                    reconstructed = reconstruct_mnemonic_from_shards(valid_shards)
                    reconstruction_success = reconstructed == self.mnemonic

                    details = {
                        "shard_files_count": len(self.shard_files),
                        "valid_shards_count": len(valid_shards),
                        "reconstruction_success": reconstruction_success,
                        "duration_ms": (time.time() - start_time) * 1000,
                    }

                    self.result.add_test_result(
                        test_name, reconstruction_success, details
                    )

                    if not reconstruction_success:
                        self.result.add_error(
                            "Existing shards failed to reconstruct original mnemonic"
                        )

                except Exception as e:
                    details = {
                        "error": str(e),
                        "duration_ms": (time.time() - start_time) * 1000,
                    }
                    self.result.add_test_result(test_name, False, details)
                    self.result.add_error(f"Shard reconstruction failed: {e}")
            else:
                self.result.add_warning(
                    f"Insufficient shards for testing: {len(valid_shards)} < 3"
                )

        except Exception as e:
            details = {
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }
            self.result.add_test_result(test_name, False, details)
            self.result.add_error(f"Existing shard file testing failed: {e}")

    def _test_round_trip_backup(self) -> None:
        """Test complete round-trip backup process."""
        test_name = "round_trip_backup"
        start_time = time.time()

        try:
            # Parse group configuration
            group_threshold, groups = self._parse_group_config(self.group_config)

            # Generate shards
            generation_start = time.time()
            shards = create_slip39_shards(
                self.mnemonic, group_threshold=group_threshold, groups=groups
            )
            generation_time = (time.time() - generation_start) * 1000

            # Write shards to temporary files
            io_start = time.time()
            shard_files = []
            for i, shard in enumerate(shards):
                shard_file = os.path.join(self.temp_dir, f"shard_{i+1}.txt")
                write_mnemonic_to_file(shard, shard_file)
                shard_files.append(shard_file)
            io_time = (time.time() - io_start) * 1000

            # Read shards back from files
            read_start = time.time()
            read_shards = []
            for shard_file in shard_files:
                shard_content = read_mnemonic_from_file(shard_file)
                read_shards.append(shard_content)
            read_time = (time.time() - read_start) * 1000

            # Reconstruct mnemonic
            reconstruction_start = time.time()
            reconstructed = reconstruct_mnemonic_from_shards(
                read_shards[:group_threshold]
            )
            reconstruction_time = (time.time() - reconstruction_start) * 1000

            # Verify reconstruction
            success = reconstructed == self.mnemonic

            details = {
                "shards_generated": len(shards),
                "files_written": len(shard_files),
                "files_read": len(read_shards),
                "reconstruction_success": success,
                "generation_time_ms": generation_time,
                "io_time_ms": io_time,
                "read_time_ms": read_time,
                "reconstruction_time_ms": reconstruction_time,
                "total_duration_ms": (time.time() - start_time) * 1000,
            }

            self.result.add_test_result(test_name, success, details)

            if not success:
                self.result.add_error(
                    "Round-trip backup failed: reconstructed mnemonic doesn't match original"
                )

        except Exception as e:
            details = {
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }
            self.result.add_test_result(test_name, False, details)
            self.result.add_error(f"Round-trip backup testing failed: {e}")

    def _test_multiple_iterations(self) -> None:
        """Test multiple backup iterations for consistency."""
        test_name = "multiple_iterations"
        start_time = time.time()

        try:
            group_threshold, groups = self._parse_group_config(self.group_config)
            successful_iterations = 0

            for iteration in range(self.iterations):
                try:
                    # Generate shards for this iteration
                    shards = create_slip39_shards(
                        self.mnemonic, group_threshold=group_threshold, groups=groups
                    )

                    # Test reconstruction
                    reconstructed = reconstruct_mnemonic_from_shards(
                        shards[:group_threshold]
                    )

                    if reconstructed == self.mnemonic:
                        successful_iterations += 1

                except Exception as e:
                    logger.debug("Iteration %d failed: %s", iteration + 1, str(e))

            success_rate = (successful_iterations / self.iterations) * 100

            details = {
                "total_iterations": self.iterations,
                "successful_iterations": successful_iterations,
                "success_rate": success_rate,
                "duration_ms": (time.time() - start_time) * 1000,
            }

            success = success_rate >= 95  # 95% success rate threshold

            self.result.add_test_result(test_name, success, details)

            if success_rate < 100:
                self.result.add_warning(
                    f"Some iterations failed: {success_rate:.1f}% success rate"
                )

        except Exception as e:
            details = {
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }
            self.result.add_test_result(test_name, False, details)
            self.result.add_error(f"Multiple iteration testing failed: {e}")

    def _test_shard_combinations(self) -> None:
        """Test different combinations of shards for reconstruction."""
        test_name = "shard_combinations"
        start_time = time.time()

        try:
            group_threshold, groups = self._parse_group_config(self.group_config)

            # Generate shards
            shards = create_slip39_shards(
                self.mnemonic, group_threshold=group_threshold, groups=groups
            )

            # Test minimum threshold
            min_threshold_success = False
            try:
                reconstructed = reconstruct_mnemonic_from_shards(
                    shards[:group_threshold]
                )
                min_threshold_success = reconstructed == self.mnemonic
            except Exception as e:
                logger.debug("Minimum threshold test failed: %s", str(e))

            # Test with all shards
            all_shards_success = False
            try:
                reconstructed = reconstruct_mnemonic_from_shards(shards)
                all_shards_success = reconstructed == self.mnemonic
            except Exception as e:
                logger.debug("All shards test failed: %s", str(e))

            details = {
                "total_shards": len(shards),
                "group_threshold": group_threshold,
                "min_threshold_success": min_threshold_success,
                "all_shards_success": all_shards_success,
                "duration_ms": (time.time() - start_time) * 1000,
            }

            success = min_threshold_success and all_shards_success

            self.result.add_test_result(test_name, success, details)

            if not min_threshold_success:
                self.result.add_error("Minimum threshold shard combination failed")
            if not all_shards_success:
                self.result.add_error("All shards combination failed")

        except Exception as e:
            details = {
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }
            self.result.add_test_result(test_name, False, details)
            self.result.add_error(f"Shard combination testing failed: {e}")

    def _test_entropy_consistency(self) -> None:
        """Test entropy consistency across multiple operations."""
        test_name = "entropy_consistency"
        start_time = time.time()

        try:
            group_threshold, groups = self._parse_group_config(self.group_config)

            # Generate multiple sets of shards
            shard_sets = []
            for i in range(3):  # Test 3 sets
                try:
                    shards = create_slip39_shards(
                        self.mnemonic, group_threshold=group_threshold, groups=groups
                    )
                    shard_sets.append(shards)
                except Exception as e:
                    logger.debug("Shard set %d generation failed: %s", i + 1, str(e))

            # Test reconstruction from each set
            consistent_reconstructions = 0
            for i, shards in enumerate(shard_sets):
                try:
                    reconstructed = reconstruct_mnemonic_from_shards(
                        shards[:group_threshold]
                    )
                    if reconstructed == self.mnemonic:
                        consistent_reconstructions += 1
                except Exception as e:
                    logger.debug("Reconstruction from set %d failed: %s", i + 1, str(e))

            consistency_rate = (
                (consistent_reconstructions / len(shard_sets)) * 100
                if shard_sets
                else 0
            )

            details = {
                "shard_sets_generated": len(shard_sets),
                "consistent_reconstructions": consistent_reconstructions,
                "consistency_rate": consistency_rate,
                "duration_ms": (time.time() - start_time) * 1000,
            }

            success = consistency_rate >= 95

            self.result.add_test_result(test_name, success, details)

            if consistency_rate < 100:
                self.result.add_warning(
                    f"Entropy consistency issues: {consistency_rate:.1f}% consistency rate"
                )

        except Exception as e:
            details = {
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }
            self.result.add_test_result(test_name, False, details)
            self.result.add_error(f"Entropy consistency testing failed: {e}")

    def _parse_group_config(self, config: str) -> tuple:
        """Parse group configuration string."""
        try:
            # Parse "3-of-5" format
            parts = config.split("-of-")
            if len(parts) != 2:
                raise ValueError(f"Invalid group configuration format: {config}")

            threshold = int(parts[0])
            total = int(parts[1])

            if threshold > total:
                raise ValueError(
                    f"Threshold ({threshold}) cannot be greater than total ({total})"
                )

            # Return in format expected by create_slip39_shards
            return 1, [(threshold, total)]  # Single group configuration

        except Exception as e:
            logger.error("Failed to parse group configuration '%s': %s", config, str(e))
            # Default fallback
            return 1, [(3, 5)]

    def _generate_recommendations(self) -> None:
        """Generate recommendations based on test results."""
        # Analyze test results and add recommendations
        failed_tests = [
            name
            for name, result in self.result.test_results.items()
            if not result["success"]
        ]

        if failed_tests:
            self.result.add_recommendation(
                f"Address failed tests: {', '.join(failed_tests)}"
            )

        if self.result.overall_score < 80:
            self.result.add_recommendation(
                "Consider regenerating backup with different parameters"
            )

        if len(self.result.warnings) > 2:
            self.result.add_recommendation(
                "Review warnings and consider backup quality improvements"
            )


def verify_backup_integrity(
    mnemonic: str,
    shard_files: Optional[List[str]] = None,
    group_config: str = "3-of-5",
    iterations: int = 10,
    stress_test: bool = False,
) -> Dict[str, Any]:
    """Verify backup integrity with comprehensive testing."""
    try:
        with BackupVerifier(
            mnemonic=mnemonic,
            shard_files=shard_files,
            group_config=group_config,
            iterations=iterations,
            stress_test=stress_test,
        ) as verifier:
            result = verifier.verify_backup_integrity(
                mnemonic, shard_files, group_config, iterations, stress_test
            )
            return result.to_dict()

    except Exception as e:
        logger.error("Backup verification failed: %s", str(e))
        error_result = BackupVerificationResult()
        error_result.add_error(f"Backup verification failed: {e}")
        return error_result.to_dict()
