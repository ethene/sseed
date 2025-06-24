"""Main entry point for CLI application.

Provides the main() function that handles argument parsing and command dispatch.
"""

import sys
from typing import List, Optional

from sseed.logging_config import get_logger

from . import EXIT_SUCCESS
from .error_handling import handle_top_level_errors
from .parser import parse_args

logger = get_logger(__name__)


@handle_top_level_errors
def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the sseed CLI application.

    Args:
        args: Command line arguments (default: None uses sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    # Parse command line arguments
    parsed_args = parse_args(args)
    
    logger.info("Starting sseed command: %s", parsed_args.command)
    
    # Dispatch to the appropriate command handler
    exit_code = parsed_args.func(parsed_args)
    
    logger.info("Command completed with exit code: %d", exit_code)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 