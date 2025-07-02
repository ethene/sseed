"""
Test coverage for sseed.cli module backward compatibility.

This module tests the backward compatibility wrapper that imports
legacy CLI functionality and exit codes.
"""

import importlib.util
import os

import pytest


# Direct import to get the actual cli.py module, not the package
def import_cli_module():
    """Import the actual cli.py module, not the cli package."""
    # Get the path to the cli.py file
    cli_file_path = os.path.join(os.path.dirname(__file__), "..", "sseed", "cli.py")
    cli_file_path = os.path.abspath(cli_file_path)

    # Load the module directly
    spec = importlib.util.spec_from_file_location("sseed_cli_module", cli_file_path)
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)
    return cli_module


class TestCliBackwardCompatibility:
    """Test the CLI backward compatibility module."""

    @pytest.fixture
    def cli_module(self):
        """Import the actual CLI module for testing."""
        return import_cli_module()

    def test_exit_codes_imported(self, cli_module):
        """Test that exit codes are properly imported."""
        # Test that all exit codes are available and have correct values
        assert cli_module.EXIT_SUCCESS == 0
        assert cli_module.EXIT_USAGE_ERROR == 1
        assert cli_module.EXIT_CRYPTO_ERROR == 2
        assert cli_module.EXIT_FILE_ERROR == 3
        assert cli_module.EXIT_VALIDATION_ERROR == 4
        assert cli_module.EXIT_INTERRUPTED == 130

    def test_main_function_import(self, cli_module):
        """Test that main function is imported."""
        # Should have main function available
        assert hasattr(cli_module, "main")

        # Should be callable
        main_func = cli_module.main
        assert callable(main_func)

    def test_module_all_exports(self, cli_module):
        """Test that __all__ exports are correct."""
        # Should have __all__ defined
        assert hasattr(cli_module, "__all__")

        # All exports should be available
        for export_name in cli_module.__all__:
            assert hasattr(cli_module, export_name)

    def test_exit_codes_types(self, cli_module):
        """Test that exit codes are integers."""
        exit_codes = [
            cli_module.EXIT_SUCCESS,
            cli_module.EXIT_USAGE_ERROR,
            cli_module.EXIT_CRYPTO_ERROR,
            cli_module.EXIT_FILE_ERROR,
            cli_module.EXIT_VALIDATION_ERROR,
            cli_module.EXIT_INTERRUPTED,
        ]

        for code in exit_codes:
            assert isinstance(code, int)
            assert 0 <= code <= 255  # Valid exit code range

    def test_module_docstring(self, cli_module):
        """Test that module has proper documentation."""
        # Should have a docstring
        assert cli_module.__doc__ is not None
        assert len(cli_module.__doc__.strip()) > 0

    def test_backward_compatibility_interface(self, cli_module):
        """Test the backward compatibility interface."""
        # Should have main function
        assert hasattr(cli_module, "main")

        # Should have all exit codes
        exit_code_names = [
            "EXIT_SUCCESS",
            "EXIT_USAGE_ERROR",
            "EXIT_CRYPTO_ERROR",
            "EXIT_FILE_ERROR",
            "EXIT_VALIDATION_ERROR",
            "EXIT_INTERRUPTED",
        ]

        for name in exit_code_names:
            assert hasattr(cli_module, name)

    def test_exit_code_values(self, cli_module):
        """Test specific exit code values."""
        assert cli_module.EXIT_SUCCESS == 0
        assert cli_module.EXIT_INTERRUPTED == 130  # Standard SIGINT exit code

        # Other exit codes should be positive
        assert cli_module.EXIT_USAGE_ERROR > 0
        assert cli_module.EXIT_CRYPTO_ERROR > 0
        assert cli_module.EXIT_FILE_ERROR > 0
        assert cli_module.EXIT_VALIDATION_ERROR > 0

    def test_main_entry_point(self, cli_module):
        """Test that main can be called as entry point."""
        # Should be importable and callable
        main_func = cli_module.main
        assert callable(main_func)
        assert hasattr(main_func, "__name__")
        assert main_func.__name__ == "main"
