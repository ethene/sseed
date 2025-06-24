"""CLI package for sseed application.

Provides command-line interface with modular command architecture.
Maintains backward compatibility with the original monolithic CLI.
"""

# Exit codes (moved from cli.py)
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130  # Standard exit code for SIGINT

# Main entry point
from .main import main

# Backward compatibility exports
__all__ = [
    "main",
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR", 
    "EXIT_CRYPTO_ERROR",
    "EXIT_FILE_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_INTERRUPTED",
] 