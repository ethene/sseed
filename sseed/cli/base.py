"""Base command class for CLI architecture.

Provides common functionality and patterns for all CLI commands.
Optimized with lazy imports for better startup performance.
"""

import argparse
from abc import (
    ABC,
    abstractmethod,
)
from typing import Optional


class BaseCommand(ABC):
    """Base class for all CLI commands.

    Provides common functionality like input/output handling,
    argument parsing patterns, and secure memory cleanup.

    Uses lazy imports to minimize startup overhead.
    """

    def __init__(self, name: str, help_text: str, description: str = ""):
        """Initialize base command.

        Args:
            name: Command name (e.g., "gen", "shard").
            help_text: Short help text for command list.
            description: Longer description for command help.
        """
        self.name = name
        self.help_text = help_text
        self.description = description or help_text

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to parser.

        Args:
            parser: ArgumentParser instance for this command.
        """

    @abstractmethod
    def handle(self, args: argparse.Namespace) -> int:
        """Execute the command logic.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code (0 for success, non-zero for error).
        """

    def handle_input(self, args: argparse.Namespace, input_arg: str = "input") -> str:
        """Common input handling pattern (file vs stdin).

        Args:
            args: Parsed command line arguments.
            input_arg: Name of the input argument (default: "input").

        Returns:
            Input content as string.
        """
        # Lazy imports for better startup performance
        from sseed.file_operations import (  # pylint: disable=import-outside-toplevel
            read_from_stdin,
            read_mnemonic_from_file,
        )
        from sseed.logging_config import (  # pylint: disable=import-outside-toplevel
            get_logger,
        )

        logger = get_logger(__name__)
        input_file = getattr(args, input_arg, None)

        if input_file:
            content = read_mnemonic_from_file(input_file)
            logger.info("Read input from file: %s", input_file)
        else:
            content = read_from_stdin()
            logger.info("Read input from stdin")

        return content

    def handle_output(
        self,
        content: str,
        args: argparse.Namespace,
        output_arg: str = "output",
        success_message: Optional[str] = None,
    ) -> None:
        """Common output handling pattern (file vs stdout).

        Args:
            content: Content to output.
            args: Parsed command line arguments.
            output_arg: Name of the output argument (default: "output").
            success_message: Optional success message to print.
        """
        # Lazy imports for better startup performance
        from sseed.file_operations import (  # pylint: disable=import-outside-toplevel
            write_mnemonic_to_file,
        )
        from sseed.logging_config import (  # pylint: disable=import-outside-toplevel
            get_logger,
        )

        logger = get_logger(__name__)
        output_file = getattr(args, output_arg, None)

        if output_file:
            write_mnemonic_to_file(content, output_file, include_comments=True)
            logger.info("Output written to file: %s", output_file)
            if success_message:
                print(success_message.format(file=output_file))
            else:
                print(f"Output written to: {output_file}")
        else:
            print(content)
            logger.info("Output written to stdout")

    def handle_entropy_display(
        self, mnemonic: str, args: argparse.Namespace, output_file: Optional[str] = None
    ) -> str:
        """Common entropy display pattern for --show-entropy flag.

        Args:
            mnemonic: Mnemonic to extract entropy from.
            args: Parsed command line arguments.
            output_file: Optional output file to append entropy to.

        Returns:
            Entropy info string (empty if not requested or failed).
        """
        entropy_info = ""

        if getattr(args, "show_entropy", False):
            # Lazy imports for better startup performance
            from sseed.bip39 import (  # pylint: disable=import-outside-toplevel
                get_mnemonic_entropy,
            )
            from sseed.entropy import (  # pylint: disable=import-outside-toplevel
                secure_delete_variable,
            )
            from sseed.logging_config import (  # pylint: disable=import-outside-toplevel
                get_logger,
            )

            logger = get_logger(__name__)

            try:
                entropy_bytes = get_mnemonic_entropy(mnemonic)
                entropy_hex = entropy_bytes.hex()
                entropy_info = f"# Entropy: {entropy_hex} ({len(entropy_bytes)} bytes)"

                logger.info(
                    "Extracted entropy for display: %d bytes", len(entropy_bytes)
                )

                # Append to file if specified
                if output_file:
                    try:
                        with open(output_file, "a", encoding="utf-8") as f:
                            f.write("\n" + entropy_info + "\n")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        logger.warning("Failed to write entropy to file: %s", e)

                # Clean up entropy from memory
                secure_delete_variable(entropy_bytes, entropy_hex)

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to extract entropy for display: %s", e)
                entropy_info = "# Entropy: <extraction failed>"

        return entropy_info

    def add_common_io_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add common input/output arguments.

        Args:
            parser: ArgumentParser to add arguments to.
        """
        parser.add_argument(
            "-i",
            "--input",
            type=str,
            metavar="FILE",
            help="Input file containing mnemonic (default: stdin)",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            metavar="FILE",
            help="Output file (default: stdout)",
        )

    def add_entropy_display_argument(self, parser: argparse.ArgumentParser) -> None:
        """Add --show-entropy argument.

        Args:
            parser: ArgumentParser to add arguments to.
        """
        parser.add_argument(
            "--show-entropy",
            action="store_true",
            help="Display the underlying entropy (hex) alongside the output",
        )
