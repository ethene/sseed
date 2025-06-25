"""File reading operations for mnemonics and shards.

Provides centralized reading functionality with UTF-8 support, comment handling,
and proper error handling for BIP-39 and SLIP-39 file formats.
"""

import sys
from pathlib import Path
from typing import List

from sseed.exceptions import FileError
from sseed.logging_config import get_logger
from sseed.validation import (
    normalize_input,
    validate_mnemonic_words,
)

logger = get_logger(__name__)


def _read_file_content(file_path: Path) -> str:
    """Common file reading with UTF-8 and error handling.

    Args:
        file_path: Path object for the file to read.

    Returns:
        File content as string.

    Raises:
        FileError: If file cannot be read or contains invalid content.
    """
    if not file_path.exists():
        raise FileError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileError(f"Path is not a file: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            raise FileError(f"File is empty: {file_path}")

        return content

    except OSError as e:
        error_msg = f"Failed to read file {file_path}: {e}"
        logger.error(error_msg)
        raise FileError(error_msg) from e


def _extract_non_comment_lines(content: str) -> List[str]:
    """Extract non-comment lines from file content.

    Args:
        content: File content as string.

    Returns:
        List of non-comment, non-empty lines.
    """
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def read_mnemonic_from_file(file_path: str) -> str:
    """Read and validate a mnemonic from a file.

    Reads a mnemonic from a file, ignoring comment lines (starting with #)
    and applying input normalization as specified in PRD Section 6.

    Args:
        file_path: Path to the file containing the mnemonic.

    Returns:
        The normalized mnemonic string.

    Raises:
        FileError: If file cannot be read or contains invalid content.
        ValidationError: If mnemonic format is invalid.
    """
    try:
        file_path_obj = Path(file_path)
        logger.info("Reading mnemonic from file: %s", file_path_obj)

        # Read file content using common helper
        content = _read_file_content(file_path_obj)

        # Extract mnemonic (ignoring comments)
        mnemonic_lines = _extract_non_comment_lines(content)

        if not mnemonic_lines:
            raise FileError(f"No mnemonic found in file: {file_path}")

        if len(mnemonic_lines) > 1:
            raise FileError(f"File contains multiple non-comment lines: {file_path}")

        mnemonic = normalize_input(mnemonic_lines[0])

        # Validate mnemonic format
        words = mnemonic.split()
        validate_mnemonic_words(words)

        logger.info("Successfully read mnemonic from file: %s", file_path_obj)
        return mnemonic

    except FileError:
        # Re-raise FileError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to read mnemonic file {file_path}: {e}"
        logger.error(error_msg)
        raise FileError(error_msg) from e


def read_shard_from_file(file_path: str) -> str:
    """Read a SLIP-39 shard from a file without BIP-39 validation.

    Reads a shard from a file, ignoring comment lines (starting with #)
    and applying input normalization, but without BIP-39 mnemonic validation.

    Args:
        file_path: Path to the file containing the shard.

    Returns:
        The normalized shard string.

    Raises:
        FileError: If file cannot be read or contains invalid content.
    """
    try:
        file_path_obj = Path(file_path)
        logger.debug("Reading shard from file: %s", file_path_obj)

        # Read file content using common helper
        content = _read_file_content(file_path_obj)

        # Extract shard (ignoring comments)
        shard_lines = _extract_non_comment_lines(content)

        if not shard_lines:
            raise FileError(f"No shard found in file: {file_path}")

        if len(shard_lines) > 1:
            raise FileError(f"File contains multiple non-comment lines: {file_path}")

        shard = normalize_input(shard_lines[0])

        # Note: No BIP-39 validation for SLIP-39 shards
        logger.debug("Successfully read shard from file: %s", file_path_obj)
        return shard

    except FileError:
        # Re-raise FileError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to read shard file {file_path}: {e}"
        logger.error(error_msg)
        raise FileError(error_msg) from e


def read_shards_from_files(file_paths: List[str]) -> List[str]:
    """Read SLIP-39 shards from multiple files.

    Reads shards from multiple files, with each file containing one shard.
    Comment lines starting with '#' are ignored.

    Args:
        file_paths: List of file paths containing shards.

    Returns:
        List of shard strings.

    Raises:
        FileError: If any file cannot be read.
    """
    try:
        shards = []

        for file_path in file_paths:
            try:
                shard = read_shard_from_file(file_path)  # Use shard-specific reader
                shards.append(shard)
                logger.debug("Read shard from file: %s", file_path)
            except FileError as e:
                # Add context about which file failed
                raise FileError(
                    f"Failed to read shard from file '{file_path}': {e.message}",
                    context={"file_path": file_path, "original_error": str(e)},
                ) from e

        logger.info("Successfully read %d shards from files", len(shards))
        return shards

    except FileError:
        # Re-raise FileError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to read shards from files: {e}"
        logger.error(error_msg)
        raise FileError(
            error_msg, context={"file_paths": file_paths, "error": str(e)}
        ) from e


def read_from_stdin() -> str:
    """Read input from stdin.

    Reads and normalizes input from stdin, handling comment lines.

    Returns:
        Normalized input string.

    Raises:
        FileError: If reading from stdin fails.
    """
    try:
        logger.info("Reading input from stdin")

        lines = []
        for line in sys.stdin:
            normalized_line = normalize_input(line)

            # Skip empty lines and comments
            if normalized_line and not normalized_line.startswith("#"):
                lines.append(normalized_line)

        if not lines:
            raise FileError(
                "No valid input received from stdin",
                context={"lines_read": len(lines)},
            )

        # Join all non-comment lines (in case input spans multiple lines)
        result = " ".join(lines)
        logger.info("Successfully read input from stdin")

        return result

    except FileError:
        # Re-raise file errors as-is
        raise
    except Exception as e:
        error_msg = f"Failed to read from stdin: {e}"
        logger.error(error_msg)
        raise FileError(error_msg, context={"error": str(e)}) from e
