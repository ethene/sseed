"""
Tests for Phase 3 of B.3 Advanced Validation: Batch Processing and Advanced Formatting.

This module tests the batch validation capabilities and advanced output formatting
features implemented in Phase 3.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from sseed.validation.batch import (
    BatchValidator,
    BatchValidationResult,
    validate_batch_files,
)
from sseed.validation.formatters import (
    ValidationFormatter,
    format_validation_output,
)


class TestBatchValidation(unittest.TestCase):
    """Test batch validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Sample mnemonic content for test files
        self.valid_mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
        self.invalid_mnemonic = "invalid mnemonic words that do not pass validation"
        
        # Create test files
        self.valid_file1 = self.temp_path / "wallet1.txt"
        self.valid_file1.write_text(self.valid_mnemonic)
        
        self.valid_file2 = self.temp_path / "wallet2.txt"
        self.valid_file2.write_text(self.valid_mnemonic)
        
        self.invalid_file = self.temp_path / "invalid.txt"
        self.invalid_file.write_text(self.invalid_mnemonic)
        
        self.empty_file = self.temp_path / "empty.txt"
        self.empty_file.write_text("")
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_batch_validation_result_initialization(self):
        """Test BatchValidationResult initialization and basic methods."""
        result = BatchValidationResult()
        
        self.assertEqual(result.total_files, 0)
        self.assertEqual(result.processed_files, 0)
        self.assertEqual(result.passed_files, 0)
        self.assertEqual(result.failed_files, 0)
        self.assertEqual(result.error_files, 0)
        self.assertEqual(result.get_success_rate(), 0.0)
        
    def test_batch_validation_result_add_file_result(self):
        """Test adding file results to batch validation result."""
        result = BatchValidationResult()
        
        # Add a passing result
        analysis_result = {"overall_score": 85, "overall_status": "pass"}
        result.add_file_result("/path/to/file.txt", analysis_result)
        
        self.assertEqual(result.passed_files, 1)
        self.assertEqual(result.failed_files, 0)
        self.assertEqual(len(result.file_results), 1)
        
        # Add a failing result
        analysis_result = {"overall_score": 45, "overall_status": "fail"}
        result.add_file_result("/path/to/file2.txt", analysis_result)
        
        self.assertEqual(result.passed_files, 1)
        self.assertEqual(result.failed_files, 1)
        self.assertEqual(len(result.file_results), 2)
        
    def test_batch_validation_result_add_error(self):
        """Test adding errors to batch validation result."""
        result = BatchValidationResult()
        
        result.add_error("/path/to/error.txt", "File not found")
        
        self.assertEqual(result.error_files, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0]["error"], "File not found")
        
    def test_batch_validation_result_calculate_statistics(self):
        """Test statistics calculation for batch results."""
        result = BatchValidationResult()
        
        # Add various results
        result.add_file_result("file1.txt", {
            "overall_score": 95,
            "checks": {
                "language": {"detected": "en"},
                "format": {"word_count": 12}
            }
        })
        result.add_file_result("file2.txt", {
            "overall_score": 75,
            "checks": {
                "language": {"detected": "es"},
                "format": {"word_count": 24}
            }
        })
        
        result.calculate_statistics()
        
        self.assertEqual(result.average_score, 85.0)
        self.assertIn("score_distribution", result.summary_stats)
        self.assertIn("quality_distribution", result.summary_stats)
        self.assertIn("language_distribution", result.summary_stats)
        self.assertIn("word_count_distribution", result.summary_stats)
        
        # Check language distribution
        lang_dist = result.summary_stats["language_distribution"]
        self.assertEqual(lang_dist["en"], 1)
        self.assertEqual(lang_dist["es"], 1)
        
    @patch('sseed.validation.batch.read_mnemonic_from_file')
    @patch('sseed.validation.batch.analyze_mnemonic_comprehensive')
    def test_batch_validator_validate_files(self, mock_analyze, mock_read):
        """Test BatchValidator file validation."""
        # Mock file reading
        mock_read.return_value = self.valid_mnemonic
        
        # Mock analysis
        mock_analyze.return_value = {
            "overall_score": 85,
            "overall_status": "pass",
            "checks": {"format": {"status": "pass"}}
        }
        
        validator = BatchValidator(max_workers=1)
        file_patterns = [str(self.temp_path / "*.txt")]
        
        result = validator.validate_files(file_patterns)
        
        self.assertGreater(result.total_files, 0)
        self.assertGreater(result.processed_files, 0)
        
    def test_batch_validator_expand_file_patterns(self):
        """Test file pattern expansion."""
        validator = BatchValidator()
        
        # Test directory pattern
        patterns = [str(self.temp_path / "*.txt")]
        files = validator._expand_file_patterns(patterns)
        
        self.assertGreater(len(files), 0)
        self.assertTrue(all(f.endswith('.txt') for f in files))
        
    @patch('sseed.validation.batch.read_mnemonic_from_file')
    def test_batch_validator_validate_single_file_success(self, mock_read):
        """Test successful single file validation."""
        mock_read.return_value = self.valid_mnemonic
        
        validator = BatchValidator()
        
        with patch('sseed.validation.batch.analyze_mnemonic_comprehensive') as mock_analyze:
            mock_analyze.return_value = {
                "overall_score": 85,
                "overall_status": "pass"
            }
            
            result = validator._validate_single_file(
                str(self.valid_file1),
                expected_language=None,
                strict_mode=False,
                include_analysis=True
            )
            
            self.assertTrue(result["success"])
            self.assertIn("analysis", result)
            
    @patch('sseed.validation.batch.read_mnemonic_from_file')
    def test_batch_validator_validate_single_file_error(self, mock_read):
        """Test single file validation with error."""
        mock_read.side_effect = Exception("File read error")
        
        validator = BatchValidator()
        
        result = validator._validate_single_file(
            str(self.valid_file1),
            expected_language=None,
            strict_mode=False,
            include_analysis=True
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        
    @patch('sseed.validation.batch.validate_batch_files')
    def test_validate_batch_files_function(self, mock_validate):
        """Test the public validate_batch_files function."""
        mock_result = {
            "summary": {
                "total_files": 2,
                "passed_files": 2,
                "success_rate": 100.0
            }
        }
        mock_validate.return_value = mock_result
        
        result = validate_batch_files(
            file_patterns=[str(self.temp_path / "*.txt")],
            expected_language="en",
            strict_mode=True,
            fail_fast=False,
            include_analysis=True,
            max_workers=2
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)


class TestValidationFormatters(unittest.TestCase):
    """Test validation output formatters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.single_result = {
            "overall_score": 85,
            "overall_status": "pass",
            "timestamp": "2024-01-01T12:00:00",
            "analysis_duration_ms": 25.5,
            "checks": {
                "format": {
                    "status": "pass",
                    "word_count": 12,
                    "message": "Valid format with 12 words"
                },
                "checksum": {
                    "status": "pass",
                    "message": "Valid BIP-39 checksum"
                }
            },
            "warnings": ["Consider using a longer mnemonic"],
            "recommendations": ["Store securely"],
            "security_notes": ["Generated with good entropy"]
        }
        
        self.batch_result = {
            "summary": {
                "total_files": 10,
                "processed_files": 10,
                "passed_files": 8,
                "failed_files": 2,
                "error_files": 0,
                "success_rate": 80.0,
                "average_score": 82.5,
                "total_duration_ms": 1250.0
            },
            "statistics": {
                "quality_distribution": {
                    "excellent": 3,
                    "good": 5,
                    "acceptable": 2,
                    "poor": 0,
                    "fail": 0
                },
                "language_distribution": {
                    "en": 8,
                    "es": 2
                },
                "word_count_distribution": {
                    "12": 6,
                    "24": 4
                }
            },
            "file_results": [],
            "errors": []
        }
        
    def test_validation_formatter_format_text_single(self):
        """Test text formatting for single validation result."""
        result = ValidationFormatter.format_text(self.single_result, use_colors=False, use_symbols=False)
        
        self.assertIn("Mnemonic Validation Report", result)
        self.assertIn("GOOD Overall Score: 85/100", result)
        self.assertIn("Status: Pass", result)
        self.assertIn("Validation Checks:", result)
        
    def test_validation_formatter_format_text_single_verbose(self):
        """Test verbose text formatting for single validation result."""
        result = ValidationFormatter.format_text(self.single_result, verbose=True, use_colors=False)
        
        self.assertIn("Valid format with 12 words", result)
        self.assertIn("Warnings:", result)
        self.assertIn("Recommendations:", result)
        self.assertIn("Security Notes:", result)
        
    def test_validation_formatter_format_text_no_colors(self):
        """Test text formatting without colors."""
        result = ValidationFormatter.format_text(
            self.single_result, 
            use_colors=False,
            use_symbols=False
        )
        
        self.assertNotIn("\033[", result)  # No ANSI codes
        self.assertIn("PASS", result)  # Text symbols instead
        
    def test_validation_formatter_format_json(self):
        """Test JSON formatting."""
        result = ValidationFormatter.format_json(self.single_result)
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed["overall_score"], 85)
        
    def test_validation_formatter_format_json_compact(self):
        """Test compact JSON formatting."""
        result = ValidationFormatter.format_json(self.single_result, compact=True)
        
        # Should not contain indentation
        self.assertNotIn("\n", result)
        self.assertNotIn("  ", result)
        
    def test_validation_formatter_format_summary_single(self):
        """Test summary formatting for single result."""
        result = ValidationFormatter.format_summary(self.single_result, use_colors=False, use_symbols=False)
        
        self.assertIn("GOOD Score: 85/100", result)
        self.assertIn("Pass", result)
        
    def test_validation_formatter_format_summary_batch(self):
        """Test summary formatting for batch result."""
        result = ValidationFormatter.format_summary(self.batch_result, use_colors=False, use_symbols=False)
        
        self.assertIn("Batch Validation:", result)
        self.assertIn("8/10 passed", result)
        
    def test_validation_formatter_format_batch_text(self):
        """Test batch text formatting."""
        result = ValidationFormatter._format_batch_text(self.batch_result, use_colors=False, use_symbols=False)
        
        self.assertIn("Batch Validation Report", result)
        self.assertIn("Overall Success Rate: 80.0%", result)
        
    def test_validation_formatter_format_batch_text_verbose(self):
        """Test verbose batch text formatting."""
        result = ValidationFormatter._format_batch_text(self.batch_result, verbose=True, use_colors=False)
        
        self.assertIn("Quality Distribution:", result)
        self.assertIn("Language Distribution:", result)
        self.assertIn("Word Count Distribution:", result)
        
    def test_validation_formatter_get_quality_level(self):
        """Test quality level determination."""
        self.assertEqual(ValidationFormatter._get_quality_level(95), "excellent")
        self.assertEqual(ValidationFormatter._get_quality_level(85), "good")
        self.assertEqual(ValidationFormatter._get_quality_level(75), "acceptable")
        self.assertEqual(ValidationFormatter._get_quality_level(55), "poor")
        self.assertEqual(ValidationFormatter._get_quality_level(35), "fail")
        
    def test_validation_formatter_get_status_color(self):
        """Test status color determination."""
        self.assertEqual(ValidationFormatter._get_status_color("pass"), "green")
        self.assertEqual(ValidationFormatter._get_status_color("warning"), "yellow")
        self.assertEqual(ValidationFormatter._get_status_color("fail"), "red")
        self.assertEqual(ValidationFormatter._get_status_color("unknown"), "white")
        
    def test_format_validation_output_text(self):
        """Test the public format_validation_output function with text format."""
        result = format_validation_output(self.single_result, output_format="text")
        
        self.assertIn("Mnemonic Validation Report", result)
        
    def test_format_validation_output_json(self):
        """Test the public format_validation_output function with JSON format."""
        result = format_validation_output(self.single_result, output_format="json")
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed["overall_score"], 85)
        
    def test_format_validation_output_summary(self):
        """Test the public format_validation_output function with summary format."""
        result = format_validation_output(self.single_result, output_format="summary", use_colors=False, use_symbols=False)
        
        self.assertIn("GOOD Score: 85/100", result)


class TestPhase3Integration(unittest.TestCase):
    """Test integration of Phase 3 features."""
    
    def test_batch_and_formatter_integration(self):
        """Test that batch validation and formatters work together."""
        # Create mock batch result
        batch_result = {
            "summary": {
                "total_files": 5,
                "passed_files": 4,
                "success_rate": 80.0
            },
            "statistics": {
                "quality_distribution": {
                    "excellent": 2,
                    "good": 2,
                    "acceptable": 1
                }
            },
            "file_results": [],
            "errors": []
        }
        
        # Test that formatter can handle batch results
        text_output = format_validation_output(batch_result, output_format="text")
        json_output = format_validation_output(batch_result, output_format="json")
        summary_output = format_validation_output(batch_result, output_format="summary", use_colors=False, use_symbols=False)
        
        self.assertIn("Batch Validation Report", text_output)
        self.assertIsInstance(json.loads(json_output), dict)
        self.assertIn("4/5 passed", summary_output)
        
    @patch('sseed.validation.batch.validate_batch_files')
    def test_validate_command_batch_integration(self, mock_batch_validate):
        """Test that validate command integrates with batch processing."""
        from sseed.cli.commands.validate import ValidateCommand
        
        # Mock batch validation
        mock_batch_validate.return_value = {
            "summary": {
                "total_files": 3,
                "passed_files": 3,
                "success_rate": 100.0
            }
        }
        
        command = ValidateCommand()
        
        # Create mock args
        args = Mock()
        args.batch = Path("/test/batch")
        args.json = False
        args.quiet = False
        args.verbose = False
        args.language = None
        args.strict = False
        args.mode = "basic"
        
        # Test batch validation
        with patch('builtins.print') as mock_print:
            result = command._batch_validate(args)
            
            self.assertEqual(result, 0)  # Success
            mock_print.assert_called()  # Should have printed output


if __name__ == '__main__':
    unittest.main() 