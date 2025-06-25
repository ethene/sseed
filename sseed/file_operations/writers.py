"""File writing operations for mnemonics and shards.

Provides centralized writing functionality with UTF-8 support, comment generation,
and secure file handling for BIP-39 and SLIP-39 file formats.
"""

import sys
from pathlib import Path
from typing import List

from sseed.exceptions import FileError
from sseed.logging_config import get_logger
from sseed.validation import sanitize_filename

from .formatters import (
    format_file_with_comments,
    format_multi_shard_content,
    generate_bip39_header,
    generate_slip39_multi_header,
    generate_slip39_single_header,
)

logger = get_logger(__name__)


def _write_file_safely(file_path: Path, content: str) -> None:
    """Common file writing with UTF-8, sanitization, and error handling.

    Args:
        file_path: Path object for the file to write.
        content: Content to write to the file.

    Raises:
        FileError: If file cannot be written.
    """
    try:
        # Sanitize only the filename component
        safe_filename = sanitize_filename(file_path.name)
        safe_path = file_path.parent / safe_filename

        # Create directory if it doesn't exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with UTF-8 encoding
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug("Successfully wrote file: %s", safe_path)

    except Exception as e:
        error_msg = f"Failed to write file '{file_path}': {e}"
        logger.error(error_msg)
        raise FileError(
            error_msg, context={"file_path": str(file_path), "error": str(e)}
        ) from e


def _create_numbered_filename(base_path: Path, index: int) -> Path:
    """Generate numbered filename for separate shard files.

    Args:
        base_path: Base path for the files.
        index: Current file index (1-based).

    Returns:
        Path object for the numbered file.
    """
    stem = base_path.stem or "shard"
    suffix = base_path.suffix or ".txt"
    directory = base_path.parent

    # Create numbered filename
    filename = f"{stem}_{index:02d}{suffix}"
    return directory / filename


def write_mnemonic_to_file(
    mnemonic: str, file_path: str, include_comments: bool = True
) -> None:
    """Write a mnemonic to a file.

    Writes a mnemonic to a file in UTF-8 format as specified in Phase 6 requirements.

    Args:
        mnemonic: Mnemonic string to write.
        file_path: Path where to write the file.
        include_comments: Whether to include descriptive comments (default: True).

    Raises:
        FileError: If file cannot be written.
    """
    try:
        file_path_obj = Path(file_path)
        logger.info("Writing mnemonic to file: %s", file_path_obj)

        # Generate content with or without comments
        if include_comments:
            header_lines = generate_bip39_header()
            content = format_file_with_comments(mnemonic, header_lines)
        else:
            content = f"{mnemonic}\n"

        # Write file using common helper
        _write_file_safely(file_path_obj, content)

        logger.info("Successfully wrote mnemonic to file: %s", file_path_obj)

    except FileError:
        # Re-raise FileError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to write mnemonic to file '{file_path}': {e}"
        logger.error(error_msg)
        raise FileError(
            error_msg, context={"file_path": str(file_path), "error": str(e)}
        ) from e


def write_shards_to_file(shards: List[str], file_path: str) -> None:
    """Write SLIP-39 shards to a single file.

    Writes multiple shards to a single file, one shard per line.
    Implements Phase 6 file format with enhanced comments and UTF-8 encoding.

    Args:
        shards: List of shard strings to write.
        file_path: Path where to write the file.

    Raises:
        FileError: If file cannot be written.
    """
    try:
        file_path_obj = Path(file_path)
        logger.info("Writing %d shards to file: %s", len(shards), file_path_obj)

        # Generate header and content
        header_lines = generate_slip39_multi_header(len(shards))
        shard_content = format_multi_shard_content(shards)
        content = format_file_with_comments(shard_content, header_lines)

        # Write file using common helper
        _write_file_safely(file_path_obj, content)

        logger.info(
            "Successfully wrote %d shards to file: %s", len(shards), file_path_obj
        )

    except FileError:
        # Re-raise FileError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to write shards to file '{file_path}': {e}"
        logger.error(error_msg)
        raise FileError(
            error_msg,
            context={
                "file_path": str(file_path),
                "shard_count": len(shards),
                "error": str(e),
            },
        ) from e


def write_shards_to_separate_files(shards: List[str], base_path: str) -> List[str]:
    """Write SLIP-39 shards to separate files.

    Writes each shard to a separate file with numbered suffixes.
    Implements Phase 6 file format with UTF-8 encoding and comment support.

    Args:
        shards: List of shard strings to write.
        base_path: Base path for the files (e.g., "shards.txt" -> "shards_01.txt", "shards_02.txt").

    Returns:
        List of file paths where shards were written.

    Raises:
        FileError: If any file cannot be written.
    """
    try:
        base_path_obj = Path(base_path)

        # Create directory if it doesn't exist
        base_path_obj.parent.mkdir(parents=True, exist_ok=True)

        file_paths = []

        for i, shard in enumerate(shards, 1):
            # Create numbered filename
            file_path = _create_numbered_filename(base_path_obj, i)

            # Generate header and content for individual shard
            header_lines = generate_slip39_single_header(i, len(shards))
            content = format_file_with_comments(shard, header_lines)

            # Write individual shard file
            _write_file_safely(file_path, content)
            file_paths.append(str(file_path))

        logger.info("Successfully wrote %d shards to separate files", len(shards))
        return file_paths

    except FileError:
        # Re-raise FileError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to write shards to separate files: {e}"
        logger.error(error_msg)
        raise FileError(
            error_msg,
            context={
                "base_path": str(base_path),
                "shard_count": len(shards),
                "error": str(e),
            },
        ) from e


def write_to_stdout(content: str) -> None:
    """Write content to stdout.

    Writes content to stdout with proper encoding.

    Args:
        content: Content to write.

    Raises:
        FileError: If writing to stdout fails.
    """
    try:
        logger.info("Writing output to stdout")

        print(content)
        sys.stdout.flush()

        logger.info("Successfully wrote output to stdout")

    except Exception as e:
        error_msg = f"Failed to write to stdout: {e}"
        logger.error(error_msg)
        raise FileError(error_msg, context={"error": str(e)}) from e
