"""Backup verification for comprehensive backup integrity testing.

This module provides backup verification capabilities including round-trip testing,
shard combination validation, and comprehensive backup integrity verification.
"""

import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from ..slip39_operations import create_slip39_shards, reconstruct_mnemonic_from_shards
from ..validation.crypto import validate_mnemonic_checksum
from ..validation.input import validate_mnemonic_words
from ..file_operations.readers import read_mnemonic_from_file
from ..file_operations.writers import write_mnemonic_to_file
from ..exceptions import ValidationError, FileError

logger = logging.getLogger(__name__)


class BackupVerificationResult:
    """Results of backup verification operation."""
    
    def __init__(self):
        self.original_mnemonic: str = ""
        self.test_type: str = ""
        self.overall_status: str = "unknown"
        self.overall_score: int = 0
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.total_duration_ms: float = 0.0
        self.tests_performed: List[str] = []
        self.test_results: Dict[str, Any] = {}
        self.shard_files: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert backup verification result to dictionary."""
        return {
            "test_type": self.test_type,
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "total_duration_ms": self.total_duration_ms,
            "tests_performed": self.tests_performed,
            "test_results": self.test_results,
            "shard_files": self.shard_files,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        
    def add_test_result(self, test_name: str, status: str, details: Dict[str, Any]) -> None:
        """Add a test result."""
        self.tests_performed.append(test_name)
        self.test_results[test_name] = {
            "status": status,
            "details": details,
        }
        
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)
        
    def calculate_overall_score(self) -> None:
        """Calculate overall verification score based on test results."""
        if not self.test_results:
            self.overall_score = 0
            self.overall_status = "fail"
            return
            
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result["status"] == "pass")
        total_tests = len(self.test_results)
        
        if total_tests == 0:
            self.overall_score = 0
            self.overall_status = "fail"
        else:
            self.overall_score = int((passed_tests / total_tests) * 100)
            
            if self.overall_score >= 90:
                self.overall_status = "excellent"
            elif self.overall_score >= 80:
                self.overall_status = "good"
            elif self.overall_score >= 70:
                self.overall_status = "acceptable"
            elif self.overall_score >= 50:
                self.overall_status = "poor"
            else:
                self.overall_status = "fail"


class BackupVerifier:
    """Comprehensive backup verification with round-trip testing."""
    
    def __init__(self):
        self.temp_dir: Optional[Path] = None
        
    def __enter__(self):
        """Context manager entry."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sseed_backup_verify_"))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            
    def _parse_group_config(self, group_config: str) -> tuple[int, list[tuple[int, int]]]:
        """Parse group configuration string."""
        if '-of-' in group_config:
            threshold_str, total_str = group_config.split('-of-')
            threshold = int(threshold_str)
            total = int(total_str)
            groups = [(threshold, total)]
            group_threshold = 1
        else:
            groups = [(3, 5)]
            group_threshold = 1
        return group_threshold, groups
            
    def verify_backup_integrity(
        self,
        mnemonic: str,
        shard_files: Optional[List[str]] = None,
        group_config: str = "3-of-5",
        iterations: int = 1,
        stress_test: bool = False,
    ) -> BackupVerificationResult:
        """Verify backup integrity through comprehensive testing."""
        result = BackupVerificationResult()
        result.start_time = time.perf_counter()
        result.original_mnemonic = mnemonic
        result.test_type = "comprehensive_backup_verification"
        
        try:
            # Test 1: Original mnemonic validation
            self._test_original_mnemonic(mnemonic, result)
            
            # Test 2: Existing shard files verification (if provided)
            if shard_files:
                result.shard_files = shard_files
                self._test_existing_shards(mnemonic, shard_files, result)
            
            # Test 3: Round-trip backup verification
            self._test_round_trip_backup(mnemonic, group_config, result)
            
            # Test 4: Multiple iteration testing
            if iterations > 1 or stress_test:
                test_iterations = max(iterations, 10 if stress_test else 1)
                self._test_multiple_iterations(mnemonic, group_config, test_iterations, result)
            
            # Test 5: Shard combination testing
            self._test_shard_combinations(mnemonic, group_config, result)
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            result.add_error(f"Verification failed: {e}")
            
        finally:
            result.end_time = time.perf_counter()
            result.total_duration_ms = (result.end_time - result.start_time) * 1000
            result.calculate_overall_score()
            
            # Add recommendations based on results
            self._generate_recommendations(result)
            
        return result
        
    def _test_original_mnemonic(self, mnemonic: str, result: BackupVerificationResult) -> None:
        """Test the original mnemonic validity."""
        try:
            words = mnemonic.strip().split()
            validate_mnemonic_words(words)
            is_valid = validate_mnemonic_checksum(mnemonic)
            
            if is_valid:
                result.add_test_result("original_mnemonic_validation", "pass", {
                    "word_count": len(words),
                    "checksum_valid": True,
                    "message": "Original mnemonic is valid"
                })
            else:
                result.add_test_result("original_mnemonic_validation", "fail", {
                    "word_count": len(words),
                    "checksum_valid": False,
                    "message": "Original mnemonic has invalid checksum"
                })
                result.add_error("Original mnemonic has invalid checksum")
                
        except ValidationError as e:
            result.add_test_result("original_mnemonic_validation", "fail", {
                "error": str(e),
                "message": "Original mnemonic validation failed"
            })
            result.add_error(f"Original mnemonic validation failed: {e}")
            
    def _test_existing_shards(self, original_mnemonic: str, shard_files: List[str], result: BackupVerificationResult) -> None:
        """Test existing shard files for reconstruction."""
        try:
            shard_contents = []
            valid_files = []
            
            for shard_file in shard_files:
                try:
                    shard_content = read_mnemonic_from_file(shard_file)
                    shard_contents.append(shard_content)
                    valid_files.append(shard_file)
                except Exception as e:
                    result.add_warning(f"Could not read shard file {shard_file}: {e}")
                    
            if not shard_contents:
                result.add_test_result("existing_shards_test", "fail", {
                    "error": "No valid shard files found",
                    "message": "Could not read any shard files"
                })
                return
                
            try:
                reconstructed_mnemonic = reconstruct_mnemonic_from_shards(shard_contents)
                
                if reconstructed_mnemonic.strip() == original_mnemonic.strip():
                    result.add_test_result("existing_shards_test", "pass", {
                        "shard_count": len(shard_contents),
                        "valid_files": len(valid_files),
                        "reconstruction_successful": True,
                        "message": "Existing shards successfully reconstruct original mnemonic"
                    })
                else:
                    result.add_test_result("existing_shards_test", "fail", {
                        "shard_count": len(shard_contents),
                        "valid_files": len(valid_files),
                        "reconstruction_successful": False,
                        "message": "Reconstructed mnemonic does not match original"
                    })
                    result.add_error("Reconstructed mnemonic does not match original")
                    
            except Exception as e:
                result.add_test_result("existing_shards_test", "fail", {
                    "shard_count": len(shard_contents),
                    "valid_files": len(valid_files),
                    "error": str(e),
                    "message": "Shard reconstruction failed"
                })
                result.add_error(f"Shard reconstruction failed: {e}")
                
        except Exception as e:
            result.add_test_result("existing_shards_test", "fail", {
                "error": str(e),
                "message": "Existing shards test failed"
            })
            result.add_error(f"Existing shards test failed: {e}")
            
    def _test_round_trip_backup(self, mnemonic: str, group_config: str, result: BackupVerificationResult) -> None:
        """Test round-trip backup generation and reconstruction."""
        try:
            if not self.temp_dir:
                raise ValueError("Temporary directory not available")
                
            # Generate shards
            start_time = time.perf_counter()
            group_threshold, groups = self._parse_group_config(group_config)
            shard_data = create_slip39_shards(mnemonic, group_threshold=group_threshold, groups=groups)
            generation_time = (time.perf_counter() - start_time) * 1000
            
            # Write shards to temporary files
            shard_files = []
            for i, shard in enumerate(shard_data):
                shard_file = self.temp_dir / f"shard_{i+1}.txt"
                write_mnemonic_to_file(shard, str(shard_file))
                shard_files.append(str(shard_file))
                
            # Read shards back
            start_time = time.perf_counter()
            read_shards = []
            for shard_file in shard_files:
                shard_content = read_mnemonic_from_file(shard_file)
                read_shards.append(shard_content)
            read_time = (time.perf_counter() - start_time) * 1000
            
            # Reconstruct mnemonic
            start_time = time.perf_counter()
            reconstructed_mnemonic = reconstruct_mnemonic_from_shards(read_shards)
            reconstruction_time = (time.perf_counter() - start_time) * 1000
            
            # Verify reconstruction matches original
            if reconstructed_mnemonic.strip() == mnemonic.strip():
                result.add_test_result("round_trip_backup", "pass", {
                    "shard_count": len(shard_data),
                    "generation_time_ms": generation_time,
                    "read_time_ms": read_time,
                    "reconstruction_time_ms": reconstruction_time,
                    "total_round_trip_time_ms": generation_time + read_time + reconstruction_time,
                    "message": "Round-trip backup verification successful"
                })
            else:
                result.add_test_result("round_trip_backup", "fail", {
                    "shard_count": len(shard_data),
                    "error": "Reconstructed mnemonic does not match original",
                    "message": "Round-trip backup verification failed"
                })
                result.add_error("Round-trip backup verification failed: mnemonic mismatch")
                
        except Exception as e:
            result.add_test_result("round_trip_backup", "fail", {
                "error": str(e),
                "message": "Round-trip backup test failed"
            })
            result.add_error(f"Round-trip backup test failed: {e}")
            
    def _test_multiple_iterations(self, mnemonic: str, group_config: str, iterations: int, result: BackupVerificationResult) -> None:
        """Test multiple backup iterations for consistency."""
        try:
            successful_iterations = 0
            total_time = 0.0
            
            for i in range(iterations):
                try:
                    start_time = time.perf_counter()
                    
                    group_threshold, groups = self._parse_group_config(group_config)
                    shard_data = create_slip39_shards(mnemonic, group_threshold=group_threshold, groups=groups)
                    reconstructed = reconstruct_mnemonic_from_shards(shard_data)
                    
                    iteration_time = (time.perf_counter() - start_time) * 1000
                    total_time += iteration_time
                    
                    if reconstructed.strip() == mnemonic.strip():
                        successful_iterations += 1
                    else:
                        result.add_warning(f"Iteration {i+1} failed: mnemonic mismatch")
                        
                except Exception as e:
                    result.add_warning(f"Iteration {i+1} failed: {e}")
                    
            success_rate = (successful_iterations / iterations) * 100
            average_time = total_time / iterations if iterations > 0 else 0
            
            if success_rate >= 95:
                status = "pass"
                message = f"Multiple iterations successful ({successful_iterations}/{iterations})"
            elif success_rate >= 80:
                status = "warning"
                message = f"Most iterations successful ({successful_iterations}/{iterations})"
            else:
                status = "fail"
                message = f"Too many iteration failures ({successful_iterations}/{iterations})"
                
            result.add_test_result("multiple_iterations", status, {
                "total_iterations": iterations,
                "successful_iterations": successful_iterations,
                "success_rate": success_rate,
                "average_time_ms": average_time,
                "total_time_ms": total_time,
                "message": message
            })
            
            if success_rate < 100:
                result.add_warning(f"Some iterations failed: {success_rate:.1f}% success rate")
                
        except Exception as e:
            result.add_test_result("multiple_iterations", "fail", {
                "error": str(e),
                "message": "Multiple iterations test failed"
            })
            result.add_error(f"Multiple iterations test failed: {e}")
            
    def _test_shard_combinations(self, mnemonic: str, group_config: str, result: BackupVerificationResult) -> None:
        """Test different shard combinations for reconstruction."""
        try:
            # Generate shards
            group_threshold, groups = self._parse_group_config(group_config)
            shard_data = create_slip39_shards(mnemonic, group_threshold=group_threshold, groups=groups)
            
            # Parse group configuration to understand threshold
            if '-of-' in group_config:
                threshold_str, total_str = group_config.split('-of-')
                threshold = int(threshold_str)
                total = int(total_str)
            else:
                threshold = 3
                total = len(shard_data)
                
            if len(shard_data) < threshold:
                result.add_test_result("shard_combinations", "fail", {
                    "error": f"Not enough shards generated: {len(shard_data)} < {threshold}",
                    "message": "Insufficient shards for combination testing"
                })
                return
                
            # Test minimum threshold combination
            test_shards = shard_data[:threshold]
            try:
                reconstructed = reconstruct_mnemonic_from_shards(test_shards)
                threshold_success = reconstructed.strip() == mnemonic.strip()
            except Exception:
                threshold_success = False
                
            # Test with all shards
            all_shards_success = False
            try:
                reconstructed_all = reconstruct_mnemonic_from_shards(shard_data)
                all_shards_success = reconstructed_all.strip() == mnemonic.strip()
            except Exception:
                all_shards_success = False
                
            combinations_tested = 2
            combinations_passed = sum([threshold_success, all_shards_success])
            
            if combinations_passed == combinations_tested:
                status = "pass"
                message = "All shard combinations successful"
            elif threshold_success:
                status = "warning"
                message = "Minimum threshold works, some combinations failed"
            else:
                status = "fail"
                message = "Minimum threshold combination failed"
                
            result.add_test_result("shard_combinations", status, {
                "threshold": threshold,
                "total_shards": len(shard_data),
                "combinations_tested": combinations_tested,
                "combinations_passed": combinations_passed,
                "threshold_success": threshold_success,
                "all_shards_success": all_shards_success,
                "message": message
            })
            
        except Exception as e:
            result.add_test_result("shard_combinations", "fail", {
                "error": str(e),
                "message": "Shard combinations test failed"
            })
            result.add_error(f"Shard combinations test failed: {e}")
            
    def _generate_recommendations(self, result: BackupVerificationResult) -> None:
        """Generate recommendations based on test results."""
        if result.overall_score >= 90:
            result.add_recommendation("Backup verification excellent - backup is reliable")
        elif result.overall_score >= 80:
            result.add_recommendation("Backup verification good - minor issues detected")
        elif result.overall_score < 70:
            result.add_recommendation("Consider regenerating backup with different parameters")
            
        if "existing_shards_test" in result.test_results:
            if result.test_results["existing_shards_test"]["status"] != "pass":
                result.add_recommendation("Verify existing shard files are not corrupted")


def verify_backup_integrity(
    mnemonic: str,
    shard_files: Optional[List[str]] = None,
    group_config: str = "3-of-5",
    iterations: int = 1,
    stress_test: bool = False,
) -> Dict[str, Any]:
    """Public interface for backup verification."""
    with BackupVerifier() as verifier:
        result = verifier.verify_backup_integrity(
            mnemonic=mnemonic,
            shard_files=shard_files,
            group_config=group_config,
            iterations=iterations,
            stress_test=stress_test,
        )
        return result.to_dict()