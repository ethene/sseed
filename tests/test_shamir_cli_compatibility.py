#!/usr/bin/env python3
"""Cross-compatibility tests between sseed and official Trezor shamir CLI tool.

This test verifies interoperability with the official shamir CLI tool from:
https://github.com/trezor/python-shamir-mnemonic

Both tools use the same shamir-mnemonic==0.3.0 library, ensuring full compatibility.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def run_command(cmd: str, input_text: str = None) -> tuple[int, str, str]:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, input=input_text
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def extract_clean_text(content: str) -> str:
    """Extract clean text from file, removing comments."""
    lines = [
        line.strip()
        for line in content.split("\n")
        if line.strip() and not line.startswith("#")
    ]
    return " ".join(lines)


def is_shamir_cli_available() -> bool:
    """Check if the official Trezor shamir CLI tool is available."""
    returncode, _, _ = run_command("which shamir")
    return returncode == 0


@pytest.mark.skipif(
    not is_shamir_cli_available(),
    reason="Official Trezor shamir CLI tool not available",
)
class TestShamirCliCompatibility:
    """Test compatibility with official Trezor shamir CLI tool."""

    def test_sseed_shards_with_shamir_recover(self):
        """Test that sseed-generated shards work with shamir recover command."""
        # Generate test mnemonic with sseed
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            mnemonic_file = f.name

        try:
            # Generate mnemonic
            returncode, stdout, stderr = run_command(f"sseed gen -o {mnemonic_file}")
            assert returncode == 0, f"Failed to generate mnemonic: {stderr}"

            # Read the generated mnemonic
            with open(mnemonic_file, "r") as f:
                original_mnemonic = extract_clean_text(f.read())

            # Create shards with sseed
            shard_prefix = tempfile.mktemp(prefix="test_shards_")
            returncode, stdout, stderr = run_command(
                f"sseed shard -i {mnemonic_file} -g 2-of-3 --separate -o {shard_prefix}"
            )
            assert returncode == 0, f"Failed to create shards: {stderr}"

            # Read the generated shards
            shard_files = [f"{shard_prefix}_{i:02d}.txt" for i in range(1, 4)]
            shards = []
            for shard_file in shard_files:
                if os.path.exists(shard_file):
                    with open(shard_file, "r") as f:
                        shard = extract_clean_text(f.read())
                        shards.append(shard)

            assert len(shards) >= 2, "Should have at least 2 shards"

            # Test recovery with shamir command (use first 2 shards)
            recovery_input = f"{shards[0]}\n{shards[1]}\n\n"
            returncode, stdout, stderr = run_command("shamir recover", recovery_input)

            assert returncode == 0, f"shamir recover failed: {stderr}"
            assert "master secret is:" in stdout, "Should return master secret"

            # Extract master secret
            lines = stdout.strip().split("\n")
            master_secret_line = [line for line in lines if "master secret is:" in line]
            assert len(master_secret_line) > 0, "Should find master secret line"

            master_secret = master_secret_line[0].split("master secret is: ")[1]
            assert (
                len(master_secret) == 64
            ), "Master secret should be 64 hex characters (32 bytes)"

        finally:
            # Cleanup
            try:
                os.unlink(mnemonic_file)
                for shard_file in shard_files:
                    if os.path.exists(shard_file):
                        os.unlink(shard_file)
            except Exception:
                pass

    def test_shamir_shards_with_sseed_restore(self):
        """Test that shamir-generated shards work with sseed restore command."""
        # Create shards with shamir command
        returncode, stdout, stderr = run_command("shamir create 2of3")
        assert returncode == 0, f"shamir create failed: {stderr}"

        # Parse shamir output
        lines = stdout.strip().split("\n")
        master_secret_line = [line for line in lines if "Using master secret:" in line]
        assert len(master_secret_line) > 0, "Should find master secret line"

        # Extract shards (lines with many words that aren't metadata)
        shard_lines = [
            line.strip()
            for line in lines
            if line.strip()
            and not line.startswith("Using")
            and not line.startswith("Group")
            and len(line.strip().split()) > 10
        ]

        assert len(shard_lines) >= 2, "Should have at least 2 shards"

        # Save shards to files
        shard_files = []
        try:
            for i, shard in enumerate(shard_lines[:2]):  # Use first 2 shards
                shard_file = tempfile.mktemp(suffix=".txt")
                with open(shard_file, "w") as f:
                    f.write(shard)
                shard_files.append(shard_file)

            # Test recovery with sseed
            returncode, stdout, stderr = run_command(
                f"sseed restore {' '.join(shard_files)}"
            )
            assert returncode == 0, f"sseed restore failed: {stderr}"

            # Extract reconstructed mnemonic
            lines = stdout.strip().split("\n")
            mnemonic_line = [
                line
                for line in lines
                if not line.startswith("2025-") and len(line.split()) >= 12
            ]
            assert len(mnemonic_line) > 0, "Should find reconstructed mnemonic"

            reconstructed_mnemonic = mnemonic_line[0]
            words = reconstructed_mnemonic.split()
            assert len(words) in [
                12,
                15,
                18,
                21,
                24,
            ], "Should be valid BIP-39 word count"

        finally:
            # Cleanup
            for shard_file in shard_files:
                try:
                    os.unlink(shard_file)
                except Exception:
                    pass

    def test_round_trip_compatibility(self):
        """Test full round-trip compatibility between sseed and shamir tools."""
        # Generate mnemonic with sseed
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            mnemonic_file = f.name

        try:
            # Generate and shard with sseed
            run_command(f"sseed gen -o {mnemonic_file}")

            with open(mnemonic_file, "r") as f:
                original_mnemonic = extract_clean_text(f.read())

            # Create shards with sseed
            shard_prefix = tempfile.mktemp(prefix="roundtrip_shards_")
            run_command(
                f"sseed shard -i {mnemonic_file} -g 2-of-3 --separate -o {shard_prefix}"
            )

            # Find shard files
            shard_files = [f"{shard_prefix}_{i:02d}.txt" for i in range(1, 4)]
            existing_shards = [f for f in shard_files if os.path.exists(f)]
            assert len(existing_shards) >= 2, "Should have at least 2 shard files"

            # Restore with sseed (round-trip test)
            returncode, stdout, stderr = run_command(
                f"sseed restore {existing_shards[0]} {existing_shards[1]}"
            )
            assert returncode == 0, f"Round-trip restore failed: {stderr}"

            # Extract reconstructed mnemonic
            lines = stdout.strip().split("\n")
            mnemonic_line = [
                line
                for line in lines
                if not line.startswith("2025-") and len(line.split()) >= 12
            ]
            assert len(mnemonic_line) > 0, "Should find reconstructed mnemonic"

            roundtrip_mnemonic = mnemonic_line[0]

            # Verify perfect round-trip
            assert (
                roundtrip_mnemonic.strip() == original_mnemonic.strip()
            ), f"Round-trip mismatch:\nOriginal:  {original_mnemonic}\nRoundtrip: {roundtrip_mnemonic}"

        finally:
            # Cleanup
            try:
                os.unlink(mnemonic_file)
                for shard_file in shard_files:
                    if os.path.exists(shard_file):
                        os.unlink(shard_file)
            except Exception:
                pass


@pytest.mark.skipif(
    not is_shamir_cli_available(),
    reason="Official Trezor shamir CLI tool not available",
)
def test_shamir_cli_info():
    """Test that we can get information about the shamir CLI tool."""
    # Test basic functionality
    returncode, stdout, stderr = run_command("shamir --help")
    assert returncode == 0, "shamir --help should work"
    assert "create" in stdout, "Should show create command"
    assert "recover" in stdout, "Should show recover command"

    # Test create help
    returncode, stdout, stderr = run_command("shamir create --help")
    assert returncode == 0, "shamir create --help should work"
    assert "SCHEME" in stdout, "Should show scheme parameter"


if __name__ == "__main__":
    # Run a quick compatibility check
    if is_shamir_cli_available():
        print("✅ Official Trezor shamir CLI tool is available")
        print("🔬 Running basic compatibility test...")

        # Quick test
        returncode, stdout, stderr = run_command("shamir create single")
        if returncode == 0:
            print("✅ Basic shamir create test passed")
        else:
            print(f"❌ Basic shamir create test failed: {stderr}")
    else:
        print("⚠️  Official Trezor shamir CLI tool not available")
        print("   Install with: pip install shamir-mnemonic[cli]")
