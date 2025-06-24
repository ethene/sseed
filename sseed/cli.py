"""CLI module for SSeed - Backward compatibility wrapper.

This module maintains backward compatibility while delegating to the new
modular CLI architecture in the sseed.cli package.

REFACTORING COMPLETE (Stage 1):
- Original cli.py (921 lines) → Modular architecture
- 8 functions → 5 command classes + base infrastructure
- 80 lines of duplicated error handling → Standardized decorators
- Mixed responsibilities → Single-responsibility modules

New modular structure:
- sseed/cli/__init__.py       - Package initialization and exit codes
- sseed/cli/main.py          - Main entry point (31 lines)
- sseed/cli/parser.py        - Argument parser creation (93 lines)
- sseed/cli/base.py          - Base command class (157 lines)
- sseed/cli/error_handling.py - Standardized error handling (84 lines)
- sseed/cli/examples.py      - Usage examples (73 lines)
- sseed/cli/commands/        - Individual command implementations (5 files)

Benefits achieved:
✅ New command addition: 921-line modification → 100-line file
✅ Error handling: 80 lines duplication → Decorator-based standardization
✅ Parser complexity: 245-line function → Modular registry system
✅ Testing: Monolithic testing → Isolated command testing
✅ Maintenance: Mixed responsibilities → Single-responsibility modules
"""

import sys

# Import the main function from the new modular CLI
from sseed.cli.main import main

# Exit codes for backward compatibility
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130  # Standard exit code for SIGINT

# Re-export only the main entry point for backward compatibility
__all__ = [
    "main",
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR",
    "EXIT_CRYPTO_ERROR",
    "EXIT_FILE_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_INTERRUPTED",
]


# For scripts that import and call main directly
if __name__ == "__main__":
    sys.exit(main())
