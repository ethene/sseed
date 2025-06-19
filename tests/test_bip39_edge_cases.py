"""Comprehensive BIP39 edge case tests for sseed."""

from unittest.mock import MagicMock, patch

import pytest

from sseed.bip39 import (generate_mnemonic, get_mnemonic_entropy,
                         parse_mnemonic, validate_mnemonic)
from sseed.exceptions import EntropyError, MnemonicError


class TestBip39EdgeCases:
    """Comprehensive BIP39 edge case tests."""

    def test_generate_mnemonic_entropy_failure(self):
        """Test mnemonic generation when entropy generation fails."""
        with patch(
            "sseed.bip39.generate_entropy_bytes",
            side_effect=EntropyError("Entropy failed"),
        ):
            with pytest.raises(EntropyError):
                generate_mnemonic()

    def test_generate_mnemonic_bip_utils_failure(self):
        """Test mnemonic generation when bip_utils fails."""
        with patch("sseed.bip39.generate_entropy_bytes", return_value=b"x" * 32):
            with patch("sseed.bip39.Bip39MnemonicGenerator") as mock_gen:
                mock_gen.return_value.FromEntropy.side_effect = Exception(
                    "BIP utils failed"
                )
                with pytest.raises(
                    MnemonicError, match="Failed to generate BIP-39 mnemonic"
                ):
                    generate_mnemonic()

    def test_generate_mnemonic_wrong_word_count(self):
        """Test mnemonic generation with wrong word count."""
        with patch("sseed.bip39.generate_entropy_bytes", return_value=b"x" * 32):
            # Mock bip_utils to return mnemonic with wrong word count
            mock_mnemonic = MagicMock()
            mock_mnemonic.__str__ = MagicMock(return_value="too few words")

            with patch("sseed.bip39.Bip39MnemonicGenerator") as mock_gen:
                mock_gen.return_value.FromEntropy.return_value = mock_mnemonic
                with pytest.raises(
                    MnemonicError, match="Generated mnemonic has 3 words, expected 24"
                ):
                    generate_mnemonic()

    def test_generate_mnemonic_validation_failure(self):
        """Test mnemonic generation when validation fails."""
        with patch("sseed.bip39.generate_entropy_bytes", return_value=b"x" * 32):
            # Mock to generate invalid mnemonic
            mock_mnemonic = MagicMock()
            mock_mnemonic.__str__ = MagicMock(return_value="abandon " * 24)

            with patch("sseed.bip39.Bip39MnemonicGenerator") as mock_gen:
                mock_gen.return_value.FromEntropy.return_value = mock_mnemonic
                with patch("sseed.bip39.validate_mnemonic_words"):
                    with patch("sseed.bip39.Bip39MnemonicValidator") as mock_val:
                        mock_val.return_value.IsValid.return_value = False
                        with pytest.raises(
                            MnemonicError,
                            match="Generated mnemonic failed BIP-39 checksum validation",
                        ):
                            generate_mnemonic()

    def test_generate_mnemonic_word_validation_failure(self):
        """Test mnemonic generation when word validation fails."""
        with patch("sseed.bip39.generate_entropy_bytes", return_value=b"x" * 32):
            mock_mnemonic = MagicMock()
            mock_mnemonic.__str__ = MagicMock(return_value="abandon " * 24)

            with patch("sseed.bip39.Bip39MnemonicGenerator") as mock_gen:
                mock_gen.return_value.FromEntropy.return_value = mock_mnemonic
                with patch(
                    "sseed.bip39.validate_mnemonic_words",
                    side_effect=Exception("Word validation failed"),
                ):
                    with pytest.raises(
                        MnemonicError, match="Failed to generate BIP-39 mnemonic"
                    ):
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
            "sseed.bip39.normalize_input", side_effect=Exception("Normalization failed")
        ):
            with pytest.raises(MnemonicError, match="Error during mnemonic validation"):
                validate_mnemonic("test input")

    def test_validate_mnemonic_word_validation_failure(self):
        """Test mnemonic validation when word validation fails."""
        with patch("sseed.bip39.normalize_input", return_value="test mnemonic"):
            with patch(
                "sseed.bip39.validate_mnemonic_words",
                side_effect=Exception("Word validation failed"),
            ):
                with pytest.raises(
                    MnemonicError, match="Error during mnemonic validation"
                ):
                    validate_mnemonic("test mnemonic")

    def test_parse_mnemonic_empty_input(self):
        """Test mnemonic parsing with empty input."""
        with pytest.raises(MnemonicError, match="Empty mnemonic provided"):
            parse_mnemonic("")

    def test_parse_mnemonic_normalization_failure(self):
        """Test mnemonic parsing when normalization fails."""
        with patch(
            "sseed.bip39.normalize_input", side_effect=Exception("Normalization failed")
        ):
            with pytest.raises(MnemonicError, match="Failed to parse mnemonic"):
                parse_mnemonic("test input")

    def test_parse_mnemonic_validation_failure(self):
        """Test mnemonic parsing when validation fails."""
        with patch("sseed.bip39.normalize_input", return_value="test mnemonic"):
            with patch(
                "sseed.bip39.validate_mnemonic_words",
                side_effect=Exception("Validation failed"),
            ):
                with pytest.raises(MnemonicError, match="Failed to parse mnemonic"):
                    parse_mnemonic("test input")

    def test_get_mnemonic_entropy_invalid_mnemonic(self):
        """Test entropy extraction from invalid mnemonic."""
        with patch("sseed.bip39.validate_mnemonic", return_value=False):
            with pytest.raises(
                MnemonicError, match="Cannot extract entropy from invalid mnemonic"
            ):
                get_mnemonic_entropy("invalid mnemonic")

    def test_get_mnemonic_entropy_decoder_failure(self):
        """Test entropy extraction when decoder fails."""
        with patch("sseed.bip39.validate_mnemonic", return_value=True):
            with patch("sseed.bip39.normalize_input", return_value="valid mnemonic"):
                with patch("sseed.bip39.Bip39MnemonicDecoder") as mock_decoder:
                    mock_decoder.return_value.Decode.side_effect = Exception(
                        "Decoder failed"
                    )
                    with pytest.raises(
                        MnemonicError, match="Failed to extract entropy from mnemonic"
                    ):
                        get_mnemonic_entropy("valid mnemonic")

    def test_get_mnemonic_entropy_exception_handling(self):
        """Test entropy extraction general exception handling."""
        with patch(
            "sseed.bip39.validate_mnemonic",
            side_effect=Exception("Validation exception"),
        ):
            with pytest.raises(
                MnemonicError, match="Failed to extract entropy from mnemonic"
            ):
                get_mnemonic_entropy("any input")

    def test_validate_mnemonic_bip_utils_exception(self):
        """Test mnemonic validation when bip_utils raises exception."""
        with patch("sseed.bip39.normalize_input", return_value="test mnemonic"):
            with patch("sseed.bip39.validate_mnemonic_words"):
                with patch("sseed.bip39.Bip39MnemonicValidator") as mock_val:
                    mock_val.return_value.IsValid.side_effect = Exception(
                        "BIP utils failed"
                    )
                    with pytest.raises(
                        MnemonicError, match="Error during mnemonic validation"
                    ):
                        validate_mnemonic("test mnemonic")
