#!/usr/bin/env python3
"""Cross-compatibility tests between sseed and official Trezor shamir CLI tool.

This test verifies interoperability with the official shamir CLI tool from:
https://github.com/trezor/python-shamir-mnemonic

Both tools use the same shamir-mnemonic==0.3.0 library, ensuring full compatibility.
These tests verify exact mathematical equivalence by comparing entropy values.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from bip_utils import Bip39MnemonicGenerator

# Import sseed functions for entropy/mnemonic conversion
from sseed.bip39 import get_mnemonic_entropy


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


def extract_hex_entropy_from_shamir_output(stdout: str) -> str:
    """Extract hex entropy from shamir recover output."""
    lines = stdout.strip().split("\n")
    for line in lines:
        if "master secret is:" in line:
            return line.split("master secret is: ")[1].strip()
    return ""


def entropy_bytes_to_hex(entropy_bytes: bytes) -> str:
    """Convert entropy bytes to hex string."""
    return entropy_bytes.hex()


def hex_to_entropy_bytes(hex_string: str) -> bytes:
    """Convert hex string to entropy bytes."""
    return bytes.fromhex(hex_string)


def entropy_to_mnemonic(entropy_hex: str) -> str:
    """Convert hex entropy to BIP-39 mnemonic."""
    entropy_bytes = hex_to_entropy_bytes(entropy_hex)
    mnemonic = Bip39MnemonicGenerator().FromEntropy(entropy_bytes)
    return str(mnemonic)


def is_shamir_cli_available() -> bool:
    """Check if the official Trezor shamir CLI tool is available."""
    try:
        returncode, stdout, stderr = run_command("shamir --help")
        return returncode == 0 and "create" in stdout and "recover" in stdout
    except Exception:
        return False


class TestShamirCliCompatibility:
    """Test compatibility with official Trezor shamir CLI tool."""

    @pytest.mark.skipif(
        not is_shamir_cli_available(),
        reason="Official Trezor shamir CLI tool not available",
    )
    def test_sseed_shards_with_shamir_recover_exact_match(self):
        """Test exact mathematical equivalence: sseed shards → shamir recover → entropy match."""
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

            # Extract original entropy from mnemonic for comparison
            original_entropy_bytes = get_mnemonic_entropy(original_mnemonic)
            original_entropy_hex = entropy_bytes_to_hex(original_entropy_bytes)

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

            # Recover entropy with shamir CLI (use first 2 shards)
            recovery_input = f"{shards[0]}\n{shards[1]}\n\n"
            returncode, stdout, stderr = run_command("shamir recover", recovery_input)

            assert returncode == 0, f"shamir recover failed: {stderr}"
            assert "master secret is:" in stdout, "Should return master secret"

            # Extract recovered entropy
            recovered_entropy_hex = extract_hex_entropy_from_shamir_output(stdout)
            assert (
                len(recovered_entropy_hex) == 64
            ), "Should be 64 hex characters (32 bytes)"

            # Verify exact mathematical equivalence
            assert recovered_entropy_hex == original_entropy_hex, (
                f"Entropy mismatch!\n"
                f"Original:  {original_entropy_hex}\n"
                f"Recovered: {recovered_entropy_hex}\n"
                f"This indicates the tools are not mathematically equivalent"
            )

            print(f"✅ EXACT MATCH: Original entropy = Recovered entropy")
            print(f"   Entropy: {original_entropy_hex}")

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
    def test_shamir_shards_with_sseed_restore_exact_match(self):
        """Test exact mathematical equivalence: shamir create → sseed restore → entropy match."""
        # Create shards with shamir command
        returncode, stdout, stderr = run_command("shamir create 2of3")
        assert returncode == 0, f"shamir create failed: {stderr}"

        # Parse shamir output to get original entropy
        lines = stdout.strip().split("\n")
        master_secret_line = [line for line in lines if "Using master secret:" in line]
        assert len(master_secret_line) > 0, "Should find master secret line"

        original_entropy_hex = (
            master_secret_line[0].split("Using master secret: ")[1].strip()
        )
        # shamir create defaults to 128-bit (32 hex chars) or 256-bit (64 hex chars) entropy
        assert len(original_entropy_hex) in [
            32,
            64,
        ], f"Should be 32 or 64 hex characters, got {len(original_entropy_hex)}"

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

            # Restore with sseed
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

            # Extract entropy from reconstructed mnemonic
            reconstructed_entropy_bytes = get_mnemonic_entropy(reconstructed_mnemonic)
            reconstructed_entropy_hex = entropy_bytes_to_hex(
                reconstructed_entropy_bytes
            )

            # Verify exact mathematical equivalence
            assert reconstructed_entropy_hex == original_entropy_hex, (
                f"Entropy mismatch!\n"
                f"Original:      {original_entropy_hex} ({len(original_entropy_hex)//2} bytes)\n"
                f"Reconstructed: {reconstructed_entropy_hex} ({len(reconstructed_entropy_hex)//2} bytes)\n"
                f"This indicates the tools are not mathematically equivalent"
            )

            print(f"✅ EXACT MATCH: Original entropy = Reconstructed entropy")
            print(
                f"   Entropy: {original_entropy_hex} ({len(original_entropy_hex)//2} bytes)"
            )
            print(f"   Mnemonic: {reconstructed_mnemonic}")

        finally:
            # Cleanup
            for shard_file in shard_files:
                try:
                    os.unlink(shard_file)
                except Exception:
                    pass

    @pytest.mark.skipif(
        not is_shamir_cli_available(),
        reason="Official Trezor shamir CLI tool not available",
    )
    def test_bidirectional_entropy_conversion(self):
        """Test bidirectional conversion: entropy ↔ mnemonic equivalence."""
        # Create shards with shamir and get original entropy
        returncode, stdout, stderr = run_command("shamir create 2of3")
        assert returncode == 0, f"shamir create failed: {stderr}"

        # Extract original entropy
        lines = stdout.strip().split("\n")
        master_secret_line = [line for line in lines if "Using master secret:" in line]
        original_entropy_hex = (
            master_secret_line[0].split("Using master secret: ")[1].strip()
        )

        # Convert entropy to BIP-39 mnemonic
        converted_mnemonic = entropy_to_mnemonic(original_entropy_hex)

        # Convert mnemonic back to entropy
        roundtrip_entropy_bytes = get_mnemonic_entropy(converted_mnemonic)
        roundtrip_entropy_hex = entropy_bytes_to_hex(roundtrip_entropy_bytes)

        # Verify perfect round-trip
        assert roundtrip_entropy_hex == original_entropy_hex, (
            f"Round-trip entropy conversion failed!\n"
            f"Original:  {original_entropy_hex}\n"
            f"Roundtrip: {roundtrip_entropy_hex}\n"
            f"Converted mnemonic: {converted_mnemonic}"
        )

        print(f"✅ PERFECT ROUND-TRIP: entropy → mnemonic → entropy")
        print(f"   Original entropy: {original_entropy_hex}")
        print(f"   Converted mnemonic: {converted_mnemonic}")
        print(f"   Roundtrip entropy: {roundtrip_entropy_hex}")

    @pytest.mark.skipif(
        not is_shamir_cli_available(),
        reason="Official Trezor shamir CLI tool not available",
    )
    def test_full_cross_tool_mathematical_equivalence(self):
        """Test complete mathematical equivalence across all tool combinations."""
        # Generate mnemonic with sseed
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            mnemonic_file = f.name

        try:
            # 1. Generate with sseed
            run_command(f"sseed gen -o {mnemonic_file}")
            with open(mnemonic_file, "r") as f:
                sseed_mnemonic = extract_clean_text(f.read())

            sseed_entropy_bytes = get_mnemonic_entropy(sseed_mnemonic)
            sseed_entropy_hex = entropy_bytes_to_hex(sseed_entropy_bytes)

            # 2. Shard with sseed → recover with shamir
            shard_prefix = tempfile.mktemp(prefix="cross_test_")
            run_command(
                f"sseed shard -i {mnemonic_file} -g 2-of-3 --separate -o {shard_prefix}"
            )

            shard_files = [f"{shard_prefix}_{i:02d}.txt" for i in range(1, 4)]
            existing_shards = [f for f in shard_files if os.path.exists(f)]

            # Read shards and recover with shamir
            shards = []
            for shard_file in existing_shards[:2]:
                with open(shard_file, "r") as f:
                    shards.append(extract_clean_text(f.read()))

            recovery_input = f"{shards[0]}\n{shards[1]}\n\n"
            returncode, stdout, stderr = run_command("shamir recover", recovery_input)

            shamir_entropy_hex = extract_hex_entropy_from_shamir_output(stdout)

            # 3. Create with shamir → restore with sseed
            returncode, stdout, stderr = run_command("shamir create 2of3")
            lines = stdout.strip().split("\n")

            # Get original entropy from shamir
            master_secret_line = [
                line for line in lines if "Using master secret:" in line
            ]
            shamir_original_entropy = (
                master_secret_line[0].split("Using master secret: ")[1].strip()
            )

            # Get shards from shamir
            shard_lines = [
                line.strip()
                for line in lines
                if line.strip()
                and not line.startswith("Using")
                and not line.startswith("Group")
                and len(line.strip().split()) > 10
            ]

            # Save shamir shards and restore with sseed
            temp_shards = []
            for i, shard in enumerate(shard_lines[:2]):
                temp_file = tempfile.mktemp(suffix=".txt")
                with open(temp_file, "w") as f:
                    f.write(shard)
                temp_shards.append(temp_file)

            returncode, stdout, stderr = run_command(
                f"sseed restore {' '.join(temp_shards)}"
            )

            # Extract mnemonic and convert to entropy
            lines = stdout.strip().split("\n")
            mnemonic_line = [
                line
                for line in lines
                if not line.startswith("2025-") and len(line.split()) >= 12
            ]
            restored_mnemonic = mnemonic_line[0]

            restored_entropy_bytes = get_mnemonic_entropy(restored_mnemonic)
            restored_entropy_hex = entropy_bytes_to_hex(restored_entropy_bytes)

            # 4. Verify all entropy values match
            print(f"\n🔍 MATHEMATICAL EQUIVALENCE TEST:")
            print(f"   SSeed original entropy:     {sseed_entropy_hex}")
            print(f"   Shamir recovered entropy:   {shamir_entropy_hex}")
            print(f"   Shamir original entropy:    {shamir_original_entropy}")
            print(f"   SSeed restored entropy:     {restored_entropy_hex}")

            # All entropy values should be mathematically equivalent
            assert (
                sseed_entropy_hex == shamir_entropy_hex
            ), "SSeed→Shamir entropy mismatch"
            assert (
                shamir_original_entropy == restored_entropy_hex
            ), "Shamir→SSeed entropy mismatch"

            print(f"✅ PERFECT MATHEMATICAL EQUIVALENCE across all tool combinations!")

            # Cleanup temp shard files
            for temp_file in temp_shards:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

        finally:
            # Cleanup
            try:
                os.unlink(mnemonic_file)
                for shard_file in existing_shards:
                    os.unlink(shard_file)
            except Exception:
                pass

    @pytest.mark.skipif(
        not is_shamir_cli_available(),
        reason="Official Trezor shamir CLI tool not available",
    )
    def test_shamir_cli_info(self):
        """Test that shamir CLI tool provides expected help information."""
        # Test that shamir command exists and provides help
        returncode, stdout, stderr = run_command("shamir --help")
        assert returncode == 0, f"shamir --help failed: {stderr}"
        assert "shamir" in stdout.lower(), "Help should mention shamir"
        assert "create" in stdout, "Help should mention create command"
        assert "recover" in stdout, "Help should mention recover command"


@pytest.mark.skipif(
    not is_shamir_cli_available(),
    reason="Official Trezor shamir CLI tool not available",
)
def test_shamir_cli_info():
    """Test that shamir CLI tool provides expected help information."""
    # Test that shamir command exists and provides help
    returncode, stdout, stderr = run_command("shamir --help")
    assert returncode == 0, f"shamir --help failed: {stderr}"
    assert "shamir" in stdout.lower(), "Help should mention shamir"
    assert "create" in stdout, "Help should mention create command"
    assert "recover" in stdout, "Help should mention recover command"


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
