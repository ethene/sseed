"""Tests for BIP85 application formatters.

Comprehensive test suite covering:
- BIP39 mnemonic generation in all supported languages
- Hex entropy generation with various byte lengths
- Password generation with different character sets
- Error handling and edge cases
- Integration with existing SSeed infrastructure
"""

import pytest
from unittest.mock import patch, MagicMock

from sseed.bip85.applications import Bip85Applications
from sseed.bip85.exceptions import Bip85ValidationError, Bip85ApplicationError
from sseed.languages import get_supported_language_codes


class TestBip85Applications:
    """Test BIP85 application formatters."""

    @pytest.fixture
    def apps(self):
        """Create BIP85 applications instance for testing."""
        return Bip85Applications()

    @pytest.fixture
    def test_master_seed(self):
        """Create test master seed (64 bytes)."""
        return bytes.fromhex("a" * 128)

    def test_init_creates_instance(self, apps):
        """Test Bip85Applications initialization."""
        assert isinstance(apps, Bip85Applications)

    # BIP39 Mnemonic Tests
    
    def test_derive_bip39_mnemonic_basic(self, apps, test_master_seed):
        """Test basic BIP39 mnemonic generation."""
        mnemonic = apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        
        words = mnemonic.split()
        assert len(words) == 12
        assert all(isinstance(word, str) for word in words)
        assert len(mnemonic) > 0

    def test_derive_bip39_mnemonic_all_word_counts(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation for all supported word counts."""
        valid_word_counts = [12, 15, 18, 21, 24]
        
        for word_count in valid_word_counts:
            mnemonic = apps.derive_bip39_mnemonic(test_master_seed, word_count, 0, "en")
            words = mnemonic.split()
            assert len(words) == word_count

    def test_derive_bip39_mnemonic_all_languages(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation in all supported languages."""
        available_languages = get_supported_language_codes()
        
        for language in available_languages:
            mnemonic = apps.derive_bip39_mnemonic(test_master_seed, 12, 0, language)
            words = mnemonic.split()
            assert len(words) == 12
            assert len(mnemonic) > 0

    def test_derive_bip39_mnemonic_different_indices(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation with different indices."""
        mnemonics = []
        
        for index in [0, 1, 2, 100, 1000]:
            mnemonic = apps.derive_bip39_mnemonic(test_master_seed, 12, index, "en")
            mnemonics.append(mnemonic)
        
        assert len(set(mnemonics)) == len(mnemonics)

    def test_derive_bip39_mnemonic_deterministic(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation is deterministic."""
        mnemonic1 = apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        mnemonic2 = apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        
        assert mnemonic1 == mnemonic2

    def test_derive_bip39_mnemonic_invalid_language(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation with invalid language."""
        with pytest.raises(Bip85ValidationError) as exc_info:
            apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "invalid")
        
        assert "Invalid language code" in str(exc_info.value)
        assert exc_info.value.parameter == "language"

    def test_derive_bip39_mnemonic_invalid_word_count(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation with invalid word count."""
        with pytest.raises(Bip85ValidationError):
            apps.derive_bip39_mnemonic(test_master_seed, 13, 0, "en")

    def test_derive_bip39_mnemonic_invalid_index(self, apps, test_master_seed):
        """Test BIP39 mnemonic generation with invalid index."""
        with pytest.raises(Bip85ValidationError):
            apps.derive_bip39_mnemonic(test_master_seed, 12, -1, "en")

    @patch('sseed.bip39.entropy_to_mnemonic')
    def test_derive_bip39_mnemonic_entropy_error(self, mock_entropy_to_mnemonic, apps, test_master_seed):
        """Test BIP39 mnemonic generation handles entropy conversion errors."""
        mock_entropy_to_mnemonic.side_effect = Exception("Entropy conversion failed")
        
        with pytest.raises(Bip85ApplicationError) as exc_info:
            apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        
        assert "BIP39 mnemonic generation failed" in str(exc_info.value)
        assert exc_info.value.application == "BIP39"

    # Hex Entropy Tests
    
    def test_derive_hex_entropy_basic(self, apps, test_master_seed):
        """Test basic hex entropy generation."""
        hex_entropy = apps.derive_hex_entropy(test_master_seed, 32, 0, False)
        
        assert isinstance(hex_entropy, str)
        assert len(hex_entropy) == 64  # 32 bytes = 64 hex chars
        assert all(c in "0123456789abcdef" for c in hex_entropy)

    def test_derive_hex_entropy_uppercase(self, apps, test_master_seed):
        """Test hex entropy generation with uppercase."""
        hex_lower = apps.derive_hex_entropy(test_master_seed, 32, 0, False)
        hex_upper = apps.derive_hex_entropy(test_master_seed, 32, 0, True)
        
        assert hex_lower.lower() == hex_upper.lower()
        assert hex_upper.isupper() or hex_upper.isdigit()

    def test_derive_hex_entropy_different_lengths(self, apps, test_master_seed):
        """Test hex entropy generation with different byte lengths."""
        test_lengths = [16, 24, 32, 48, 64]
        
        for byte_length in test_lengths:
            hex_entropy = apps.derive_hex_entropy(test_master_seed, byte_length, 0)
            assert len(hex_entropy) == byte_length * 2

    def test_derive_hex_entropy_different_indices(self, apps, test_master_seed):
        """Test hex entropy generation with different indices."""
        entropies = []
        
        for index in [0, 1, 2, 100, 1000]:
            entropy = apps.derive_hex_entropy(test_master_seed, 32, index)
            entropies.append(entropy)
        
        assert len(set(entropies)) == len(entropies)

    def test_derive_hex_entropy_deterministic(self, apps, test_master_seed):
        """Test hex entropy generation is deterministic."""
        entropy1 = apps.derive_hex_entropy(test_master_seed, 32, 0)
        entropy2 = apps.derive_hex_entropy(test_master_seed, 32, 0)
        
        assert entropy1 == entropy2

    def test_derive_hex_entropy_invalid_length(self, apps, test_master_seed):
        """Test hex entropy generation with invalid byte length."""
        with pytest.raises(Bip85ValidationError):
            apps.derive_hex_entropy(test_master_seed, 15, 0)  # Below minimum

        with pytest.raises(Bip85ValidationError):
            apps.derive_hex_entropy(test_master_seed, 65, 0)  # Above maximum

    # Password Generation Tests
    
    def test_derive_password_basic(self, apps, test_master_seed):
        """Test basic password generation."""
        password = apps.derive_password(test_master_seed, 20, 0, "base64")
        
        assert isinstance(password, str)
        assert len(password) == 20

    def test_derive_password_all_character_sets(self, apps, test_master_seed):
        """Test password generation with all character sets."""
        charsets = ["base64", "base85", "alphanumeric", "ascii"]
        
        for charset in charsets:
            password = apps.derive_password(test_master_seed, 20, 0, charset)
            assert len(password) == 20
            assert isinstance(password, str)

    def test_derive_password_character_set_validation(self, apps, test_master_seed):
        """Test password generation validates character sets correctly."""
        # Test base64 characters
        password = apps.derive_password(test_master_seed, 20, 0, "base64")
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/")
        assert all(c in valid_chars for c in password)

        # Test alphanumeric characters
        password = apps.derive_password(test_master_seed, 20, 0, "alphanumeric")
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        assert all(c in valid_chars for c in password)

    def test_derive_password_different_lengths(self, apps, test_master_seed):
        """Test password generation with different lengths."""
        test_lengths = [10, 20, 50, 100, 128]
        
        for length in test_lengths:
            password = apps.derive_password(test_master_seed, length, 0, "base64")
            assert len(password) == length

    def test_derive_password_different_indices(self, apps, test_master_seed):
        """Test password generation with different indices."""
        passwords = []
        
        for index in [0, 1, 2, 100, 1000]:
            password = apps.derive_password(test_master_seed, 20, index, "base64")
            passwords.append(password)
        
        assert len(set(passwords)) == len(passwords)

    def test_derive_password_deterministic(self, apps, test_master_seed):
        """Test password generation is deterministic."""
        password1 = apps.derive_password(test_master_seed, 20, 0, "base64")
        password2 = apps.derive_password(test_master_seed, 20, 0, "base64")
        
        assert password1 == password2

    def test_derive_password_invalid_character_set(self, apps, test_master_seed):
        """Test password generation with invalid character set."""
        with pytest.raises(Bip85ValidationError) as exc_info:
            apps.derive_password(test_master_seed, 20, 0, "invalid")
        
        assert "Invalid character set" in str(exc_info.value)
        assert exc_info.value.parameter == "character_set"

    def test_derive_password_invalid_length(self, apps, test_master_seed):
        """Test password generation with invalid length."""
        with pytest.raises(Bip85ValidationError):
            apps.derive_password(test_master_seed, 9, 0, "base64")  # Below minimum

        with pytest.raises(Bip85ValidationError):
            apps.derive_password(test_master_seed, 129, 0, "base64")  # Above maximum

    # Entropy to Password Conversion Tests
    
    def test_entropy_to_password_character_distribution(self, apps):
        """Test entropy to password conversion has reasonable character distribution."""
        test_entropy = bytes([i % 256 for i in range(32)])  # Predictable entropy
        
        password = apps._entropy_to_password(test_entropy, 100, "base64")
        
        # Should have reasonable character distribution
        unique_chars = set(password)
        assert len(unique_chars) > 10  # At least 10 different characters

    def test_entropy_to_password_long_passwords(self, apps):
        """Test entropy to password conversion handles long passwords."""
        test_entropy = bytes([42] * 64)  # Fixed entropy
        
        # Test password longer than entropy
        password = apps._entropy_to_password(test_entropy, 100, "base64")
        assert len(password) == 100

    # Application Info Tests
    
    def test_get_application_info_supported(self, apps):
        """Test getting information for supported applications."""
        info = apps.get_application_info(39)
        
        assert info["application"] == 39
        assert info["name"] == "BIP39 Mnemonic"
        assert info["supported"] is True
        assert "BIP39 mnemonic" in info["description"]

    def test_get_application_info_unsupported(self, apps):
        """Test getting information for unsupported applications."""
        info = apps.get_application_info(999)
        
        assert info["application"] == 999
        assert info["supported"] is False
        assert "Unknown application" in info["description"]

    def test_list_supported_applications(self, apps):
        """Test listing all supported applications."""
        supported = apps.list_supported_applications()
        
        assert len(supported) == 3  # BIP39, Hex, Password
        app_ids = [app["application"] for app in supported]
        assert 39 in app_ids  # BIP39
        assert 128 in app_ids  # Hex
        assert 9999 in app_ids  # Password

    # Edge Cases and Error Handling
    
    def test_master_seed_variations(self, apps):
        """Test applications work with different master seed formats."""
        # Test with different seed values
        seeds = [
            bytes([0] * 64),  # All zeros
            bytes([255] * 64),  # All ones
            bytes(range(64)),  # Sequential
            bytes([i % 256 for i in range(64)])  # Modular
        ]
        
        for seed in seeds:
            mnemonic = apps.derive_bip39_mnemonic(seed, 12, 0, "en")
            assert len(mnemonic.split()) == 12
            
            hex_entropy = apps.derive_hex_entropy(seed, 32, 0)
            assert len(hex_entropy) == 64
            
            password = apps.derive_password(seed, 20, 0, "base64")
            assert len(password) == 20

    @patch('sseed.bip85.applications.derive_bip85_entropy')
    def test_derive_bip85_entropy_error_handling(self, mock_derive, apps, test_master_seed):
        """Test error handling when BIP85 entropy derivation fails."""
        mock_derive.side_effect = Exception("Derivation failed")
        
        with pytest.raises(Bip85ApplicationError):
            apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        
        with pytest.raises(Bip85ApplicationError):
            apps.derive_hex_entropy(test_master_seed, 32, 0)
        
        with pytest.raises(Bip85ApplicationError):
            apps.derive_password(test_master_seed, 20, 0, "base64")

    def test_entropy_to_password_conversion_error(self, apps):
        """Test entropy to password conversion error handling."""
        with patch.object(apps, '_entropy_to_password') as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")
            
            with pytest.raises(Bip85ApplicationError) as exc_info:
                apps.derive_password(bytes([0] * 64), 20, 0, "base64")
            
            assert "Password generation failed" in str(exc_info.value)
            assert exc_info.value.application == "Password"

    # Security and Memory Tests
    
    def test_no_sensitive_data_in_exceptions(self, apps, test_master_seed):
        """Test that exceptions don't leak sensitive data."""
        try:
            apps.derive_bip39_mnemonic(test_master_seed, 13, 0, "en")  # Invalid word count
        except Bip85ValidationError as e:
            # Exception should not contain master seed
            assert test_master_seed.hex() not in str(e)
            assert "aaaa" not in str(e)  # Partial seed data

    def test_deterministic_across_instances(self, test_master_seed):
        """Test that results are deterministic across different instances."""
        apps1 = Bip85Applications()
        apps2 = Bip85Applications()
        
        mnemonic1 = apps1.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        mnemonic2 = apps2.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
        
        assert mnemonic1 == mnemonic2

    # Integration Tests
    
    def test_integration_with_existing_sseed_infrastructure(self, apps, test_master_seed):
        """Test integration with existing SSeed components."""
        # Test that multi-language support works
        languages = ["en", "es", "fr", "it"]
        
        for language in languages:
            mnemonic = apps.derive_bip39_mnemonic(test_master_seed, 12, 0, language)
            # Should use SSeed's existing BIP39 infrastructure
            assert len(mnemonic.split()) == 12

    def test_logging_and_security_events(self, apps, test_master_seed):
        """Test that operations are properly logged."""
        with patch('sseed.bip85.applications.log_security_event') as mock_log:
            apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en")
            
            # Should log security events for BIP85 operations
            assert mock_log.call_count >= 2  # Start and completion events 