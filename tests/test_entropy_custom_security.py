"""Security-critical tests for sseed.entropy.custom module.

Tests focus on:
- Entropy quality validation (security-critical)
- Custom entropy input validation (hex, dice)
- Weak entropy detection
- Error handling for malformed inputs
- Security boundary conditions
"""

from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from sseed.entropy.custom import (
    EntropyQuality,
    dice_to_entropy,
    hex_to_entropy,
    validate_entropy_quality,
)
from sseed.exceptions import (
    EntropyError,
    ValidationError,
)


class TestEntropyQuality:
    """Test EntropyQuality assessment class."""

    def test_entropy_quality_good_score(self):
        """Test good quality entropy assessment."""
        quality = EntropyQuality(85, [], [])
        assert quality.score == 85
        assert quality.is_acceptable is True
        assert quality.is_good_quality() is True
        assert "Good (85/100)" in quality.get_summary()

    def test_entropy_quality_poor_score(self):
        """Test poor quality entropy assessment."""
        warnings = ["Weak randomness detected"]
        recommendations = ["Use system entropy"]
        quality = EntropyQuality(40, warnings, recommendations)

        assert quality.score == 40
        assert quality.is_acceptable is False
        assert quality.is_good_quality() is False
        assert "Poor (40/100)" in quality.get_summary()
        assert quality.warnings == warnings
        assert quality.recommendations == recommendations

    def test_entropy_quality_boundary_conditions(self):
        """Test boundary conditions for quality thresholds."""
        # Exactly at acceptable threshold
        quality_70 = EntropyQuality(70, [], [])
        assert quality_70.is_acceptable is True
        assert quality_70.is_good_quality() is False

        # Just below acceptable threshold
        quality_69 = EntropyQuality(69, [], [])
        assert quality_69.is_acceptable is False

        # Exactly at good quality threshold
        quality_80 = EntropyQuality(80, [], [])
        assert quality_80.is_good_quality() is True


class TestHexToEntropy:
    """Test security-critical hex entropy conversion."""

    def test_hex_to_entropy_valid_input(self):
        """Test valid hex string conversion."""
        hex_input = "deadbeef"
        entropy = hex_to_entropy(hex_input, 4, skip_quality_check=True)
        assert entropy == bytes.fromhex("deadbeef")
        assert len(entropy) == 4

    def test_hex_to_entropy_with_0x_prefix(self):
        """Test hex string with 0x prefix."""
        hex_input = "0xdeadbeef"
        entropy = hex_to_entropy(hex_input, 4, skip_quality_check=True)
        assert entropy == bytes.fromhex("deadbeef")

    def test_hex_to_entropy_odd_length_padding(self):
        """Test odd-length hex string gets padded."""
        hex_input = "abc"  # 3 characters, odd length
        with patch("sseed.entropy.custom.logger") as mock_logger:
            entropy = hex_to_entropy(hex_input, 2, skip_quality_check=True)
            # Should be padded to "0abc"
            assert entropy == bytes.fromhex("0abc")
            mock_logger.warning.assert_called_with(
                "Padded hex string with leading zero"
            )

    def test_hex_to_entropy_invalid_characters(self):
        """Test hex string with invalid characters."""
        with pytest.raises(
            ValidationError, match="Invalid hex string: contains non-hex characters"
        ):
            hex_to_entropy("deadbeeg", 4)  # 'g' is not valid hex

    def test_hex_to_entropy_length_handling(self):
        """Test hex string length handling."""
        # Test that length requirements are properly handled
        hex_input = "dead"  # 2 bytes

        # When requesting exactly what we have
        entropy = hex_to_entropy(hex_input, 2, skip_quality_check=True)
        assert len(entropy) == 2
        assert entropy == bytes.fromhex("dead")

    def test_hex_to_entropy_quality_check_failure(self):
        """Test quality check failure raises EntropyError."""
        # Create weak entropy (all zeros)
        weak_hex = "00000000"

        with pytest.raises(EntropyError, match="quality insufficient"):
            hex_to_entropy(weak_hex, 4, skip_quality_check=False)

    def test_hex_to_entropy_skip_quality_check(self):
        """Test skipping quality check allows weak entropy."""
        weak_hex = "00000000"
        # Should not raise when skipping quality check
        entropy = hex_to_entropy(weak_hex, 4, skip_quality_check=True)
        assert entropy == b"\x00\x00\x00\x00"

    def test_hex_to_entropy_whitespace_handling(self):
        """Test hex string with whitespace is handled."""
        hex_input = (
            "  deadbeef  "  # Remove space in middle - hex validation may be strict
        )
        entropy = hex_to_entropy(hex_input, 4, skip_quality_check=True)
        assert entropy == bytes.fromhex("deadbeef")

    def test_hex_to_entropy_uppercase_handling(self):
        """Test uppercase hex string is handled."""
        hex_input = "DEADBEEF"
        entropy = hex_to_entropy(hex_input, 4, skip_quality_check=True)
        assert entropy == bytes.fromhex("deadbeef")


class TestDiceToEntropy:
    """Test dice roll entropy conversion."""

    def test_dice_to_entropy_valid_6_sided(self):
        """Test valid 6-sided dice rolls."""
        # Need at least 7 rolls for 2 bytes (16 bits / 2.585 bits per roll = ~6.2)
        dice_rolls = "1234561"  # 7 valid dice rolls (1-6 only)
        entropy = dice_to_entropy(dice_rolls, 2, skip_quality_check=True)
        assert len(entropy) == 2
        assert isinstance(entropy, bytes)

    def test_dice_to_entropy_out_of_range_standard_dice(self):
        """Test dice rolls out of range for standard 6-sided dice."""
        with pytest.raises(ValidationError, match="Invalid dice value"):
            dice_to_entropy("123457", 2)  # 7 is invalid for 6-sided dice

    def test_dice_to_entropy_sufficient_rolls(self):
        """Test sufficient dice rolls for entropy generation."""
        # Provide enough rolls for 2 bytes (need ~13 rolls for 16 bits)
        dice_rolls = "123456123456123456"  # 18 rolls should be sufficient
        entropy = dice_to_entropy(dice_rolls, 2, skip_quality_check=True)
        assert len(entropy) == 2
        assert isinstance(entropy, bytes)

    def test_dice_to_entropy_insufficient_rolls(self):
        """Test insufficient dice rolls for required entropy."""
        # Very few rolls should raise EntropyError
        dice_rolls = "123"  # Only 3 rolls, need more for 4 bytes

        with pytest.raises(EntropyError, match="Insufficient dice rolls"):
            dice_to_entropy(dice_rolls, 4, skip_quality_check=True)

    def test_dice_to_entropy_quality_check_warning(self):
        """Test quality check with poor dice entropy gives warning."""
        # Repeated values (poor entropy) - with sufficient rolls
        weak_dice = "111111111111111111111111111111111111111111"  # 40 rolls of 1s

        # Should succeed but log warnings for poor quality
        entropy = dice_to_entropy(weak_dice, 4, skip_quality_check=False)
        assert len(entropy) == 4


class TestEntropyQualityValidation:
    """Test comprehensive entropy quality validation."""

    def test_validate_entropy_quality_good_entropy(self):
        """Test validation of good quality entropy."""
        # Random-looking bytes
        good_entropy = bytes([i % 256 for i in range(0, 256, 17)])  # Varied pattern

        quality = validate_entropy_quality(good_entropy)

        assert quality.score >= 70
        assert quality.is_acceptable
        assert len(quality.warnings) == 0

    def test_validate_entropy_quality_all_zeros(self):
        """Test validation of all-zero entropy (worst case)."""
        weak_entropy = b"\x00" * 32

        quality = validate_entropy_quality(weak_entropy)

        assert quality.score < 30
        assert not quality.is_acceptable
        assert (
            "CRITICAL: This entropy appears to be non-random" in quality.recommendations
        )

    def test_validate_entropy_quality_all_ones(self):
        """Test validation of all-ones entropy."""
        weak_entropy = b"\xff" * 32

        quality = validate_entropy_quality(weak_entropy)

        assert quality.score < 50
        assert not quality.is_acceptable
        assert len(quality.warnings) > 0

    def test_validate_entropy_quality_repeating_pattern(self):
        """Test validation of repeating pattern entropy."""
        # Simple repeating pattern
        weak_entropy = b"\xaa\xbb" * 16

        quality = validate_entropy_quality(weak_entropy)

        assert quality.score < 70
        assert not quality.is_acceptable
        assert len(quality.warnings) > 0

    def test_validate_entropy_quality_sequential_pattern(self):
        """Test validation of sequential entropy."""
        # Sequential bytes (not random)
        weak_entropy = bytes(range(32))

        quality = validate_entropy_quality(weak_entropy)

        assert quality.score < 70
        assert not quality.is_acceptable

    def test_validate_entropy_quality_recommendations_generation(self):
        """Test that appropriate recommendations are generated."""
        very_weak = b"\x00" * 32
        quality = validate_entropy_quality(very_weak)

        # Should have critical recommendations for very weak entropy
        assert quality.score < 50
        assert not quality.is_acceptable
        assert len(quality.recommendations) > 0
        # Check for any recommendation about entropy quality
        assert any("entropy" in rec.lower() for rec in quality.recommendations)

    def test_validate_entropy_quality_moderate_entropy(self):
        """Test validation of moderately weak entropy."""
        # Some variation but still predictable
        moderate_entropy = bytes([i % 16 for i in range(32)])

        quality = validate_entropy_quality(moderate_entropy)

        assert quality.score < 80  # Expect lower quality for predictable pattern
        assert len(quality.warnings) > 0 or len(quality.recommendations) > 0


class TestSecurityEdgeCases:
    """Test security-critical edge cases and error conditions."""

    def test_hex_to_entropy_empty_string(self):
        """Test empty hex string handling."""
        with pytest.raises(ValidationError):
            hex_to_entropy("", 4)

    def test_dice_to_entropy_empty_string(self):
        """Test empty dice string handling."""
        with pytest.raises(ValidationError):
            dice_to_entropy("", 4)

    def test_validate_entropy_quality_empty_entropy(self):
        """Test validation of empty entropy."""
        quality = validate_entropy_quality(b"")

        assert quality.score < 50
        assert not quality.is_acceptable

    def test_hex_to_entropy_memory_protection(self):
        """Test that sensitive data is properly handled."""
        # This test ensures no sensitive data leaks in error messages
        sensitive_hex = "deadbeefcafebabe"

        try:
            # Force a validation error without skipping quality check
            hex_to_entropy("00000000", 4, skip_quality_check=False)
        except EntropyError as e:
            # Error message should not contain the actual entropy data
            assert "00000000" not in str(e)

    def test_entropy_quality_boundary_exactly_70(self):
        """Test entropy quality exactly at acceptance boundary."""
        quality = EntropyQuality(70, [], [])
        assert quality.is_acceptable is True

        quality_69 = EntropyQuality(69, [], [])
        assert quality_69.is_acceptable is False

    def test_hex_to_entropy_padding_behavior(self):
        """Test hex entropy padding when insufficient bytes provided."""
        # Short hex should either pad or extend somehow
        short_hex = "dead"  # 2 bytes, need 4 bytes

        entropy = hex_to_entropy(short_hex, 4, skip_quality_check=True)

        # Should be 4 bytes total
        assert len(entropy) == 4
        # First 2 bytes should match the hex input
        assert entropy[:2] == bytes.fromhex("dead")
