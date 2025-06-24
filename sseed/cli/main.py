"""Main entry point for the CLI application.

Handles command-line argument parsing and command dispatch.
"""

from .error_handling import handle_top_level_errors
from .parser import create_parser

# Define exit codes locally to avoid circular import
EXIT_SUCCESS = 0


@handle_top_level_errors
def main() -> int:
    """Main entry point for the CLI application.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Dispatch to the appropriate command handler
    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return EXIT_SUCCESS
