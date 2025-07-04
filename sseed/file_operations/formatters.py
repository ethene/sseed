"""File format and comment generation utilities.

Provides centralized comment generation for BIP-39 and SLIP-39 file formats,
eliminating duplication and enabling consistent file formatting.
"""

import datetime
from typing import List


def generate_bip39_header() -> List[str]:
    """Generate BIP-39 file header comments.

    Returns:
        List of comment lines for BIP-39 mnemonic files.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        "# BIP-39 Mnemonic File",
        f"# Generated by sseed on {timestamp}",
        "#",
        "# This file contains a BIP-39 mnemonic for cryptocurrency wallet recovery.",
        "# Keep this file extremely secure and consider splitting into SLIP-39 shards.",
        "# Anyone with access to this mnemonic can access your funds.",
        "#",
        "# File format: Plain text UTF-8",
        "# Lines starting with '#' are comments and will be ignored.",
        "#",
    ]


def generate_slip39_multi_header(shard_count: int) -> List[str]:
    """Generate SLIP-39 multi-shard file header comments.

    Args:
        shard_count: Number of shards in the file.

    Returns:
        List of comment lines for multi-shard SLIP-39 files.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        "# SLIP-39 Shards File",
        f"# Generated by sseed on {timestamp}",
        f"# Contains {shard_count} SLIP-39 shards",
        "#",
        "# This file contains multiple SLIP-39 shards for mnemonic reconstruction.",
        "# Keep this file secure and consider splitting shards into separate files.",
        "# You need at least the threshold number of shards to reconstruct the original mnemonic.",
        "#",
        "# File format: Plain text UTF-8",
        "# Lines starting with '#' are comments and will be ignored.",
        "# Each shard is on its own line after the shard number comment.",
        "#",
    ]


def generate_slip39_single_header(shard_num: int, total_shards: int) -> List[str]:
    """Generate SLIP-39 single shard file header comments.

    Args:
        shard_num: Current shard number (1-based).
        total_shards: Total number of shards.

    Returns:
        List of comment lines for single shard SLIP-39 files.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        "# SLIP-39 Shard File",
        f"# Generated by sseed on {timestamp}",
        f"# Shard {shard_num} of {total_shards}",
        "#",
        "# This file contains a SLIP-39 shard for mnemonic reconstruction.",
        "# Keep this shard secure and separate from other shards.",
        "# You need at least the threshold number of shards to reconstruct the original mnemonic.",
        "#",
        "# File format: Plain text UTF-8",
        "# Lines starting with '#' are comments and will be ignored.",
        "#",
    ]


def format_file_with_comments(content: str, header_lines: List[str]) -> str:
    """Combine header comments with content.

    Args:
        content: The main content to write.
        header_lines: List of header comment lines.

    Returns:
        Formatted file content with header and content.
    """
    # Join header lines
    header = "\n".join(header_lines)

    # Combine header with content
    if header:
        return f"{header}\n{content}\n"
    return f"{content}\n"


def format_multi_shard_content(shards: List[str]) -> str:
    """Format multiple shards with individual shard comments.

    Args:
        shards: List of shard strings.

    Returns:
        Formatted content with shard number comments.
    """
    lines = []

    for i, shard in enumerate(shards, 1):
        lines.append(f"# Shard {i} of {len(shards)}")
        lines.append(shard)
        lines.append("")  # Empty line between shards for readability

    return "\n".join(lines)
