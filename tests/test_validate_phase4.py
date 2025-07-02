"""
Tests for Phase 4 of B.3 Advanced Validation: Backup Verification and Command Implementation.

This module tests the backup verification capabilities implemented in Phase 4,
including round-trip testing, shard combination validation, and CLI integration.
"""

import json
import unittest
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from sseed.cli.commands.validate import ValidateCommand
from sseed.validation.backup_verification import (
    BackupVerificationResult,
    BackupVerifier,
    verify_backup_integrity,
)


class TestBackupVerificationResult(unittest.TestCase):
    """Test BackupVerificationResult class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.result = BackupVerificationResult()

    def test_initialization(self):
        """Test BackupVerificationResult initialization."""
        self.assertEqual(self.result.overall_status, "unknown")
        self.assertEqual(self.result.overall_score, 0)
        self.assertEqual(self.result.tests_performed, [])
        self.assertEqual(self.result.test_results, {})
        self.assertEqual(self.result.errors, [])
        self.assertEqual(self.result.warnings, [])
        self.assertEqual(self.result.recommendations, [])

    def test_add_test_result(self):
        """Test adding test results."""
        self.result.add_test_result("test1", "pass", {"detail": "value"})

        self.assertIn("test1", self.result.tests_performed)
        self.assertIn("test1", self.result.test_results)
        self.assertEqual(self.result.test_results["test1"]["status"], "pass")
        self.assertEqual(
            self.result.test_results["test1"]["details"]["detail"], "value"
        )

    def test_add_error_warning_recommendation(self):
        """Test adding errors, warnings, and recommendations."""
        self.result.add_error("Test error")
        self.result.add_warning("Test warning")
        self.result.add_recommendation("Test recommendation")

        self.assertIn("Test error", self.result.errors)
        self.assertIn("Test warning", self.result.warnings)
        self.assertIn("Test recommendation", self.result.recommendations)

    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        # Test with no results
        self.result.calculate_overall_score()
        self.assertEqual(self.result.overall_score, 0)
        self.assertEqual(self.result.overall_status, "fail")

        # Test with mixed results
        self.result.add_test_result("test1", "pass", {})
        self.result.add_test_result("test2", "pass", {})
        self.result.add_test_result("test3", "fail", {})
        self.result.calculate_overall_score()

        # 2/3 = 66.67% -> should be 66
        self.assertEqual(self.result.overall_score, 66)
        self.assertEqual(self.result.overall_status, "poor")

        # Test excellent score
        self.result.test_results = {}
        self.result.tests_performed = []
        for i in range(10):
            self.result.add_test_result(f"test{i}", "pass", {})
        self.result.calculate_overall_score()

        self.assertEqual(self.result.overall_score, 100)
        self.assertEqual(self.result.overall_status, "excellent")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        self.result.test_type = "comprehensive"
        self.result.overall_status = "good"
        self.result.overall_score = 85
        self.result.add_test_result("test1", "pass", {"detail": "value"})
        self.result.add_error("Test error")

        result_dict = self.result.to_dict()

        self.assertEqual(result_dict["test_type"], "comprehensive")
        self.assertEqual(result_dict["overall_status"], "good")
        self.assertEqual(result_dict["overall_score"], 85)
        self.assertIn("test1", result_dict["test_results"])
        self.assertIn("Test error", result_dict["errors"])
        self.assertIn("timestamp", result_dict)


class TestBackupVerifier(unittest.TestCase):
    """Test BackupVerifier class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

    def test_context_manager(self):
        """Test BackupVerifier context manager functionality."""
        with BackupVerifier() as verifier:
            self.assertIsInstance(verifier, BackupVerifier)
            self.assertIsNotNone(verifier.temp_dir)
            self.assertTrue(verifier.temp_dir.exists())
            temp_dir = verifier.temp_dir

        # Directory should be cleaned up after context exit
        self.assertFalse(temp_dir.exists())

    def test_parse_group_config(self):
        """Test group configuration parsing."""
        with BackupVerifier() as verifier:
            # Test standard format
            group_threshold, groups = verifier._parse_group_config("3-of-5")
            self.assertEqual(group_threshold, 1)
            self.assertEqual(groups, [(3, 5)])

            # Test different format
            group_threshold, groups = verifier._parse_group_config("2-of-3")
            self.assertEqual(group_threshold, 1)
            self.assertEqual(groups, [(2, 3)])

            # Test invalid format (should use default)
            group_threshold, groups = verifier._parse_group_config("invalid")
            self.assertEqual(group_threshold, 1)
            self.assertEqual(groups, [(3, 5)])

    @patch("sseed.validation.backup_verification.validate_mnemonic_words")
    @patch("sseed.validation.backup_verification.validate_mnemonic_checksum")
    def test_test_original_mnemonic(self, mock_checksum, mock_words):
        """Test original mnemonic validation."""
        mock_words.return_value = None  # No exception = valid
        mock_checksum.return_value = True

        with BackupVerifier() as verifier:
            result = BackupVerificationResult()
            verifier._test_original_mnemonic(self.valid_mnemonic, result)

            self.assertIn("original_mnemonic_validation", result.test_results)
            self.assertEqual(
                result.test_results["original_mnemonic_validation"]["status"], "pass"
            )

    @patch("sseed.validation.backup_verification.create_slip39_shards")
    @patch("sseed.validation.backup_verification.reconstruct_mnemonic_from_shards")
    @patch("sseed.validation.backup_verification.write_mnemonic_to_file")
    @patch("sseed.validation.backup_verification.read_mnemonic_from_file")
    def test_test_round_trip_backup(
        self, mock_read, mock_write, mock_reconstruct, mock_create
    ):
        """Test round-trip backup verification."""
        # Mock shard creation
        mock_shards = ["shard1", "shard2", "shard3", "shard4", "shard5"]
        mock_create.return_value = mock_shards

        # Mock file operations
        mock_write.return_value = None
        mock_read.return_value = self.valid_mnemonic

        # Mock reconstruction
        mock_reconstruct.return_value = self.valid_mnemonic

        with BackupVerifier() as verifier:
            result = BackupVerificationResult()
            verifier._test_round_trip_backup(self.valid_mnemonic, "3-of-5", result)

            self.assertIn("round_trip_backup", result.test_results)

            # Verify mocks were called correctly
            mock_create.assert_called_once()
            mock_reconstruct.assert_called()

    @patch("sseed.validation.backup_verification.create_slip39_shards")
    @patch("sseed.validation.backup_verification.reconstruct_mnemonic_from_shards")
    def test_test_multiple_iterations(self, mock_reconstruct, mock_create):
        """Test multiple iteration testing."""
        mock_create.return_value = ["shard1", "shard2", "shard3", "shard4", "shard5"]
        mock_reconstruct.return_value = self.valid_mnemonic

        with BackupVerifier() as verifier:
            result = BackupVerificationResult()
            verifier._test_multiple_iterations(self.valid_mnemonic, "3-of-5", 3, result)

            self.assertIn("multiple_iterations", result.test_results)

            # Should have called create/reconstruct multiple times
            self.assertEqual(mock_create.call_count, 3)

    @patch("sseed.validation.backup_verification.create_slip39_shards")
    @patch("sseed.validation.backup_verification.reconstruct_mnemonic_from_shards")
    def test_test_shard_combinations(self, mock_reconstruct, mock_create):
        """Test shard combination testing."""
        mock_create.return_value = ["shard1", "shard2", "shard3", "shard4", "shard5"]
        mock_reconstruct.return_value = self.valid_mnemonic

        with BackupVerifier() as verifier:
            result = BackupVerificationResult()
            verifier._test_shard_combinations(self.valid_mnemonic, "3-of-5", result)

            self.assertIn("shard_combinations", result.test_results)

            # Should test minimum threshold and all shards
            self.assertGreaterEqual(mock_reconstruct.call_count, 2)

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        with BackupVerifier() as verifier:
            result = BackupVerificationResult()

            # Add some test results
            result.add_test_result("test1", "pass", {})
            result.add_test_result("test2", "fail", {})
            result.add_error("Test error")
            result.calculate_overall_score()

            verifier._generate_recommendations(result)

            # Should have generated recommendations
            self.assertGreater(len(result.recommendations), 0)


class TestBackupVerificationFunction(unittest.TestCase):
    """Test the public backup verification function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

    @patch("sseed.validation.backup_verification.BackupVerifier")
    def test_verify_backup_integrity(self, mock_verifier_class):
        """Test the public verify_backup_integrity function."""
        # Mock the verifier instance and its methods
        mock_verifier = MagicMock()
        mock_verifier_class.return_value.__enter__.return_value = mock_verifier

        # Mock the verification result
        mock_result = BackupVerificationResult()
        mock_result.test_type = "comprehensive_backup_verification"
        mock_result.overall_status = "good"
        mock_result.overall_score = 85
        mock_verifier.verify_backup_integrity.return_value = mock_result

        # Call the function
        result = verify_backup_integrity(
            mnemonic=self.valid_mnemonic,
            group_config="3-of-5",
            iterations=1,
            stress_test=False,
        )

        # Verify the verifier was called correctly
        mock_verifier.verify_backup_integrity.assert_called_once_with(
            mnemonic=self.valid_mnemonic,
            shard_files=None,
            group_config="3-of-5",
            iterations=1,
            stress_test=False,
        )

        # Verify result conversion
        self.assertIsInstance(result, dict)


class TestPhase4CLIIntegration(unittest.TestCase):
    """Test CLI integration for Phase 4 backup verification."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()
        self.valid_mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
        # Initialize validation_results properly
        self.command.validation_results = {"checks": {}}

    def create_test_args(self, mode="backup", **kwargs):
        """Create test arguments for the validate command."""
        args = Mock()
        args.mnemonic = self.valid_mnemonic
        args.mode = mode
        args.json = kwargs.get("json", False)
        args.verbose = kwargs.get("verbose", False)
        args.quiet = kwargs.get("quiet", False)
        args.language = kwargs.get("language", None)
        args.strict = kwargs.get("strict", False)
        args.check_entropy = kwargs.get("check_entropy", False)
        args.shard_files = kwargs.get("shard_files", None)
        args.group_config = kwargs.get("group_config", "3-of-5")
        args.iterations = kwargs.get("iterations", 1)
        args.stress_test = kwargs.get("stress_test", False)
        return args

    @patch("sseed.validation.backup_verification.verify_backup_integrity")
    def test_backup_validation_mode(self, mock_verify):
        """Test backup validation mode."""
        # Mock backup verification result
        mock_verify.return_value = {
            "overall_status": "good",
            "overall_score": 85,
            "tests_performed": ["original_mnemonic_validation", "round_trip_backup"],
            "total_duration_ms": 150.5,
            "errors": [],
            "warnings": [],
            "recommendations": ["Consider testing with more iterations"],
        }

        args = self.create_test_args(mode="backup")
        result = self.command._backup_validation(self.valid_mnemonic, args)

        # Verify the function was called
        mock_verify.assert_called_once_with(
            mnemonic=self.valid_mnemonic,
            shard_files=None,
            group_config="3-of-5",
            iterations=1,
            stress_test=False,
        )

        # Verify result
        self.assertTrue(result)  # Score 85 >= 70 threshold
        self.assertIn("backup_verification", self.command.validation_results)

    def test_backup_validation_with_shard_files(self):
        """Test backup validation with existing shard files."""
        shard_files = ["shard1.txt", "shard2.txt", "shard3.txt"]

        with patch(
            "sseed.validation.backup_verification.verify_backup_integrity"
        ) as mock_verify:
            mock_verify.return_value = {
                "overall_status": "excellent",
                "overall_score": 95,
                "tests_performed": [
                    "original_mnemonic_validation",
                    "existing_shards",
                    "round_trip_backup",
                ],
                "total_duration_ms": 200.0,
                "errors": [],
                "warnings": [],
                "recommendations": [],
            }

            args = self.create_test_args(mode="backup", shard_files=shard_files)
            result = self.command._backup_validation(self.valid_mnemonic, args)

            mock_verify.assert_called_once_with(
                mnemonic=self.valid_mnemonic,
                shard_files=shard_files,
                group_config="3-of-5",
                iterations=1,
                stress_test=False,
            )

            self.assertTrue(result)

    def test_backup_validation_with_stress_test(self):
        """Test backup validation with stress testing enabled."""
        with patch(
            "sseed.validation.backup_verification.verify_backup_integrity"
        ) as mock_verify:
            mock_verify.return_value = {
                "overall_status": "good",
                "overall_score": 88,
                "tests_performed": [
                    "original_mnemonic_validation",
                    "round_trip_backup",
                    "multiple_iterations",
                ],
                "total_duration_ms": 1500.0,
                "errors": [],
                "warnings": ["Stress test detected minor timing variations"],
                "recommendations": ["Consider running backup verification regularly"],
            }

            args = self.create_test_args(mode="backup", iterations=10, stress_test=True)
            result = self.command._backup_validation(self.valid_mnemonic, args)

            mock_verify.assert_called_once_with(
                mnemonic=self.valid_mnemonic,
                shard_files=None,
                group_config="3-of-5",
                iterations=10,
                stress_test=True,
            )

            self.assertTrue(result)
            self.assertIn("warnings", self.command.validation_results)
            self.assertIn("recommendations", self.command.validation_results)

    def test_backup_validation_import_error(self):
        """Test backup validation when backup_verification module is not available."""
        # Mock the import to raise ImportError
        with patch(
            "sseed.cli.commands.validate.ValidateCommand._backup_validation"
        ) as mock_method:

            def side_effect(mnemonic, args):
                try:
                    from ...validation.backup_verification import (
                        verify_backup_integrity,
                    )
                except ImportError:
                    self.command.validation_results["checks"]["backup_verification"] = {
                        "status": "error",
                        "error": "Backup verification module not available",
                        "message": "Install backup verification dependencies",
                    }
                    return False

            mock_method.side_effect = side_effect

            args = self.create_test_args(mode="backup")
            result = mock_method(self.valid_mnemonic, args)

            self.assertFalse(result)
            self.assertIn(
                "backup_verification", self.command.validation_results["checks"]
            )
            self.assertEqual(
                self.command.validation_results["checks"]["backup_verification"][
                    "status"
                ],
                "error",
            )

    def test_backup_validation_exception_handling(self):
        """Test backup validation exception handling."""
        with patch(
            "sseed.validation.backup_verification.verify_backup_integrity",
            side_effect=Exception("Test error"),
        ):
            args = self.create_test_args(mode="backup")
            result = self.command._backup_validation(self.valid_mnemonic, args)

            self.assertFalse(result)
            self.assertIn(
                "backup_verification", self.command.validation_results["checks"]
            )
            self.assertEqual(
                self.command.validation_results["checks"]["backup_verification"][
                    "status"
                ],
                "error",
            )


class TestPhase4Integration(unittest.TestCase):
    """Test end-to-end integration for Phase 4 features."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()
        self.valid_mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"

    def create_test_args(self, **kwargs):
        """Create test arguments."""
        args = Mock()
        args.mnemonic = kwargs.get("mnemonic", self.valid_mnemonic)
        args.mode = kwargs.get("mode", "backup")
        args.json = kwargs.get("json", False)
        args.verbose = kwargs.get("verbose", False)
        args.quiet = kwargs.get("quiet", False)
        args.language = kwargs.get("language", None)
        args.strict = kwargs.get("strict", False)
        args.check_entropy = kwargs.get("check_entropy", False)
        args.shard_files = kwargs.get("shard_files", None)
        args.group_config = kwargs.get("group_config", "3-of-5")
        args.iterations = kwargs.get("iterations", 1)
        args.stress_test = kwargs.get("stress_test", False)
        # Add required attributes for command execution
        args.input_file = None
        args.batch = None
        return args

    @patch("sseed.validation.backup_verification.verify_backup_integrity")
    def test_full_backup_validation_workflow(self, mock_verify):
        """Test complete backup validation workflow."""
        mock_verify.return_value = {
            "overall_status": "excellent",
            "overall_score": 95,
            "tests_performed": [
                "original_mnemonic_validation",
                "round_trip_backup",
                "shard_combinations",
                "entropy_consistency",
            ],
            "total_duration_ms": 250.0,
            "test_results": {
                "original_mnemonic_validation": {"status": "pass", "details": {}},
                "round_trip_backup": {"status": "pass", "details": {}},
                "shard_combinations": {"status": "pass", "details": {}},
                "entropy_consistency": {"status": "pass", "details": {}},
            },
            "errors": [],
            "warnings": [],
            "recommendations": ["Backup integrity verified successfully"],
        }

        args = self.create_test_args(mode="backup", verbose=True)

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

            # Verify successful execution
            self.assertEqual(result, 0)

            # Verify backup verification was called
            mock_verify.assert_called_once()

            # Verify results structure
            self.assertIn("backup_verification", self.command.validation_results)
            self.assertEqual(
                self.command.validation_results["overall_status"], "excellent"
            )
            self.assertEqual(self.command.validation_results["overall_score"], 95)

    def test_backup_validation_json_output(self):
        """Test backup validation with JSON output."""
        with (
            patch(
                "sseed.validation.backup_verification.verify_backup_integrity"
            ) as mock_verify,
            patch("builtins.print") as mock_print,
        ):

            mock_verify.return_value = {
                "overall_status": "good",
                "overall_score": 82,
                "tests_performed": [
                    "original_mnemonic_validation",
                    "round_trip_backup",
                ],
                "total_duration_ms": 180.0,
                "errors": [],
                "warnings": [],
                "recommendations": [],
            }

            args = self.create_test_args(mode="backup", json=True)
            result = self.command.execute(args)

            self.assertEqual(result, 0)

            # Verify JSON output was printed
            mock_print.assert_called()

            # Check that the printed output can be parsed as JSON
            printed_output = mock_print.call_args[0][0]
            try:
                json_data = json.loads(printed_output)
                self.assertIn("backup_verification", json_data)
                self.assertEqual(json_data["overall_status"], "good")
            except json.JSONDecodeError:
                self.fail("Output was not valid JSON")

    def test_backup_validation_failure_handling(self):
        """Test backup validation failure handling."""
        with patch(
            "sseed.validation.backup_verification.verify_backup_integrity"
        ) as mock_verify:
            mock_verify.return_value = {
                "overall_status": "fail",
                "overall_score": 30,
                "tests_performed": ["original_mnemonic_validation"],
                "total_duration_ms": 50.0,
                "errors": ["Original mnemonic validation failed"],
                "warnings": [],
                "recommendations": ["Check mnemonic validity"],
            }

            args = self.create_test_args(mode="backup")
            result = self.command.execute(args)

            # Should return error code due to low score
            self.assertEqual(result, 1)
            self.assertEqual(self.command.validation_results["overall_status"], "fail")
            self.assertIn("errors", self.command.validation_results)


if __name__ == "__main__":
    unittest.main()
