"""Version command implementation.

Displays comprehensive version and system information.
"""

import argparse
import json
import platform
import sys
from importlib import metadata
from typing import (
    Any,
    Dict,
)

from sseed import __version__
from sseed.logging_config import get_logger

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit codes locally to avoid circular import
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1

logger = get_logger(__name__)


class VersionCommand(BaseCommand):
    """Show detailed version and system information."""

    def __init__(self) -> None:
        super().__init__(
            name="version",
            help_text="Show version and system information",
            description="Display comprehensive version and system information.",
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add version command arguments."""
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output version information in JSON format",
        )

    @handle_common_errors("version display")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the version command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code (always 0 for success).
        """
        try:
            # Core version information
            version_info: Dict[str, Any] = {
                "sseed": __version__,
                "python": sys.version.split()[0],
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "machine": platform.machine(),
                    "architecture": platform.architecture()[0],
                },
            }

            # Dependency versions
            dependencies: Dict[str, str] = {}
            try:
                dependencies["bip-utils"] = metadata.version("bip-utils")
            except metadata.PackageNotFoundError:
                dependencies["bip-utils"] = "not installed"

            try:
                dependencies["slip39"] = metadata.version("slip39")
            except metadata.PackageNotFoundError:
                dependencies["slip39"] = "not installed"

            version_info["dependencies"] = dependencies

            # Build and environment information
            version_info["build"] = {
                "python_implementation": platform.python_implementation(),
                "python_compiler": platform.python_compiler(),
            }

            if args.json:
                # JSON output for scripting
                print(json.dumps(version_info, indent=2))
            else:
                # Human-readable output
                print(f"🔐 SSeed v{version_info['sseed']}")
                print("=" * 40)
                print()
                print("📋 Core Information:")
                print(f"   Version: {version_info['sseed']}")
                python_impl = version_info["build"]["python_implementation"]
                print(f"   Python:  {version_info['python']} ({python_impl})")
                print()
                print("🖥️  System Information:")
                os_name = version_info["platform"]["system"]
                os_release = version_info["platform"]["release"]
                print(f"   OS:           {os_name} {os_release}")
                machine = version_info["platform"]["machine"]
                arch = version_info["platform"]["architecture"]
                print(f"   Architecture: {machine} ({arch})")
                print()
                print("📦 Dependencies:")
                for dep, ver in version_info["dependencies"].items():
                    status = "✅" if ver != "not installed" else "❌"
                    print(f"   {status} {dep}: {ver}")
                print()
                print("🔗 Links:")
                print("   Repository: https://github.com/ethene/sseed")
                print("   PyPI:       https://pypi.org/project/sseed/")
                print("   Issues:     https://github.com/ethene/sseed/issues")

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error displaying version information: %s", e)
            print(f"Error: Failed to gather version information: {e}", file=sys.stderr)
            return EXIT_USAGE_ERROR

        return EXIT_SUCCESS


# Backward compatibility wrapper
def handle_version_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for original handle_version_command."""
    return VersionCommand().handle(args)
