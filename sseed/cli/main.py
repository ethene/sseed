"""Main CLI entry point.

Handles command dispatch and top-level error handling.
"""

import logging
import sys
from typing import (
    List,
    Optional,
)

from sseed.logging_config import get_logger

from . import EXIT_SUCCESS
from .error_handling import handle_top_level_errors
from .parser import parse_args

logger = get_logger(__name__)


@handle_top_level_errors
def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command line arguments (default: None uses sys.argv[1:]).

    Returns:
        Exit code.
    """
    # Parse arguments first
    parsed_args = parse_args(args)

    # Configure logging level based on argument
    if hasattr(parsed_args, "log_level"):
        # Set the root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, parsed_args.log_level))

        # Also set the sseed logger level specifically
        sseed_logger = logging.getLogger("sseed")
        sseed_logger.setLevel(getattr(logging, parsed_args.log_level))

    logger.debug("CLI execution starting with command: %s", parsed_args.command)

    # Dispatch to command handler
    exit_code = parsed_args.func(parsed_args)

    logger.debug("CLI execution completed with exit code: %d", exit_code)
    return exit_code or EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
