"""Tests for Phase 2 validation functionality - Deep Analysis Integration.

This module tests the enhanced validation capabilities including:
- Unified analysis engine
- Cross-tool compatibility testing  
- Advanced entropy analysis
- Comprehensive reporting
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from argparse import Namespace

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
            'mnemonic': self.test_mnemonic,
            'mode': 'basic',
            'language': None,
            'strict': False,
            'check_entropy': False,
            'json': False,
            'quiet': False,
            'verbose': False,
            'input_file': None,
            'batch': False
        }
        defaults.update(kwargs)
        return Namespace(**defaults)
        
    def test_comprehensive_analysis_integration(self):
        """Test integration with unified analysis engine."""
        args = self.create_test_args(mode='advanced', strict=True, verbose=True)
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze:
            # Mock comprehensive analysis result
            mock_analyze.return_value = {
                "overall_score": 85,
                "overall_status": "good",
                "checks": {
                    "format_validation": {"status": "pass", "message": "Valid format"},
                    "language_detection": {"status": "pass", "message": "English detected"},
                    "checksum_validation": {"status": "pass", "message": "Valid checksum"},
                    "weak_patterns": {"status": "pass", "message": "No weak patterns"},
                    "entropy_analysis": {"status": "pass", "message": "Good entropy quality"}
                },
                "analysis_details": {
                    "entropy_quality": "high",
                    "security_score": 90,
                    "language_confidence": 0.95
                }
            }
            
            result = self.command.execute(args)
            
            # Verify comprehensive analysis was called
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            self.assertEqual(call_args[0][0], self.test_mnemonic)  # mnemonic argument
            self.assertEqual(call_args[1]['strict_mode'], True)
            
            # Verify successful execution
            self.assertEqual(result, 0)
            
    def test_comprehensive_analysis_fallback(self):
        """Test fallback to basic validation when comprehensive analysis fails."""
        args = self.create_test_args(mode='advanced', strict=True)
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze:
            # Mock analysis failure
            mock_analyze.side_effect = Exception("Analysis module not available")
            
            result = self.command.execute(args)
            
            # Should fallback gracefully and still succeed
            self.assertEqual(result, 0)
            
    def test_cross_tool_compatibility_with_tools(self):
        """Test cross-tool compatibility when external tools are available."""
        args = self.create_test_args(mode='compatibility', verbose=True)
        
        with patch('sseed.validation.cross_tool.get_available_tools') as mock_get_tools, \
             patch('sseed.validation.cross_tool.test_cross_tool_compatibility') as mock_test:
            
            # Mock available tools
            mock_get_tools.return_value = ['trezor_shamir']
            
            # Mock compatibility test result
            mock_test.return_value = {
                "overall_status": "good",
                "compatibility_score": 85,
                "tools_tested": ["trezor_shamir"],
                "tool_results": {
                    "trezor_shamir": {
                        "status": "pass",
                        "message": "Full compatibility",
                        "tests": {
                            "slip39_round_trip": {"status": "pass"},
                            "entropy_verification": {"status": "pass"}
                        }
                    }
                },
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
            
            result = self.command.execute(args)
            
            # Verify tools were checked and testing was performed
            mock_get_tools.assert_called_once()
            mock_test.assert_called_once_with(self.test_mnemonic)
            
            # Verify successful execution
            self.assertEqual(result, 0)
            
            # Check that compatibility results are in validation results
            self.assertIn("compatibility", self.command.validation_results["checks"])
            compat_check = self.command.validation_results["checks"]["compatibility"]
            self.assertEqual(compat_check["status"], "pass")
            self.assertEqual(compat_check["compatibility_score"], 85)
            
    def test_cross_tool_compatibility_no_tools(self):
        """Test cross-tool compatibility when no external tools are available."""
        args = self.create_test_args(mode='compatibility')
        
        with patch('sseed.validation.cross_tool.get_available_tools') as mock_get_tools:
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
        args = self.create_test_args(mode='compatibility')
        
        with patch('sseed.validation.cross_tool.get_available_tools') as mock_get_tools:
            # Mock exception in compatibility testing
            mock_get_tools.side_effect = Exception("Tool detection failed")
            
            result = self.command.execute(args)
            
            # Should handle error gracefully
            self.assertEqual(result, 0)
            
            # Check that error is reported
            self.assertIn("compatibility", self.command.validation_results["checks"])
            compat_check = self.command.validation_results["checks"]["compatibility"]
            self.assertEqual(compat_check["status"], "error")
            
    def test_enhanced_entropy_validation(self):
        """Test enhanced entropy validation using comprehensive analysis."""
        args = self.create_test_args(mode='entropy', verbose=True)
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze:
            # Mock comprehensive analysis with detailed entropy results
            mock_analyze.return_value = {
                "overall_score": 90,
                "checks": {
                    "entropy_analysis": {
                        "status": "pass",
                        "entropy_bits": 128,
                        "quality_score": 95,
                        "quality_level": "excellent",
                        "randomness_tests": {
                            "chi_square": "pass",
                            "runs_test": "pass",
                            "frequency_test": "pass"
                        },
                        "message": "Excellent entropy quality (95/100)"
                    }
                }
            }
            
            result = self.command.execute(args)
            
            # Verify comprehensive analysis was used
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            self.assertEqual(call_args[1]['strict_mode'], True)  # Entropy mode uses strict
            
            # Verify successful execution
            self.assertEqual(result, 0)
            
            # Check entropy analysis results
            self.assertIn("entropy_analysis", self.command.validation_results["checks"])
            entropy_check = self.command.validation_results["checks"]["entropy_analysis"]
            self.assertEqual(entropy_check["status"], "pass")
            self.assertEqual(entropy_check["quality_score"], 95)
            
    def test_enhanced_entropy_validation_fallback(self):
        """Test fallback entropy validation when comprehensive analysis fails."""
        args = self.create_test_args(mode='entropy')
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze:
            # Mock analysis failure
            mock_analyze.side_effect = Exception("Entropy analysis failed")
            
            result = self.command.execute(args)
            
            # Should fallback to basic entropy analysis
            self.assertEqual(result, 0)
            
            # Check that basic entropy analysis was performed
            self.assertIn("entropy_analysis", self.command.validation_results["checks"])
            entropy_check = self.command.validation_results["checks"]["entropy_analysis"]
            self.assertIn("estimated_bits", entropy_check)
            
    def test_json_output_with_comprehensive_data(self):
        """Test JSON output includes comprehensive analysis data."""
        args = self.create_test_args(mode='advanced', json=True, verbose=True)
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze, \
             patch('builtins.print') as mock_print:
            
            # Mock comprehensive analysis result
            mock_analyze.return_value = {
                "overall_score": 88,
                "overall_status": "good",
                "checks": {
                    "format_validation": {"status": "pass"},
                    "language_detection": {"status": "pass"},
                    "checksum_validation": {"status": "pass"},
                    "weak_patterns": {"status": "pass"},
                    "entropy_analysis": {"status": "pass"}
                },
                "analysis_details": {
                    "entropy_quality": "high",
                    "security_score": 90,
                    "language_confidence": 0.95,
                    "pattern_analysis": {
                        "repeated_words": 0,
                        "sequential_patterns": 0,
                        "dictionary_words": 12
                    }
                },
                "timestamp": "2025-01-01 12:00:00 UTC"
            }
            
            result = self.command.execute(args)
            
            # Verify JSON output was called
            mock_print.assert_called_once()
            
            # Parse the JSON output
            json_output = mock_print.call_args[0][0]
            output_data = json.loads(json_output)
            
            # Verify comprehensive data is included
            self.assertEqual(output_data["overall_score"], 88)
            self.assertEqual(output_data["overall_status"], "good")
            self.assertIn("analysis_details", output_data)
            self.assertIn("entropy_quality", output_data["analysis_details"])
            self.assertIn("pattern_analysis", output_data["analysis_details"])
            
    def test_verbose_output_formatting(self):
        """Test verbose output includes detailed analysis information."""
        args = self.create_test_args(mode='advanced', verbose=True)
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze, \
             patch('builtins.print') as mock_print:
            
            # Mock comprehensive analysis result
            mock_analyze.return_value = {
                "overall_score": 92,
                "overall_status": "excellent",
                "checks": {
                    "format_validation": {"status": "pass", "message": "Valid 12-word format"},
                    "language_detection": {"status": "pass", "message": "English (confidence: 0.98)"},
                    "checksum_validation": {"status": "pass", "message": "Valid BIP-39 checksum"},
                    "weak_patterns": {"status": "pass", "message": "No weak patterns detected"},
                    "entropy_analysis": {"status": "pass", "message": "Excellent entropy (128 bits)"}
                }
            }
            
            result = self.command.execute(args)
            
            # Verify successful execution
            self.assertEqual(result, 0)
            
            # Check that print was called multiple times for verbose output
            self.assertTrue(mock_print.called)
            
            # Verify validation results contain comprehensive data
            self.assertEqual(self.command.validation_results["overall_score"], 92)
            self.assertEqual(self.command.validation_results["overall_status"], "excellent")
            
    def test_language_specific_validation(self):
        """Test validation with specific language parameter."""
        args = self.create_test_args(mode='advanced', language='es')
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze:
            mock_analyze.return_value = {
                "overall_score": 80,
                "overall_status": "good",
                "checks": {}
            }
            
            result = self.command.execute(args)
            
            # Verify language was passed to analysis
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            self.assertEqual(call_args[1]['expected_language'], 'es')
            
            self.assertEqual(result, 0)
            
    def test_strict_mode_validation(self):
        """Test validation in strict mode."""
        args = self.create_test_args(mode='advanced', strict=True)
        
        with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze:
            mock_analyze.return_value = {
                "overall_score": 75,
                "overall_status": "good",
                "checks": {}
            }
            
            result = self.command.execute(args)
            
            # Verify strict mode was enabled
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            self.assertEqual(call_args[1]['strict_mode'], True)
            
            self.assertEqual(result, 0)
            
    def test_multiple_validation_modes_integration(self):
        """Test that all validation modes work with new Phase 2 features."""
        modes = ['basic', 'advanced', 'compatibility', 'entropy']
        
        for mode in modes:
            with self.subTest(mode=mode):
                args = self.create_test_args(mode=mode)
                
                # Mock the comprehensive analysis and cross-tool functions
                with patch('sseed.validation.analysis.analyze_mnemonic_comprehensive') as mock_analyze, \
                     patch('sseed.validation.cross_tool.get_available_tools') as mock_get_tools, \
                     patch('sseed.validation.cross_tool.test_cross_tool_compatibility') as mock_test:
                    
                    # Set up mocks
                    mock_analyze.return_value = {
                        "overall_score": 85,
                        "overall_status": "good",
                        "checks": {}
                    }
                    mock_get_tools.return_value = ['trezor_shamir']
                    mock_test.return_value = {
                        "overall_status": "good",
                        "compatibility_score": 85,
                        "tools_tested": ["trezor_shamir"]
                    }
                    
                    result = self.command.execute(args)
                    self.assertEqual(result, 0, f"Mode {mode} should succeed")


if __name__ == '__main__':
    unittest.main() 