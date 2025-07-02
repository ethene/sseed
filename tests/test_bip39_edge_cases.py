"""Comprehensive BIP39 edge case tests for sseed."""

from unittest.mock import patch

import pytest

from sseed.bip39 import (
    generate_mnemonic,
    get_mnemonic_entropy,
    parse_mnemonic,
    validate_mnemonic,
)
from sseed.exceptions import (
    CryptoError,
    MnemonicError,
)


class TestBip39EdgeCases:
    """Comprehensive BIP39 edge case tests."""

    def test_generate_mnemonic_bip_utils_failure(self):
        """Test mnemonic generation when bip_utils fails."""
        with patch("sseed.bip39.Bip39MnemonicGenerator") as mock_gen:
            mock_gen.return_value.FromWordsNumber.side_effect = Exception(
                "BIP utils failed"
            )
            with pytest.raises(CryptoError, match="Failed to generate mnemonic"):
                generate_mnemonic()

    def test_generate_mnemonic_empty_result(self):
        """Test mnemonic generation when empty result is returned."""
        with patch("sseed.bip39.entropy_to_mnemonic") as mock_entropy_to_mnemonic:
            mock_entropy_to_mnemonic.return_value = ""
            with pytest.raises(CryptoError, match="Generated mnemonic is empty"):
                generate_mnemonic()

    def test_validate_mnemonic_empty_input(self):
        """Test mnemonic validation with empty input."""
        result = validate_mnemonic("")
        assert result is False

    def test_validate_mnemonic_whitespace_only(self):
        """Test mnemonic validation with whitespace only."""
        result = validate_mnemonic("   ")
        assert result is False

    def test_validate_mnemonic_exception_handling(self):
        """Test mnemonic validation exception handling."""
        with patch(
            "sseed.bip39._normalize_mnemonic",
            side_effect=Exception("Normalization failed"),
        ):
            result = validate_mnemonic("test input")
            assert result is False

    def test_validate_mnemonic_bip_utils_exception(self):
        """Test mnemonic validation when bip_utils raises exception."""
        with patch("sseed.bip39.Bip39MnemonicValidator") as mock_val:
            mock_val.return_value.IsValid.side_effect = Exception("BIP utils failed")
            result = validate_mnemonic("test mnemonic")
            assert result is False

    def test_parse_mnemonic_empty_input(self):
        """Test mnemonic parsing with empty input."""
        with pytest.raises(MnemonicError, match="Mnemonic cannot be empty"):
            parse_mnemonic("")

    def test_parse_mnemonic_normalization_failure(self):
        """Test mnemonic parsing when normalization fails."""
        with patch(
            "sseed.bip39._normalize_mnemonic",
            side_effect=MnemonicError("Normalization failed"),
        ):
            with pytest.raises(MnemonicError, match="Normalization failed"):
                parse_mnemonic("test input")

    def test_parse_mnemonic_validation_failure(self):
        """Test mnemonic parsing when validation fails."""
        with patch("sseed.bip39._normalize_mnemonic", return_value="test mnemonic"):
            with patch("sseed.bip39.validate_mnemonic", return_value=False):
                with pytest.raises(MnemonicError, match="Invalid mnemonic"):
                    parse_mnemonic("test input")

    def test_get_mnemonic_entropy_invalid_mnemonic(self):
        """Test entropy extraction from invalid mnemonic."""
        with patch("sseed.bip39.validate_mnemonic", return_value=False):
            with pytest.raises(
                MnemonicError, match="Cannot extract entropy from invalid mnemonic"
            ):
                get_mnemonic_entropy("invalid mnemonic")

    def test_get_mnemonic_entropy_decoder_failure(self):
        """Test entropy extraction when hash operation fails."""
        with patch("sseed.bip39.validate_mnemonic", return_value=True):
            with patch(
                "sseed.bip39._normalize_mnemonic", return_value="valid mnemonic"
            ):
                with patch("sseed.bip39.hashlib.sha256") as mock_hash:
                    mock_hash.side_effect = Exception("Hash failed")
                    with pytest.raises(
                        MnemonicError, match="Failed to extract entropy"
                    ):
                        get_mnemonic_entropy("valid mnemonic")

    def test_get_mnemonic_entropy_exception_handling(self):
        """Test entropy extraction general exception handling."""
        with patch(
            "sseed.bip39.validate_mnemonic",
            side_effect=Exception("Validation exception"),
        ):
            with pytest.raises(MnemonicError, match="Failed to extract entropy"):
                get_mnemonic_entropy("any input")
