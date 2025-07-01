"""Tests for sseed.__main__ entry point."""

import subprocess
import sys
from unittest.mock import patch


class TestMainEntry:
    """Test the main entry point."""

    def test_main_import_available(self):
        """Test that main function is importable."""
        from sseed.__main__ import main

        assert callable(main)

    def test_main_module_execution(self):
        """Test running sseed as a module."""
        # Test that the module can be executed (will fail with no args, but that's expected)
        result = subprocess.run(
            [sys.executable, "-m", "sseed", "--help"],
            capture_output=True,
            text=True,
        )
        # Should show help and exit cleanly
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "sseed" in result.stdout

    def test_main_function_callable(self):
        """Test that main function from __main__ is callable."""
        import sseed.__main__

        # Verify the main function is imported and callable
        assert hasattr(sseed.__main__, "main")
        assert callable(sseed.__main__.main)

        # Verify sys module is imported
        assert hasattr(sseed.__main__, "sys")
