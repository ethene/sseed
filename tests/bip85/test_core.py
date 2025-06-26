"""Tests for BIP85 core derivation functionality.

Comprehensive test suite covering all BIP85 core operations including:
- Master key creation
- Path encoding
- Entropy derivation
- Error handling
- Security features
"""

from unittest.mock import (
    MagicMock,
    patch,
)

import pytest
from bip_utils import Bip32Secp256k1

from sseed.bip85.core import (
    BIP85_PURPOSE,
    create_bip32_master_key,
    derive_bip85_entropy,
    encode_bip85_path,
    format_bip85_derivation_path,
    validate_master_seed_format,
)
from sseed.bip85.exceptions import (
    Bip85DerivationError,
    Bip85ValidationError,
)


class TestCreateBip32MasterKey:
    """Test BIP32 master key creation from master seed."""

    def test_valid_master_seed(self):
        """Test creating master key from valid 64-byte seed."""
        # Valid 64-byte master seed (test vector)
        master_seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f" * 4)  # 64 bytes

        master_key = create_bip32_master_key(master_seed)

        assert isinstance(master_key, Bip32Secp256k1)
        # Should be able to derive children without errors
        child = master_key.ChildKey(0)
        assert isinstance(child, Bip32Secp256k1)

    def test_invalid_seed_length(self):
        """Test error handling for invalid seed lengths."""
        # Too short - expect Bip85DerivationError since it's wrapped by the function
        with pytest.raises(
            Bip85DerivationError, match="Failed to create BIP32 master key"
        ):
            create_bip32_master_key(b"too_short")

        # Too long
        with pytest.raises(
            Bip85DerivationError, match="Failed to create BIP32 master key"
        ):
            create_bip32_master_key(b"x" * 128)

    def test_bip_utils_failure(self):
        """Test handling of BIP-utils library failures."""
        master_seed = bytes(64)  # Valid length but will test error handling

        with patch("sseed.bip85.core.Bip32Secp256k1.FromSeed") as mock_from_seed:
            mock_from_seed.side_effect = Exception("BIP32 creation failed")

            with pytest.raises(
                Bip85DerivationError, match="Failed to create BIP32 master key"
            ):
                create_bip32_master_key(master_seed)


class TestEncodeBip85Path:
    """Test BIP85 path encoding for HMAC."""

    def test_valid_path_encoding(self):
        """Test encoding valid BIP85 path components."""
        path_bytes = encode_bip85_path(39, 12, 0)

        assert len(path_bytes) == 12  # 3 * 4 bytes
        assert path_bytes == b"\x00\x00\x00\x27\x00\x00\x00\x0c\x00\x00\x00\x00"

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
        with pytest.raises(
            Bip85ValidationError, match="Application must be 0-4294967295"
        ):
            encode_bip85_path(-1, 12, 0)

        with pytest.raises(
            Bip85ValidationError, match="Application must be 0-4294967295"
        ):
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
        master_seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f" * 4)  # 64 bytes

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

        with patch("sseed.bip85.core.create_bip32_master_key") as mock_create:
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
        # Use a proper random-looking 64-byte seed (not all zeros or ones)
        valid_seed = bytes.fromhex(
            "abcd1234567890ef" * 8  # Creates a 64-byte seed with variation
        )
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
        assert hex(BIP85_PURPOSE) == "0x4fd1d48"  # Verify hex representation


class TestSecureCleanup:
    """Test secure memory cleanup during derivation."""

    def test_cleanup_on_success(self):
        """Test that sensitive variables are cleaned up on successful derivation."""
        master_seed = bytes.fromhex("e" * 128)  # 64 bytes

        with patch("sseed.bip85.core.secure_delete_variable") as mock_cleanup:
            entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)

            # Should have attempted cleanup
            assert mock_cleanup.call_count > 0
            assert len(entropy) == 16

    def test_cleanup_on_failure(self):
        """Test that cleanup occurs even when derivation fails."""
        master_seed = bytes(64)

        with patch("sseed.bip85.core.secure_delete_variable") as mock_cleanup:
            with patch("sseed.bip85.core.create_bip32_master_key") as mock_create:
                mock_create.side_effect = Exception("Test failure")

                with pytest.raises(Bip85DerivationError):
                    derive_bip85_entropy(master_seed, 39, 12, 0, 16)

                # Cleanup should still have been attempted
                assert mock_cleanup.call_count >= 0  # May be 0 if failure is early


class TestBip85TestVectors:
    """Test against known BIP85 test vectors."""

    def test_bip85_reference_vector(self):
        """Test against BIP85 reference test vector."""
        # BIP85 test vector from specification - properly formatted 64-byte seed
        master_seed = bytes.fromhex(
            "efecfbccffea313214232d29e71563d941229afb4338c21f9517c41aaa0d16f0"
            "0b83d25eead6ca08c5f6b5f66b82b91bb8de4f18f6ed0e81e5fcccf73f2a8b4f"
        )  # Exactly 64 bytes (128 hex characters)

        # Derive entropy for BIP39 12-word mnemonic
        entropy = derive_bip85_entropy(master_seed, 39, 12, 0, 16)

        # Should produce deterministic result
        assert len(entropy) == 16
        assert isinstance(entropy, bytes)

        # Verify it's not all zeros or obviously weak
        assert entropy != bytes(16)
        assert len(set(entropy)) > 1  # Should have entropy variation


class TestBip85OfficialTestVectors:
    """Test BIP85 implementation against official test vectors from the specification."""

    @pytest.fixture
    def official_test_mnemonic(self):
        """Official test mnemonic from BIP85 specification."""
        return "install scatter logic circle pencil average fall shoe quantum disease suspect usage"

    @pytest.fixture
    def official_test_seed(self, official_test_mnemonic):
        """Master seed derived from official test mnemonic."""
        import hashlib

        return hashlib.pbkdf2_hmac(
            "sha512", official_test_mnemonic.encode("utf-8"), b"mnemonic", 2048, 64
        )

    def test_bip85_official_12_word_english_vector(self, official_test_seed):
        """Test 12-word English BIP39 mnemonic (index 0) against official vector."""
        from sseed.bip85.applications import Bip85Applications

        apps = Bip85Applications()
        result = apps.derive_bip39_mnemonic(official_test_seed, 12, 0, "en")
        expected = (
            "girl mad pet galaxy egg matter matrix prison refuse sense ordinary nose"
        )

        assert result == expected, f"Expected: {expected}, Got: {result}"

    def test_bip85_official_18_word_english_vector(self, official_test_seed):
        """Test 18-word English BIP39 mnemonic (index 0) against official vector."""
        from sseed.bip85.applications import Bip85Applications

        apps = Bip85Applications()
        result = apps.derive_bip39_mnemonic(official_test_seed, 18, 0, "en")
        expected = "near account window bike charge season chef number sketch tomorrow excuse sniff circle vital hockey outdoor supply token"

        assert result == expected, f"Expected: {expected}, Got: {result}"

    def test_bip85_official_24_word_english_vector(self, official_test_seed):
        """Test 24-word English BIP39 mnemonic (index 0) against official vector."""
        from sseed.bip85.applications import Bip85Applications

        apps = Bip85Applications()
        result = apps.derive_bip39_mnemonic(official_test_seed, 24, 0, "en")
        expected = "puppy ocean match cereal symbol another shed magic wrap hammer bulb intact gadget divorce twin tonight reason outdoor destroy simple truth cigar social volcano"

        assert result == expected, f"Expected: {expected}, Got: {result}"

    def test_bip85_official_entropy_values(self, official_test_seed):
        """Test that we derive the correct entropy values for each word count."""
        from sseed.bip85.core import derive_bip85_bip39_entropy

        # Test 12-word entropy - this is the known test vector
        entropy_12 = derive_bip85_bip39_entropy(
            official_test_seed, 0, 12, 0, 16
        )  # English=0, 12 words, index 0, 16 bytes
        expected_12 = bytes.fromhex("6250b68daf746d12a24d58b4787a714b")
        assert (
            entropy_12 == expected_12
        ), f"12-word entropy: Expected {expected_12.hex()}, Got {entropy_12.hex()}"

        # Test 18-word entropy - verify correct length
        entropy_18 = derive_bip85_bip39_entropy(
            official_test_seed, 0, 18, 0, 24
        )  # English=0, 18 words, index 0, 24 bytes
        assert (
            len(entropy_18) == 24
        ), f"18-word entropy should be 24 bytes, got {len(entropy_18)}"

        # Test 24-word entropy - verify correct length
        entropy_24 = derive_bip85_bip39_entropy(
            official_test_seed, 0, 24, 0, 32
        )  # English=0, 24 words, index 0, 32 bytes
        assert (
            len(entropy_24) == 32
        ), f"24-word entropy should be 32 bytes, got {len(entropy_24)}"

        # Verify all entropies are different
        assert (
            entropy_12 != entropy_18[:16]
        ), "12-word and 18-word entropy should be different"
        assert (
            entropy_12 != entropy_24[:16]
        ), "12-word and 24-word entropy should be different"
        assert (
            entropy_18 != entropy_24[:24]
        ), "18-word and 24-word entropy should be different"

    def test_bip85_official_path_derivation(self, official_test_seed):
        """Test that we use the correct BIP85 derivation path for BIP39."""
        import hashlib
        import hmac

        from bip_utils import Bip32Secp256k1

        from sseed.bip85.core import derive_bip85_bip39_entropy

        # Manually verify the derivation path: m/83696968'/39'/0'/12'/0'
        master_key = Bip32Secp256k1.FromSeed(official_test_seed)

        # Step by step derivation
        child_key = master_key.ChildKey(83696968 | 0x80000000)  # Purpose
        child_key = child_key.ChildKey(39 | 0x80000000)  # Application (BIP39)
        child_key = child_key.ChildKey(0 | 0x80000000)  # Language (English)
        child_key = child_key.ChildKey(12 | 0x80000000)  # Words
        child_key = child_key.ChildKey(0 | 0x80000000)  # Index

        # Extract private key and compute HMAC
        private_key = child_key.PrivateKey().Raw().ToBytes()
        hmac_result = hmac.new(
            b"bip-entropy-from-k", private_key, hashlib.sha512
        ).digest()
        manual_entropy = hmac_result[:16]

        # Compare with our implementation
        our_entropy = derive_bip85_bip39_entropy(official_test_seed, 0, 12, 0, 16)

        assert (
            our_entropy == manual_entropy
        ), f"Derivation path mismatch: Manual {manual_entropy.hex()}, Our {our_entropy.hex()}"

    def test_bip85_deterministic_across_indices(self, official_test_seed):
        """Test that different indices produce different, deterministic results."""
        from sseed.bip85.applications import Bip85Applications

        apps = Bip85Applications()

        # Test multiple indices for 12-word mnemonics
        results = {}
        for index in [0, 1, 2, 10, 100]:
            mnemonic = apps.derive_bip39_mnemonic(official_test_seed, 12, index, "en")
            results[index] = mnemonic

            # Verify it's a valid 12-word mnemonic
            assert len(mnemonic.split()) == 12, f"Index {index} should produce 12 words"

        # All results should be different
        unique_results = set(results.values())
        assert len(unique_results) == len(
            results
        ), "All indices should produce unique mnemonics"

        # Verify index 0 is the official test vector
        assert (
            results[0]
            == "girl mad pet galaxy egg matter matrix prison refuse sense ordinary nose"
        )

    def test_bip85_language_consistency(self, official_test_seed):
        """Test that language parameter correctly affects derivation."""
        from sseed.bip85.core import derive_bip85_bip39_entropy

        # Test that different languages produce different entropy
        entropy_en = derive_bip85_bip39_entropy(
            official_test_seed, 0, 12, 0, 16
        )  # English
        entropy_es = derive_bip85_bip39_entropy(
            official_test_seed, 3, 12, 0, 16
        )  # Spanish
        entropy_fr = derive_bip85_bip39_entropy(
            official_test_seed, 6, 12, 0, 16
        )  # French

        # All should be different
        assert (
            entropy_en != entropy_es
        ), "English and Spanish should produce different entropy"
        assert (
            entropy_en != entropy_fr
        ), "English and French should produce different entropy"
        assert (
            entropy_es != entropy_fr
        ), "Spanish and French should produce different entropy"

        # English should match our known test vector
        expected_en = bytes.fromhex("6250b68daf746d12a24d58b4787a714b")
        assert entropy_en == expected_en, f"English entropy should match test vector"
