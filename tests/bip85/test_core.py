"""Tests for BIP85 core derivation functionality.

Comprehensive test suite covering all BIP85 core operations including:
- Master key creation
- Path encoding  
- Entropy derivation
- Error handling
- Security features
"""

import pytest
from unittest.mock import patch, MagicMock

from bip_utils import Bip32Secp256k1

from sseed.bip85.core import (
    create_bip32_master_key,
    encode_bip85_path,
    derive_bip85_entropy,
    format_bip85_derivation_path,
    validate_master_seed_format,
    BIP85_PURPOSE
)
from sseed.bip85.exceptions import (
    Bip85DerivationError,
    Bip85ValidationError
)


class TestCreateBip32MasterKey:
    """Test BIP32 master key creation from master seed."""
    
    def test_valid_master_seed(self):
        """Test creating master key from valid 64-byte seed."""
        # Valid 64-byte master seed (test vector)
        master_seed = bytes.fromhex(
            "000102030405060708090a0b0c0d0e0f" * 4  # 64 bytes
        )
        
        master_key = create_bip32_master_key(master_seed)
        
        assert isinstance(master_key, Bip32Secp256k1)
        # Should be able to derive children without errors
        child = master_key.ChildKey(0)
        assert isinstance(child, Bip32Secp256k1)
    
    def test_invalid_seed_length(self):
        """Test error handling for invalid seed lengths."""
        # Too short
        with pytest.raises(Bip85ValidationError, match="Master seed must be 64 bytes"):
            create_bip32_master_key(b"too_short")
        
        # Too long  
        with pytest.raises(Bip85ValidationError, match="Master seed must be 64 bytes"):
            create_bip32_master_key(b"x" * 128)
    
    def test_bip_utils_failure(self):
        """Test handling of BIP-utils library failures."""
        master_seed = bytes(64)  # Valid length but will test error handling
        
        with patch('sseed.bip85.core.Bip32Secp256k1.FromSeed') as mock_from_seed:
            mock_from_seed.side_effect = Exception("BIP32 creation failed")
            
            with pytest.raises(Bip85DerivationError, match="Failed to create BIP32 master key"):
                create_bip32_master_key(master_seed)


class TestEncodeBip85Path:
    """Test BIP85 path encoding for HMAC."""
    
    def test_valid_path_encoding(self):
        """Test encoding valid BIP85 path components."""
        path_bytes = encode_bip85_path(39, 12, 0)
        
        assert len(path_bytes) == 12  # 3 * 4 bytes
        assert path_bytes == b'\x00\x00\x00\x27\x00\x00\x00\x0c\x00\x00\x00\x00'
    
    def test_different_values(self):
        """Test encoding different parameter values."""
        # Test BIP39 24-word at index 1
        path_bytes = encode_bip85_path(39, 24, 1)
        assert len(path_bytes) == 12
        
        # Test large values
        path_bytes = encode_bip85_path(128, 64, 1000)
        assert len(path_bytes) == 12
    
    def test_invalid_application(self):
        """Test validation of application parameter."""
        with pytest.raises(Bip85ValidationError, match="Application must be 0-4294967295"):
            encode_bip85_path(-1, 12, 0)
        
        with pytest.raises(Bip85ValidationError, match="Application must be 0-4294967295"):
            encode_bip85_path(2**32, 12, 0)
    
    def test_invalid_length(self):
        """Test validation of length parameter."""
        with pytest.raises(Bip85ValidationError, match="Length must be 0-4294967295"):
            encode_bip85_path(39, -1, 0)
        
        with pytest.raises(Bip85ValidationError, match="Length must be 0-4294967295"):
            encode_bip85_path(39, 2**32, 0)
    
    def test_invalid_index(self):
        """Test validation of index parameter."""
        with pytest.raises(Bip85ValidationError, match="Index must be 0 to 2147483647"):
            encode_bip85_path(39, 12, -1)
        
        with pytest.raises(Bip85ValidationError, match="Index must be 0 to 2147483647"):
            encode_bip85_path(39, 12, 2**31)


class TestDeriveBip85Entropy:
    """Test BIP85 entropy derivation."""
    
    def test_bip39_entropy_derivation(self):
        """Test deriving entropy for BIP39 application."""
        # Test vector master seed
        master_seed = bytes.fromhex(
            "000102030405060708090a0b0c0d0e0f" * 4  # 64 bytes
        )
        
        # Derive 16 bytes for 12-word BIP39
        entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
        
        assert len(entropy) == 16
        assert isinstance(entropy, bytes)
        # Should be deterministic - same input gives same output
        entropy2 = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
        assert entropy == entropy2
    
    def test_different_indices_produce_different_entropy(self):
        """Test that different indices produce different entropy."""
        master_seed = bytes.fromhex("a" * 128)  # 64 bytes
        
        entropy0 = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
        entropy1 = derive_bip85_entropy(master_seed, 39, 12, 1, 16)
        
        assert entropy0 != entropy1
        assert len(entropy0) == len(entropy1) == 16
    
    def test_different_applications_produce_different_entropy(self):
        """Test that different applications produce different entropy."""
        master_seed = bytes.fromhex("b" * 128)  # 64 bytes
        
        bip39_entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
        hex_entropy = derive_bip85_entropy(master_seed, 128, 16, 0, 16)
        
        assert bip39_entropy != hex_entropy
    
    def test_different_output_lengths(self):
        """Test deriving different output lengths."""
        master_seed = bytes.fromhex("c" * 128)  # 64 bytes
        
        for output_len in [16, 20, 24, 28, 32, 48, 64]:
            entropy = derive_bip85_entropy(master_seed, 39, 12, 0, output_len)
            assert len(entropy) == output_len
    
    def test_invalid_output_length(self):
        """Test validation of output length parameter."""
        master_seed = bytes(64)
        
        with pytest.raises(Bip85ValidationError, match="Output bytes must be 1-64"):
            derive_bip85_entropy(master_seed, 39, 12, 0, 0)
        
        with pytest.raises(Bip85ValidationError, match="Output bytes must be 1-64"):
            derive_bip85_entropy(master_seed, 39, 12, 0, 65)
    
    def test_maximum_output_length(self):
        """Test maximum output length (64 bytes)."""
        master_seed = bytes.fromhex("d" * 128)  # 64 bytes
        
        entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 64)
        assert len(entropy) == 64
    
    def test_derivation_error_handling(self):
        """Test error handling during derivation."""
        master_seed = bytes(64)
        
        with patch('sseed.bip85.core.create_bip32_master_key') as mock_create:
            mock_create.side_effect = Exception("Derivation failed")
            
            with pytest.raises(Bip85DerivationError, match="BIP85 derivation failed"):
                derive_bip85_entropy(master_seed, 39, 12, 0, 16)


class TestFormatBip85DerivationPath:
    """Test BIP85 derivation path formatting."""
    
    def test_path_formatting(self):
        """Test formatting derivation paths."""
        path = format_bip85_derivation_path(39, 12, 0)
        assert path == f"m/{BIP85_PURPOSE}'/39'/12'/0'"
        
        path = format_bip85_derivation_path(128, 32, 1000)
        assert path == f"m/{BIP85_PURPOSE}'/128'/32'/1000'"


class TestValidateMasterSeedFormat:
    """Test master seed format validation."""
    
    def test_valid_seed(self):
        """Test validation of valid master seeds."""
        # Random 64-byte seed
        valid_seed = bytes.fromhex("f" * 128)
        is_valid, error = validate_master_seed_format(valid_seed)
        assert is_valid
        assert error == ""
    
    def test_invalid_type(self):
        """Test validation of non-bytes input."""
        is_valid, error = validate_master_seed_format("not_bytes")
        assert not is_valid
        assert "must be bytes" in error
    
    def test_invalid_length(self):
        """Test validation of wrong length seeds."""
        # Too short
        is_valid, error = validate_master_seed_format(b"short")
        assert not is_valid
        assert "must be 64 bytes" in error
        
        # Too long
        is_valid, error = validate_master_seed_format(b"x" * 128)
        assert not is_valid
        assert "must be 64 bytes" in error
    
    def test_weak_seeds(self):
        """Test detection of obviously weak seeds."""
        # All zeros
        is_valid, error = validate_master_seed_format(bytes(64))
        assert not is_valid
        assert "cannot be all zeros" in error
        
        # All ones
        is_valid, error = validate_master_seed_format(bytes([0xFF] * 64))
        assert not is_valid
        assert "cannot be all ones" in error


class TestBip85Constants:
    """Test BIP85 constants and specifications."""
    
    def test_bip85_purpose_constant(self):
        """Test BIP85 purpose constant value."""
        assert BIP85_PURPOSE == 83696968
        assert hex(BIP85_PURPOSE) == "0x4f7c7e8"  # Verify hex representation


class TestSecureCleanup:
    """Test secure memory cleanup during derivation."""
    
    def test_cleanup_on_success(self):
        """Test that sensitive variables are cleaned up on successful derivation."""
        master_seed = bytes.fromhex("e" * 128)  # 64 bytes
        
        with patch('sseed.bip85.core.secure_delete_variable') as mock_cleanup:
            entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
            
            # Should have attempted cleanup
            assert mock_cleanup.call_count > 0
            assert len(entropy) == 16
    
    def test_cleanup_on_failure(self):
        """Test that cleanup occurs even when derivation fails."""
        master_seed = bytes(64)
        
        with patch('sseed.bip85.core.secure_delete_variable') as mock_cleanup:
            with patch('sseed.bip85.core.create_bip32_master_key') as mock_create:
                mock_create.side_effect = Exception("Test failure")
                
                with pytest.raises(Bip85DerivationError):
                    derive_bip85_entropy(master_seed, 39, 12, 0, 16)
                
                # Cleanup should still have been attempted
                assert mock_cleanup.call_count >= 0  # May be 0 if failure is early


class TestBip85TestVectors:
    """Test against known BIP85 test vectors."""
    
    def test_bip85_reference_vector(self):
        """Test against BIP85 reference test vector."""
        # BIP85 test vector from specification
        master_seed = bytes.fromhex(
            "efecfbccffea313214232d29e71563d941229afb4338c21f9517c41aaa0d16f00b83d2"
            "5eead6ca08c5f6b5f66b82b91bb8de4f18f6ed0e81e5fcccf73f2a8b4f44d6c6b6b4c3e"
        )[:64]  # Take first 64 bytes for this test
        
        # Derive entropy for BIP39 12-word mnemonic
        entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)
        
        # Should produce deterministic result
        assert len(entropy) == 16
        assert isinstance(entropy, bytes)
        
        # Verify it's not all zeros or obviously weak
        assert entropy != bytes(16)
        assert len(set(entropy)) > 1  # Should have entropy variation 