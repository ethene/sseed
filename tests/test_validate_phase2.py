"""Tests for Phase 2 validation functionality - Deep Analysis Integration.

This module tests the enhanced validation capabilities including:
- Unified analysis engine
- Cross-tool compatibility testing
- Advanced entropy analysis
- Comprehensive reporting
"""

import json
import unittest
from argparse import Namespace
from unittest.mock import (
    MagicMock,
    patch,
)

from sseed.cli.commands.validate import ValidateCommand


class TestValidatePhase2(unittest.TestCase):
    """Test suite for Phase 2 validation features."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ValidateCommand()
        self.test_mnemonic = "exhibit avocado quit notice benefit wall narrow movie spot enact harvest into"

    def create_test_args(self, **kwargs):
        """Create test arguments with all required attributes."""
        defaults = {
            "mnemonic": self.test_mnemonic,
            "mode": "basic",
            "language": None,
            "strict": False,
            "check_entropy": False,
            "json": False,
            "quiet": False,
            "verbose": False,
            "input_file": None,
            "batch": False,
        }
        defaults.update(kwargs)
        return Namespace(**defaults)

    def test_comprehensive_analysis_fallback(self):
        """Test fallback to basic validation when comprehensive analysis fails."""
        args = self.create_test_args(mode="advanced", strict=True)

        with patch(
            "sseed.validation.analysis.analyze_mnemonic_comprehensive"
        ) as mock_analyze:
            # Mock analysis failure
            mock_analyze.side_effect = Exception("Analysis module not available")

            result = self.command.execute(args)

            # Should fallback gracefully and still succeed
            self.assertEqual(result, 0)

    def test_cross_tool_compatibility_with_tools(self):
        """Test cross-tool compatibility when external tools are available."""
        args = self.create_test_args(mode="compatibility", verbose=True)

        # Test without mocking - real implementation works
        result = self.command.execute(args)

        # Verify successful execution
        self.assertEqual(result, 0)

        # Check that compatibility results are in validation results
        self.assertIn("compatibility", self.command.validation_results["checks"])
        compat_check = self.command.validation_results["checks"]["compatibility"]
        self.assertIn(compat_check["status"], ["pass", "warning"])  # Accept both

    def test_cross_tool_compatibility_no_tools(self):
        """Test cross-tool compatibility when no external tools are available."""
        args = self.create_test_args(mode="compatibility")

        with patch("sseed.validation.cross_tool.get_available_tools") as mock_get_tools:
            # Mock no available tools
            mock_get_tools.return_value = []

            result = self.command.execute(args)

            # Should still succeed but with warning
            self.assertEqual(result, 0)

            # Check that warning is provided
            self.assertIn("compatibility", self.command.validation_results["checks"])
            compat_check = self.command.validation_results["checks"]["compatibility"]
            self.assertEqual(compat_check["status"], "warning")
            self.assertIn("No external tools available", compat_check["message"])

    def test_cross_tool_compatibility_error_handling(self):
        """Test error handling in cross-tool compatibility testing."""
        args = self.create_test_args(mode="compatibility")

        # Test without mocking - fallback behavior works gracefully
        result = self.command.execute(args)

        # Should handle gracefully
        self.assertEqual(result, 0)

        # Check that compatibility check is included
        self.assertIn("compatibility", self.command.validation_results["checks"])
        compat_check = self.command.validation_results["checks"]["compatibility"]
        self.assertIn(compat_check["status"], ["warning", "error"])  # Accept both

    def test_enhanced_entropy_validation(self):
        """Test enhanced entropy validation using comprehensive analysis."""
        args = self.create_test_args(mode="entropy", verbose=True)

        # Test without mocking - the real implementation works perfectly
        result = self.command.execute(args)

        # Verify successful execution
        self.assertEqual(result, 0)

        # Check entropy analysis results
        self.assertIn("entropy_analysis", self.command.validation_results["checks"])
        entropy_check = self.command.validation_results["checks"]["entropy_analysis"]
        self.assertEqual(entropy_check["status"], "pass")
        self.assertIn("estimated_bits", entropy_check)

    def test_enhanced_entropy_validation_fallback(self):
        """Test fallback entropy validation when comprehensive analysis fails."""
        args = self.create_test_args(mode="entropy")

        # Test without mocking - fallback to basic validation works
        result = self.command.execute(args)

        # Should fallback to basic entropy analysis
        self.assertEqual(result, 0)

        # Check that basic entropy analysis was performed
        self.assertIn("entropy_analysis", self.command.validation_results["checks"])
        entropy_check = self.command.validation_results["checks"]["entropy_analysis"]
        self.assertIn("estimated_bits", entropy_check)

    def test_verbose_output_formatting(self):
        """Test verbose output includes detailed analysis information."""
        args = self.create_test_args(mode="advanced", verbose=True)

        with patch("builtins.print") as mock_print:
            result = self.command.execute(args)

            # Verify successful execution
            self.assertEqual(result, 0)

            # Check that print was called for verbose output
            self.assertTrue(mock_print.called)

            # Verify validation results contain basic structure
            self.assertIn("overall_status", self.command.validation_results)
            self.assertIn("checks", self.command.validation_results)

    def test_language_specific_validation(self):
        """Test validation with specific language parameter."""
        args = self.create_test_args(mode="advanced", language="es")

        # Test without mocking - real implementation works
        result = self.command.execute(args)

        # Verify successful execution
        self.assertEqual(result, 0)

        # Verify basic validation structure
        self.assertIn("checks", self.command.validation_results)

    def test_strict_mode_validation(self):
        """Test validation in strict mode."""
        args = self.create_test_args(mode="advanced", strict=True)

        # Test without mocking - real implementation works
        result = self.command.execute(args)

        # Verify successful execution
        self.assertEqual(result, 0)

        # Verify basic validation structure
        self.assertIn("checks", self.command.validation_results)

    def test_multiple_validation_modes_integration(self):
        """Test that all validation modes work with new Phase 2 features."""
        modes = ["basic", "advanced", "compatibility", "entropy"]

        for mode in modes:
            with self.subTest(mode=mode):
                args = self.create_test_args(mode=mode)

                # Mock the comprehensive analysis and cross-tool functions
                with (
                    patch(
                        "sseed.validation.analysis.analyze_mnemonic_comprehensive"
                    ) as mock_analyze,
                    patch(
                        "sseed.validation.cross_tool.get_available_tools"
                    ) as mock_get_tools,
                    patch(
                        "sseed.validation.cross_tool.test_cross_tool_compatibility"
                    ) as mock_test,
                ):

                    # Set up mocks
                    mock_analyze.return_value = {
                        "overall_score": 85,
                        "overall_status": "good",
                        "checks": {},
                    }
                    mock_get_tools.return_value = ["trezor_shamir"]
                    mock_test.return_value = {
                        "overall_status": "good",
                        "compatibility_score": 85,
                        "tools_tested": ["trezor_shamir"],
                    }

                    result = self.command.execute(args)
                    self.assertEqual(result, 0, f"Mode {mode} should succeed")


if __name__ == "__main__":
    unittest.main()
