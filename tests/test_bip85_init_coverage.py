"""Tests for BIP85 module initialization and package-level functions."""

import pytest

from sseed.bip85 import (
    Bip85Applications,
    create_optimized_bip85,
    create_standard_bip85,
    generate_bip39_mnemonic,
    generate_hex_entropy,
    generate_password,
    get_bip85_info,
)
from sseed.bip85.exceptions import (
    Bip85ApplicationError,
    Bip85ValidationError,
)


class TestBip85Init:
    """Test BIP85 package initialization and convenience functions."""

    def test_generate_bip39_mnemonic_function(self):
        """Test package-level generate_bip39_mnemonic function."""
        # Test master seed (64 bytes)
        master_seed = b"\x12\x34\x56\x78" * 16

        result = generate_bip39_mnemonic(
            master_seed=master_seed, word_count=12, index=0, language="en"
        )

        assert isinstance(result, str)
        assert len(result.split()) == 12

    def test_generate_bip39_mnemonic_invalid_params(self):
        """Test generate_bip39_mnemonic with invalid parameters."""
        master_seed = b"\x12\x34\x56\x78" * 16

        # Invalid word count
        with pytest.raises(Bip85ValidationError):
            generate_bip39_mnemonic(
                master_seed=master_seed,
                word_count=13,  # Invalid
                index=0,
                language="en",
            )

    def test_generate_hex_entropy_function(self):
        """Test package-level generate_hex_entropy function."""
        master_seed = b"\x12\x34\x56\x78" * 16

        result = generate_hex_entropy(
            master_seed=master_seed, byte_length=32, index=0, uppercase=False
        )

        assert isinstance(result, str)
        assert len(result) == 64  # 32 bytes = 64 hex chars
        assert result.islower()

    def test_generate_hex_entropy_uppercase(self):
        """Test generate_hex_entropy with uppercase option."""
        master_seed = b"\x12\x34\x56\x78" * 16

        result = generate_hex_entropy(
            master_seed=master_seed, byte_length=16, index=0, uppercase=True
        )

        assert isinstance(result, str)
        assert len(result) == 32  # 16 bytes = 32 hex chars
        assert result.isupper()

    def test_generate_hex_entropy_invalid_params(self):
        """Test generate_hex_entropy with invalid parameters."""
        master_seed = b"\x12\x34\x56\x78" * 16

        # Invalid byte length
        with pytest.raises(Bip85ValidationError):
            generate_hex_entropy(
                master_seed=master_seed, byte_length=8, index=0  # Too small
            )

    def test_generate_password_function(self):
        """Test package-level generate_password function."""
        master_seed = b"\x12\x34\x56\x78" * 16

        result = generate_password(
            master_seed=master_seed, length=20, index=0, character_set="base64"
        )

        assert isinstance(result, str)
        assert len(result) == 20

    def test_generate_password_different_charsets(self):
        """Test generate_password with different character sets."""
        master_seed = b"\x12\x34\x56\x78" * 16
        charsets = ["base64", "alphanumeric"]  # Only test supported ones

        for charset in charsets:
            result = generate_password(
                master_seed=master_seed, length=16, index=0, character_set=charset
            )

            assert isinstance(result, str)
            assert len(result) == 16

    def test_generate_password_invalid_params(self):
        """Test generate_password with invalid parameters."""
        master_seed = b"\x12\x34\x56\x78" * 16

        # Invalid length
        with pytest.raises(Bip85ValidationError):
            generate_password(
                master_seed=master_seed,
                length=5,  # Too short
                index=0,
                character_set="base64",
            )

    def test_get_bip85_info_function(self):
        """Test package-level get_bip85_info function."""
        info = get_bip85_info()

        assert isinstance(info, dict)
        assert "version" in info
        assert "description" in info
        assert "features" in info
        assert "performance" in info

        # Check features structure
        features = info["features"]
        assert "applications" in features
        assert "optimization" in features
        assert "compliance" in features

        # Check applications
        apps = features["applications"]
        assert "bip39" in apps
        assert "hex" in apps
        assert "password" in apps

    def test_create_standard_bip85(self):
        """Test create_standard_bip85 function."""
        apps = create_standard_bip85()
        assert isinstance(apps, Bip85Applications)

        # Verify it has expected methods
        assert hasattr(apps, "derive_bip39_mnemonic")
        assert hasattr(apps, "derive_hex_entropy")
        assert hasattr(apps, "derive_password")

    def test_create_optimized_bip85(self):
        """Test create_optimized_bip85 function."""
        apps = create_optimized_bip85()
        assert apps is not None

        # Test with caching disabled
        apps_no_cache = create_optimized_bip85(enable_caching=False)
        assert apps_no_cache is not None

    def test_applications_class_import(self):
        """Test that Bip85Applications class is properly imported."""
        apps = Bip85Applications()
        assert apps is not None

        # Verify it has expected methods
        assert hasattr(apps, "derive_bip39_mnemonic")
        assert hasattr(apps, "derive_hex_entropy")
        assert hasattr(apps, "derive_password")

    def test_convenience_functions_match_class_methods(self):
        """Test that convenience functions produce same results as class methods."""
        master_seed = b"\x12\x34\x56\x78" * 16
        apps = Bip85Applications()

        # Test BIP39 mnemonic
        func_result = generate_bip39_mnemonic(master_seed, 12, 0, "en")
        class_result = apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")
        assert func_result == class_result

        # Test hex entropy
        func_result = generate_hex_entropy(master_seed, 32, 0, False)
        class_result = apps.derive_hex_entropy(master_seed, 32, 0, False)
        assert func_result == class_result

        # Test password
        func_result = generate_password(master_seed, 20, 0, "base64")
        class_result = apps.derive_password(master_seed, 20, 0, "base64")
        assert func_result == class_result

    def test_error_propagation(self):
        """Test that errors are properly propagated from convenience functions."""
        invalid_seed = b"\x12\x34"  # Too short

        # Test that each function properly propagates validation errors
        with pytest.raises((Bip85ValidationError, Bip85ApplicationError)):
            generate_bip39_mnemonic(invalid_seed, 12, 0, "en")

        with pytest.raises((Bip85ValidationError, Bip85ApplicationError)):
            generate_hex_entropy(invalid_seed, 32, 0, False)

        with pytest.raises((Bip85ValidationError, Bip85ApplicationError)):
            generate_password(invalid_seed, 20, 0, "base64")

    def test_different_indices(self):
        """Test that different indices produce different results."""
        master_seed = b"\x12\x34\x56\x78" * 16

        # Test with different indices
        result1 = generate_bip39_mnemonic(master_seed, 12, 0, "en")
        result2 = generate_bip39_mnemonic(master_seed, 12, 1, "en")

        assert result1 != result2  # Different indices should produce different results

        # Same for hex entropy
        hex1 = generate_hex_entropy(master_seed, 32, 0)
        hex2 = generate_hex_entropy(master_seed, 32, 1)

        assert hex1 != hex2

    def test_different_languages(self):
        """Test BIP39 generation in different languages."""
        master_seed = b"\x12\x34\x56\x78" * 16
        languages = ["en", "es", "fr"]  # Only test supported languages

        results = {}
        for lang in languages:
            result = generate_bip39_mnemonic(master_seed, 12, 0, lang)
            results[lang] = result
            assert isinstance(result, str)
            assert len(result.split()) == 12

        # Different languages should produce different mnemonics
        unique_results = set(results.values())
        assert len(unique_results) == len(languages)

    def test_factory_functions_work(self):
        """Test that factory functions create working instances."""
        master_seed = b"\x12\x34\x56\x78" * 16

        # Test standard implementation
        standard_apps = create_standard_bip85()
        result1 = standard_apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")

        # Test optimized implementation
        optimized_apps = create_optimized_bip85()
        result2 = optimized_apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")

        # Both should work and produce valid results
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert len(result1.split()) == 12
        assert len(result2.split()) == 12

    def test_info_function_completeness(self):
        """Test that info function provides comprehensive information."""
        info = get_bip85_info()

        # Check all required top-level keys
        required_keys = ["version", "description", "author", "features", "performance"]
        for key in required_keys:
            assert key in info

        # Check feature completeness
        features = info["features"]
        assert "applications" in features
        assert "optimization" in features
        assert "compliance" in features

        # Check application support
        applications = features["applications"]
        for app_type in ["bip39", "hex", "password"]:
            assert app_type in applications
            assert applications[app_type]["supported"] is True
