"""Backup verification module for comprehensive SLIP-39 backup testing."""

import logging
import tempfile
import time
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
        self.timing_data: Dict[str, float] = {}
        self.overall_score: int = 0
        self.is_valid: bool = False

    def add_test_result(self, test_name: str, result: Dict[str, Any]) -> None:
        """Add a test result."""
        self.tests_performed.append(test_name)
        self.test_results[test_name] = result

        if not result.get("passed", False):
            self.errors.append(f"{test_name}: {result.get('error', 'Unknown error')}")

    def add_timing(self, operation: str, duration: float) -> None:
        """Add timing data for an operation."""
        self.timing_data[operation] = duration

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)

    def calculate_score(self) -> None:
        """Calculate overall backup verification score."""
        if not self.tests_performed:
            self.overall_score = 0
            return

        passed_tests = sum(
            1 for test in self.test_results.values() if test.get("passed", False)
        )
        total_tests = len(self.tests_performed)

        base_score = (passed_tests / total_tests) * 100

        # Deduct points for warnings
        warning_penalty = len(self.warnings) * 5
        self.overall_score = max(0, int(base_score - warning_penalty))

        self.is_valid = self.overall_score >= 70

    def get_status_level(self) -> str:
        """Get status level based on score."""
        if self.overall_score >= 90:
            return "excellent"
        if self.overall_score >= 80:
            return "good"
        if self.overall_score >= 70:
            return "acceptable"
        if self.overall_score >= 50:
            return "poor"
        return "fail"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "is_valid": self.is_valid,
            "overall_score": self.overall_score,
            "status_level": self.get_status_level(),
            "tests_performed": self.tests_performed,
            "test_results": self.test_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "timing_data": self.timing_data,
            "mode": "backup_verification",
        }


class BackupVerifier:
    """Context manager for backup verification operations."""

    def __init__(
        self,
        mnemonic: str,
        shard_files: Optional[List[str]] = None,
        group_config: str = "3-of-5",
        iterations: int = 5,
        stress_test: bool = False,
    ):
        """Initialize backup verifier."""
        self.mnemonic = mnemonic
        self.shard_files = shard_files or []
        self.group_config = group_config
        self.iterations = iterations
        self.stress_test = stress_test
        self.temp_dir = None
        self.result = BackupVerificationResult()

    def __enter__(self):
        """Enter context manager."""
        self.temp_dir = tempfile.mkdtemp(prefix="backup_verification_")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.temp_dir:
            import shutil

            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning("Failed to cleanup temp directory: %s", e)

    def verify_backup_integrity(self) -> BackupVerificationResult:
        """Perform comprehensive backup verification."""
        try:
            # Test 1: Validate original mnemonic
            self._test_original_mnemonic()

            # Test 2: Verify existing shard files (if provided)
            if self.shard_files:
                self._test_existing_shards()

            # Test 3: Round-trip backup verification
            self._test_round_trip_backup()

            # Test 4: Multiple iteration testing
            if self.iterations > 1:
                self._test_multiple_iterations()

            # Test 5: Shard combination testing
            self._test_shard_combinations()

            # Test 6: Entropy consistency verification
            self._test_entropy_consistency()

            # Calculate final score and recommendations
            self.result.calculate_score()
            self._generate_recommendations()

            return self.result

        except Exception as e:
            logger.error("Backup verification failed: %s", e)
            self.result.add_test_result(
                "verification", {"passed": False, "error": str(e)}
            )
            self.result.calculate_score()
            return self.result

    def _test_original_mnemonic(self) -> None:
        """Test original mnemonic validity."""
        start_time = time.time()
        try:
            is_valid = validate_mnemonic(self.mnemonic)
            duration = time.time() - start_time

            self.result.add_test_result(
                "original_mnemonic",
                {
                    "passed": is_valid,
                    "duration": duration,
                    "details": "Original mnemonic validation",
                },
            )
            self.result.add_timing("mnemonic_validation", duration)

            if not is_valid:
                self.result.add_warning("Original mnemonic failed validation")

        except Exception as e:
            self.result.add_test_result(
                "original_mnemonic", {"passed": False, "error": str(e)}
            )

    def _test_existing_shards(self) -> None:
        """Test existing shard files."""
        start_time = time.time()
        try:
            shard_mnemonics = []
            for shard_file in self.shard_files:
                shard_mnemonic = read_mnemonic_from_file(shard_file)
                shard_mnemonics.append(shard_mnemonic)

            # Try to reconstruct from existing shards
            reconstructed = reconstruct_mnemonic_from_shards(shard_mnemonics)
            duration = time.time() - start_time

            # Verify reconstruction matches original
            matches_original = reconstructed.strip() == self.mnemonic.strip()

            self.result.add_test_result(
                "existing_shards",
                {
                    "passed": matches_original,
                    "duration": duration,
                    "shard_count": len(shard_mnemonics),
                    "reconstructed_matches": matches_original,
                },
            )
            self.result.add_timing("shard_reconstruction", duration)

            if not matches_original:
                self.result.add_warning(
                    "Existing shards do not reconstruct to original mnemonic"
                )

        except Exception as e:
            self.result.add_test_result(
                "existing_shards", {"passed": False, "error": str(e)}
            )

    def _test_round_trip_backup(self) -> None:
        """Test complete round-trip backup process."""
        start_time = time.time()
        try:
            # Parse group configuration
            group_threshold, groups = self._parse_group_config(self.group_config)

            # Generate shards
            generation_start = time.time()
            shards = create_slip39_shards(
                self.mnemonic, group_threshold=group_threshold, groups=groups
            )
            generation_time = time.time() - generation_start

            # Write shards to temporary files
            io_start = time.time()
            shard_files = []
            for i, shard in enumerate(shards):
                shard_file = f"{self.temp_dir}/shard_{i}.txt"
                write_mnemonic_to_file(shard, shard_file)
                shard_files.append(shard_file)
            io_time = time.time() - io_start

            # Read shards back
            read_start = time.time()
            read_shards = []
            for shard_file in shard_files:
                shard_content = read_mnemonic_from_file(shard_file)
                read_shards.append(shard_content)
            read_time = time.time() - read_start

            # Reconstruct mnemonic
            reconstruction_start = time.time()
            reconstructed = reconstruct_mnemonic_from_shards(read_shards)
            reconstruction_time = time.time() - reconstruction_start

            total_duration = time.time() - start_time

            # Verify reconstruction
            matches_original = reconstructed.strip() == self.mnemonic.strip()

            self.result.add_test_result(
                "round_trip_backup",
                {
                    "passed": matches_original,
                    "duration": total_duration,
                    "generation_time": generation_time,
                    "io_time": io_time,
                    "read_time": read_time,
                    "reconstruction_time": reconstruction_time,
                    "shard_count": len(shards),
                    "matches_original": matches_original,
                },
            )

            self.result.add_timing("total_round_trip", total_duration)
            self.result.add_timing("shard_generation", generation_time)
            self.result.add_timing("file_io", io_time + read_time)

            if not matches_original:
                self.result.add_warning(
                    "Round-trip backup failed to reconstruct original mnemonic"
                )

        except Exception as e:
            self.result.add_test_result(
                "round_trip_backup", {"passed": False, "error": str(e)}
            )

    def _test_multiple_iterations(self) -> None:
        """Test multiple backup iterations for consistency."""
        start_time = time.time()
        try:
            successful_iterations = 0
            iteration_times = []

            for i in range(self.iterations):
                try:
                    iteration_start = time.time()

                    # Parse group configuration
                    group_threshold, groups = self._parse_group_config(
                        self.group_config
                    )

                    # Generate and test shards
                    shards = create_slip39_shards(
                        self.mnemonic, group_threshold=group_threshold, groups=groups
                    )
                    reconstructed = reconstruct_mnemonic_from_shards(shards)

                    iteration_time = time.time() - iteration_start
                    iteration_times.append(iteration_time)

                    if reconstructed.strip() == self.mnemonic.strip():
                        successful_iterations += 1

                except Exception as e:
                    logger.warning("Iteration %d failed: %s", i, e)

            total_duration = time.time() - start_time
            success_rate = (successful_iterations / self.iterations) * 100
            avg_iteration_time = (
                sum(iteration_times) / len(iteration_times) if iteration_times else 0
            )

            self.result.add_test_result(
                "multiple_iterations",
                {
                    "passed": success_rate >= 95,  # 95% success rate required
                    "duration": total_duration,
                    "iterations": self.iterations,
                    "successful_iterations": successful_iterations,
                    "success_rate": success_rate,
                    "average_iteration_time": avg_iteration_time,
                },
            )

            self.result.add_timing("multi_iteration_test", total_duration)

            if success_rate < 100:
                self.result.add_warning(
                    f"Only {success_rate:.1f}% of iterations successful"
                )

        except Exception as e:
            self.result.add_test_result(
                "multiple_iterations", {"passed": False, "error": str(e)}
            )

    def _test_shard_combinations(self) -> None:
        """Test different shard combinations."""
        start_time = time.time()
        try:
            # Parse group configuration
            group_threshold, groups = self._parse_group_config(self.group_config)

            # Generate shards
            shards = create_slip39_shards(
                self.mnemonic, group_threshold=group_threshold, groups=groups
            )

            # Test minimum threshold
            threshold = groups[0][0]  # Get threshold from first group
            min_shards = shards[:threshold]
            reconstructed_min = reconstruct_mnemonic_from_shards(min_shards)
            min_success = reconstructed_min.strip() == self.mnemonic.strip()

            # Test with all shards
            reconstructed_all = reconstruct_mnemonic_from_shards(shards)
            all_success = reconstructed_all.strip() == self.mnemonic.strip()

            duration = time.time() - start_time

            self.result.add_test_result(
                "shard_combinations",
                {
                    "passed": min_success and all_success,
                    "duration": duration,
                    "threshold_test": min_success,
                    "all_shards_test": all_success,
                    "threshold": threshold,
                    "total_shards": len(shards),
                },
            )

            self.result.add_timing("shard_combination_test", duration)

            if not min_success:
                self.result.add_warning("Minimum threshold reconstruction failed")
            if not all_success:
                self.result.add_warning("All shards reconstruction failed")

        except Exception as e:
            self.result.add_test_result(
                "shard_combinations", {"passed": False, "error": str(e)}
            )

    def _test_entropy_consistency(self) -> None:
        """Test entropy consistency across operations."""
        start_time = time.time()
        try:
            # Generate multiple shard sets and verify consistency
            shard_sets = []
            for i in range(3):  # Generate 3 sets for comparison
                try:
                    group_threshold, groups = self._parse_group_config(
                        self.group_config
                    )
                    shards = create_slip39_shards(
                        self.mnemonic, group_threshold=group_threshold, groups=groups
                    )
                    reconstructed = reconstruct_mnemonic_from_shards(shards)
                    shard_sets.append(reconstructed.strip())
                except Exception as e:
                    logger.warning("Entropy test iteration %d failed: %s", i, e)

            # Check consistency
            all_consistent = all(
                shard_set == self.mnemonic.strip() for shard_set in shard_sets
            )
            duration = time.time() - start_time

            self.result.add_test_result(
                "entropy_consistency",
                {
                    "passed": all_consistent,
                    "duration": duration,
                    "test_iterations": len(shard_sets),
                    "consistent_results": all_consistent,
                },
            )

            self.result.add_timing("entropy_consistency_test", duration)

            if not all_consistent:
                self.result.add_warning("Entropy consistency test failed")

        except Exception as e:
            self.result.add_test_result(
                "entropy_consistency", {"passed": False, "error": str(e)}
            )

    def _parse_group_config(self, config: str) -> tuple:
        """Parse group configuration string."""
        try:
            # Parse "3-of-5" format
            parts = config.split("-of-")
            if len(parts) != 2:
                raise ValueError(f"Invalid group config format: {config}")

            threshold = int(parts[0])
            total = int(parts[1])

            return 1, [(threshold, total)]  # Single group configuration

        except Exception as e:
            logger.error("Failed to parse group config: %s", e)
            return 1, [(3, 5)]  # Default fallback

    def _generate_recommendations(self) -> None:
        """Generate recommendations based on test results."""
        try:
            if self.result.overall_score >= 90:
                self.result.add_recommendation(
                    "Backup verification passed with excellent results"
                )
            elif self.result.overall_score >= 70:
                self.result.add_recommendation(
                    "Backup verification passed but consider improvements"
                )
            else:
                self.result.add_recommendation(
                    "Backup verification failed - review and fix issues"
                )

            # Performance recommendations
            total_time = sum(self.result.timing_data.values())
            if total_time > 10:  # More than 10 seconds
                self.result.add_recommendation(
                    "Consider optimizing backup process for better performance"
                )

            # Iteration recommendations
            if "multiple_iterations" in self.result.test_results:
                success_rate = self.result.test_results["multiple_iterations"].get(
                    "success_rate", 0
                )
                if success_rate < 100:
                    self.result.add_recommendation(
                        "Investigate consistency issues with backup process"
                    )

        except Exception as e:
            logger.error("Failed to generate recommendations: %s", e)


def verify_backup_integrity(
    mnemonic: str,
    shard_files: Optional[List[str]] = None,
    group_config: str = "3-of-5",
    iterations: int = 5,
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
            result = verifier.verify_backup_integrity()
            return result.to_dict()
    except Exception as e:
        logger.error("Backup verification failed: %s", e)
        return {
            "is_valid": False,
            "mode": "backup_verification",
            "error": str(e),
            "overall_score": 0,
        }
