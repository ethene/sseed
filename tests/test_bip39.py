"""Tests for sseed.bip39 module.

Tests BIP-39 mnemonic generation and validation as implemented in Phase 2.
"""

import pytest

from sseed.bip39 import generate_mnemonic, validate_mnemonic, parse_mnemonic, get_mnemonic_entropy
from sseed.exceptions import MnemonicError


class TestBip39Operations:
    """Test BIP-39 mnemonic operations."""

    def test_generate_mnemonic(self) -> None:
        """Test BIP-39 mnemonic generation."""
        mnemonic = generate_mnemonic()

        # Should be a string with 24 words
        assert isinstance(mnemonic, str)
        words = mnemonic.split()
        assert len(words) == 24

        # All words should be lowercase alphabetic
        for word in words:
            assert word.islower()
            assert word.isalpha()

    def test_generate_mnemonic_uniqueness(self) -> None:
        """Test that generated mnemonics are unique."""
        mnemonics = [generate_mnemonic() for _ in range(10)]

        # All mnemonics should be unique
        assert len(set(mnemonics)) == 10

    def test_validate_mnemonic_valid(self) -> None:
        """Test validation of valid mnemonics."""
        mnemonic = generate_mnemonic()

        assert validate_mnemonic(mnemonic) is True

    def test_validate_mnemonic_invalid(self) -> None:
        """Test validation of invalid mnemonics."""
        # Invalid checksum - using words that exist but wrong checksum
        invalid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"

        assert validate_mnemonic(invalid_mnemonic) is False

    def test_validate_mnemonic_empty(self) -> None:
        """Test validation of empty mnemonic."""
        assert validate_mnemonic("") is False
        assert validate_mnemonic("   ") is False

    def test_parse_mnemonic(self) -> None:
        """Test mnemonic parsing."""
        mnemonic = generate_mnemonic()
        words = parse_mnemonic(mnemonic)

        assert isinstance(words, list)
        assert len(words) == 24
        assert all(isinstance(word, str) for word in words)

    def test_parse_mnemonic_with_whitespace(self) -> None:
        """Test parsing mnemonic with extra whitespace."""
        mnemonic = generate_mnemonic()
        mnemonic_with_spaces = f"  {mnemonic}  "

        words = parse_mnemonic(mnemonic_with_spaces)
        assert len(words) == 24

    def test_parse_mnemonic_invalid(self) -> None:
        """Test parsing invalid mnemonic."""
        with pytest.raises(MnemonicError):
            parse_mnemonic("")

        with pytest.raises(MnemonicError):
            parse_mnemonic("invalid word count")

    def test_get_mnemonic_entropy(self) -> None:
        """Test entropy extraction from mnemonic."""
        mnemonic = generate_mnemonic()
        entropy = get_mnemonic_entropy(mnemonic)

        assert isinstance(entropy, bytes)
        assert len(entropy) == 32  # 256 bits for 24-word mnemonic

    def test_get_mnemonic_entropy_invalid(self) -> None:
        """Test entropy extraction from invalid mnemonic."""
        invalid_mnemonic = "invalid mnemonic with wrong checksum"

        with pytest.raises(MnemonicError):
            get_mnemonic_entropy(invalid_mnemonic)

    def test_round_trip(self) -> None:
        """Test round-trip: generate -> validate -> extract entropy."""
        # Generate mnemonic
        mnemonic = generate_mnemonic()

        # Validate it
        assert validate_mnemonic(mnemonic) is True

        # Extract entropy
        entropy = get_mnemonic_entropy(mnemonic)
        assert len(entropy) == 32

        # Parse words
        words = parse_mnemonic(mnemonic)
        assert len(words) == 24
