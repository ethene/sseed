"""Tests for master seed generation functionality in sseed.bip39 module.

Tests BIP-39 master seed generation using PBKDF2-HMAC-SHA512 as specified in BIP-39.
"""

import hashlib
from unittest.mock import patch

import pytest

from sseed.bip39 import (
    generate_master_seed,
    generate_mnemonic,
    mnemonic_to_hex_seed,
)
from sseed.exceptions import MnemonicError


class TestMasterSeedGeneration:
    """Test master seed generation from BIP-39 mnemonics."""

    def test_generate_master_seed_basic(self) -> None:
        """Test basic master seed generation."""
        mnemonic = generate_mnemonic()
        seed = generate_master_seed(mnemonic)

        # Should be 64 bytes (512 bits)
        assert isinstance(seed, bytes)
        assert len(seed) == 64

    def test_generate_master_seed_with_passphrase(self) -> None:
        """Test master seed generation with passphrase."""
        mnemonic = generate_mnemonic()
        passphrase = "test_passphrase"
        
        seed_without = generate_master_seed(mnemonic)
        seed_with = generate_master_seed(mnemonic, passphrase)

        # Seeds should be different
        assert seed_without != seed_with
        assert len(seed_with) == 64

    def test_generate_master_seed_deterministic(self) -> None:
        """Test that master seed generation is deterministic."""
        mnemonic = generate_mnemonic()
        passphrase = "test_passphrase"
        
        seed1 = generate_master_seed(mnemonic, passphrase)
        seed2 = generate_master_seed(mnemonic, passphrase)

        # Should be identical
        assert seed1 == seed2

    def test_generate_master_seed_different_iterations(self) -> None:
        """Test master seed generation with different iteration counts."""
        mnemonic = generate_mnemonic()
        
        seed_2048 = generate_master_seed(mnemonic, iterations=2048)
        seed_4096 = generate_master_seed(mnemonic, iterations=4096)

        # Seeds should be different with different iteration counts
        assert seed_2048 != seed_4096
        assert len(seed_2048) == 64
        assert len(seed_4096) == 64

    def test_generate_master_seed_invalid_mnemonic(self) -> None:
        """Test master seed generation with invalid mnemonic."""
        invalid_mnemonic = "invalid invalid invalid invalid invalid invalid"
        
        with pytest.raises(MnemonicError, match="Failed to generate master seed"):
            generate_master_seed(invalid_mnemonic)

    def test_generate_master_seed_empty_mnemonic(self) -> None:
        """Test master seed generation with empty mnemonic."""
        with pytest.raises(MnemonicError):
            generate_master_seed("")

    def test_generate_master_seed_unicode_normalization(self) -> None:
        """Test that Unicode normalization works correctly."""
        mnemonic = generate_mnemonic()
        passphrase1 = "café"  # NFC form
        passphrase2 = "cafe\u0301"  # NFD form (e + combining acute accent)
        
        seed1 = generate_master_seed(mnemonic, passphrase1)
        seed2 = generate_master_seed(mnemonic, passphrase2)

        # Should be identical after NFKD normalization
        assert seed1 == seed2

    def test_mnemonic_to_hex_seed(self) -> None:
        """Test conversion of mnemonic to hexadecimal seed."""
        mnemonic = generate_mnemonic()
        hex_seed = mnemonic_to_hex_seed(mnemonic)

        # Should be 128 hex characters (64 bytes * 2)
        assert isinstance(hex_seed, str)
        assert len(hex_seed) == 128
        assert all(c in "0123456789abcdef" for c in hex_seed)

    def test_mnemonic_to_hex_seed_with_passphrase(self) -> None:
        """Test hex seed generation with passphrase."""
        mnemonic = generate_mnemonic()
        passphrase = "test_passphrase"
        
        hex_seed_without = mnemonic_to_hex_seed(mnemonic)
        hex_seed_with = mnemonic_to_hex_seed(mnemonic, passphrase)

        # Should be different
        assert hex_seed_without != hex_seed_with
        assert len(hex_seed_with) == 128

    def test_mnemonic_to_hex_seed_consistency(self) -> None:
        """Test that hex seed matches binary seed."""
        mnemonic = generate_mnemonic()
        passphrase = "test_passphrase"
        
        binary_seed = generate_master_seed(mnemonic, passphrase)
        hex_seed = mnemonic_to_hex_seed(mnemonic, passphrase)

        # Hex seed should match binary seed
        assert hex_seed == binary_seed.hex()

    def test_master_seed_bip39_compliance(self) -> None:
        """Test that master seed generation follows BIP-39 specification."""
        # Use a known test vector (if available) or verify the algorithm
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        passphrase = "TREZOR"
        
        # Generate seed using our function
        seed = generate_master_seed(mnemonic, passphrase, iterations=2048)
        
        # Verify using direct PBKDF2 calculation
        import unicodedata
        normalized_mnemonic = unicodedata.normalize("NFKD", mnemonic.strip())
        normalized_passphrase = unicodedata.normalize("NFKD", passphrase)
        password = normalized_mnemonic.encode("utf-8")
        salt = ("mnemonic" + normalized_passphrase).encode("utf-8")
        
        expected_seed = hashlib.pbkdf2_hmac("sha512", password, salt, 2048, dklen=64)
        
        assert seed == expected_seed

    def test_master_seed_memory_cleanup(self) -> None:
        """Test that sensitive variables are properly cleaned up."""
        mnemonic = generate_mnemonic()
        passphrase = "test_passphrase"
        
        with patch("sseed.bip39.secure_delete_variable") as mock_cleanup:
            generate_master_seed(mnemonic, passphrase)
            
            # Should call secure_delete_variable for password and salt
            assert mock_cleanup.call_count >= 2

    def test_hex_seed_memory_cleanup(self) -> None:
        """Test that hex seed function cleans up memory."""
        mnemonic = generate_mnemonic()
        
        with patch("sseed.bip39.secure_delete_variable") as mock_cleanup:
            mnemonic_to_hex_seed(mnemonic)
            
            # Should clean up the master seed
            mock_cleanup.assert_called()


class TestMasterSeedEdgeCases:
    """Test edge cases for master seed generation."""

    def test_generate_master_seed_pbkdf2_failure(self) -> None:
        """Test master seed generation when PBKDF2 fails."""
        mnemonic = generate_mnemonic()
        
        with patch("hashlib.pbkdf2_hmac", side_effect=Exception("PBKDF2 failed")):
            with pytest.raises(MnemonicError, match="Failed to generate master seed"):
                generate_master_seed(mnemonic)

    def test_generate_master_seed_validation_failure(self) -> None:
        """Test master seed generation when mnemonic validation fails."""
        with patch("sseed.bip39.validate_mnemonic", return_value=False):
            with pytest.raises(MnemonicError, match="Cannot generate master seed from invalid mnemonic"):
                generate_master_seed("some mnemonic")

    def test_mnemonic_to_hex_seed_cleanup_failure(self) -> None:
        """Test hex seed generation when cleanup fails."""
        mnemonic = generate_mnemonic()
        
        with patch("sseed.bip39.secure_delete_variable", side_effect=Exception("Cleanup failed")):
            # Should raise MnemonicError when cleanup fails in generate_master_seed
            with pytest.raises(MnemonicError, match="Failed to generate master seed"):
                mnemonic_to_hex_seed(mnemonic)

    def test_master_seed_extreme_iterations(self) -> None:
        """Test master seed generation with extreme iteration counts."""
        mnemonic = generate_mnemonic()
        
        # Very low iterations (not recommended but should work)
        seed_low = generate_master_seed(mnemonic, iterations=1)
        assert len(seed_low) == 64
        
        # High iterations (slower but should work)
        seed_high = generate_master_seed(mnemonic, iterations=10000)
        assert len(seed_high) == 64
        
        # Should be different
        assert seed_low != seed_high

    def test_master_seed_special_characters_passphrase(self) -> None:
        """Test master seed generation with special characters in passphrase."""
        mnemonic = generate_mnemonic()
        special_passphrase = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        
        seed = generate_master_seed(mnemonic, special_passphrase)
        assert len(seed) == 64

    def test_master_seed_long_passphrase(self) -> None:
        """Test master seed generation with very long passphrase."""
        mnemonic = generate_mnemonic()
        long_passphrase = "a" * 1000  # 1000 character passphrase
        
        seed = generate_master_seed(mnemonic, long_passphrase)
        assert len(seed) == 64

    def test_master_seed_empty_passphrase_vs_none(self) -> None:
        """Test that empty string passphrase equals default None passphrase."""
        mnemonic = generate_mnemonic()
        
        seed_empty = generate_master_seed(mnemonic, "")
        seed_default = generate_master_seed(mnemonic)
        
        assert seed_empty == seed_default 